import cv2
import pandas as pd
import os
from pathlib import Path
from tqdm import tqdm

def process_session(session_dir):
    session_dir = Path(session_dir)
    
    csv_path = session_dir / "inputs.csv"
    video_path = session_dir / "session_recording.mkv"
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Le fichier CSV n'existe pas : {csv_path}")
    if not video_path.exists():
        raise FileNotFoundError(f"Le fichier vidéo n'existe pas : {video_path}")
        
    print(f"Lecture du fichier CSV : {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"Nombre de lignes dans le CSV original : {len(df)}")
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise Exception("Impossible d'ouvrir la vidéo")
    
    # La vidéo est désormais filmée à 10 FPS, pas de sous-échantillonnage nécessaire
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_interval = 1  # Extraction de toutes les frames
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    expected_frames = total_frames  # Toutes les frames sont attendues
    
    print(f"FPS de la vidéo : {fps}")
    print(f"Nombre total de frames dans la vidéo : {total_frames}")
    print(f"Nombre de frames attendu (10 FPS) : {expected_frames}")
    
    images_dir = session_dir / "processed_images"
    images_dir.mkdir(exist_ok=True)
    
    processed_data = []
    
    for frame_count in tqdm(range(0, total_frames, frame_interval)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        ret, frame = cap.read()
        if not ret:
            print(f"Erreur de lecture à la frame {frame_count}")
            break
            
        frame_data = df[df['Frame'] == frame_count]
        
        if not frame_data.empty:
            image_name = f"frame_{frame_count:06d}.jpg"
            cv2.imwrite(str(images_dir / image_name), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            processed_data.append({
                'image_name': image_name,
                'steering': frame_data['Steering'].iloc[0],
                'throttle': frame_data['Throttle'].iloc[0],
                'brake': frame_data['Brake'].iloc[0],
                'speed': frame_data['SpeedKmh'].iloc[0],
                'gear': frame_data['Gear'].iloc[0]
            })
    
    cap.release()
    
    if not processed_data:
        raise Exception("Aucune donnée n'a été traitée !")
    
    print("\nCréation du DataFrame final...")
    processed_df = pd.DataFrame(processed_data)
    
    output_csv = session_dir / "processed_data.csv"
    processed_df.to_csv(output_csv, index=False)
    print(f"Dataset sauvegardé dans : {output_csv}")
    print(f"Nombre d'images traitées : {len(processed_data)} (10 FPS)")

def compile_sessions(base_dir, output_dir):
    """Compile plusieurs sessions en un seul dataset"""
    all_data = []
    
    for session_dir in Path(base_dir).glob("*"):
        if session_dir.is_dir():
            processed_csv = session_dir / "processed_data.csv"
            if processed_csv.exists():
                df = pd.read_csv(processed_csv)
                df['image_name'] = session_dir.name + "/processed_images/" + df['image_name']
                all_data.append(df)
    
    final_df = pd.concat(all_data, ignore_index=True)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    final_df.to_csv(output_dir / "complete_dataset.csv", index=False)

if __name__ == "__main__":
    session_dir = input("Entrez le chemin du dossier de session (ex: ac_telemetry_data/20240209_171203): ")
    try:
        process_session(session_dir)
    except Exception as e:
        print(f"Erreur : {e}")