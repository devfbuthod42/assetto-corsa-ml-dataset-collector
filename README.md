# Assetto Corsa Training Data Collector

Un outil Python pour collecter simultanément les données de télémétrie d'Assetto Corsa et l'enregistrement vidéo via OBS Studio. Idéal pour créer des datasets d'apprentissage automatique pour la simulation de course.

---

## 🛠️ Récupération des données

### 🎮 Fonctionnalités

- Capture synchronisée des données de télémétrie et de la vidéo
- Enregistrement des inputs (volant, accélérateur, frein) et de la vitesse
- Sauvegarde automatique dans des dossiers de session horodatés
- Enregistrement vidéo via OBS Studio à 10 FPS
- Interface simple avec arrêt via touche Échap

### 📋 Prérequis

- Python 3.7+
- OBS Studio avec plugin obs-websocket
- Assetto Corsa
- Bibliothèques Python requises (voir `requirements.txt`)

### 🛠️ Installation

1. Clonez ce repository :
```bash
git clone https://github.com/tony-b/ac-telemetry-collector.git
cd ac-telemetry-collector
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurez OBS Studio :
   - Installez le plugin obs-websocket
   - Configurez le mot de passe dans les paramètres de obs-websocket
   - Mettez à jour les paramètres de connexion dans `master_script.py`

### ⚙️ Configuration

Modifiez les variables suivantes dans `master_script.py` selon votre configuration :

```python
OBS_HOST = "192.168.1.32"  # IP de ton serveur OBS
OBS_PORT = 4444  # Port de ton serveur OBS
OBS_PASSWORD = "votre_mot_de_passe"  # Mot de passe de ton serveur OBS
```

### 🚀 Utilisation

1. Lancez Assetto Corsa et entrez dans une session
2. Démarrez OBS Studio
3. Exécutez le script :

```bash
python master_script.py
```

4. Appuyez sur Échap pour arrêter l'enregistrement

### 📁 Structure des données

Chaque session crée un dossier avec :
- `inputs.csv` : Données de télémétrie
- `session_recording.mkv` : Enregistrement vidéo

Format du CSV :
```
csv
Timestamp,Frame,Steering,Throttle,Brake,SpeedKmh
0.0,0,0.001500,0.0,1.0,0.0
```

### 📷 Conversion de la vidéo en dataset d'images

Le script `convert_videos_to_dataset.py` a pour objectif de transformer une vidéo enregistrée d'une session d'Assetto Corsa en un dataset d'images annotées. Concrètement, il effectue les étapes suivantes :

1. Lit le fichier vidéo (`session_recording.mkv`) ainsi que le fichier CSV associé (`inputs.csv`) contenant les données de télémétrie (direction, accélérateur, frein, vitesse, etc.) pour chaque frame.
2. Parcourt toutes les frames de la vidéo (filmé à 10 FPS) et extrait chacune d'elles.
3. Pour chaque frame, il cherche dans le CSV les données correspondant au numéro de frame, puis enregistre l'image extraite dans un dossier nommé `processed_images`.
4. Il génère également un nouveau fichier CSV (`processed_data.csv`) qui référence toutes les images extraites avec leurs annotations associées.

Cet outil permet ainsi d'aligner facilement les images avec les inputs collectés lors de la session, ce qui est particulièrement utile pour constituer un dataset destiné à l'entraînement de modèles d'apprentissage automatique pour la simulation de course.

---

## 🤖 Test en jeu

### scripts/test_ac.py

Ce fichier permet de tester le modèle d'apprentissage automatique pour Assetto Corsa en réalisant les opérations suivantes :

- **Capture et prétraitement d'image**  
  Capture l'écran de la fenêtre d'Assetto Corsa grâce à la bibliothèque `mss` et prétraite l'image (découpage, redimensionnement et normalisation) pour préparer les données en entrée du modèle.

- **Chargement et restauration du modèle**  
  Initialise une session TensorFlow, reconstruit le graphe du modèle via la fonction `create_model` définie dans `scripts/best_save.py` et restaure les poids sauvegardés (les fichiers `.meta`, `.index` et `.data-00000-of-00001`).

- **Exécution en temps réel et débogage**  
  Exécute une boucle principale qui :
  - Capture l'écran de l'application.
  - Effectue une prédiction à partir du modèle (direction, accélérateur, etc.).
  - Applique ces prédictions au gamepad virtuel (via `vgamepad`) afin d'émuler les commandes de conduite.
  - Logge les informations importantes à une fréquence réduite (une fois par seconde) pour faciliter le débogage.

#### Utilisation
Le fichier se lance en ligne de commande avec l'argument `--model` pour spécifier le chemin du modèle à utiliser. Par exemple :

```bash
python scripts/test_ac.py --model "chemin/vers/le/model.ckpt"
```

Si aucun chemin n’est fourni, le modèle par défaut est `best_save/model.ckpt`.

### scripts/best_save.py

Ce fichier contient la définition du modèle d'apprentissage utilisé lors de l'entraînement. La fonction principale, généralement nommée `create_model`, y est définie et utilisée dans `scripts/test_ac.py` pour :

- Créer le graphe TensorFlow correspondant au modèle (architecture, couches, etc.).
- Assurer la correspondance entre le prétraitement appliqué aux images capturées et la structure d'entrée attendue par le modèle.
- Générer les sorties (par exemple, la commande de direction, accélérateur, frein) qui sont ensuite transformées et appliquées aux commandes du gamepad.

### Autres précisions

- Le prétraitement des images se focalise sur la partie inférieure de l'écran (celle affichant la route) pour une meilleure précision du modèle.
- Le fichier `test_ac.py` utilise plusieurs bibliothèques, telles que TensorFlow, OpenCV, mss, vgamepad et win32gui, afin de gérer la capture d'écran, le traitement d'image et l'émulation des commandes du jeu.
- Les logs détaillés, actualisés une fois par seconde, permettent de suivre le flux des commandes et d'identifier rapidement les potentielles anomalies (par exemple, l'inversion ou l'amplification des valeurs de direction).