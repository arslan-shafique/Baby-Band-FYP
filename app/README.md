# 📱 Smart Baby Band – Mobile Application

> Cross-platform mobile dashboard for the Smart Baby Band IoT system, built with Flutter.

---

## 📌 Overview

The mobile application acts as the primary user interface for parents, providing real-time insights into their baby's health and environment.

It connects directly to **Firebase (Firestore)** to fetch real-time sensor updates and interfaces with our **FastAPI Backend** for complex aggregate analytics and Machine Learning-based cry classification results.

## ✨ Key Features

* **Real-Time Dashboard**: See live heart rate, temperature, SpO2, and sleep status.
* **Cry History & Alerts**: View history of detected cries classified by the ML model (Hunger, Pain, Discomfort, Normal).
* **Sleep Tracking**: Track baby's sleep patterns (Deep, Light, Awake) with graphical history.
* **Environment Monitoring**: Check room temperature and humidity with instant alerts for anomalies.
* **Push Notifications**: Receive immediate alerts for high heart rate, abnormal temperature, or crying events.
* **Authentication**: Secure login via Firebase Auth.

## 🛠️ Technology Stack

* **Framework**: Flutter (Dart)
* **Real-time Database**: Firebase Firestore
* **Authentication**: Firebase Authentication
* **Backend API**: FastAPI (Python) for ML predictions and health report generation

## 🚀 Getting Started

Ensure you have [Flutter](https://docs.flutter.dev/get-started/install) installed on your system.

```bash
# Get dependencies
flutter pub get

# Run the app
flutter run
```

## 📂 Architecture Note

The app uses an **API-First** and **Real-time Listener** approach:

* **Direct to Firebase**: Sensor data, baby profiles, and settings are streamed directly from Firestore using real-time listeners.
* **via FastAPI**: Summaries, weekly/monthly reports, and initial cry classifications go through the Python backend.
