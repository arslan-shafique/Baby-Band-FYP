"""
Cloud cry detection inference module.
"""
import os
import json
import tensorflow as tf
from ml_model.cry_classification.preprocess import preprocess_audio

class CryDetector:
    def __init__(self, model_path: str, threshold: float = 0.5):
        self.model_path = model_path
        self.threshold = threshold
        
        # Load threshold from threshold.json if it exists next to the model
        model_dir = os.path.dirname(self.model_path)
        thresh_path = os.path.join(model_dir, "threshold.json")
        if os.path.exists(thresh_path):
            try:
                with open(thresh_path, 'r') as f:
                    data = json.load(f)
                    self.threshold = data.get("threshold", self.threshold)
            except Exception as e:
                print(f"Warning: failed to load threshold.json - {e}")
                
        # Load model once at init
        try:
            self.model = tf.keras.models.load_model(self.model_path, compile=False)
        except Exception as e:
            print(f"Failed to load cloud detection model: {e}")
            self.model = None

    def is_cry(self, audio_bytes: bytes) -> tuple[bool, float]:
        """
        Runs the detection model on raw audio bytes.
        Returns (is_cry, confidence)
        """
        if not self.model:
            return False, 0.0
            
        # Use shared preprocessing
        features = preprocess_audio(audio_bytes)
        
        # Predict
        prediction = self.model.predict(features, verbose=0)
        confidence = float(prediction[0][0])
        
        return (confidence >= self.threshold, confidence)
