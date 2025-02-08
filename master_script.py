#!/usr/bin/env python
import subprocess
import time
import sys
import asyncio
import simpleobsws
import keyboard
import os
from datetime import datetime

# Configuration OBS
OBS_HOST = "192.168.1.32"  # Modification de localhost vers l'IP spécifique
OBS_PORT = 4444
OBS_PASSWORD = "mVKiAVwWbz2nGBnW"  # Remplace "secret" par ton mot de passe OBS si nécessaire

# Chemin vers ton script de télémétrie
GET_INPUTS_SCRIPT = "get_inputs.py"  # Assure-toi que le script se trouve dans le même dossier ou ajuste le chemin

# Création du dossier de session
BASE_DIR = "ac_telemetry_data"
SESSION_DIR = os.path.join(BASE_DIR, datetime.now().strftime("%Y%m%d_%H%M%S"))

async def start_obs_recording():
    """
    Se connecte à OBS via obs-websocket et démarre l'enregistrement.
    """
    print(f"Tentative de connexion à OBS sur {OBS_HOST}:{OBS_PORT}")
    
    ws = simpleobsws.WebSocketClient(
        url=f"ws://{OBS_HOST}:{OBS_PORT}",
        password=OBS_PASSWORD
    )
    
    try:
        await ws.connect()
        await ws.wait_until_identified()
        print("Connexion établie avec succès")
        
        # Configurer OBS pour un enregistrement à 30 FPS
        settings_request = simpleobsws.Request('SetVideoSettings', requestData={
            'fpsNumerator': 30,
            'fpsDenominator': 1,
            'baseWidth': 1920,
            'baseHeight': 1080,
            'outputWidth': 1920,
            'outputHeight': 1080
        })
        await ws.call(settings_request)
        
        # Créer le chemin absolu pour la vidéo
        video_path = os.path.abspath(os.path.join(SESSION_DIR, "session_recording.mkv"))
        print(f"Chemin d'enregistrement configuré : {video_path}")
        
        # Configurer le chemin de sortie
        set_path_request = simpleobsws.Request('SetRecordDirectory', requestData={'recordDirectory': os.path.dirname(video_path)})
        await ws.call(set_path_request)
        
        # Démarrer l'enregistrement de manière synchronisée
        start_request = simpleobsws.Request('StartRecord', requestData={'outputPath': video_path})
        response = await ws.call(start_request)
        
        # Marquer le temps de départ
        start_time = time.time()
        os.environ['RECORDING_START_TIME'] = str(start_time)
        
        # Vérifier l'état
        await asyncio.sleep(1)
        status_request = simpleobsws.Request('GetRecordStatus')
        status_response = await ws.call(status_request)
        
        if status_response.responseData.get('outputActive', False):
            print(f"OBS : Enregistrement démarré avec succès dans {video_path}")
        else:
            print("OBS : Erreur - L'enregistrement n'a pas démarré.")
            print(f"État détaillé : {status_response.responseData}")
            
        print("Appuyez sur la touche 'Échap' pour arrêter l'enregistrement...")
        return ws
    except Exception as e:
        print(f"Erreur de connexion : {str(e)}")
        if ws:
            await ws.disconnect()
        raise

async def stop_obs_recording(ws):
    """
    Stoppe l'enregistrement dans OBS et ferme la connexion WebSocket.
    """
    try:
        # Vérifier l'état avant l'arrêt
        status_request = simpleobsws.Request('GetRecordStatus')
        status_response = await ws.call(status_request)
        print(f"État avant arrêt : {status_response.responseData}")

        if status_response.responseData.get('outputActive', False):
            stop_request = simpleobsws.Request('StopRecord')
            response = await asyncio.wait_for(ws.call(stop_request), timeout=5.0)
            print(f"Réponse de la commande d'arrêt : {response.responseData}")
            
            # Attendre un peu et vérifier l'état final
            await asyncio.sleep(1)
            status_request = simpleobsws.Request('GetRecordStatus')
            status_response = await ws.call(status_request)
            
            if not status_response.responseData.get('outputActive', True):
                print("OBS : Enregistrement arrêté avec succès.")
                print(f"Vidéo sauvegardée : {response.responseData.get('outputPath', 'Chemin inconnu')}")
            else:
                print("OBS : Erreur - L'enregistrement n'a pas été arrêté.")
                print(f"État détaillé : {status_response.responseData}")
        else:
            print("OBS : L'enregistrement n'était pas actif.")
            
    except asyncio.TimeoutError:
        print("Timeout lors de l'arrêt de l'enregistrement")
    except Exception as e:
        print(f"Erreur lors de l'arrêt de l'enregistrement : {e}")
    finally:
        try:
            await ws.disconnect()
        except:
            pass

async def main_async():
    telemetry_proc = None
    ws = None
    
    try:
        # S'assurer que le dossier de session existe
        if not os.path.exists(SESSION_DIR):
            os.makedirs(SESSION_DIR)
            
        # Préparer l'environnement avec le timestamp de départ
        start_time = time.time()
        env = os.environ.copy()
        env['SESSION_DIR'] = SESSION_DIR
        env['RECORDING_START_TIME'] = str(start_time)
        
        # Lancer le script de télémétrie avec le timestamp
        telemetry_proc = subprocess.Popen(["python", GET_INPUTS_SCRIPT], env=env)
        
        # Se connecter à OBS
        ws = simpleobsws.WebSocketClient(
            url=f"ws://{OBS_HOST}:{OBS_PORT}",
            password=OBS_PASSWORD
        )
        await ws.connect()
        await ws.wait_until_identified()
        
        # Préparer OBS
        video_path = os.path.abspath(os.path.join(SESSION_DIR, "session_recording.mkv"))
        set_path_request = simpleobsws.Request('SetRecordDirectory', 
            requestData={'recordDirectory': os.path.dirname(video_path)})
        await ws.call(set_path_request)
        
        # Petite pause pour s'assurer que tout est prêt
        await asyncio.sleep(0.5)
        
        # Démarrer l'enregistrement
        start_request = simpleobsws.Request('StartRecord', requestData={'outputPath': video_path})
        await ws.call(start_request)
        
        print(f"Enregistrement démarré à {start_time}")
        print("Appuyez sur la touche 'Échap' pour arrêter l'enregistrement...")
        
        # Attendre la touche Échap
        while not keyboard.is_pressed('esc'):
            await asyncio.sleep(0.1)
            
        print("\nTouche Échap détectée, arrêt en cours...")
        await stop_obs_recording(ws)
        
    finally:
        if telemetry_proc:
            print("Arrêt du processus de télémétrie...")
            telemetry_proc.terminate()
            telemetry_proc.wait()
        print("Session terminée.")

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nInterruption détectée, arrêt du programme...")
    except Exception as e:
        print(f"\nErreur inattendue : {e}")

if __name__ == '__main__':
    main()
