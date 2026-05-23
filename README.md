# 🍼 Smart Baby Band – Cry & Sleep Monitoring System

> AI-Powered IoT Wearable for Infant Cry Classification & Sleep Tracking
> Final Year Project – University of Central Punjab (Fall 2025)

---

## 📌 Project Overview

The **Smart Baby Band** is an AI-enabled IoT wearable device designed to monitor infant health and behavior in real time. The system integrates embedded hardware, cloud computing, machine learning, and a mobile application into one complete end-to-end solution.

The objective is to assist parents in understanding baby needs through intelligent cry detection, sleep tracking, and environmental monitoring.

### Core Capabilities

* 🎤 AI-Based Cry Classification (Hunger, Pain, Discomfort, Normal)
* 💤 Sleep Stage Detection (Awake, Light, Deep)
* 💓 Heart Rate Monitoring (MAX30102)
* 🌡️ Temperature & Humidity Monitoring (BME280 / DHT11)
* 📡 Real-Time Cloud Communication (MQTT / Firebase)
* 📱 Mobile Dashboard with Alerts & Reports (Flutter)

---

## 🏗️ System Architecture

### End-to-End Data Flow

1. Sensors collect physiological and environmental data.
2. ESP32 processes signals and formats data packets.
3. Data is transmitted securely via MQTT over WiFi to AWS IoT Core.
4. AWS Lambda bridges sensor data to Firebase Firestore for storage and real-time syncing.
5. FastAPI backend runs sliding-window statistical analysis for sleep and executes Keras/TFLite models for cry classification.
6. Mobile application streams insights via Firestore/RTDB and receives real-time FCM Push Notifications for alerts.

This architecture ensures low latency, secure communication, and scalability.

---

## 🔧 Hardware Stack

| Component      | Purpose                                  |
| -------------- | ---------------------------------------- |
| ESP32          | Main microcontroller with WiFi & BLE     |
| INMP441        | Digital microphone (I2S) for cry capture |
| MPU6050        | Motion tracking for sleep detection      |
| MAX30102       | Heart rate & pulse monitoring            |
| BME280 / DHT11 | Temperature & humidity monitoring        |
| Battery Module | Portable wearable power system           |

### Embedded System Responsibilities

* Sensor data acquisition
* Signal preprocessing
* Secure MQTT publishing
* Local buffering & fault handling
* Power optimization for wearable usage

---

## 🧠 Artificial Intelligence & Machine Learning

### 🎤 Cry Classification

* Audio preprocessing using MFCC (Mel-Frequency Cepstral Coefficients)
* Neural network model trained on labeled cry dataset
* Classification categories: Hunger, Pain, Discomfort, Normal

### 💤 Sleep Stage Detection

* Motion analysis using MPU6050
* Heart rate variability analysis
* Sleep state estimation: Awake, Light Sleep, Deep Sleep

### ML Technology Stack

* **Python** (TensorFlow / PyTorch / Librosa / Scikit-learn)
* **TensorFlow Lite / ONNX** (Model deployment)

---

## ☁️ Cloud Infrastructure

### Communication Protocol

* MQTT over WiFi (ESP32 to AWS IoT Core)
* Secure TLS-based communication
* REST APIs & Real-time Listeners (FastAPI & Flutter to Firebase)

### Cloud Platforms & Backend Setup

* **AWS IoT Core**: Cloud MQTT broker for IoT devices
* **AWS Lambda**: Serverless bridge between AWS IoT and Firebase
* **Firebase (Firestore + RTDB + FCM)**: Real-time database for streams, and Cloud Messaging for emergency push notifications
* **FastAPI (Python)**: Core backend server handling sliding-window telemetry buffers, ML inference (Keras/TFLite), safety classification, and alerting

### Cloud Capabilities

* Real-time device data ingestion
* Secure device authentication (certificates)
* Data storage & analytics
* Alert triggering system
* Weekly health reports generation

---

## 📱 Mobile Application (Flutter)

### Key Features

* Live sensor readings via Firebase Real-Time Database (RTDB) and Firestore streams
* Real-time FCM Push Notifications for cry detection and environment danger
* Dynamic Sleep tracking and Environment dashboards using `StreamBuilder`
* Secure authentication system with dynamic `device_id` resolution for multi-user mapping

The mobile application acts as the primary user interface for parents.

---

## 👨‍💻 Team Members & Roles

* **Umair Imran** → AI/ML Engineer
* **Arslan Shafique** → Hardware Developer
* **Uzair Ghaffar** → Mobile App Developer

---

## 📂 Repository Structure

```text
Smart-Baby-Band-FYP/
├── app/               # Flutter mobile app
├── backend/           # FastAPI backend (Python + Firebase + AWS Lambda)
├── docs/              # Reports, diagrams, presentations
├── hardware/          # Hardware code (ESP32 + sensors)
├── ml_model/          # Cry detection model (datasets, training, inference)
├── .gitignore         # Root git ignore patterns
└── requirements.txt   # Python dependencies
```

---

## 🚀 Technical Skills Demonstrated

* Embedded Systems Engineering (ESP32)
* IoT Architecture Design
* MQTT Protocol Implementation
* Cloud Computing (AWS IoT Core / AWS Lambda / Firebase)
* AI Model Development & Deployment
* Edge Processing
* Real-Time Data Streaming
* Sensor Fusion Techniques
* Secure Communication Architecture
* Cross-Platform Mobile Development (Flutter)

---

## 🎯 Project Impact

The Smart Baby Band improves upon existing baby monitoring solutions by combining:

* Real-time AI classification
* Multi-sensor health monitoring
* Integrated cloud analytics
* Affordable and scalable hardware design

It demonstrates the ability to design and deploy a full-stack IoT + AI system from hardware to cloud to user interface.

---

## 🏆 Recruiter Summary

This project showcases:

* Complete IoT product development lifecycle
* Hardware + AI + Cloud integration
* Production-level architecture thinking
* Secure real-time data engineering
* Strong cross-team collaboration

It reflects practical industry-ready skills in IoT, AI systems, and cloud integration.

---

## 📜 License

Academic Research Project – University of Central Punjab (2025)

For demonstration and educational purposes.
