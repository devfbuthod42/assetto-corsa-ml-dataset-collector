import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import scripts.best_save as best_save
import cv2
import numpy as np
import time
import mss
import vgamepad as vg
import win32gui
import win32con
import logging
import os
import sys
import argparse

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_ac_window():
    """Trouve la fenêtre d'Assetto Corsa"""
    logging.info("Recherche de la fenêtre Assetto Corsa...")
    window = win32gui.FindWindow(None, "Assetto Corsa")
    if window:
        logging.info("Fenêtre Assetto Corsa trouvée")
    else:
        logging.warning("Fenêtre Assetto Corsa non trouvée")
        return None
    return window

def capture_game_frame(monitor):
    """Capture l'écran de jeu"""
    try:
        with mss.mss() as sct:
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame
    except Exception as e:
        logging.error(f"Erreur capture: {e}")
        return None

def preprocess_image(image):
    """Prétraite l'image pour le modèle"""
    try:
        # Afficher l'image originale pour debug
        cv2.imshow('Original', image)
        
        # Découper l'image pour ne garder que la partie inférieure
        height = image.shape[0]
        crop_height = 150
        cropped = image[height-crop_height:height, :]
        
        # Afficher l'image découpée
        cv2.imshow('Cropped', cropped)
        
        # Redimensionner
        resized = cv2.resize(cropped, (200, 66))
        
        # Afficher l'image redimensionnée
        cv2.imshow('Resized', resized)
        
        # Normaliser
        normalized = resized.astype(np.float32) / 255.0
        
        return normalized
    except Exception as e:
        logging.error(f"Erreur prétraitement: {e}")
        return None

def initialize_gamepad():
    """Initialise et teste le gamepad virtuel"""
    try:
        logging.info("Tentative d'initialisation du gamepad virtuel...")
        gamepad = vg.VX360Gamepad()
        
        # Test initial des contrôles
        logging.info("Test des contrôles du gamepad...")
        
        # Test direction
        logging.info("Test direction gauche")
        gamepad.left_joystick_float(x_value_float=-1.0, y_value_float=0.0)
        gamepad.update()
        time.sleep(0.5)
        
        logging.info("Test direction droite")
        gamepad.left_joystick_float(x_value_float=1.0, y_value_float=0.0)
        gamepad.update()
        time.sleep(0.5)
        
        # Test accélérateur
        logging.info("Test accélérateur")
        gamepad.right_trigger_float(value_float=1.0)
        gamepad.update()
        time.sleep(0.5)
        
        # Test frein
        logging.info("Test frein")
        gamepad.left_trigger_float(value_float=1.0)
        gamepad.update()
        time.sleep(0.5)
        
        # Reset
        gamepad.reset()
        gamepad.update()
        
        logging.info("Gamepad virtuel initialisé et testé avec succès")
        return gamepad
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation du gamepad: {e}")
        return None

