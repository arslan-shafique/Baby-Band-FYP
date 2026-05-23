"""
Script to train the cloud-side binary cry detection model.
"""
import os
import sys
import json
import glob
import numpy as np
import librosa
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, BatchNormalization, ReLU, MaxPool2D, Flatten, Dense, Dropout
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Add workspace root to sys.path so ml_model module can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from ml_model.cry_classification.preprocess import preprocess_audio

ICSD_DIR = "data/ICSD"

def load_audio_as_pcm_bytes(filepath, sr=16000):
    """Loads an audio file and converts it to raw int16 PCM bytes to match the FastAPI input format."""
    try:
        y, _ = librosa.load(filepath, sr=sr, mono=True)
        y_int16 = (y * 32767).astype(np.int16)
        return y_int16.tobytes()
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def load_split_data(split_name):
    X_features = []
    Y_labels = []
    split_dir = os.path.join(ICSD_DIR, split_name)
    if not os.path.exists(split_dir):
        print(f"Split '{split_name}' not found at {split_dir}.")
        return None, None
        
    wav_files = glob.glob(os.path.join(split_dir, "**/*.wav"), recursive=True)
    if not wav_files:
        print(f"No .wav files found in {split_dir}")
        return None, None
        
    print(f"Loading {len(wav_files)} files from {split_name} split...")
    for i, fpath in enumerate(wav_files):
        if i > 0 and i % 500 == 0:
            print(f"  Processed {i}/{len(wav_files)} files...")
        b = load_audio_as_pcm_bytes(fpath)
        if b:
            feat = preprocess_audio(b)
            X_features.append(feat)
            
            # Labeling based on filename: 'infantcry' -> 1, anything else ('snoring', etc) -> 0
            filename = os.path.basename(fpath).lower()
            if "infantcry" in filename or "cry" in filename:
                Y_labels.append(1)
            else:
                Y_labels.append(0)
    
    if not X_features:
        return None, None
        
    return np.vstack(X_features), np.array(Y_labels)

def get_training_data():
    print("Loading data from local ICSD dataset...")
    X_train, Y_train = load_split_data("train")
    X_val, Y_val = load_split_data("validation")
    X_test, Y_test = load_split_data("test")
    
    return X_train, Y_train, X_val, Y_val, X_test, Y_test


def build_model():
    model = Sequential([
        Conv2D(16, (3, 3), padding='same', kernel_regularizer=l2(0.001), input_shape=(128, 128, 1)),
        BatchNormalization(),
        ReLU(),
        MaxPool2D((2, 2)),
        
        Conv2D(32, (3, 3), padding='same', kernel_regularizer=l2(0.001)),
        BatchNormalization(),
        ReLU(),
        MaxPool2D((2, 2)),
        
        Conv2D(32, (3, 3), padding='same', kernel_regularizer=l2(0.001)),
        BatchNormalization(),
        ReLU(),
        MaxPool2D((2, 2)),
        
        Flatten(),
        Dense(32, kernel_regularizer=l2(0.001)),
        ReLU(),
        Dropout(0.3),
        
        Dense(16, kernel_regularizer=l2(0.001)),
        ReLU(),
        Dropout(0.3),
        
        Dense(1, activation='sigmoid')
    ])
    
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                  loss='binary_crossentropy',
                  metrics=['accuracy'])
    return model


def main():
    print("Initializing Cloud Cry Detection Model Training...")
    
    X_train, Y_train, X_val, Y_val, X_test, Y_test = get_training_data()
    if X_train is None:
        print("No training data found. Please check your data/ICSD directory.")
        return
        
    print(f"Train Set: {len(X_train)} samples. Positive (Cry): {np.sum(Y_train==1)}, Negative (Non-Cry): {np.sum(Y_train==0)}")
    
    # Handle Class Imbalance
    weights = compute_class_weight('balanced', classes=np.unique(Y_train), y=Y_train)
    class_weight_dict = dict(enumerate(weights))
    print(f"Computed Class Weights: {class_weight_dict}")
    
    model = build_model()
    model.summary()
    
    # Callbacks
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', patience=3, factor=0.5, min_lr=1e-6)
    
    print("\nStarting training...")
    
    # If validation set was not loaded, use a subset of training data
    val_data = (X_val, Y_val) if X_val is not None else None
    val_split = 0.2 if val_data is None else 0.0
    
    model.fit(
        X_train, Y_train,
        validation_data=val_data,
        validation_split=val_split,
        epochs=50,
        batch_size=32,
        class_weight=class_weight_dict,
        callbacks=[early_stop, reduce_lr]
    )
    
    # Use validation data for evaluation if test data is missing
    eval_x, eval_y = (X_test, Y_test) if X_test is not None else (X_val, Y_val)
    if eval_x is not None:
        print("\nEvaluating on evaluation set...")
        Y_pred_prob = model.predict(eval_x)
        Y_pred = (Y_pred_prob >= 0.5).astype(int).flatten()
        
        print("\nClassification Report:")
        print(classification_report(eval_y, Y_pred, target_names=["Non-Cry (0)", "Cry (1)"]))
        
        print("\nConfusion Matrix:")
        print(confusion_matrix(eval_y, Y_pred))
    
    # Save Model and Threshold
    out_dir = "models/cloud_detection"
    os.makedirs(out_dir, exist_ok=True)
    
    model_path = os.path.join(out_dir, "cry_detection_cloud.h5")
    model.save(model_path)
    print(f"\nModel successfully saved to {model_path}")
    
    thresh_path = os.path.join(out_dir, "threshold.json")
    with open(thresh_path, "w") as f:
        json.dump({"threshold": 0.5}, f)
    print(f"Threshold configuration saved to {thresh_path}")

if __name__ == "__main__":
    main()

