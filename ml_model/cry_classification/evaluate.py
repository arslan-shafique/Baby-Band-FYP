import os
import json
import argparse
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from train import load_data, create_dataset, TARGET_CLASSES, LABEL_MAP
from model import build_model

MODELS_DIR = "models/"
LOGS_DIR = "logs/"

def evaluate_model(model, ds, y_true, title_suffix=""):
    print(f"\n--- Evaluation: {title_suffix} ---")
    loss, acc = model.evaluate(ds, verbose=0)
    print(f"Loss: {loss:.4f}, Accuracy: {acc:.4f}")
    
    y_pred_probs = model.predict(ds)
    y_pred = np.argmax(y_pred_probs, axis=1)
    
    # Explicitly provide labels to avoid errors when some classes are missing in cross-dataset testing
    labels = list(range(len(TARGET_CLASSES)))
    
    # classification report
    report = classification_report(y_true, y_pred, labels=labels, target_names=TARGET_CLASSES, output_dict=True, zero_division=0)
    print("Classification Report:")
    print(classification_report(y_true, y_pred, labels=labels, target_names=TARGET_CLASSES, zero_division=0))
    
    # confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', xticklabels=TARGET_CLASSES, yticklabels=TARGET_CLASSES, cmap='Blues')
    plt.title(f"Confusion Matrix {title_suffix}")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(os.path.join(LOGS_DIR, f"confusion_matrix{'_' + title_suffix.replace(' ', '_') if title_suffix else ''}.png"))
    
    return report

def cross_dataset_experiment():
    print("\n--- Running Cross-Dataset Experiment ---")
    splits_path = "data/processed/splits.csv"
    if not os.path.exists(splits_path):
        print("splits.csv not found.")
        return
        
    df = pd.read_csv(splits_path)
    
    # DaC classes: hungry, discomfort, belly_pain, burping
    # Actually DaC has tired too. 
    # The text says: Retrain on DaC only (hungry, discomfort, belly_pain, burping)
    # Test on baby_crying (hungry, discomfort only)
    
    # Train on DaC
    train_dac_df = df[(df["source_dataset"].str.startswith("DaC")) & (df["split"] == "train")]
    train_dac_df = train_dac_df[train_dac_df["label"].isin(["hungry", "discomfort", "belly_pain", "burping"])]
    
    # Val on DaC
    val_dac_df = df[(df["source_dataset"].str.startswith("DaC")) & (df["split"] == "val")]
    val_dac_df = val_dac_df[val_dac_df["label"].isin(["hungry", "discomfort", "belly_pain", "burping"])]
    
    # Test on baby_crying
    test_bc_df = df[(df["source_dataset"].str.startswith("baby_crying")) & (df["split"] == "test")]
    test_bc_df = test_bc_df[test_bc_df["label"].isin(["hungry", "discomfort"])]
    
    def get_paths_and_labels(subset_df):
        paths = []
        labels = []
        for _, row in subset_df.iterrows():
            filename = f"{row['label']}_{row.name}.npy" # Not exact name since row.name is df index, not the original index! 
            # We should probably look up the actual filename or just recreate path. 
            # But the features.py saved them as label_index.npy. We didn't save filepath in df for features.
            # Let's search the features dir.
            split = row['split']
            feat_dir = os.path.join("features", split)
            for f in os.listdir(feat_dir):
                if f.startswith(row['label'] + "_"):
                    # This is an approximation since we don't have perfect mapping from df to feature file name easily.
                    # Actually, features.py enumerates over split_df! So i is the index in split_df!
                    pass
        # Because filename mapping is hard, let's just train on DaC paths by filtering the load_data output
        return paths, labels

    print("Note: To fully run cross-dataset experiment, feature files must map to datasets.")
    
    # We will filter load_data instead:
    train_paths, train_y = load_data("train")
    val_paths, val_y = load_data("val")
    test_paths, test_y = load_data("test")
    
    def filter_by_dataset_and_classes(paths, y, dataset_keyword, class_list):
        # We need to map path -> original df row.
        # Since df is ordered, we can do it if we read split_df again.
        split = "train" if "train" in paths[0] else ("val" if "val" in paths[0] else "test")
        split_df = df[df["split"] == split].reset_index(drop=True)
        
        filtered_paths = []
        filtered_y = []
        # In features.py: filename = f"{row['label']}_{i}.npy" where i is the index in split_df.iterrows() which is the original df index!
        # wait: "for i, row in split_df.iterrows(): filename = f'{label}_{i}.npy'"
        
        for path, label_idx in zip(paths, y):
            filename = os.path.basename(path)
            # e.g., hungry_42.npy
            try:
                idx = int(filename.split("_")[-1].split(".")[0])
                row = df.loc[idx]
                if dataset_keyword in row["source_dataset"] and row["label"] in class_list:
                    filtered_paths.append(path)
                    filtered_y.append(label_idx)
            except Exception:
                pass
        return filtered_paths, filtered_y
        
    train_dac_paths, train_dac_y = filter_by_dataset_and_classes(train_paths, train_y, "DaC", ["hungry", "discomfort", "belly_pain", "burping"])
    val_dac_paths, val_dac_y = filter_by_dataset_and_classes(val_paths, val_y, "DaC", ["hungry", "discomfort", "belly_pain", "burping"])
    test_bc_paths, test_bc_y = filter_by_dataset_and_classes(test_paths, test_y, "baby_crying", ["hungry", "discomfort"])
    
    if not train_dac_paths or not test_bc_paths:
        print("Not enough data for cross-dataset experiment.")
        return
        
    train_ds = create_dataset(train_dac_paths, train_dac_y, batch_size=32, shuffle=True)
    val_ds = create_dataset(val_dac_paths, val_dac_y, batch_size=32, shuffle=False)
    test_ds = create_dataset(test_bc_paths, test_bc_y, batch_size=32, shuffle=False)
    
    for x, y in train_ds.take(1):
        input_shape = x.shape[1:]
        break
        
    print("Training model on DaC only...")
    model = build_model(input_shape=input_shape, num_classes=len(TARGET_CLASSES))
    model.fit(train_ds, validation_data=val_ds, epochs=10, verbose=1) # Train for a few epochs
    
    evaluate_model(model, test_ds, test_bc_y, title_suffix="Cross-Dataset BC Test")
    print("Cross-Dataset Experiment Finished.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-cross-dataset", action="store_true", help="Skip the cross dataset experiment")
    args = parser.parse_args()
    
    model_path = os.path.join(MODELS_DIR, "best_model.keras")
    if not os.path.exists(model_path):
        print(f"Error: {model_path} not found.")
        return
        
    from model import SparseCategoricalFocalLoss
    model = tf.keras.models.load_model(model_path, custom_objects={'SparseCategoricalFocalLoss': SparseCategoricalFocalLoss})
    
    test_paths, test_y = load_data("test")
    if not test_paths:
        print("No test data found.")
        return
        
    test_ds = create_dataset(test_paths, test_y, batch_size=32, shuffle=False)
    
    evaluate_model(model, test_ds, test_y, title_suffix="Standard Test Set")
    
    if not args.skip_cross_dataset:
        cross_dataset_experiment()

if __name__ == "__main__":
    main()
