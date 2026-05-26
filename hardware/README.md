# Smart Baby Band - ESP32-S3 Hardware Firmware

> Embedded IoT wearable firmware for real-time baby vitals monitoring and cry-event audio upload.  
> Final Year Project - University of Central Punjab  
> Group ID: F25CS085

---

## Project Overview

The Smart Baby Band is an ESP32-S3 based wearable system that monitors baby vitals and environmental conditions in real time. The firmware reads data from motion, heart-rate, environment, and audio sensors, then sends the data through two separate communication paths:

1. **Vitals telemetry path**: sensor summary data is published as JSON to a local Mosquitto MQTT broker.
2. **Audio event path**: cry-like audio events are detected locally using a lightweight VAD gate, then a 3-second raw PCM audio clip is uploaded to a FastAPI backend using HTTP POST.

AWS IoT Core has been removed from the current firmware. The current implementation uses local Wi-Fi, Mosquitto MQTT on port `1883`, and FastAPI HTTP upload for audio classification.

---

## Current Architecture

```text
                 ┌────────────────────┐
                 │    ESP32-S3 Board   │
                 └─────────┬──────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
  MAX30102 Heart     MPU6050 Motion     BME280 Temp/Humidity
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
             10-second averaged vitals JSON
                           ▼
                Local Mosquitto MQTT Broker
                           ▼
                    Backend / Firebase / App


  INMP441 I2S Microphone
           │
           ▼
  ESP32-S3 lightweight VAD
  Energy + ZCR + Peak threshold
           │
           ▼
  If cry-like event detected
           │
           ▼
  3-second raw int16 PCM clip
  2 sec pre-trigger + 1 sec post-trigger
           │
           ▼
  HTTP POST to FastAPI /predict
           │
           ▼
  Cry classification model / backend result
```

---

## Main Firmware Responsibilities

- Connect ESP32-S3 to Wi-Fi using station mode.
- Read motion data from MPU6050 over I2C.
- Read temperature and humidity from BME280 over I2C.
- Read heart-rate signal from MAX30102 over I2C.
- Capture audio from INMP441 microphone over I2S.
- Run lightweight voice activity detection using:
  - audio energy,
  - zero crossing rate,
  - peak amplitude.
- Store recent audio in a 3-second circular PCM buffer using PSRAM.
- Publish vitals JSON to local Mosquitto MQTT topic `babyband/01/data`.
- Upload cry-triggered 3-second PCM audio clip to FastAPI `/predict` endpoint using HTTP POST.
- Keep MQTT reconnection non-blocking using retry/backoff logic.

---

## Hardware Components

| Component | Purpose | Interface |
|---|---|---|
| ESP32-S3 | Main microcontroller | Wi-Fi, I2C, I2S |
| INMP441 | Digital microphone for audio capture | I2S |
| MPU6050 | Motion detection using accelerometer data | I2C |
| MAX30102 | Heart-rate / PPG sensor | I2C |
| BME280 | Temperature and humidity sensor | I2C |
| Local computer/server | Runs Mosquitto broker and FastAPI backend | Wi-Fi/LAN |

---

## Pin Configuration

### I2S Microphone - INMP441

| INMP441 Pin | ESP32-S3 GPIO |
|---|---:|
| SD | GPIO 42 |
| WS / LRCL | GPIO 41 |
| SCK / BCLK | GPIO 40 |
| VCC | 3.3V |
| GND | GND |

### I2C Sensors - MPU6050, MAX30102, BME280

| I2C Signal | ESP32-S3 GPIO |
|---|---:|
| SDA | GPIO 8 |
| SCL | GPIO 9 |
| VCC | 3.3V |
| GND | GND |

All I2C sensors share the same SDA/SCL bus.

---

## Network Configuration

The firmware currently uses local network communication.

```cpp
const char* mqtt_server = "YOUR_BROKER_IP";
const int mqtt_port = 1883;
const char* mqtt_client_id = "ESP32_001";
const char* mqtt_topic = "babyband/01/data";
const char* audio_post_url = "http://YOUR_BACKEND_IP:8000/predict";
```

Replace `YOUR_BROKER_IP` and `YOUR_BACKEND_IP` with the IP address of the laptop/server running Mosquitto and FastAPI.

