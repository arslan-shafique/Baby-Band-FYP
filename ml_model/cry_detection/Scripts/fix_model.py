#!/usr/bin/env python3

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, BatchNormalization, Activation
import numpy as np

print("=" * 70)
print("BUILDING FULLY CONVOLUTIONAL SEQUENTIAL MODEL (KERAS 3 FIX)")
print("=" * 70)

print("\n[1/5] Loading original weights...")
old_model = tf.keras.models.load_model("../models/cry_detection/cnn_model-v2.h5")

print("\n[2/5] Architecting Fully Convolutional Graph via Sequential API...")
# Keras 3 often crashes on converting Functional models, so we convert the FCN
# back into a Sequential model.
model = Sequential([
    # Block 1
    tf.keras.Input(batch_shape=(1, 128, 26, 1)),
    Conv2D(16, (3, 3), padding='same'),
    BatchNormalization(),
    Activation('relu'),
    MaxPooling2D((2, 2)),

    # Block 2
    Conv2D(32, (3, 3), padding='same'),
    BatchNormalization(),
    Activation('relu'),
    MaxPooling2D((2, 2)),

    # Block 3
    Conv2D(32, (3, 3), padding='same'),
    BatchNormalization(),
    Activation('relu'),
    MaxPooling2D((2, 2)),

    # --- THE ABSOLUTE FIX ---
    # Instead of flattening, we physically compress the spatial dimensions 
    # executing a Conv2D with a (16, 3) kernel. Mathematically mirrors Dense.
    Conv2D(32, (16, 3), padding='valid', activation='relu'),

    # Apply 1x1 convolutions which mimic fully-connected layers purely natively
    Conv2D(16, (1, 1), padding='valid', activation='relu'),
    Conv2D(1, (1, 1), padding='valid', activation='sigmoid')
])

print("\n[3/5] Transplanting and reshaping trained weights to Convolutional format...")
# Carefully extract weights from only the layers in the old and new models that have them.
old_weights = [layer.get_weights() for layer in old_model.layers if len(layer.get_weights()) > 0]
new_weight_layers = [layer for layer in model.layers if len(layer.get_weights()) > 0]

# 0-5 are the standard Conv2D and BatchNormalization layers which haven't changed shape
for i in range(6):
    new_weight_layers[i].set_weights(old_weights[i])

# 6 is Dense(32) -> Conv2D(32) kernel and bias
old_dense_1_w, old_dense_1_b = old_weights[6]
# Shape map: (1536, 32) -> (16, 3, 32, 32)
new_conv_1_w = old_dense_1_w.reshape(16, 3, 32, 32)
new_weight_layers[6].set_weights([new_conv_1_w, old_dense_1_b])

# 7 is Dense(16) -> Conv2D(16) kernel and bias
old_dense_2_w, old_dense_2_b = old_weights[7]
# Shape map: (32, 16) -> (1, 1, 32, 16)
new_conv_2_w = old_dense_2_w.reshape(1, 1, 32, 16)
new_weight_layers[7].set_weights([new_conv_2_w, old_dense_2_b])

# 8 is Dense(1) -> Conv2D(1) kernel and bias
old_dense_3_w, old_dense_3_b = old_weights[8]
# Shape map: (16, 1) -> (1, 1, 16, 1)
new_conv_3_w = old_dense_3_w.reshape(1, 1, 16, 1)
new_weight_layers[8].set_weights([new_conv_3_w, old_dense_3_b])

print("\n[4/5] Executing precise TFLite conversion parameters from Hardware PDF...")
# KERAS 3 BUG WORKAROUND:
# from_keras_model() crashes with "NoneType object is not callable" in modern Keras 3 environments.
# To bypass, we serialize the raw TensorFlow graph to disk and load it back without Keras AST tracking.
export_dir = "temp_saved_model"
try:
    model.export(export_dir)
except AttributeError:
    model.save(export_dir)

converter = tf.lite.TFLiteConverter.from_saved_model(export_dir)
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]

# Because our FCN completely eliminated the Flatten() layer natively, we can now safely
# use the default MLIR new converter without fear of SHAPE/PACK injection!
# This is required because from_saved_model crashes if experimental_new_converter=False
converter.experimental_new_converter = True

converter.inference_input_type = tf.float32
converter.inference_output_type = tf.float32

tflite_model = converter.convert()

output_filename = "cnn_model_fixed.tflite"
with open(output_filename, "wb") as f:
    f.write(tflite_model)
    
print(f"\n[5/5] ✓ Model exported beautifully to {output_filename} ({len(tflite_model) / 1024:.1f} KB)")

print("\n" + "=" * 70)
print("FINAL HARDWARE TEAM VERIFICATION (OP LIST)")
print("=" * 70)
interpreter = tf.lite.Interpreter(model_path=output_filename)
interpreter.allocate_tensors()
for op in interpreter._get_ops_details():
    # Ignore the dynamic DELEGATE nodes inserted by PC interpreters, 
    # we just want the raw model ops intended for ESP32.
    if op['op_name'] != "DELEGATE":
        print(f"✔ {op['op_name']}")