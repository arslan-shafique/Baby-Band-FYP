
import os
import numpy as np
import tensorflow as tf
from pathlib import Path

# ============================================================================
# CONFIG
# ============================================================================

MODELS_DIR = Path(__file__).parent.parent / "models" / "cry_detection"
INPUT_MODEL = MODELS_DIR / "cnn_model_v1.h5"
OUTPUT_MODEL = MODELS_DIR / "cnn_model_v1_quantized.tflite"

# ============================================================================
# QUANTIZE MODEL
# ============================================================================

def convert_to_tflite_quantized():
    """
    Convert Keras model to TFLite with int8 quantization.
    This reduces model size ~4x and speeds up inference on microcontrollers.
    """
    
    if not INPUT_MODEL.exists():
        print(f"ERROR: Model not found at {INPUT_MODEL}")
        exit(1)
    
    print(f"Loading model from {INPUT_MODEL}...")
    model = tf.keras.models.load_model(INPUT_MODEL)
    
    print(f"Model architecture:")
    model.summary()
    
    # Create converter
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Optimization 1: Post-training quantization (int8)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    # Convert
    print("\nConverting to TFLite...")
    tflite_model = converter.convert()
    
    # Save
    with open(OUTPUT_MODEL, 'wb') as f:
        f.write(tflite_model)
    
    # Check size
    input_size = INPUT_MODEL.stat().st_size / (1024 * 1024)  # MB
    output_size = OUTPUT_MODEL.stat().st_size / (1024 * 1024)  # MB
    compression_ratio = input_size / output_size
    
    print(f"\n✅ Conversion complete!")
    print(f"Original model:    {input_size:.2f} MB")
    print(f"Quantized model:   {output_size:.2f} MB")
    print(f"Compression ratio: {compression_ratio:.1f}x")
    print(f"\nSaved to: {OUTPUT_MODEL}")
    
# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("Converting CNN model to TensorFlow Lite\n")
    
    convert_to_tflite_quantized()
    test_inference()
    
    print("\n✅ Done!")
    print(f"\nNext steps:")
    print(f"1. Copy {OUTPUT_MODEL} to your ESP32 project")
    print(f"2. Use TensorFlow Lite Micro to run inference on device")
    print(f"3. See esp32_inference.cpp for example C++ code")
