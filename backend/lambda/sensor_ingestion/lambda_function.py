"""
AWS Lambda: Sensor Data Ingestion

This Lambda function is triggered by an AWS IoT Core Rule when the ESP32
publishes sensor data via MQTT.

Flow: ESP32 → MQTT → AWS IoT Core → IoT Rule → This Lambda → Firestore

DEPLOYMENT:
1. Zip this file + requirements.txt dependencies
2. Upload to AWS Lambda
3. Set environment variable: FIREBASE_CREDENTIALS (base64 encoded service account JSON)
4. Create IoT Rule: SELECT * FROM 'smartbabyband/sensors' → Lambda

MQTT TOPIC: smartbabyband/sensors/{device_id}
"""

import json
import os
import base64
import tempfile
from datetime import datetime


def lambda_handler(event, context):
    """
    Lambda entry point — receives MQTT payload from IoT Core.

    Expected MQTT payload (from ESP32):
    {
        "device_id": "ESP32_001",
        "baby_id": "firestore_baby_doc_id",
        "heart_rate": 120,
        "spo2": 98,
        "temperature": 22.5,
        "humidity": 55,
        "motion": {"x": 0.1, "y": -0.3, "z": 9.8}
    }
    """
    import firebase_admin
    from firebase_admin import credentials, firestore

    # Initialize Firebase (Lambda cold start)
    if not firebase_admin._apps:
        # Decode service account from environment variable
        cred_base64 = os.environ.get("FIREBASE_CREDENTIALS", "")
        cred_json = base64.b64decode(cred_base64).decode("utf-8")

        # Write to temp file (Firebase SDK needs a file path)
        cred_path = os.path.join(tempfile.gettempdir(), "firebase-cred.json")
        with open(cred_path, "w") as f:
            f.write(cred_json)

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Parse the MQTT payload
    sensor_data = {
        "device_id": event.get("device_id", "unknown"),
        "baby_id": event.get("baby_id", ""),
        "heart_rate": event.get("heart_rate"),
        "spo2": event.get("spo2"),
        "temperature": event.get("temperature"),
        "humidity": event.get("humidity"),
        "motion": event.get("motion", {"x": 0, "y": 0, "z": 0}),
        "timestamp": datetime.utcnow(),
    }

    # Write to Firestore
    db.collection("sensor_data").add(sensor_data)

    print(f"✅ Sensor data saved for device {sensor_data['device_id']}")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Sensor data saved successfully"}),
    }