def main(model_path):
    logging.info("Démarrage du programme...")
    logging.info(f"Utilisation du modèle: {model_path}")
    
    try:
        # Initialisation du gamepad avec tests
        gamepad = initialize_gamepad()
        if gamepad is None:
            logging.error("Impossible d'initialiser le gamepad. Arrêt du programme.")
            return
            
        # Attente pour s'assurer que le gamepad est bien détecté
        logging.info("Pause de 3 secondes pour la détection du gamepad...")
        time.sleep(3)
        
        # Configuration de TensorFlow
        logging.info("Initialisation de TensorFlow...")
        sess = tf.InteractiveSession()
        
        # Vérification de l'existence des fichiers du modèle
        files_needed = [
            f"{model_path}.meta",
            f"{model_path}.index",
            f"{model_path}.data-00000-of-00001"
        ]
        for file in files_needed:
            if not os.path.exists(file):
                logging.error(f"Fichier manquant: {file}")
                return
        logging.info("Tous les fichiers du modèle sont présents")
        
        # Chargement du modèle
        logging.info("Création du graphe TensorFlow...")
        # Importation du modèle depuis best_save
        x = tf.placeholder(tf.float32, shape=[None, 66, 200, 3])
        keep_prob = tf.placeholder(tf.float32)
        y = best_save.create_model(x, keep_prob)  # Assurez-vous que cette fonction existe dans best_save
        
        logging.info("Création du Saver...")
        saver = tf.train.Saver()
        
        logging.info("Restauration du modèle...")
        saver.restore(sess, model_path)
        logging.info("Modèle chargé avec succès")
        
        # Trouver la fenêtre AC
        ac_window = get_ac_window()
        if not ac_window:
            logging.error("Assetto Corsa n'est pas en cours d'exécution")
            return
            
        # Obtenir les dimensions de la fenêtre
        logging.info("Récupération des dimensions de la fenêtre...")
        rect = win32gui.GetWindowRect(ac_window)
        monitor = {
            "top": rect[1],
            "left": rect[0],
            "width": rect[2] - rect[0],
            "height": rect[3] - rect[1]
        }
        logging.info(f"Dimensions de la fenêtre: {monitor}")
        
        logging.info("Démarrage de la boucle principale. Appuyez sur 'Q' pour quitter")
        
        # Avant la boucle principale, on initialise une variable pour suivre le temps du dernier log
        last_log_time = 0

        while True:
            try:
                frame = capture_game_frame(monitor)
                if frame is None:
                    raise Exception("Échec de la capture d'écran")
                
                processed_frame = preprocess_image(frame)
                if processed_frame is None:
                    raise Exception("Échec du prétraitement")
                
                # Récupération des prédictions du modèle
                predictions = sess.run(y, feed_dict={
                    x: [processed_frame],
                    keep_prob: 1.0
                })[0]
                
                # Extraction des prédictions
                steering_raw = float(predictions[0])
                throttle_raw = float(predictions[2])

                # Valeur neutre déterminée à partir des logs (à ajuster si besoin)
                neutral_offset = 0.021

                # Amplifier la différence par rapport au neutre
                steering_scale = 40.0
                steering = (steering_raw - neutral_offset) * steering_scale

                # Transformation non linéaire (exponentielle)
                steering_power = 1.2
                if abs(steering) > 0.05:
                    steering = (abs(steering) ** steering_power) * (1 if steering >= 0 else -1)
                else:
                    steering = 0.0

                # Contrainte de l'intervalle [-1, 1]
                steering = max(-1.0, min(1.0, steering))
                throttle = max(0.0, min(1.0, throttle_raw * 2.0))
                
                # Log uniquement si au moins 1 seconde s'est écoulée depuis le dernier log
                current_time = time.time()
                if current_time - last_log_time >= 1:
                    logging.info("=== Traitement direction ===")
                    logging.info(f"Direction brute : {steering_raw:>8.3f}")
                    logging.info(f"Après offset et scale : {steering:>8.3f}")
                    logging.info(f"Direction finale : {steering:>8.3f}")
                    logging.info(f"Accélérateur final : {throttle:>8.3f}")
                    last_log_time = current_time
                
                # Application des commandes sur le gamepad
                try:
                    gamepad.reset()
                    gamepad.left_joystick_float(x_value_float=steering, y_value_float=0.0)
                    gamepad.right_trigger_float(value_float=throttle)
                    gamepad.update()
                except Exception as e:
                    logging.error(f"Erreur gamepad : {e}")
                
                # Pause courte
                time.sleep(0.02)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
            except Exception as e:
                logging.error(f"Erreur boucle : {e}")
                time.sleep(1)
        
    except Exception as e:
        logging.error(f"Erreur fatale: {e}")
    finally:
        logging.info("Nettoyage...")
        try:
            if gamepad:
                gamepad.reset()
                gamepad.update()
        except:
            pass
        cv2.destroyAllWindows()
        sess.close()

if __name__ == "__main__":
    # Configuration des logs détaillés
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('controller_debug.log')
        ]
    )
    
    # Ajout des arguments en ligne de commande
    parser = argparse.ArgumentParser(description='Test du modèle AC')
    parser.add_argument('--model', type=str, default="best_save/model.ckpt",
                      help='Chemin vers le modèle (sans extension)')
    args = parser.parse_args()
    
    main(args.model) 