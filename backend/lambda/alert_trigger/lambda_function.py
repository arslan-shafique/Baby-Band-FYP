"""
AWS Lambda: Alert Trigger

This Lambda function can be triggered by Firestore (via Cloud Functions) or
invoked by the sensor_ingestion Lambda to check alert thresholds.

When a new sensor reading arrives, this checks:
- Heart rate > threshold → create critical notification
- Temperature > threshold → create warning notification
- SpO2 < threshold → create critical notification

DEPLOYMENT: Same as sensor_ingestion Lambda.
"""

import json
import os
import base64
import tempfile
from datetime import datetime


def lambda_handler(event, context):
    """
    Check sensor data against alert thresholds and create notifications.

    Expected input: sensor_data document from Firestore
    """
    import firebase_admin
    from firebase_admin import credentials, firestore

    # Initialize Firebase
    if not firebase_admin._apps:
        cred_base64 = os.environ.get("FIREBASE_CREDENTIALS", "")
        cred_json = base64.b64decode(cred_base64).decode("utf-8")
        cred_path = os.path.join(tempfile.gettempdir(), "firebase-cred.json")
        with open(cred_path, "w") as f:
            f.write(cred_json)
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Get sensor data from event
    baby_id = event.get("baby_id", "")
    heart_rate = event.get("heart_rate")
    temperature = event.get("temperature")
    spo2 = event.get("spo2")

    # Find the parent user for this baby
    baby_docs = db.collection("baby_profiles").where("__name__", "==", baby_id).limit(1).stream()
    user_id = ""
    for doc in baby_docs:
        user_id = doc.to_dict().get("user_id", "")

    if not user_id:
        print(f"⚠️ No user found for baby_id: {baby_id}")
        return {"statusCode": 200, "body": "No user found"}

    # Get user's alert thresholds
    user_doc = db.collection("users").document(user_id).get()
    settings = user_doc.to_dict().get("settings", {}) if user_doc.exists else {}
    hr_threshold = settings.get("hr_alert_threshold", 150)
    temp_threshold = settings.get("temp_alert_threshold", 37.5)

    alerts = []

    # Check heart rate
    if heart_rate and heart_rate > hr_threshold:
        alerts.append({
            "type": "critical",
            "title": "⚠️ High Heart Rate Alert",
            "message": f"Heart rate reached {heart_rate} BPM (threshold: {hr_threshold} BPM)",
        })

    # Check temperature
    if temperature and temperature > temp_threshold:
        alerts.append({
            "type": "warning",
            "title": "🌡️ High Temperature Alert",
            "message": f"Temperature reached {temperature}°C (threshold: {temp_threshold}°C)",
        })

    # Check SpO2
    if spo2 and spo2 < 90:
        alerts.append({
            "type": "critical",
            "title": "🫁 Low Blood Oxygen Alert",
            "message": f"SpO2 dropped to {spo2}% (normal: >95%)",
        })

    # Create notifications
    for alert in alerts:
        db.collection("notifications").add({
            "user_id": user_id,
            "baby_id": baby_id,
            "type": alert["type"],
            "title": alert["title"],
            "message": alert["message"],
            "is_read": False,
            "created_at": datetime.utcnow(),
        })
        print(f"🔔 Alert created: {alert['title']}")

    return {
        "statusCode": 200,
        "body": json.dumps({"alerts_created": len(alerts)}),
    }
