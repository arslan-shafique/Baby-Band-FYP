import os
import json
import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from train import load_data, create_dataset
from model import SparseCategoricalFocalLoss

# 1. Load the model
model_path = "models/best_model.keras"
model = tf.keras.models.load_model(model_path, custom_objects={'SparseCategoricalFocalLoss': SparseCategoricalFocalLoss})

# 2. Load the test set
test_paths, test_y = load_data("test")
test_ds = create_dataset(test_paths, test_y, batch_size=32, shuffle=False)

# Predict
y_pred_probs = model.predict(test_ds)
y_pred = np.argmax(y_pred_probs, axis=1)

# The data generator returns labels as integer indices, and keeps the original order since shuffle=False
y_true = np.array(test_y)

class_names = ['Hunger', 'Tiredness', 'Discomfort', 'Diaper']

# Classification report
print("=== CLASSIFICATION REPORT ===")
print(classification_report(y_true, y_pred, target_names=class_names, zero_division=0))

# Confusion matrix
print("=== CONFUSION MATRIX ===")
cm = confusion_matrix(y_true, y_pred)
print(repr(cm))

# Overall accuracy
print(f"\nOverall Accuracy: {accuracy_score(y_true, y_pred):.4f}")

# Training history
history_path = "logs/training_history.json"
if os.path.exists(history_path):
    with open(history_path, "r") as f:
        history = json.load(f)
        
    final_train_acc = history["accuracy"][-1]
    final_val_acc = history["val_accuracy"][-1]
    final_train_loss = history["loss"][-1]
    final_val_loss = history["val_loss"][-1]
    
    print("\n=== TRAINING HISTORY ===")
    print(f"Final Train Accuracy: {final_train_acc:.4f}")
    print(f"Final Val Accuracy:   {final_val_acc:.4f}")
    print(f"Final Train Loss:     {final_train_loss:.4f}")
    print(f"Final Val Loss:       {final_val_loss:.4f}")