Example:

```cpp
const char* mqtt_server = "192.168.1.20";
const char* audio_post_url = "http://192.168.1.20:8000/predict";
```

The ESP32-S3 and backend machine must be connected to the same Wi-Fi/network.

---

## Secrets Handling

Do not commit Wi-Fi credentials to GitHub.

Create a local `secrets.h` file:

```cpp
#pragma once

const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";
```

Include it in the firmware:

```cpp
#include "secrets.h"
```

Add this to `.gitignore`:

```gitignore
secrets.h
```

Important: remove old AWS certificates, private keys, Wi-Fi passwords, and any other sensitive values from the public repository.

---

## MQTT Vitals Publishing

The firmware publishes vitals to the following MQTT topic:

```text
babyband/01/data
```

MQTT broker:

```text
Local Mosquitto broker
Port: 1883
TLS: Not used in current firmware
```

Publish interval:

```text
10 seconds
```

### Example MQTT JSON Payload

```json
{
  "device_id": "babyband_01",
  "timestamp": 123456,
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

## Sensor Polling Intervals

| Task | Interval |
|---|---:|
| Motion read | 200 ms |
| Environment read | 2000 ms |
| Heart-rate read | 40 ms |
| Vitals MQTT publish | 10000 ms |
| MQTT reconnect retry | 15000 ms |

The firmware collects sensor readings continuously and publishes averaged data every 10 seconds instead of publishing every raw sensor read.

---

## Audio Capture and VAD

The firmware captures audio from the INMP441 digital microphone using I2S.

| Parameter | Value |
|---|---:|
| Sample rate | 16 kHz |
| VAD frame size | 20 ms |
| Samples per VAD frame | 320 samples |
| Audio format | raw int16 PCM |
| Pre-trigger audio | 2 seconds |
| Post-trigger audio | 1 second |
| Full uploaded clip | 3 seconds |
| Full clip samples | 48,000 samples |
| Full clip size | ~96 KB |

### Current VAD Thresholds

| Parameter | Value |
|---|---:|
| Energy threshold | 7000 |
| ZCR minimum | 35 |
| ZCR maximum | 110 |
| Peak threshold | 14000 |
| Cry count trigger | 12 frames |
| Cooldown | 8000 ms |

The VAD does not classify cry reason. It only detects whether the recent audio looks like a possible cry-like event. The actual cry classification should be handled by the backend ML model.

---

## HTTP Audio Upload

When VAD triggers, the firmware prepares a 3-second audio clip:

```text
2 seconds from circular buffer + 1 second newly captured audio
```

The clip is sent to FastAPI using HTTP POST:

```text
POST /predict
Content-Type: application/octet-stream
Body: raw int16 little-endian PCM audio bytes
Expected size: about 96,000 bytes
```

Example endpoint:

```text
http://192.168.1.20:8000/predict
```

The FastAPI backend should read the raw request body, convert the PCM bytes into an audio array, run the ML model, and return the prediction.

---

## Minimal FastAPI Test Server

Use this test server before connecting the real ML model:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/predict")
async def predict(request: Request):
    audio_bytes = await request.body()
    print("Received audio bytes:", len(audio_bytes))
    return {
        "status": "ok",
        "received_bytes": len(audio_bytes),
        "expected_bytes": 96000
    }
```

Run it with:

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

---

## Running Mosquitto Locally

### Start Mosquitto broker

```bash
mosquitto -v
```

### Subscribe to vitals topic

Replace `192.168.1.20` with your broker machine IP:

```bash
mosquitto_sub -h 192.168.1.20 -t babyband/01/data -v
```

If the ESP32-S3 is working correctly, JSON vitals should appear every 10 seconds.

---

## Arduino IDE Setup

Recommended board settings:

| Setting | Value |
|---|---|
| Board | ESP32S3 Dev Module |
| USB CDC On Boot | Enabled, if required by board |
| PSRAM | Enabled |
| Upload Speed | 115200 or 921600 |
| Serial Monitor | 115200 baud |

Required libraries:

- PubSubClient
- Adafruit BME280 Library
- Adafruit Unified Sensor
- SparkFun MAX3010x Sensor Library
- MPU6050 library
- ESP32 Arduino core

