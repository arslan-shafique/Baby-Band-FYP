# Smart Baby Band - Hardware System Documentation

> Embedded IoT Wearable - ESP32-S3 Firmware and Sensor Integration  
> Final Year Project - University of Central Punjab (Fall 2025)  
> Group ID: F25CS085 | Advisor: Muhammad Ammar Hassan

---

## Hardware Overview

The Smart Baby Band is a low-power IoT wearable that monitors infant vitals and the environment in real time. The ESP32-S3 performs lightweight audio gating and continuous sensing, then streams only relevant audio to the cloud for classification.

The device uses a split-compute architecture: the edge runs a lightweight VAD (energy + ZCR + peak) to decide whether a cry-like event exists, while the cloud performs multi-class cry classification. This keeps the ESP32 responsive and reduces bandwidth and power consumption.

---

## Hardware Objectives

- Capture infant audio from a digital I2S microphone at 16 kHz
- Run a lightweight VAD gate on the ESP32-S3 (cry vs. no-cry)
- Maintain a 3-second circular PCM buffer in PSRAM (2 s pre + 1 s post)
- Upload raw int16 PCM clips to the cloud over HTTP
- Publish 10-second windowed aggregates (mean, variance, spikes) for vitals via MQTT over TLS
- Keep sensor and MQTT loops responsive using FreeRTOS tasks

---

## Core Microcontroller

### ESP32-S3

**Key specifications used:**

| Feature | Detail |
|---|---|
| Processor | Dual-core Xtensa LX7 @ 240MHz |
| SRAM | 512KB internal |
| PSRAM | 8MB external (ring buffer + clip buffer) |
| Wi-Fi | 802.11 b/g/n 2.4GHz |
| Audio interface | I2S (INMP441 microphone) |
| Sensor interface | I2C (MAX30102, MPU6050, BME280) |
| Framework | ESP-IDF 5.x with FreeRTOS |
| Language | C++ |

**Firmware responsibilities:**

- Sensor initialization and polling on boot
- 20 ms VAD frames with energy, ZCR, and peak checks
- Continuous 3-second circular buffer in PSRAM
- Trigger capture: 2 s pre-trigger + 1 s post-trigger
- HTTP POST of raw PCM to the FastAPI /predict endpoint
- MQTT vitals publishing to AWS IoT Core over TLS
- NTP time sync for TLS certificate validation

---

## Sensor Modules

### INMP441 - Digital Microphone (I2S)

- Captures audio at 16 kHz, mono, 16-bit PCM
- VAD uses 20 ms frames (320 samples)
- Ring buffer stores 3 seconds of PCM in PSRAM
- On trigger, preserves 2 s pre-trigger and captures 1 s post-trigger

**VAD parameters (configurable):**

| Parameter | Value |
|---|---|
| Frame size | 20 ms (320 samples) |
| Energy threshold | 9000 (mean abs) |
| ZCR range | 45 to 95 |
| Peak threshold | 14000 |
| Cry count trigger | 25 frames |
| Cooldown | 8 seconds |

---

### MAX30102 - Heart Rate Sensor (I2C)

- Optical PPG sensor measuring heart rate (BPM)
- I2C address: 0x57
- 10-second rolling average for stable output

---

### MPU6050 - Motion Sensor (I2C)

- 3-axis accelerometer and gyroscope
- I2C address: 0x68
- Motion index derived from acceleration magnitude

---

### BME280 - Environmental Sensor (I2C)

- Measures room temperature (C) and relative humidity (%)
- I2C address: 0x76
- 10-second rolling average for stable readings

---

## Communication Interfaces

| Interface | Purpose |
|---|---|
| I2S | INMP441 microphone - digital audio |
| I2C | MAX30102, MPU6050, BME280 - shared bus |
| Wi-Fi (MQTT TLS) | Vitals to AWS IoT Core |
| Wi-Fi (HTTP) | Raw PCM upload to FastAPI |

**I2C bus management:** Sensors are polled in the main loop at fixed intervals:

| Sensor | Interval |
|---|---|
| Motion | 200 ms |
| Environment | 2 s |
| Heart rate | 40 ms |
| Vitals publish | 10 s |

---

## MQTT Payload Schema (Vitals Only)

Vitals are published periodically to AWS IoT Core on topic `babyband/01/data`:

```json
{
  "device_id": "babyband_01",
  "timestamp": 1715420000,
  "event": "sensor_status",
  "avgWindowSec": 10,
  "motion": {
    "meanMag": 0.0123,
    "varianceMag": 0.0002,
    "spikeCount": 0,
    "detected": false
  },
  "heart": {
    "bpm": 124.5,
    "varianceBpm": 2.1,
    "fingerDetected": true,
    "valid": true
  },
  "environment": {
    "temperature": 24.6,
    "humidity": 58.2,
    "valid": true
  }
}
```

---

## HTTP Audio Upload (Cry Gate)

When VAD triggers, the ESP32 sends a 3-second raw PCM clip:

- Content-Type: application/octet-stream
- Body: raw int16 little-endian PCM (48000 samples / 96 KB)
- Endpoint: `http://10.9.202.162:8000/predict`

The 3-second clip is composed of the **last 2 seconds in the ring buffer** plus **1 second of newly captured audio**.

---

## Security Implementation

- MQTT uses mutual TLS on port 8883
- NTP time sync is required before TLS handshake
- Device uses X.509 certs + AWS root CA
- HTTP audio upload is plain HTTP on the local network (can be upgraded to HTTPS)

**Files required in firmware:**

- `device_cert.pem` - device certificate
- `private_key.pem` - device private key
- `aws_root_ca.pem` - AWS root CA

---

## Power System

- Rechargeable LiPo battery - 3.7V nominal
- 3.3V regulated supply via onboard LDO

**Power optimization techniques:**

| Technique | Implementation |
|---|---|
| VAD gate | Upload audio only on cry-like events |
| Ring buffer | Avoids blocking capture loops |
| MQTT batching | Periodic vitals instead of per-read streaming |
| Lightweight DSP | Energy + ZCR + peak only |

---

## Engineering Challenges and Solutions

| Challenge | Solution |
|---|---|
| MQTT TLS failed on boot | Forced strict NTP sync (UTC+5) with 20s timeout before TLS connect |
| Audio capture blocked MQTT | Ring buffer + async capture/upload tasks |
| MQTT reconnect froze main loop | Implemented non-blocking single-attempt connect with 15s backoff |
| False positives in VAD | Energy + ZCR + peak + cooldown |
| Limited RAM | 3-second PCM buffers in PSRAM |
| DNS resolution failures | Bypass restrictive networks using Google Public DNS (8.8.8.8) |

---

## Current Status

**Completed:**

- ESP32-S3 firmware with VAD gate and ring buffer
- Vitals sensing (MAX30102, MPU6050, BME280)
- MQTT vitals publishing over TLS
- HTTP PCM upload to cloud
- NTP time sync for TLS validation

**In Progress:**

- Cloud cry classification pipeline integration
- End-to-end telemetry and alert testing
- Wearable enclosure integration

---

## References

1. Espressif Systems. ESP32-S3 Technical Reference Manual v1.1. 2023.
2. OASIS Standard. MQTT Version 3.1.1 Specification. 2014.
3. InvenSense. MPU6050 Product Specification. 2013.

---

*Academic Project - University of Central Punjab, Faculty of Information Technology and Computer Science, 2025*
