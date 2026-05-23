import os
import glob
import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

# Constants
SR = 16000
DURATION = 3.0
SAMPLES = int(SR * DURATION)
TOP_DB = 20

# 4 Harmonized classes (belly_pain and burping explicitly dropped)
TARGET_CLASSES = ["hungry", "tired", "discomfort", "diaper"]

def get_dac_files(base_dir):
    records = []
    if not os.path.exists(base_dir):
        print(f"Warning: DaC dir {base_dir} not found.")
        return records
    for label in os.listdir(base_dir):
        label_dir = os.path.join(base_dir, label)
        if os.path.isdir(label_dir) and label in TARGET_CLASSES:
            for f in glob.glob(os.path.join(label_dir, "*.wav")):
                records.append({
                    "filepath": f,
                    "label": label,
                    "source_dataset": "DaC"
                })
    return records

def get_baby_crying_files(base_dir):
    records = []
    if not os.path.exists(base_dir):
        print(f"Warning: baby_crying dir {base_dir} not found.")
        return records
    
    for split in ["train", "test", "raw"]:
        split_dir = os.path.join(base_dir, split)
        if not os.path.exists(split_dir):
            continue
        for label in os.listdir(split_dir):
            label_dir = os.path.join(split_dir, label)
            if not os.path.isdir(label_dir):
                continue
                
            mapped_label = None
            if label == "hungry":
                mapped_label = "hungry"
            elif label == "sleepy":
                mapped_label = "tired"
            elif label == "uncomfortable":
                mapped_label = "discomfort"
            elif label == "diaper":
                mapped_label = "diaper"
            elif label in ["hug", "awake", "belly_pain", "burping"]:
                continue 
            
            if mapped_label and mapped_label in TARGET_CLASSES:
                for f in glob.glob(os.path.join(label_dir, "*.wav")):
                    records.append({
                        "filepath": f,
                        "label": mapped_label,
                        "source_dataset": "baby_crying"
                    })
    return records

def process_audio(filepath):
    y, sr = librosa.load(filepath, sr=SR, mono=True)
    y_trimmed, _ = librosa.effects.trim(y, top_db=TOP_DB)
    
    if len(y_trimmed) == 0:
        y_trimmed = np.zeros(SAMPLES)
        
    if len(y_trimmed) >= SAMPLES:
        y_final = y_trimmed[:SAMPLES]
    else:
        # Repeat the audio to fill the 3 seconds instead of padding with silence
        repeats = int(np.ceil(SAMPLES / len(y_trimmed)))
        y_final = np.tile(y_trimmed, repeats)[:SAMPLES]
        
    if np.max(np.abs(y_final)) > 0:
        y_final = y_final / np.max(np.abs(y_final))
        
    return y_final

def main():
    dac_dir = "data/raw/donateacry-corpus-master/donateacry_corpus_cleaned_and_updated_data/"
    baby_crying_dir = "data/raw/baby-crying/"
    processed_dir = "data/processed/"
    os.makedirs(processed_dir, exist_ok=True)
    
    records = get_dac_files(dac_dir) + get_baby_crying_files(baby_crying_dir)
    df = pd.DataFrame(records)
    print(f"Total files collected: {len(df)}")
    
    processed_records = []
    for i, row in df.iterrows():
        try:
            y = process_audio(row["filepath"])
            filename = f"processed_{i}.wav"
            out_path = os.path.join(processed_dir, filename)
            sf.write(out_path, y, SR)
            
            processed_records.append({
                "filepath": out_path,
                "label": row["label"],
                "source_dataset": row["source_dataset"]
            })
        except Exception as e:
            print(f"Error processing {row['filepath']}: {e}")
            
    df_processed = pd.DataFrame(processed_records)
    
    train_val, test = train_test_split(df_processed, test_size=0.1, stratify=df_processed["label"], random_state=42)
    train, val = train_test_split(train_val, test_size=1/9, stratify=train_val["label"], random_state=42) 
    
    train["split"] = "train"
    val["split"] = "val"
    test["split"] = "test"
    
    splits_df = pd.concat([train, val, test])
    splits_df.to_csv(os.path.join(processed_dir, "splits.csv"), index=False)
    
    plt.figure(figsize=(10, 6))
    splits_df["label"].value_counts().plot(kind="bar")
    plt.title("Class Distribution")
    plt.xlabel("Class")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(os.path.join(processed_dir, "class_distribution.png"))
    print("Dataset preparation complete. Splits saved.")

if __name__ == "__main__":
    main()