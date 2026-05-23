# 🧠 Smart Baby Band — Cry Classification ML Model

> Machine Learning model for classifying infant cries based on audio features.

---

## 📌 Overview

This directory contains the machine learning pipeline used to train and export the cry classification model.
The final model runs inference on an incoming set of audio features extracted by the ESP32 (such as MFCCs).Calisto MT

## 🛠️ Technology Stack

* **Frameworks**: TensorFlow / Keras
* **Language**: Python
* **Deployment**: TensorFlow Lite (`.tflite`) for efficient inference in our FastAPI backend (and potentially on-edge).
* **Technique**: Supervised learning on labeled cry datasets (extracting Mel-Frequency Cepstral Coefficients - MFCCs).

## 🧩 Architecture Fit

1. **ESP32**: Captures raw audio via I2S digital microphone, extracts crucial MFCC features.
2. **Transmission**: ESP32 sends the extracted features to our Backend via AWS IoT Core -> Lambda -> FastAPI endpoint.
3. **Inference**: The FastAPI backend loads this TFLite model, runs inference on the MFCC features, and predicts the cry type.
4. **Classes Output**: `hunger`, `pain`, `discomfort`, `tired`, `normal`

## 📂 Directory Structure

* `/datasets` — Training and validation data (not committed)
* `/Scripts` — Python training, quantization, and evaluation scripts (e.g. `train_cry_detection.py`)
* `/models` — Checkpoints and exported `.tflite` deployed models

## 🚀 Model Deployment

After training in `Scripts`, generate a quantized `.tflite` model and drop it into `backend/ml_models/cry_detection_model.tflite` so the FastAPI backend can load it.
