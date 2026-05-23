import os
import pandas as pd
import numpy as np
import librosa
import soundfile as sf
import random
from audiomentations import Compose, TimeStretch, PitchShift, AddBackgroundNoise, TimeMask

# Constants
SR = 16000
TARGET_COUNT = 600
PROCESSED_DIR = "data/processed/"
AUGMENTED_DIR = "data/augmented/"
ESC50_DIR = "/home/umairimran/OLD DISK/Smart Baby Band FYP/ml_model/cry_detection/data/ESC-50-master/audio"

# Hardcoded to prevent dirty CSVs from ruining your dataset again
TARGET_CLASSES = ["hungry", "tired", "discomfort", "diaper"]

def get_augmenter():
    # Only add background noise if ESC-50 exists
    transforms = [
        TimeStretch(min_rate=0.85, max_rate=1.15, p=0.5),
        PitchShift(min_semitones=-2, max_semitones=2, p=0.5),
        TimeMask(min_band_part=0.05, max_band_part=0.15, fade_duration=0.0, p=0.5)
    ]
    if os.path.exists(ESC50_DIR) and len(os.listdir(ESC50_DIR)) > 0:
        transforms.insert(2, AddBackgroundNoise(sounds_path=ESC50_DIR, min_snr_db=10, max_snr_db=20, p=0.5))
    else:
        print("Warning: ESC-50 directory not found or empty. Skipping AddBackgroundNoise.")
        
    return Compose(transforms)

def main():
    os.makedirs(AUGMENTED_DIR, exist_ok=True)
    splits_path = os.path.join(PROCESSED_DIR, "splits.csv")
    if not os.path.exists(splits_path):
        print(f"Error: {splits_path} not found. Run dataset.py first.")
        return
        
    df = pd.read_csv(splits_path)
    
    # Filter for training split AND strictly enforce the 4 target classes
    train_df = df[(df["split"] == "train") & (df["label"].isin(TARGET_CLASSES))]
    
    class_counts = train_df["label"].value_counts()
    print("Filtered Train Class Counts:\n", class_counts)
    
    augmenter = get_augmenter()
    augmented_records = []
    
    for label, count in class_counts.items():
        needed = TARGET_COUNT - count
        if needed <= 0:
            print(f"Class {label} has enough samples ({count}).")
            continue
            
        print(f"Augmenting {label} by {needed} samples...")
        label_df = train_df[train_df["label"] == label]
        
        for i in range(needed):
            # randomly pick a sample from this class
            sample_row = label_df.sample(1).iloc[0]
            y, sr = librosa.load(sample_row["filepath"], sr=SR, mono=True)
            
            y_aug = augmenter(samples=y, sample_rate=sr)
            
            aug_filename = f"aug_{label}_{i}.wav"
            aug_filepath = os.path.join(AUGMENTED_DIR, aug_filename)
            sf.write(aug_filepath, y_aug, SR)
            
            augmented_records.append({
                "filepath": aug_filepath,
                "label": label,
                "split": "train",
                "source_dataset": sample_row["source_dataset"] + "_aug"
            })
            
    if augmented_records:
        aug_df = pd.DataFrame(augmented_records)
        final_df = pd.concat([df, aug_df], ignore_index=True)
        final_df.to_csv(splits_path, index=False)
        print(f"Appended {len(augmented_records)} augmented samples to splits.csv.")
    else:
        print("No augmentation needed.")

if __name__ == "__main__":
    main()