---

## Expected Serial Output

On successful boot:

```text
===== SMART BABY BAND LOCAL MQTT START =====
I2C started on SDA=8 SCL=9
MPU6050 connected.
BME280 connected at 0x76.
MAX30102 connected.
Audio capture ready.
WiFi connected via DHCP.
[MQTT] Connecting to Local Mosquitto Broker...connected!
===== SYSTEM READY =====
```

During normal operation:

```text
──────────── VITALS ────────────
Motion: meanMag=...
Heart: bpm=...
Env: temp=... humidity=...
[MQTT] Published vitals
```

When a cry-like sound is detected:

```text
[VAD] Cry detected
[AUDIO] Capture complete
[HTTP] Status: 200
[HTTP] Response: ...
[HTTP] Upload success
```

---

## How to Test Step by Step

1. Connect ESP32-S3 and all sensors.
2. Start Mosquitto broker on your laptop/server.
3. Start FastAPI backend on the same laptop/server.
4. Update `mqtt_server` and `audio_post_url` in the firmware.
5. Upload firmware to ESP32-S3.
6. Open Serial Monitor at 115200 baud.
7. Confirm Wi-Fi connection.
8. Confirm MQTT connection.
9. Run `mosquitto_sub` and check if vitals JSON appears.
10. Produce a cry-like/loud sound and check if FastAPI receives around 96 KB of audio data.
11. Connect FastAPI output to ML model and Firebase/mobile app.

---

## Troubleshooting

### ESP32 does not connect to Wi-Fi

- Check SSID and password.
- Make sure the ESP32 is connecting to a 2.4 GHz Wi-Fi network.
- Make sure credentials are correctly written in `secrets.h`.

### MQTT does not connect

- Confirm Mosquitto is running.
- Confirm ESP32 and broker are on the same network.
- Confirm `mqtt_server` IP is correct.
- Confirm firewall allows port `1883`.
- Test with `mosquitto_sub` from another terminal.

### No vitals JSON appears

- Check Serial Monitor for sensor initialization errors.
- Confirm MQTT topic is `babyband/01/data`.
- Confirm publish interval has passed at least 10 seconds.

### FastAPI does not receive audio

- Confirm FastAPI is running with `--host 0.0.0.0`.
- Confirm `audio_post_url` uses the correct backend IP.
- Confirm firewall allows port `8000`.
- Confirm ESP32 and backend are on the same network.

### Audio uploads too often or false positives happen

- Increase `ENERGY_THRESHOLD`.
- Narrow the ZCR range.
- Increase `CRY_COUNT_TRIGGER`.
- Increase `CRY_COOLDOWN_MS`.

---

## Current Status

Completed in current firmware:

- ESP32-S3 Wi-Fi connection.
- Local Mosquitto MQTT vitals publishing.
- 10-second averaged vitals JSON.
- MPU6050 motion sensing.
- BME280 temperature/humidity sensing.
- MAX30102 heart-rate signal reading.
- INMP441 I2S audio capture.
- Lightweight VAD using energy, ZCR, and peak threshold.
- PSRAM-based circular audio buffer.
- HTTP POST upload of 3-second PCM audio clips to FastAPI.

In progress / next integration steps:

- Connect FastAPI `/predict` endpoint to final cry classification model.
- Store MQTT vitals and prediction output in Firebase.
- Connect Firebase/backend data to mobile app dashboard.
- Improve VAD thresholds using real test data.
- Add authentication/security if backend is exposed outside local network.

---

## Important Notes

- AWS IoT Core, AWS certificates, and MQTT over TLS are not part of the current firmware path.
- Current MQTT communication is local Mosquitto over port `1883`.
- Current audio upload is plain HTTP to FastAPI.
- For production or external network deployment, HTTPS and MQTT authentication should be added.
- Do not push secrets, Wi-Fi passwords, certificates, or private keys to GitHub.

---

## References

- ESP32-S3 Arduino Core / ESP-IDF I2S driver
- Mosquitto MQTT broker
- PubSubClient Arduino MQTT library
- FastAPI HTTP backend
- INMP441, MPU6050, MAX30102, and BME280 sensor documentation
