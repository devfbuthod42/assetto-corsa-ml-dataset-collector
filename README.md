# Assetto Corsa Training Data Collector

Un outil Python pour collecter simultanément les données de télémétrie d'Assetto Corsa et l'enregistrement vidéo via OBS Studio. Idéal pour créer des datasets d'apprentissage automatique pour la simulation de course.

## 🎮 Fonctionnalités

- Capture synchronisée des données de télémétrie et de la vidéo
- Enregistrement des inputs (volant, accélérateur, frein) et de la vitesse
- Sauvegarde automatique dans des dossiers de session horodatés
- Enregistrement vidéo via OBS Studio à 30 FPS
- Interface simple avec arrêt via touche Échap

## 📋 Prérequis

- Python 3.7+
- OBS Studio avec plugin obs-websocket
- Assetto Corsa
- Bibliothèques Python requises (voir `requirements.txt`)

## 🛠️ Installation

1. Clonez ce repository
```bash
git clone https://github.com/tony-b/ac-telemetry-collector.git
cd ac-telemetry-collector
```


2. Installez les dépendances
```	bash
pip install -r requirements.txt
```


3. Configurez OBS Studio :
   - Installez le plugin obs-websocket
   - Configurez le mot de passe dans les paramètres de obs-websocket
   - Mettez à jour les paramètres de connexion dans `master_script.py`

## ⚙️ Configuration

Modifiez les variables suivantes dans `master_script.py` selon votre configuration :

```python
OBS_HOST = "192.168.1.32"  # IP de ton serveur OBS
OBS_PORT = 4444  # Port de ton serveur OBS
OBS_PASSWORD = "votre_mot_de_passe"  # Mot de passe de ton serveur OBS
```


## 🚀 Utilisation

1. Lancez Assetto Corsa et entrez dans une session
2. Démarrez OBS Studio
3. Exécutez le script :

```bash
python master_script.py
```

4. Appuyez sur Échap pour arrêter l'enregistrement

## 📁 Structure des données

Chaque session crée un dossier avec :
- `inputs.csv` : Données de télémétrie
- `session_recording.mkv` : Enregistrement vidéo

Format du CSV :
```
csv
Timestamp,Frame,Steering,Throttle,Brake,SpeedKmh
0.0,0,0.001500,0.0,1.0,0.0
```


## 🤖 Utilisation pour le Machine Learning

Les données collectées sont structurées pour l'entraînement de modèles :
- Timestamps synchronisés entre vidéo et données
- Numéros de frames pour un alignement facile
- Format CSV compatible avec pandas/numpy

## 🔧 Dépannage

- Vérifiez que OBS Studio est en cours d'exécution
- Confirmez les paramètres de connexion obs-websocket
- Assurez-vous qu'Assetto Corsa est en mode fenêtré ou plein écran sans bordure

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commit vos changements
4. Push vers la branche
5. Ouvrir une Pull Request

## ✨ Remerciements

- OBS Studio pour leur excellent logiciel
- La communauté Assetto Corsa pour la documentation sur la shared memory