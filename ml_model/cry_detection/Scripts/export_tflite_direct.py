#!/usr/bin/env python3
"""
export_tflite_direct.py — Export the trained Keras model directly to TFLite.

Bypasses fix_model.py entirely. No FCN conversion, no weight reshaping.
Uses the original Flatten → Dense architecture which TFLite Micro supports
via RESHAPE + FULLY_CONNECTED ops.

IMPORTANT: Rebuilds the model with a fixed batch_size=1 input so that
Flatten compiles to a static RESHAPE op, avoiding SHAPE/STRIDED_SLICE/PACK
ops that TFLite Micro cannot handle.
"""

import os
import sys
import numpy as np

# ============================================================================
# STEP 1: Load the trained Keras model
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))

H5_PATH = os.path.join(SCRIPT_DIR, "..", "models", "cry_detection", "cnn_model-v2.h5")
OUTPUT_TFLITE = os.path.join(SCRIPT_DIR, "..", "models", "cry_detection", "cnn_model_direct.tflite")
OUTPUT_HEADER = os.path.join(PROJECT_ROOT, "hardware", "include", "model_data.h")

print("=" * 70)
print("DIRECT TFLITE EXPORT (NO FCN CONVERSION)")
print("=" * 70)

import tensorflow as tf
print(f"\nTensorFlow version: {tf.__version__}")

print(f"\n[1/6] Loading original Keras model from {H5_PATH}...")
model = tf.keras.models.load_model(H5_PATH)
model.summary()

# ============================================================================
# STEP 2: Verify the model works before export
# ============================================================================

print(f"\n[2/6] Pre-export verification...")
test_zeros = np.zeros((1, 128, 26, 1), dtype=np.float32)
test_rand = np.random.randn(1, 128, 26, 1).astype(np.float32)

out_zeros = model.predict(test_zeros, verbose=0).flatten()[0]
out_rand = model.predict(test_rand, verbose=0).flatten()[0]
print(f"  Keras zero-input:   {out_zeros:.6f}")
print(f"  Keras random-input: {out_rand:.6f}")

print(f"\n[3/6] Rebuilding model with fixed batch_size=1 and converting to TFLite...")

# Rebuild the model with a fixed batch_size=1 input.
# This is critical: without it, Flatten generates SHAPE/STRIDED_SLICE/PACK
# ops for dynamic shape inference, which TFLite Micro does NOT support.
from tensorflow.keras import layers, models

fixed_model = models.Sequential()
fixed_model.add(layers.Input(batch_shape=(1, 128, 26, 1)))

# Copy all layers except the original InputLayer
for layer in model.layers:
    if 'input' in layer.name:
        continue
    fixed_model.add(layer)

# Verify the fixed model produces identical output
fixed_out = fixed_model.predict(test_zeros, verbose=0).flatten()[0]
print(f"  Fixed model zero-input: {fixed_out:.6f} (original: {out_zeros:.6f})")
assert abs(fixed_out - out_zeros) < 1e-5, "Fixed model output diverged!"

# Convert using from_keras_model first, fall back to saved_model
try:
    converter = tf.lite.TFLiteConverter.from_keras_model(fixed_model)
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    converter.inference_input_type = tf.float32
    converter.inference_output_type = tf.float32
    tflite_model = converter.convert()
    print(f"  ✅ Direct conversion succeeded!")
except Exception as e:
    print(f"  ⚠ Direct conversion failed: {e}")
    print(f"  Trying saved_model workaround...")
    
    import tempfile
    export_dir = tempfile.mkdtemp()
    try:
        fixed_model.export(export_dir)
    except AttributeError:
        fixed_model.save(export_dir)
    
    converter = tf.lite.TFLiteConverter.from_saved_model(export_dir)
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    converter.inference_input_type = tf.float32
    converter.inference_output_type = tf.float32
    tflite_model = converter.convert()
    print(f"  ✅ SavedModel conversion succeeded!")

print(f"  Model size: {len(tflite_model)} bytes ({len(tflite_model)/1024:.1f} KB)")

# Save the .tflite file
with open(OUTPUT_TFLITE, "wb") as f:
    f.write(tflite_model)
print(f"  Saved to: {OUTPUT_TFLITE}")

# ============================================================================
# STEP 4: Verify the TFLite model matches the Keras model
# ============================================================================

