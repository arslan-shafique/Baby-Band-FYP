"""
Cry Service — Business logic for cry classification and cry event management.

This service:
1. Loads the TFLite cry detection model
2. Runs inference on MFCC features from ESP32
3. Stores classification results in Firestore
4. Queries cry event history
"""

from datetime import datetime, timedelta
from typing import Optional, List
from app.firebase_client import get_firestore_client
from app.schemas.cry_event import CryClassifyRequest, CryClassifyResponse
from app.config import get_settings
from app.services.notification_service import NotificationService

import os
import sys
import tempfile
import numpy as np
import soundfile as sf
from firebase_admin import db

# Ensure features.py is accessible
ML_MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ml_model/cry_classification"))
if ML_MODEL_DIR not in sys.path:
    sys.path.append(ML_MODEL_DIR)
try:
    from features import extract_features
except ImportError:
    print("Warning: Could not import features.py from ml_model")
    extract_features = None

# Cry type labels — must match your training labels
CRY_LABELS = ["hungry", "tired", "discomfort", "diaper"]


class CryService:
    """Service for cry classification and event management."""

    _tflite_model = None
    _keras_model_instance = None

    def __init__(self):
        self.db = get_firestore_client()
        self.collection = "cry_events"

    def _load_model(self):
        """
        Lazy-load the TFLite model.
        Called only when classify_cry() is first used.
        """
        if CryService._tflite_model is not None:
            self._model = CryService._tflite_model
            return

        settings = get_settings()
        import tensorflow as tf
        print(f"Loading ML Model from: {settings.CRY_MODEL_PATH}")
        CryService._tflite_model = tf.lite.Interpreter(model_path=settings.CRY_MODEL_PATH)
        CryService._tflite_model.allocate_tensors()
        self._model = CryService._tflite_model
        
        self.input_details = self._model.get_input_details()
        self.output_details = self._model.get_output_details()

    def _load_keras_model(self):
        """Lazy-load the Keras classification model globally."""
        if CryService._keras_model_instance is not None:
            self._keras_model = CryService._keras_model_instance
            return

        settings = get_settings()
        import tensorflow as tf
        print(f"Loading Keras Model from: {settings.KERAS_MODEL_PATH}")
        try:
            CryService._keras_model_instance = tf.keras.models.load_model(settings.KERAS_MODEL_PATH, compile=False)
            self._keras_model = CryService._keras_model_instance
        except Exception as e:
            print(f"Failed to load Keras model: {e}")
            self._keras_model = None

    async def predict_audio(self, audio_bytes: bytes, device_id: str = "babyband_01") -> dict:
        """
        New prediction pipeline:
        1. Receive raw audio bytes (16-bit PCM float32/int16)
        2. Convert to wav in memory
        3. Extract features using features.py
        4. Run Keras model inference
        5. Push to Firebase RTDB
        """
        self._load_keras_model()
        if not hasattr(self, '_keras_model') or not self._keras_model:
            raise Exception("Keras model not loaded.")

        if not extract_features:
            raise Exception("features.py could not be loaded. Check path.")

        # Parse raw audio (Assuming 16-bit PCM)
        try:
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception as e:
            raise Exception(f"Failed to parse audio bytes: {e}")

        # Extract features using temporary wav file
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_name = tmp.name
        tmp.close() # Close immediately so we can write/read by name without lock issues
        
        try:
            sf.write(tmp_name, audio_data, 16000)
            spectrogram = extract_features(tmp_name)
        finally:
            if os.path.exists(tmp_name):
                try:
                    os.remove(tmp_name)
                except Exception:
                    pass

        # Run Inference -> Add batch dimension (1, 128, 128, 1)
        input_batch = np.expand_dims(spectrogram, axis=0)
        predictions = self._keras_model.predict(input_batch)[0]
        
        pred_dict = {label: float(prob) for label, prob in zip(CRY_LABELS, predictions)}
        cry_type = max(pred_dict, key=pred_dict.get)
        confidence = pred_dict[cry_type]

        # Read user's cry sensitivity setting from Firestore
        confidence_threshold = 0.60  # default: Medium
        try:
            from firebase_admin import firestore as fs_admin
            db_fs = fs_admin.client()
            # Find user from device
            baby_docs = db_fs.collection("baby_profiles").where("device_id", "==", device_id).limit(1).stream()
            for baby_doc in baby_docs:
                user_id = baby_doc.to_dict().get("user_id", "")
                if user_id:
                    user_doc = db_fs.collection("users").document(user_id).get()
                    if user_doc.exists:
                        settings = user_doc.to_dict().get("settings", {})
                        sensitivity = settings.get("cry_sensitivity", "Medium")
                        sensitivity_map = {"Low": 0.80, "Medium": 0.60, "High": 0.40}
                        confidence_threshold = sensitivity_map.get(sensitivity, 0.60)
        except Exception as e:
            print(f"⚠️ Could not read cry sensitivity, using default: {e}")

        if confidence < confidence_threshold:
            cry_type = "unknown"

        # Push to RTDB
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "device_id": device_id,
            "cry_label": cry_type,
            "confidence": confidence,
            "all_predictions": pred_dict
        }
        
        try:
            ref = db.reference("cry_classifications")
            ref.push(payload)
            print("✅ Successfully pushed prediction to Firebase RTDB")
        except Exception as e:
            print(f"Failed to push to RTDB: {e}")

        return payload

    async def classify_cry(self, request: CryClassifyRequest) -> CryClassifyResponse:
        """
        Run ML inference on MFCC audio features.
        """
        self._load_model()
        import numpy as np

        # Convert to numpy array
        input_data = np.array(request.audio_features, dtype=np.float32)

        # Reshape to expected input shape
        expected_shape = self.input_details[0]['shape']
        input_data = input_data.reshape(expected_shape)

        # Run inference
        self._model.set_tensor(self.input_details[0]['index'], input_data)
        self._model.invoke()

        # Get output
        output_data = self._model.get_tensor(self.output_details[0]['index'])[0]

        # Map predictions to labels
        predictions = {label: float(prob) for label, prob in zip(CRY_LABELS, output_data)}
        
        cry_type = max(predictions, key=predictions.get)
        confidence = predictions[cry_type]

        # If confidence is lower than 72%, classify as "unknown"
        if confidence < 0.72:
            cry_type = "unknown"

        # Store the event in Firestore
        event_data = {
            "baby_id": request.baby_id,
            "cry_type": cry_type,
            "confidence": confidence,
            "duration_seconds": request.duration_seconds,
            "timestamp": datetime.utcnow(),
        }
        self.db.collection(self.collection).add(event_data)

        # Trigger Real-Time Notification
        try:
            # 1. Fetch the baby profile to find the parent's user_id
            baby_doc = self.db.collection("baby_profiles").document(request.baby_id).get()
            if baby_doc.exists:
                user_id = baby_doc.to_dict().get("user_id")
                
                if user_id:
                    # 2. Determine the notification message
                    title = "Baby Cry Alert 🍼"
                    if cry_type == "hungry":
                        message = "Your baby might be hungry."
                    elif cry_type == "tired":
                        message = "Your baby seems tired and needs sleep."
                    elif cry_type == "discomfort":
                        message = "Your baby is experiencing discomfort."
                    elif cry_type == "diaper":
                        message = "Your baby might need a diaper change."
                    else:
                        message = "Your baby is crying! (Unknown reason)"
                        
                    # 3. Call the notification service
                    notif_service = NotificationService()
                    # We only await this because we want to trigger the push notification
                    await notif_service.create_notification(
                        user_id=user_id,
                        baby_id=request.baby_id,
                        title=title,
                        message=message,
                        notif_type="cry_alert"
                    )
        except Exception as e:
            print(f"Failed to send notification: {e}")

        return CryClassifyResponse(
            cry_type=cry_type,
            confidence=confidence,
            all_predictions=predictions,
        )

    async def get_history(
        self,
        baby_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        cry_type: Optional[str] = None,
        limit: int = 50,
    ) -> dict:
        """Get cry event history with optional filtering."""
        query = (
            self.db.collection(self.collection)
            .where("baby_id", "==", baby_id)
        )

        if start_date:
            query = query.where("timestamp", ">=", start_date)
        if end_date:
            query = query.where("timestamp", "<=", end_date)
        if cry_type:
            query = query.where("cry_type", "==", cry_type)

        query = query.order_by("timestamp", direction="DESCENDING").limit(limit)

        docs = list(query.stream())
        data = []
        for doc in docs:
            item = doc.to_dict()
            item["id"] = doc.id
            data.append(item)

        return {"data": data, "total": len(data)}

    async def get_latest_event(self, baby_id: str) -> Optional[dict]:
        """Get the most recent cry event for a baby."""
        docs = (
            self.db.collection(self.collection)
            .where("baby_id", "==", baby_id)
            .order_by("timestamp", direction="DESCENDING")
            .limit(1)
            .stream()
        )

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            return data

        return None
