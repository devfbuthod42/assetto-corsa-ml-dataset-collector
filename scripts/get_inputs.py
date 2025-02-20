import struct
import time
import csv
import os
import sys
import mmap
from datetime import datetime
import math
from colorama import init, Fore, Back, Style

# Initialiser colorama
init()

# Utiliser le dossier de session passé en variable d'environnement
SESSION_DIR = os.environ.get('SESSION_DIR')
if not SESSION_DIR:
    print("Erreur : SESSION_DIR n'est pas défini")
    sys.exit(1)

# Chemin du fichier CSV pour enregistrer les données
CSV_FILE = os.environ.get('CSV_FILE') or os.path.join(SESSION_DIR, "inputs.csv")

# Configuration
START_TIME = None  # Pour le timestamp relatif
SAMPLE_RATE = 30  # 30 Hz pour correspondre au FPS de la vidéo
SLEEP_TIME = 1 / SAMPLE_RATE

# Au début du script
import time
while 'RECORDING_START_TIME' not in os.environ:
    time.sleep(0.01)  # Attendre que le timestamp soit disponible

START_TIME = float(os.environ['RECORDING_START_TIME'])

class SMElement:
    def __init__(self, data):
        # Structure officielle AC
        self.speedKmh = struct.unpack('f', data[28:32])[0]
        self.gas = struct.unpack('f', data[4:8])[0]             # Gas pedal position 0-1
        self.brake = struct.unpack('f', data[8:12])[0]          # Brake pedal position 0-1
        self.steer = struct.unpack('f', data[24:28])[0]
        raw_gear = struct.unpack('i', data[16:20])[0]          # Gear: -1=R 0=N 1-6=1st-6th
        # Correction des valeurs de gear
        if raw_gear == 1:
            self.gear = 6  # Si 1, c'est la 6ème
        else:
            self.gear = raw_gear - 1  # Pour les autres vitesses, on soustrait 2

def read_shared_memory():
    try:
        mm = mmap.mmap(0, 408, "Local\\acpmf_physics")
        data = mm.read(408)
        mm.close()
        
        physics = SMElement(data)
        current_time = time.time()
        
        # Calcul du numéro de frame
        elapsed_time = current_time - START_TIME
        frame_number = int(elapsed_time * 30)
        
        return {
            "Frame": frame_number,
            "Steering": physics.steer,
            "Throttle": physics.gas,
            "Brake": physics.brake,
            "SpeedKmh": physics.speedKmh,
            "Gear": physics.gear
        }
    except Exception as e:
        print(f"Erreur : {e}")
        return None

# Création du fichier CSV avec les en-têtes
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Frame', 'Steering', 'Throttle', 'Brake', 'SpeedKmh', 'Gear'])

time.sleep(0.1)  # Petite pause pour s'assurer que le fichier est bien créé

# Afficher le chemin du dossier de session
print(f"Données enregistrées dans : {SESSION_DIR}")
print("Démarrage de la capture des données... (Ctrl+C pour arrêter)")

try:
    last_sample_time = time.time()
    while True:
        current_time = time.time()
        
        data = read_shared_memory()
        
        if data:
            with open(CSV_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    data["Frame"],
                    data["Steering"],
                    data["Throttle"],
                    data["Brake"],
                    data["SpeedKmh"],
                    data["Gear"]
                ])
            
            # Affichage coloré des données avec ajout du gear
            print(f"\r{Fore.CYAN}Vitesse: {Fore.YELLOW}{data['SpeedKmh']:.1f} km/h {Style.RESET_ALL}| "
                  f"{Fore.GREEN}Acc: {data['Throttle']:.2f} {Style.RESET_ALL}| "
                  f"{Fore.RED}Frein: {data['Brake']:.2f} {Style.RESET_ALL}| "
                  f"{Fore.BLUE}Volant: {data['Steering']:.2f} {Style.RESET_ALL}| "
                  f"{Fore.MAGENTA}Gear: {data['Gear']}{Style.RESET_ALL}", end="")
        
        sleep_time = max(0, SLEEP_TIME - (time.time() - current_time))
        time.sleep(sleep_time)
        last_sample_time = current_time

except KeyboardInterrupt:
    print(f"\n{Fore.GREEN}Capture des données arrêtée. Fichier sauvegardé dans : {CSV_FILE}{Style.RESET_ALL}")
