import numpy as np
import tensorflow as tf
from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix
import matplotlib.pyplot as plt
import os

print("Loading test data...")
X_test = np.load("../data/processed_v2/test/X_test.npy")
y_test = np.load("../data/processed_v2/test/y_test.npy")


print("Normalizing test data...")
stats = np.load("../models/cry_detection/normalization_stats-v2.npz")
X_test = (X_test - stats['mean']) / stats['std']

X_test = np.expand_dims(X_test, axis=-1)

print("Loading model...")
model = tf.keras.models.load_model("../models/cry_detection/cnn_model-v2.h5")

print("Getting predictions...")
y_pred_probs = model.predict(X_test).flatten()

thresholds = [0.35, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 0.98, 0.99]

print("\n" + "="*70)
print("THRESHOLD ANALYSIS")
print("="*70)
print(f"{'Threshold':<10} | {'Precision':<10} | {'Recall':<10} | {'F1 Score':<10} | {'FP':<5} | {'FN':<5}")
print("-" * 70)

for t in thresholds:
    y_pred = (y_pred_probs > t).astype(int)
    p = precision_score(y_test, y_pred, zero_division=0)
    r = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    # cm[0,0] TN, cm[0,1] FP, cm[1,0] FN, cm[1,1] TP
    fp = cm[0, 1] if cm.shape == (2,2) else 0
    fn = cm[1, 0] if cm.shape == (2,2) else 0
    print(f"{t:<10.2f} | {p:<10.4f} | {r:<10.4f} | {f1:<10.4f} | {fp:<5} | {fn:<5}")
print("="*70)

print("\n\n" + "="*70)
print("TEMPORAL SMOOTHING (3-WINDOW VOTING) ANALYSIS")
print("Simulating a requirement for sustained audio (Avg. prob over 3 frames)")
print("="*70)
print(f"{'Threshold':<10} | {'Precision':<10} | {'Recall':<10} | {'F1 Score':<10} | {'FP':<5} | {'FN':<5}")
print("-" * 70)

# Simulate continuous audio by separating the classes and applying a moving average
cry_probs = y_pred_probs[y_test == 1]
noncry_probs = y_pred_probs[y_test == 0]

# 3-window moving average
window = 3
if len(cry_probs) >= window and len(noncry_probs) >= window:
    smoothed_cry = np.convolve(cry_probs, np.ones(window)/window, mode='valid')
    smoothed_noncry = np.convolve(noncry_probs, np.ones(window)/window, mode='valid')

    # Combine back into a test set
    smooth_y_test = np.concatenate([np.ones_like(smoothed_cry), np.zeros_like(smoothed_noncry)])
    smooth_y_pred_probs = np.concatenate([smoothed_cry, smoothed_noncry])

    for t in thresholds:
        y_pred = (smooth_y_pred_probs > t).astype(int)
        p = precision_score(smooth_y_test, y_pred, zero_division=0)
        r = recall_score(smooth_y_test, y_pred, zero_division=0)
        f1 = f1_score(smooth_y_test, y_pred, zero_division=0)
        cm = confusion_matrix(smooth_y_test, y_pred)
        fp = cm[0, 1] if cm.shape == (2,2) else 0
        fn = cm[1, 0] if cm.shape == (2,2) else 0
        
        print(f"{t:<10.2f} | {p:<10.4f} | {r:<10.4f} | {f1:<10.4f} | {fp:<5} | {fn:<5}")
print("="*70)
