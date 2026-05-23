import os
import json
import librosa
import numpy as np
import pandas as pd
from tqdm import tqdm

# Config
SR = 16000
DURATION = 3.0
SAMPLES = int(SR * DURATION)
N_FFT = 512
HOP_LENGTH = 375
N_MELS = 128
N_MFCC = 40
FMIN = 0
FMAX = 8000

PROCESSED_DIR = "data/processed/"
FEATURES_DIR = "features/"
MODELS_DIR = "models/"

import tensorflow_hub as hub
import tensorflow as tf

def extract_features(audio_path):
    # Load audio
    y, sr = librosa.load(audio_path, sr=SR, mono=True)
    if len(y) > SAMPLES:
        y = y[:SAMPLES]
    else:
        # Wrap audio instead of padding with silence
        repeats = int(np.ceil(SAMPLES / len(y))) if len(y) > 0 else 1
        y = np.tile(y, repeats)[:SAMPLES]
        
    # Mel Spectrogram
    mel = librosa.feature.melspectrogram(y=y, sr=SR, n_fft=N_FFT, hop_length=HOP_LENGTH, 
                                         n_mels=N_MELS, fmin=FMIN, fmax=FMAX)
    mel_db = librosa.power_to_db(mel, ref=np.max) # (128, 128)
    
    # Truncate to 128 frames across time axis just to be safe
    mel_db = mel_db[:, :128]
    
    if mel_db.shape[1] < 128:
        pad_width = 128 - mel_db.shape[1]
        mel_db = np.pad(mel_db, ((0,0), (0,pad_width)), 'constant')
        
    # Normalize per-channel (here per-feature matrix) to [0, 1]
    min_val = np.min(mel_db)
    max_val = np.max(mel_db)
    if max_val > min_val:
        mel_db = (mel_db - min_val) / (max_val - min_val)
    else:
        mel_db = mel_db - min_val
        
    # Add channel dim
    features = np.expand_dims(mel_db, axis=-1) # (128, 128, 1)
    return features

def main():
    os.makedirs(FEATURES_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    splits_path = os.path.join(PROCESSED_DIR, "splits.csv")
    if not os.path.exists(splits_path):
        print(f"Error: {splits_path} not found. Run dataset.py and augment.py first.")
        return
        
    df = pd.read_csv(splits_path)
    
    shape = None
    
    for split in ["train", "val", "test"]:
        os.makedirs(os.path.join(FEATURES_DIR, split), exist_ok=True)
        split_df = df[df["split"] == split]
        
        for i, row in tqdm(split_df.iterrows(), total=len(split_df), desc=f"Extracting {split}"):
            feat = extract_features(row["filepath"])
            if shape is None:
                shape = feat.shape
                
            filename = f"{row['label']}_{i}.npy"
            out_path = os.path.join(FEATURES_DIR, split, filename)
            np.save(out_path, feat)
            
    # Save config
    config = {
        "sr": SR,
        "duration": DURATION,
        "n_fft": N_FFT,
        "hop_length": HOP_LENGTH,
        "n_mels": N_MELS,
        "n_mfcc": N_MFCC,
        "fmin": FMIN,
        "fmax": FMAX,
        "feature_shape": shape
    }
    with open(os.path.join(MODELS_DIR, "feature_config.json"), "w") as f:
        json.dump(config, f, indent=4)
        
    print(f"Feature extraction complete. Shape: {shape}. Config saved.")

if __name__ == "__main__":
    main()
