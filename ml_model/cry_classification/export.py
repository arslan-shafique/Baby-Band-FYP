import os
import json
import shutil
import tensorflow as tf

MODELS_DIR = "models/"
LABEL_MAP = {
    0: "hungry", 
    1: "tired", 
    2: "discomfort",
    3: "diaper"
}

def main():
    if not os.path.exists(MODELS_DIR):
        print(f"Error: {MODELS_DIR} not found.")
        return
        
    best_model_path = os.path.join(MODELS_DIR, "best_model.keras")
    export_keras_path = os.path.join(MODELS_DIR, "model.keras")
    export_tflite_path = os.path.join(MODELS_DIR, "model.tflite")
    
    if os.path.exists(best_model_path):
        # 1. Copy the keras model
        shutil.copy(best_model_path, export_keras_path)
        print(f"Exported Keras model to {export_keras_path}")
        
        # 2. Convert to TFLite
        try:
            print("Converting model to TFLite...")
            # Load original weights (bypassing custom loss with compile=False)
            original_model = tf.keras.models.load_model(best_model_path, compile=False)
            
            # TFLite Micro on ESP32 requires a STATIC batch size for LSTM layers!
            # We rebuild the exact same model but hardcode batch_size=1
            from model import build_model
            static_model = build_model(input_shape=(128, 128, 1), num_classes=4, batch_size=1)
            static_model.set_weights(original_model.get_weights())
            
            converter = tf.lite.TFLiteConverter.from_keras_model(static_model)
            
            # ESP32 requires built-in ops.
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
            
            tflite_model = converter.convert()
            
            with open(export_tflite_path, "wb") as f:
                f.write(tflite_model)
            print(f"Successfully exported TFLite model to {export_tflite_path}")
        except Exception as e:
            print(f"Error during TFLite conversion: {e}")
            
    else:
        print(f"Warning: {best_model_path} not found. Ensure train.py has completed.")
        
    label_map_path = os.path.join(MODELS_DIR, "label_map.json")
    with open(label_map_path, "w") as f:
        json.dump(LABEL_MAP, f, indent=4)
    print(f"Saved label map to {label_map_path}")
    
    config_path = os.path.join(MODELS_DIR, "feature_config.json")
    if os.path.exists(config_path):
        print(f"Feature config already exists at {config_path}")
    else:
        print(f"Warning: {config_path} not found. Ensure features.py has completed.")
        
    print("Export process complete. Artifacts are ready in the models/ directory.")

if __name__ == "__main__":
    main()
