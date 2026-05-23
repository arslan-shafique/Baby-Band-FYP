"""
🍼 Smart Baby Band - Hardware & ML Simulation Suite

This interactive suite acts as your physical Smart Baby Band wearable and ML pipeline.
It generates realistic vitals, environment logs, cry detections, and threshold-based
emergency notifications to Firestore/RTDB, allowing you to fully test the Flutter app
without any hardware!
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Adjust path so we can import from backend app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import firebase_admin
from firebase_admin import credentials, firestore, db

# --- Config ---
SERVICE_ACCOUNT_PATH = "firebase-service-account.json"
RTDB_URL = "https://smart-baby-band-default-rtdb.firebaseio.com"

# --- Colors for Terminal ---
CLR_HEADER = '\033[95m'
CLR_BLUE = '\033[94m'
CLR_GREEN = '\033[92m'
CLR_WARNING = '\033[93m'
CLR_FAIL = '\033[91m'
CLR_END = '\033[0m'
CLR_BOLD = '\033[1m'

def print_banner():
    print(f"{CLR_HEADER}{CLR_BOLD}")
    print(" 🍼  SMART BABY BAND - HARDWARE & ML PIPELINE SIMULATOR  🍼 ")
    print("=" * 60)
    print(f"{CLR_END}")
    print("Welcome! Use this tool to test cry classification and trigger alerts.")
    print("Make sure your Flutter app is running on your device or emulator.")
    print("-" * 60)

def init_firebase():
    """Initializes Firebase Admin SDK."""
    if not firebase_admin._apps:
        print(f"🔄 Connecting to Firebase using {SERVICE_ACCOUNT_PATH}...")
        try:
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred, {
                'databaseURL': RTDB_URL
            })
            print(f"{CLR_GREEN}✅ Successfully connected to Firebase!{CLR_END}\n")
        except Exception as e:
            print(f"{CLR_FAIL}❌ Failed to connect to Firebase: {e}{CLR_END}")
            print("Please ensure your firebase-service-account.json is in this folder.")
            sys.exit(1)

def get_linked_user_and_baby():
    """Finds the link between user and baby_profiles."""
    db_fs = firestore.client()
    profiles = db_fs.collection("baby_profiles").limit(1).get()
    
    if not profiles:
        print(f"{CLR_WARNING}⚠️ No baby profiles found in Firestore!{CLR_END}")
        print("Please register a baby profile in the app first.")
        return None, None
        
    profile = profiles[0].to_dict()
    device_id = profile.get("device_id", "babyband_01")
    user_id = profile.get("user_id", "")
    baby_name = profile.get("name", "Baby")
    
    print(f"👶 Mapped Baby Profile: {CLR_BOLD}{baby_name}{CLR_END} (Device ID: {device_id})")
    print(f"👤 Linked Parent UID: {user_id}\n")
    return user_id, device_id

def simulate_cry_event(user_id, device_id):
    """Simulates the Cry Detection and Classification ML pipeline."""
    db_fs = firestore.client()
    
    print(f"\n{CLR_BLUE}=== ML Cry Classification Simulator ==={CLR_END}")
    print("Select a cry reason to classify:")
    print("1) Hungry Cry")
    print("2) Tired Cry (Sleepy)")
    print("3) Discomfort Cry")
    print("4) Diaper Change needed")
    print("5) High Pain Cry (Will trigger critical notification!)")
    
    choice = input("Select option (1-5): ").strip()
    
    cry_types = {
        "1": ("hungry", 0.94, "Hunger"),
        "2": ("tired", 0.88, "Tiredness"),
        "3": ("discomfort", 0.82, "Discomfort"),
        "4": ("diaper", 0.91, "Wet Diaper"),
        "5": ("pain", 0.97, "Severe Pain")
    }
    
    if choice not in cry_types:
        print(f"{CLR_FAIL}Invalid choice. Cancelled.{CLR_END}")
        return
        
    cry_label, confidence, displayName = cry_types[choice]
    now = datetime.utcnow()
    
    # 1. Update Firebase RTDB (Live Cry classification)
    print("⚡ Pushing live cry detection to Realtime Database...")
    rtdb_ref = db.reference("cry_classifications")
    rtdb_ref.push({
        "timestamp": now.isoformat() + "Z",
        "device_id": device_id,
        "cry_label": cry_label,
        "confidence": confidence
    })
    
    # 2. Add to Firestore Cry Events collection
    print("💾 Saving Cry Event to Firestore History...")
    db_fs.collection("cry_events").add({
        "baby_id": device_id,
        "cry_type": cry_label,
        "confidence": confidence,
        "timestamp": now
    })
    
    # 3. If Pain / Critical, trigger a Notification alert immediately
    if cry_label == "pain":
        print("🚨 Critical Pain Cry detected! Triggering notification...")
        db_fs.collection("notifications").add({
            "user_id": user_id,
            "baby_id": device_id,
            "type": "critical",
            "title": "🚨 Sudden Pain Cry Detected",
            "message": f"Your baby is crying intensely (Severe Pain, confidence {confidence*100:.0f}%). Please check immediately!",
            "is_read": False,
            "created_at": now
        })
    else:
        # Standard cry info alert
        db_fs.collection("notifications").add({
            "user_id": user_id,
            "baby_id": device_id,
            "type": "warning",
            "title": "🍼 Cry Detected",
            "message": f"Cry reason classified as: {displayName} ({confidence*100:.0f}% confidence)",
            "is_read": False,
            "created_at": now
        })
        
    print(f"{CLR_GREEN}🎉 Success! Cry simulated. Look at your Mobile App's Dashboard & Alerts screen!{CLR_END}\n")

def simulate_realtime_vitals(user_id, device_id):
    """Simulates real-time sensor telemetry and evaluates alerts against parent thresholds."""
    db_fs = firestore.client()
    
    print(f"\n{CLR_BLUE}=== Vitals & Environmental Telemetry Simulator ==={CLR_END}")
    print("Choose vitals status:")
    print("1) Safe & Healthy (HR: 120 BPM, Temp: 36.5°C)")
    print("2) High Heart Rate Alert (HR: 185 BPM - Danger!)")
    print("3) High Temperature Alert (Temp: 39.1°C - Fever warning!)")
    
    choice = input("Select option (1-3): ").strip()
    
    # Load parent settings to read their dynamic alert thresholds
    print("🔍 Reading customized parent alert thresholds from Firestore...")
    user_doc = db_fs.collection("users").document(user_id).get()
    settings = {}
    if user_doc.exists:
        settings = user_doc.to_dict().get("settings", {})
        
    hr_thresh = settings.get("hr_alert_threshold", 150)
    temp_thresh = settings.get("temp_alert_threshold", 37.5)
    
    print(f"   ↳ Custom Heart Rate Threshold: {hr_thresh} BPM")
    print(f"   ↳ Custom Temperature Threshold: {temp_thresh}°C")
    
    if choice == "1":
        bpm = 120
        temp = 36.5
        humidity = 55.0
        status_msg = "Safe & Healthy"
    elif choice == "2":
        bpm = 185
        temp = 36.7
        humidity = 52.0
        status_msg = "Dangerous Heart Rate"
    elif choice == "3":
        bpm = 128
        temp = 39.1
        humidity = 48.0
        status_msg = "High Temperature Fever"
    else:
        print(f"{CLR_FAIL}Invalid choice. Cancelled.{CLR_END}")
        return
        
    now = datetime.utcnow()
    
    # 1. Pushing Vitals to Firestore
    print("💾 Pushing sensor telemetry to Firestore...")
    db_fs.collection("sensor_data").add({
        "device_id": device_id,
        "heart_rate": bpm,
        "timestamp": now
    })
    
    db_fs.collection("environment_logs").add({
        "device_id": device_id,
        "temperature": temp,
        "humidity": humidity,
        "overall": "danger" if (bpm > hr_thresh or temp > temp_thresh) else "normal",
        "timestamp": now
    })
    
    # 2. Check and trigger Notifications
    if bpm > hr_thresh:
        print(f"🚨 Heart Rate {bpm} BPM exceeds threshold of {hr_thresh}! Pushing alert...")
        db_fs.collection("notifications").add({
            "user_id": user_id,
            "baby_id": device_id,
            "type": "critical",
            "title": "⚠️ High Heart Rate Alert",
            "message": f"Heart rate reached {bpm} BPM, which is above your safe limit of {hr_thresh} BPM.",
            "is_read": False,
            "created_at": now
        })
        
    if temp > temp_thresh:
        print(f"🌡️ Temperature {temp}°C exceeds threshold of {temp_thresh}! Pushing alert...")
        db_fs.collection("notifications").add({
            "user_id": user_id,
            "baby_id": device_id,
            "type": "warning",
            "title": "🌡️ High Temperature Alert",
            "message": f"Baby's temperature is {temp}°C, exceeding your configured threshold of {temp_thresh}°C.",
            "is_read": False,
            "created_at": now
        })
        
    print(f"{CLR_GREEN}🎉 Success! Vitals telemetry pushed. Check your App's Dashboard, Charts & Alerts!{CLR_END}\n")

def generate_24h_history(user_id, device_id):
    """Generates 24-hours of realistic, fluctuating history records for premium chart views."""
    db_fs = firestore.client()
    
    print(f"\n{CLR_BLUE}=== 24-Hour Premium Trend Data Generator ==={CLR_END}")
    print("This will populate 24 hours of chronologically historical data.")
    print("This is perfect to show off the gorgeous time-based history area charts!")
    confirm = input("Generate 24h history? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Cancelled.")
        return
        
    print("🧹 Cleaning up old historical data for a clean slate...")
    # Delete old logs to avoid overcrowding
    batch = db_fs.batch()
    old_sensors = db_fs.collection("sensor_data").where("device_id", "==", device_id).get()
    for doc in old_sensors:
        batch.delete(doc.reference)
    old_env = db_fs.collection("environment_logs").where("device_id", "==", device_id).get()
    for doc in old_env:
        batch.delete(doc.reference)
    batch.commit()
    
    print("✍️ Generating 144 fluctuating data points for the past 24 hours...")
    
    batch = db_fs.batch()
    now = datetime.utcnow()
    
    base_hr = 120
    base_temp = 36.6
    
    for i in range(144):
        # 144 data points spaced every 10 minutes (24 hours total)
        time_offset = timedelta(minutes=10 * (144 - i))
        entry_time = now - time_offset
        
        # Add random realistic fluctuations
        hr_variation = random.choice([-5, -3, -1, 0, 1, 3, 5, 8])
        temp_variation = random.choice([-0.2, -0.1, 0.0, 0.1, 0.2, 0.3])
        
        bpm = base_hr + hr_variation
        temp = base_temp + temp_variation
        humidity = 52.0 + random.uniform(-3, 3)
        
        # Vitals doc
        sensor_ref = db_fs.collection("sensor_data").document()
        batch.set(sensor_ref, {
            "device_id": device_id,
            "heart_rate": bpm,
            "timestamp": entry_time
        })
        
        # Env doc
        env_ref = db_fs.collection("environment_logs").document()
        batch.set(env_ref, {
            "device_id": device_id,
            "temperature": round(temp, 2),
            "humidity": round(humidity, 1),
            "overall": "normal",
            "timestamp": entry_time
        })
        
        # Commit in batches of 40 to avoid Firestore limits
        if (i + 1) % 20 == 0:
            batch.commit()
            batch = db_fs.batch()
            
    batch.commit()
    print(f"{CLR_GREEN}✅ Success! 144 data points populated. Reopen the History page in the app to view the gorgeous area trend charts!{CLR_END}\n")

def main():
    print_banner()
    init_firebase()
    user_id, device_id = get_linked_user_and_baby()
    
    if not user_id or not device_id:
        return
        
    while True:
        print("✨ MAIN MENU - SELECT SIMULATION ACTION ✨")
        print("=" * 45)
        print("1) Simulate Cry ML Inference (Detection + Classification)")
        print("2) Simulate Vitals Telemetry (Heart Rate & Room Temperature)")
        print("3) Populate 24-Hour Vitals History Charts (Premium Graph Demo)")
        print("4) Exit")
        print("=" * 45)
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            simulate_cry_event(user_id, device_id)
        elif choice == "2":
            simulate_realtime_vitals(user_id, device_id)
        elif choice == "3":
            generate_24h_history(user_id, device_id)
        elif choice == "4":
            print("\n👋 Happy testing! See you soon!")
            break
        else:
            print(f"{CLR_FAIL}Invalid choice. Try again.{CLR_END}\n")

if __name__ == "__main__":
    main()