print(f"\n[4/6] Post-export verification...")

interpreter = tf.lite.Interpreter(model_content=tflite_model)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print(f"  Input shape:  {input_details[0]['shape']}")
print(f"  Input dtype:  {input_details[0]['dtype']}")
print(f"  Output shape: {output_details[0]['shape']}")
print(f"  Output dtype: {output_details[0]['dtype']}")

# Test with zeros
interpreter.set_tensor(input_details[0]['index'], test_zeros)
interpreter.invoke()
tflite_zeros = interpreter.get_tensor(output_details[0]['index']).flatten()[0]

# Test with same random input
interpreter.set_tensor(input_details[0]['index'], test_rand)
interpreter.invoke()
tflite_rand = interpreter.get_tensor(output_details[0]['index']).flatten()[0]

print(f"\n  Comparison (Keras vs TFLite):")
print(f"    Zero input:   Keras={out_zeros:.6f}  TFLite={tflite_zeros:.6f}  diff={abs(out_zeros-tflite_zeros):.6f}")
print(f"    Random input: Keras={out_rand:.6f}  TFLite={tflite_rand:.6f}  diff={abs(out_rand-tflite_rand):.6f}")

if abs(out_zeros - tflite_zeros) < 0.001 and abs(out_rand - tflite_rand) < 0.001:
    print(f"  ✅ PERFECT MATCH: TFLite model faithfully represents the Keras model")
else:
    print(f"  ⚠ SOME DIVERGENCE detected (may be acceptable floating point differences)")

# Print ops used
print(f"\n  Ops used in model:")
for op in interpreter._get_ops_details():
    name = op.get('op_name', 'UNKNOWN')
    if name != 'DELEGATE':
        print(f"    ✔ {name}")

# ============================================================================
# STEP 5: Generate C header file for ESP32
# ============================================================================

print(f"\n[5/6] Generating C header for ESP32...")

with open(OUTPUT_HEADER, "w") as f:
    f.write("// Auto-generated TFLite model data\n")
    f.write("// Source: cnn_model-v2.h5 → direct TFLite export (no FCN conversion)\n")
    f.write(f"// Size: {len(tflite_model)} bytes\n\n")
    f.write("#ifndef MODEL_DATA_H\n")
    f.write("#define MODEL_DATA_H\n\n")
    f.write(f"const unsigned char cnn_model_tflite[] = {{\n")
    
    for i in range(0, len(tflite_model), 12):
        chunk = tflite_model[i:i+12]
        hex_str = ", ".join(f"0x{b:02x}" for b in chunk)
        if i + 12 < len(tflite_model):
            f.write(f"  {hex_str},\n")
        else:
            f.write(f"  {hex_str}\n")
    
    f.write("};\n\n")
    f.write(f"const unsigned int cnn_model_tflite_len = {len(tflite_model)};\n\n")
    f.write("#endif // MODEL_DATA_H\n")

print(f"  ✅ Header written to: {OUTPUT_HEADER}")
print(f"  Array name: cnn_model_tflite")
print(f"  Length var:  cnn_model_tflite_len = {len(tflite_model)}")

# ============================================================================
# STEP 6: Final summary
# ============================================================================

print(f"\n[6/6] Verifying header byte integrity...")

# Re-read the header and verify
with open(OUTPUT_HEADER, "r") as f:
    header_content = f.read()

import re
hex_values = re.findall(r'0x([0-9a-fA-F]{2})', header_content)
header_bytes = bytes([int(h, 16) for h in hex_values])

if header_bytes == tflite_model:
    print(f"  ✅ Header bytes are IDENTICAL to .tflite file ({len(header_bytes)} bytes)")
else:
    print(f"  🔴 MISMATCH: header has {len(header_bytes)} bytes, tflite has {len(tflite_model)} bytes")

print(f"\n{'=' * 70}")
print("EXPORT COMPLETE")
print("=" * 70)
print(f"\nNext steps for hardware team:")
print(f"  1. The header file is already at: {OUTPUT_HEADER}")
print(f"  2. Flash the firmware with PlatformIO Upload button")
print(f"  3. Check the MODEL DIAGNOSTICS output on boot")
print(f"  4. Zero-input confidence should be ~{out_zeros:.4f} (not 0.4967)")
