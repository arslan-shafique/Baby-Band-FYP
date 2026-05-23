#include <Arduino.h>
#include <Wire.h>
#include <math.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include "driver/i2s.h"
#include "esp_heap_caps.h"
#include <arduinoFFT.h>
#include <MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <MAX30105.h>
#include <heartRate.h>

// TFLite
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "model_data.h"
#include "mfcc_norm_stats.h"

// =========================
// WIFI / AWS IOT
// =========================
const char* ssid = "MS-Router_Plus";
const char* password = "zee12345";

const char* mqtt_server = "a36ya5skrm71sd-ats.iot.ap-southeast-2.amazonaws.com";
const int mqtt_port = 8883;
const char* mqtt_client_id = "babyband_01";
const char* mqtt_topic = "babyband/01/data";

// Amazon Root CA 
static const char AMAZON_ROOT_CA[] PROGMEM = R"EOF(-----BEGIN CERTIFICATE-----
MIIDQTCCAimgAwIBAgITBmyfz5m/jAo54vB4ikPmljZbyjANBgkqhkiG9w0BAQsF
ADA5MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6
b24gUm9vdCBDQSAxMB4XDTE1MDUyNjAwMDAwMFoXDTM4MDExNzAwMDAwMFowOTEL
MAkGA1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJv
b3QgQ0EgMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALJ4gHHKeNXj
ca9HgFB0fW7Y14h29Jlo91ghYPl0hAEvrAIthtOgQ3pOsqTQNroBvo3bSMgHFzZM
9O6II8c+6zf1tRn4SWiw3te5djgdYZ6k/oI2peVKVuRF4fn9tBb6dNqcmzU5L/qw
IFAGbHrQgLKm+a/sRxmPUDgH3KKHOVj4utWp+UhnMJbulHheb4mjUcAwhmahRWa6
VOujw5H5SNz/0egwLX0tdHA114gk957EWW67c4cX8jJGKLhD+rcdqsq08p8kDi1L
93FcXmn/6pUCyziKrlA4b9v7LWIbxcceVOF34GfID5yHI9Y/QCB/IIDEgEw+OyQm
jgSubJrIqg0CAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0OBBYEFIQYzIU07LwMlJQuCFmcx7IQTgoIMA0GCSqGSIb3DQEBCwUA
A4IBAQCY8jdaQZChGsV2USggNiMOruYou6r4lK5IpDB/G/wkjUu0yKGX9rbxenDI
U5PMCCjjmCXPI6T53iHTfIUJrU6adTrCC2qJeHZERxhlbI1Bjjt/msv0tadQ1wUs
N+gDS63pYaACbvXy8MWy7Vu33PqUXHeeE6V/Uq2V8viTO96LXFvKWlJbYK8U90vv
o/ufQJVtMVT8QtPHRh8jrdkPSHCa2XV4cdFyQzR1bldZwgJcJmApzyMZFo6IQ6XU
5MsI+yMRQ+hDKXJioaldXgjUkK642M4UwtBV8ob2xJNDd2ZhwLnoQdeXeGADbkpy
rqXRfboQnoZsG4q5WTP468SQvvG5
-----END CERTIFICATE-----)EOF";

// Device Certificate
static const char DEVICE_CERT[] PROGMEM = R"KEY(-----BEGIN CERTIFICATE-----
MIIDWTCCAkGgAwIBAgIUbTkZnpVvmtFewZkDwnjsVbnKvpkwDQYJKoZIhvcNAQEL
BQAwTTFLMEkGA1UECwxCQW1hem9uIFdlYiBTZXJ2aWNlcyBPPUFtYXpvbi5jb20g
SW5jLiBMPVNlYXR0bGUgU1Q9V2FzaGluZ3RvbiBDPVVTMB4XDTI2MDQwMzE0MjQz
OFoXDTQ5MTIzMTIzNTk1OVowHjEcMBoGA1UEAwwTQVdTIElvVCBDZXJ0aWZpY2F0
ZTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKLvwdy+IxAhVa4VY4DW
FfUf7MZD1+Tp/FCJf84H31V8QPom9tPSq1xxLUkuvvHw0XOMDRz+UQ4cGj8uwTDC
MbX7PTc1n7eFL12mwaruuXJjqhk4AWGQ0tYplEvWcrJOaQkcOfeUNyFVVQT4jNlI
Vng1Z4VE4wvwlF2VOr8jS4V/2oaZIgXP7Zx9C0Oin5aIhCFyWt9yAioooe2DqFco
S1sPndQpj2b7xHoUHjxI8HRf34F9IzvqDmpHEWnE3TNDITk30zLtH/cs+RWKNsbd
Wl7wYaV1yBY4xKVePZlZBIKAEu7cuRhikQu4ZPvAadsVEgnvLk5t9Nt8OXhPFDlp
L7sCAwEAAaNgMF4wHwYDVR0jBBgwFoAU9RQA/kh70lbbB5a1I/zdUbPEGl8wHQYD
VR0OBBYEFCaIu9XV5lxQ4u+VhGLyJOWTYZ1oMAwGA1UdEwEB/wQCMAAwDgYDVR0P
AQH/BAQDAgeAMA0GCSqGSIb3DQEBCwUAA4IBAQAI7HzMVZF23/MSpM1r7TxVWoOa
deSZVPn8y308nWK/eYT+W5XnQZLOGvCmKnFpVEgSxt10z2lGNMQeAb3Ln0Nev6A9
lD2kjQECnsWF75dz1JJQJnEhfJBxJQJIrsGj+FexLEVhzW58nLiIk8lJBw1rd+GZ
aU6UxT5L4zSn8r9rr6QqQY1pWS2l8Z0mzTVnlloZLQiqQxmiCVfDxD8q4UCLcBXs
kKw9wzgppbtCWuooT7kggMwSTUvM7KfVAc+9sLZbzzcqoeYAZt4GVeBl+s07wldd
VR7uiAdGum0K1Fwhn1CaKp3Syxxw0bnqACHjTjhEWjV83iIr7Cs6mofdNVFy
-----END CERTIFICATE-----)KEY";

// Device Private Key
static const char DEVICE_PRIVATE_KEY[] PROGMEM = R"KEY(-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAou/B3L4jECFVrhVjgNYV9R/sxkPX5On8UIl/zgffVXxA+ib2
09KrXHEtSS6+8fDRc4wNHP5RDhwaPy7BMMIxtfs9NzWft4UvXabBqu65cmOqGTgB
YZDS1imUS9Zysk5pCRw595Q3IVVVBPiM2UhWeDVnhUTjC/CUXZU6vyNLhX/ahpki
Bc/tnH0LQ6KfloiEIXJa33ICKiih7YOoVyhLWw+d1CmPZvvEehQePEjwdF/fgX0j
O+oOakcRacTdM0MhOTfTMu0f9yz5FYo2xt1aXvBhpXXIFjjEpV49mVkEgoAS7ty5
GGKRC7hk+8Bp2xUSCe8uTm3023w5eE8UOWkvuwIDAQABAoIBAQCVOk9sk/vbDxzA
1rgOTIVJvtaFc6ds8dx0CqqyEUW7rpR4R21y7ZSiksluKFEbl3rNf+yWrFmiOZzU
V0b7GDCdQqB7SzKfy2xpMoxXuFLCcINem4uwRwrCuMwodR0RL31FqcNxfB7N+bBn
YBjn/Det2wOX7FKiIdJQr5dhbbsCZXNSxAkyud+U/gOypNALZSwjeQUDjV7tmeGV
2o05znfHiGzPXznYrpB+NKPi5kgD5RkmOLCoX7EFkcDHuciPumZC3pzq8E4S+cHR
4jELu8DB6v8IKuXsxGII+dnycgkOapd5TCG6AmidFClILLtLt2tRspzaV8xkNmEZ
kMfrSGepAoGBANVFBQzOnYLfuZc/ZLtMlD5xPkADZz1hZ1Eta5NjOyfyRBgOJI27
uQFHJNPGIocYbQzEcqRRwq5HldKc3bpZJTT3I4lNNImJk1rRsTtbhbAt2ExMFxq9
e39LP6v6kctpp0Ict8L60Jc06nUhOG64oPEg5rfSBQCZwpD9HBB+RDRVAoGBAMOV
EJ4g35sT6rfop0K8tDWL8iGfFr9C160bQ0cak8zrNL1K1AaljFRL2+fpUWdIBq0+
QU1LheMO3pTDq8LrtdbO4ZuyxAjvO280yadk7Kcvs1FmaaAFFFV2us9gaj0rEZNB
cBO37xZjGobeUp6CTHNohg+4YLgwH9npx3217mPPAoGAFA/jErpY/Ne46K5w9mGU
zG7wsSrgylhgVLWWGg5KoU5b83tZGvAeziz4HOfVlanJkFrmgeijDKv1PxO8k+wQ
4POipybZG1sSvoddSb0pTVJyt3Ks9bn/ZREaEz6F+oGc105GRxQ7DQ5QQ+Z1HY1G
roguy/n4uH6+W89DlZWbKuUCgYEAqu9XLLzScTkBBWci+CLw5XPAVT4zpUmIMlUH
gddqochXubDyijSZ5vq94Xx7lubOXw9wB1wgUggm5KH3Nk7ICEubxnaA+sYLje/2
5oRAiQYZlOULH74QvXkdYC2F7Jv9qlOg3rr9DPXks0cPslVy99K8iHS+o3v7+npl
zir5hOUCgYAqTxGdvE4zWsH1oH9c3vmAZo4B7G3gjKH4E8yJAg/baox4VJWooVEN
avK04588DicUVFxSiidvd7kftJkFdrE7kS800cwBN5fxc2mZzqAMyAz4bHv1wYOB
+qpSVNVJbid3f9CE8/rO3KBP9Q/akZ2FhyuHDor8dZbWSdYzpGqpLg==
-----END RSA PRIVATE KEY-----)KEY";

// =========================
// PIN DEFINITIONS
// =========================
#define I2S_SD   42
#define I2S_WS   41
#define I2S_SCK  40
#define I2S_PORT I2S_NUM_0

#define I2C_SDA  8
#define I2C_SCL  9

// =========================
// AUDIO CONFIG
// =========================
#define SAMPLE_RATE       16000
#define AUDIO_BUFFER_SIZE 8000
#define FRAME_LENGTH      400
#define FRAME_STEP        160
#define MFCC_FEATURES     26
#define MFCC_FRAMES       128
#define MEL_FILTERS       26
#define FFT_SIZE          512
#define PREEMPHASIS       0.97f

// =========================
// THRESHOLDS / INTERVALS
// =========================
#define ENERGY_THRESHOLD  0.10f
#define CRY_THRESHOLD     0.40f

const unsigned long MOTION_INTERVAL = 200;
const unsigned long ENV_INTERVAL    = 2000;
const unsigned long HEART_INTERVAL  = 100;
const unsigned long CRY_INTERVAL    = 3500;

const unsigned long STATUS_PUBLISH_INTERVAL = 10000;
const unsigned long CRY_EVENT_COOLDOWN      = 8000;

const float MOTION_THRESHOLD = 0.18f;
const float MOTION_BASELINE_ALPHA = 0.95f;
const long  FINGER_IR_THRESHOLD = 50000;

const char* DEVICE_ID = "babyband_01";

// =========================
// SENSOR OBJECTS
// =========================
MPU6050 mpu;
Adafruit_BME280 bme;
MAX30105 particleSensor;

bool mpuReady = false;
bool bmeReady = false;
bool maxReady = false;

// I2C MUTEX FOR DUAL CORE SAFETY
SemaphoreHandle_t i2cMutex;

// GLOBAL FLAG TO PAUSE I2C DURING HEAVY AI MATH
volatile bool isInferencing = false;

// =========================
// MQTT / WIFI OBJECTS
// =========================
WiFiClientSecure net;
PubSubClient client(net);

// =========================
// DATA STRUCTURE
// =========================
struct SensorData {
  bool cryDetected;
  float cryConfidence;
  float audioEnergy;

  float motionMagnitude;
  bool motionDetected;

  float heartRateAvg;
  bool fingerDetected;
  bool heartRateValid;

  float temperatureAvg;
  float humidityAvg;
  bool envValid;

  unsigned long timestamp;
};

SensorData dataPacket;

// =========================
// TFLITE / AUDIO BUFFERS
// =========================
float* audioBuffer = nullptr;
float* mfccMatrix = nullptr;
uint8_t* tensorArena = nullptr;

double vReal[FFT_SIZE];
double vImag[FFT_SIZE];
ArduinoFFT<double> FFT = ArduinoFFT<double>(vReal, vImag, FFT_SIZE, SAMPLE_RATE);

const tflite::Model* model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input = nullptr;
TfLiteTensor* output = nullptr;

// =========================
// TIMERS
// =========================
unsigned long lastMotionRead = 0;
unsigned long lastEnvRead = 0;
unsigned long lastHeartRead = 0;
unsigned long lastCryCheck = 0;
unsigned long lastStatusPublish = 0;
unsigned long lastCryEventSent = 0;
bool previousCryDetected = false;

// =========================
// MOTION BASELINE
// =========================
bool motionBaselineReady = false;
float motionBaseX = 0.0f;
float motionBaseY = 0.0f;
float motionBaseZ = 1.0f;

// =========================
// HEART VARIABLES (FREERTOS TASK)
// =========================
TaskHandle_t HeartRateTask;
const byte RATE_SIZE = 4;
byte rates[RATE_SIZE]; 
byte rateSpot = 0;
long lastBeat = 0;
float beatsPerMinute = 0;
int beatAvg = 0;

// =========================
// 10-SECOND AVERAGE WINDOWS
// =========================
float envTempSum = 0.0f;
float envHumiditySum = 0.0f;
int envSampleCount = 0;

// =========================
// FUNCTION DECLARATIONS
// =========================
void initPacket();
void initI2CBus();
void initMPU6050();
void initBME280();
void initMAX30105();
void initCryModel();
void setupI2S();
void captureAudio();
float computeEnergy();
void computeMFCC();
int calculateValidMfccFrames();
float hzToMel(float hz);
float melToHz(float mel);
void applyHammingWindow(float *frame, int len);

void connectWiFi();
void connectMQTT();
void ensureMqttConnection();
bool publishMessage(const String& payload);

void readMotionSensor();
void readEnvironmentSensor();
void readHeartRateSensor();
void runCryDetection();

void updateAverageSnapshot();
void resetAverageWindows();

String buildStatusPayload();
String buildCryEventPayload();

// =========================
// BACKGROUND HEART RATE TASK (CORE 0)
// =========================
void heartRateTaskCode(void * pvParameters) {
  for(;;) {
    // If the AI model is running on Core 1, completely pause this task
    // to prevent the I2C bus from crashing (Error 259).
    if (isInferencing) {
      vTaskDelay(pdMS_TO_TICKS(20));
      continue;
    }

    if (maxReady) {
      long irValue = 0;

      // Request I2C access safely
      if (xSemaphoreTake(i2cMutex, portMAX_DELAY)) {
        irValue = particleSensor.getIR();
        xSemaphoreGive(i2cMutex); // Release I2C immediately
      }

      if (irValue < FINGER_IR_THRESHOLD) {
        dataPacket.fingerDetected = false;
        beatsPerMinute = 0;
        beatAvg = 0;
      } else {
        dataPacket.fingerDetected = true;
        
        if (checkForBeat(irValue) == true) {
          long delta = millis() - lastBeat;
          lastBeat = millis();

          beatsPerMinute = 60.0f / (delta / 1000.0f);

          if (beatsPerMinute < 255 && beatsPerMinute > 20) {
            rates[rateSpot++] = (byte)beatsPerMinute; 
            rateSpot %= RATE_SIZE; 

            beatAvg = 0;
            for (byte x = 0 ; x < RATE_SIZE ; x++) {
              beatAvg += rates[x];
            }
            beatAvg /= RATE_SIZE;
            
          }
        }
      }
      vTaskDelay(pdMS_TO_TICKS(10)); 
    } else {
      vTaskDelay(pdMS_TO_TICKS(1000));
    }
  }
}

// =========================
// SETUP
// =========================
void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("===== SMART BABY BAND AWS START =====");

  // Initialize the I2C Mutex
  i2cMutex = xSemaphoreCreateMutex();

  initPacket();
  initI2CBus();
  initMPU6050();
  initBME280();
  initMAX30105();
  initCryModel();

  connectWiFi();

  net.setCACert(AMAZON_ROOT_CA);
  net.setCertificate(DEVICE_CERT);
  net.setPrivateKey(DEVICE_PRIVATE_KEY);

  client.setServer(mqtt_server, mqtt_port);
  client.setBufferSize(1024);

  connectMQTT();

  // Start Heart Rate Task pinned to Core 0
  xTaskCreatePinnedToCore(
    heartRateTaskCode, 
    "HeartRateTask",   
    4096,              
    NULL,              
    1,                 
    &HeartRateTask,    
    0);                

  Serial.println("===== SYSTEM READY =====");
}

// =========================
// LOOP (CORE 1)
// =========================
void loop() {
  unsigned long now = millis();

  ensureMqttConnection();
  client.loop();

  // Only read other sensors if AI is NOT running
  if (!isInferencing) {
    if (now - lastMotionRead >= MOTION_INTERVAL) {
      lastMotionRead = now;
      readMotionSensor();
    }

    if (now - lastEnvRead >= ENV_INTERVAL) {
      lastEnvRead = now;
      readEnvironmentSensor();
    }

    if (now - lastHeartRead >= HEART_INTERVAL) {
      lastHeartRead = now;
      readHeartRateSensor();
    }
  }

  if (now - lastCryCheck >= CRY_INTERVAL) {
    lastCryCheck = now;
    runCryDetection();
  }

  if (now - lastStatusPublish >= STATUS_PUBLISH_INTERVAL) {
    lastStatusPublish = now;
    dataPacket.timestamp = millis();

    updateAverageSnapshot();

    String statusPayload = buildStatusPayload();
    Serial.println("Publishing STATUS:");
    Serial.println(statusPayload);
    publishMessage(statusPayload);

    resetAverageWindows();
  }
}

// =========================
// WIFI / MQTT
// =========================
void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to AWS IoT MQTT...");

    if (client.connect(mqtt_client_id)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}

void ensureMqttConnection() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi lost. Reconnecting...");
    connectWiFi();
  }

  if (!client.connected()) {
    connectMQTT();
  }
}

bool publishMessage(const String& payload) {
  bool ok = client.publish(mqtt_topic, payload.c_str());
  if (!ok) {
    Serial.println("MQTT publish failed");
  }
  return ok;
}

// =========================
// INITIALIZATION
// =========================
void initPacket() {
  dataPacket.cryDetected = false;
  dataPacket.cryConfidence = 0.0f;
  dataPacket.audioEnergy = 0.0f;

  dataPacket.motionMagnitude = 0.0f;
  dataPacket.motionDetected = false;

  dataPacket.heartRateAvg = 0.0f;
  dataPacket.fingerDetected = false;
  dataPacket.heartRateValid = false;

  dataPacket.temperatureAvg = 0.0f;
  dataPacket.humidityAvg = 0.0f;
  dataPacket.envValid = false;

  dataPacket.timestamp = 0;
}

void initI2CBus() {
  Wire.begin(I2C_SDA, I2C_SCL);
  Wire.setClock(100000); // Force standard 100kHz speed for stability
  Serial.print("I2C started on SDA=");
  Serial.print(I2C_SDA);
  Serial.print(" SCL=");
  Serial.println(I2C_SCL);
}

void initMPU6050() {
  Serial.println("Initializing MPU6050...");
  mpu.initialize();

  if (!mpu.testConnection()) {
    Serial.println("MPU6050 connection failed!");
    mpuReady = false;
    return;
  }

  mpu.setDLPFMode(MPU6050_DLPF_BW_20);
  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_4);
  mpuReady = true;
  Serial.println("MPU6050 connected.");
}

void initBME280() {
  Serial.println("Initializing BME280...");

  if (bme.begin(0x76)) {
    bmeReady = true;
    Serial.println("BME280 connected at 0x76.");
    return;
  }

  if (bme.begin(0x77)) {
    bmeReady = true;
    Serial.println("BME280 connected at 0x77.");
    return;
  }

  Serial.println("BME280 not detected at 0x76 or 0x77!");
  bmeReady = false;
}

void initMAX30105() {
  Serial.println("Initializing MAX30105...");

  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30105 was not found. Please check wiring/power.");
    maxReady = false;
    return;
  }

  particleSensor.setup(); 
  particleSensor.setPulseAmplitudeRed(0x0A); 
  particleSensor.setPulseAmplitudeGreen(0);  
  
  maxReady = true;
  Serial.println("MAX30105 connected.");
}

void initCryModel() {
  Serial.println("Initializing cry detection model...");

  if (!psramFound()) {
    Serial.println("PSRAM NOT FOUND");
    while (1);
  }

  audioBuffer = (float*) heap_caps_malloc(sizeof(float) * AUDIO_BUFFER_SIZE, MALLOC_CAP_SPIRAM);
  mfccMatrix  = (float*) heap_caps_malloc(sizeof(float) * MFCC_FRAMES * MFCC_FEATURES, MALLOC_CAP_SPIRAM);
  tensorArena = (uint8_t*) heap_caps_malloc(300 * 1024, MALLOC_CAP_SPIRAM);

  if (!audioBuffer || !mfccMatrix || !tensorArena) {
    Serial.println("Cry model memory allocation failed");
    while (1);
  }

  setupI2S();

  model = tflite::GetModel(cnn_model_tflite);

  static tflite::MicroMutableOpResolver<10> resolver;
  resolver.AddConv2D();
  resolver.AddDepthwiseConv2D();
  resolver.AddFullyConnected();
  resolver.AddSoftmax();
  resolver.AddReshape();
  resolver.AddMaxPool2D();
  resolver.AddLogistic();

  static tflite::MicroInterpreter static_interpreter(model, resolver, tensorArena, 300 * 1024);
  interpreter = &static_interpreter;

  if (interpreter->AllocateTensors() != kTfLiteOk) {
    Serial.println("Tensor allocation failed");
    while (1);
  }

  input = interpreter->input(0);
  output = interpreter->output(0);

  if (!input || !output) {
    Serial.println("Tensor pointer error");
    while (1);
  }

  Serial.println("Cry model ready.");
}

// =========================
// AVERAGE HELPERS
// =========================
void updateAverageSnapshot() {
  if (envSampleCount > 0) {
    dataPacket.temperatureAvg = envTempSum / envSampleCount;
    dataPacket.humidityAvg = envHumiditySum / envSampleCount;
    dataPacket.envValid = true;
  } else {
    dataPacket.temperatureAvg = 0.0f;
    dataPacket.humidityAvg = 0.0f;
    dataPacket.envValid = false;
  }

  if (dataPacket.fingerDetected && beatAvg > 0) {
    dataPacket.heartRateAvg = beatAvg;
    dataPacket.heartRateValid = true;
  } else {
    dataPacket.heartRateAvg = 0.0f;
    dataPacket.heartRateValid = false;
  }
}

void resetAverageWindows() {
  envTempSum = 0.0f;
  envHumiditySum = 0.0f;
  envSampleCount = 0;
}

// =========================
// SENSOR READ FUNCTIONS
// =========================
void readMotionSensor() {
  if (!mpuReady) return;

  int16_t ax = 0, ay = 0, az = 0;
  
  // Request I2C access safely
  if (xSemaphoreTake(i2cMutex, portMAX_DELAY)) {
    mpu.getAcceleration(&ax, &ay, &az);
    xSemaphoreGive(i2cMutex);
  }

  float accel_x = ax / 8192.0f;
  float accel_y = ay / 8192.0f;
  float accel_z = az / 8192.0f;

  if (!motionBaselineReady) {
    motionBaseX = accel_x;
    motionBaseY = accel_y;
    motionBaseZ = accel_z;
    motionBaselineReady = true;
  }

  float deltaX = accel_x - motionBaseX;
  float deltaY = accel_y - motionBaseY;
  float deltaZ = accel_z - motionBaseZ;

  float motionScore = sqrt((deltaX * deltaX) + (deltaY * deltaY) + (deltaZ * deltaZ));

  if (motionScore < 0.03f) {
    motionScore = 0.0f;
  }

  dataPacket.motionMagnitude = motionScore;
  dataPacket.motionDetected = (motionScore > MOTION_THRESHOLD);

  motionBaseX = (MOTION_BASELINE_ALPHA * motionBaseX) + ((1.0f - MOTION_BASELINE_ALPHA) * accel_x);
  motionBaseY = (MOTION_BASELINE_ALPHA * motionBaseY) + ((1.0f - MOTION_BASELINE_ALPHA) * accel_y);
  motionBaseZ = (MOTION_BASELINE_ALPHA * motionBaseZ) + ((1.0f - MOTION_BASELINE_ALPHA) * accel_z);
}

void readEnvironmentSensor() {
  if (!bmeReady) {
    dataPacket.envValid = false;
    return;
  }

  float temperature = 0.0;
  float humidity = 0.0;

  // Request I2C access safely
  if (xSemaphoreTake(i2cMutex, portMAX_DELAY)) {
    temperature = bme.readTemperature();
    humidity = bme.readHumidity();
    xSemaphoreGive(i2cMutex);
  }

  if (isnan(temperature) || isnan(humidity)) {
    dataPacket.envValid = false;
    return;
  }

  envTempSum += temperature;
  envHumiditySum += humidity;
  envSampleCount++;

  updateAverageSnapshot();
}

void readHeartRateSensor() {
  if (!maxReady || !dataPacket.fingerDetected) {
    dataPacket.heartRateAvg = 0.0f;
    dataPacket.heartRateValid = false;
    return;
  }
  updateAverageSnapshot();
}

void runCryDetection() {
  captureAudio();

  float energy = computeEnergy();
  dataPacket.audioEnergy = energy;

  if (energy < ENERGY_THRESHOLD) {
    dataPacket.cryConfidence = 0.0f;
    dataPacket.cryDetected = false;
    previousCryDetected = false;
    return;
  }

  // --- START HEAVY MATH: PAUSE I2C SENSORS ---
  isInferencing = true;

  computeMFCC();

  // Normalize the MFCC Matrix before feeding to TFLite
  for (int f = 0; f < MFCC_FRAMES; f++) {
    for (int c = 0; c < MFCC_FEATURES; c++) {
      int index = f * MFCC_FEATURES + c;
      mfccMatrix[index] = (mfccMatrix[index] - MFCC_MEAN[c]) / MFCC_STD[c];
    }
  }

  int idx = 0;
  int maxFloats = input->bytes / sizeof(float);
  int needed = MFCC_FRAMES * MFCC_FEATURES;

  if (maxFloats < needed) {
    Serial.println("Input tensor too small");
    dataPacket.cryConfidence = 0.0f;
    dataPacket.cryDetected = false;
    previousCryDetected = false;
    isInferencing = false; // RELEASE I2C
    return;
  }

  for (int i = 0; i < MFCC_FRAMES; i++) {
    for (int j = 0; j < MFCC_FEATURES; j++) {
      input->data.f[idx++] = mfccMatrix[i * MFCC_FEATURES + j];
    }
  }

  if (interpreter->Invoke() != kTfLiteOk) {
    Serial.println("Cry inference failed");
    dataPacket.cryConfidence = 0.0f;
    dataPacket.cryDetected = false;
    previousCryDetected = false;
    isInferencing = false; // RELEASE I2C
    return;
  }

  // --- END HEAVY MATH: RESUME I2C SENSORS ---
  isInferencing = false;

  float result = output->data.f[0];
  
  // Temporal Smoothing (Consecutive Voting)
  static int consecutive_cries = 0;
  bool currentCry = false;

  if (result >= CRY_THRESHOLD && energy > ENERGY_THRESHOLD) {
      consecutive_cries++;
      if (consecutive_cries >= 3) {
          currentCry = true;
      }
  } else {
      // Reset counter if crying stops
      consecutive_cries = 0;
  }

  dataPacket.cryConfidence = result;
  dataPacket.cryDetected = currentCry;

  if (currentCry) {
    unsigned long now = millis();
    bool risingEdge = !previousCryDetected;
    bool cooldownExpired = (now - lastCryEventSent >= CRY_EVENT_COOLDOWN);

    if (risingEdge || cooldownExpired) {
      dataPacket.timestamp = now;
      updateAverageSnapshot();

      String cryPayload = buildCryEventPayload();
      Serial.println("Publishing CRY EVENT:");
      Serial.println(cryPayload);
      publishMessage(cryPayload);

      lastCryEventSent = now;
    }
  }

  previousCryDetected = currentCry;
}

// =========================
// JSON BUILDERS
// =========================
String buildStatusPayload() {
  String json = "{";
  json += "\"device_id\":\"" + String(DEVICE_ID) + "\"";
  json += ",\"timestamp\":" + String(dataPacket.timestamp);
  json += ",\"event\":\"sensor_status\"";
  json += ",\"avgWindowSec\":10";

  json += ",\"motion\":{";
  json += "\"magnitude\":" + String(dataPacket.motionMagnitude, 4);
  json += ",\"detected\":" + String(dataPacket.motionDetected ? "true" : "false");
  json += "}";

  json += ",\"heart\":{";
  json += "\"bpm\":" + String(dataPacket.heartRateAvg, 2);
  json += ",\"fingerDetected\":" + String(dataPacket.fingerDetected ? "true" : "false");
  json += ",\"valid\":" + String(dataPacket.heartRateValid ? "true" : "false");
  json += "}";

  json += ",\"environment\":{";
  json += "\"temperature\":" + String(dataPacket.temperatureAvg, 2);
  json += ",\"humidity\":" + String(dataPacket.humidityAvg, 2);
  json += ",\"valid\":" + String(dataPacket.envValid ? "true" : "false");
  json += "}";

  json += "}";
  return json;
}

String buildCryEventPayload() {
  String json = "{";
  json += "\"device_id\":\"" + String(DEVICE_ID) + "\"";
  json += ",\"timestamp\":" + String(dataPacket.timestamp);
  json += ",\"event\":\"cry_alert\"";
  json += ",\"avgWindowSec\":10";
  json += ",\"cryDetected\":true";
  json += ",\"cryConfidence\":" + String(dataPacket.cryConfidence, 4);
  json += ",\"audioEnergy\":" + String(dataPacket.audioEnergy, 4);

  json += ",\"motion\":{";
  json += "\"magnitude\":" + String(dataPacket.motionMagnitude, 4);
  json += ",\"detected\":" + String(dataPacket.motionDetected ? "true" : "false");
  json += "}";

  json += ",\"heart\":{";
  json += "\"bpm\":" + String(dataPacket.heartRateAvg, 2);
  json += ",\"fingerDetected\":" + String(dataPacket.fingerDetected ? "true" : "false");
  json += ",\"valid\":" + String(dataPacket.heartRateValid ? "true" : "false");
  json += "}";

  json += ",\"environment\":{";
  json += "\"temperature\":" + String(dataPacket.temperatureAvg, 2);
  json += ",\"humidity\":" + String(dataPacket.humidityAvg, 2);
  json += ",\"valid\":" + String(dataPacket.envValid ? "true" : "false");
  json += "}";

  json += "}";
  return json;
}

// =========================
// I2S / AUDIO HELPERS
// =========================
void setupI2S() {
  i2s_config_t config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = 0,
    .dma_buf_count = 8,
    .dma_buf_len = 256
  };

  i2s_pin_config_t pins = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };

  i2s_driver_install(I2S_PORT, &config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pins);
  i2s_zero_dma_buffer(I2S_PORT);
}

void captureAudio() {
  size_t bytesRead = 0;
  int index = 0;

  while (index < AUDIO_BUFFER_SIZE) {
    int32_t temp[256];
    i2s_read(I2S_PORT, temp, sizeof(temp), &bytesRead, portMAX_DELAY);

    int samples = bytesRead / sizeof(int32_t);

    for (int i = 0; i < samples && index < AUDIO_BUFFER_SIZE; i++) {
      float val = (float)temp[i] / 8388608.0f;

      if (val > 1.0f) val = 1.0f;
      if (val < -1.0f) val = -1.0f;

      audioBuffer[index++] = val;
    }
  }
}

float computeEnergy() {
  float sum = 0.0f;
  for (int i = 0; i < AUDIO_BUFFER_SIZE; i++) {
    sum += fabs(audioBuffer[i]);
  }
  return sum / AUDIO_BUFFER_SIZE;
}

int calculateValidMfccFrames() {
  if (AUDIO_BUFFER_SIZE <= 0) return 0;
  if (AUDIO_BUFFER_SIZE < FRAME_LENGTH) return 1;

  int frames = 1 + ((AUDIO_BUFFER_SIZE - FRAME_LENGTH) / FRAME_STEP);
  if (frames < 1) frames = 1;
  if (frames > MFCC_FRAMES) frames = MFCC_FRAMES;
  return frames;
}

void computeMFCC() {
  for (int i = AUDIO_BUFFER_SIZE - 1; i > 0; i--) {
    audioBuffer[i] -= PREEMPHASIS * audioBuffer[i - 1];
  }

  int validFrames = calculateValidMfccFrames();

  static float melBank[MEL_FILTERS][FFT_SIZE / 2 + 1];
  static bool built = false;

  if (!built) {
    for (int m = 0; m < MEL_FILTERS; m++) {
      for (int k = 0; k <= FFT_SIZE / 2; k++) {
        melBank[m][k] = 0.0f;
      }
    }

    float lowMel = hzToMel(0.0f);
    float highMel = hzToMel((float)SAMPLE_RATE / 2.0f);

    float melPts[MEL_FILTERS + 2];
    int bins[MEL_FILTERS + 2];

    for (int i = 0; i < MEL_FILTERS + 2; i++) {
      melPts[i] = lowMel + (highMel - lowMel) * i / (MEL_FILTERS + 1);
      float hz = melToHz(melPts[i]);
      bins[i] = (int)(((FFT_SIZE + 1) * hz) / SAMPLE_RATE);

      if (bins[i] < 0) bins[i] = 0;
      if (bins[i] > FFT_SIZE / 2) bins[i] = FFT_SIZE / 2;
    }

    for (int m = 1; m <= MEL_FILTERS; m++) {
      int left = bins[m - 1];
      int center = bins[m];
      int right = bins[m + 1];

      if (center <= left) center = left + 1;
      if (right <= center) right = center + 1;
      if (right > FFT_SIZE / 2) right = FFT_SIZE / 2;

      for (int k = left; k < center; k++) {
        melBank[m - 1][k] = (float)(k - left) / (float)(center - left);
      }

      for (int k = center; k < right; k++) {
        melBank[m - 1][k] = (float)(right - k) / (float)(right - center);
      }
    }

    built = true;
  }

  for (int f = 0; f < MFCC_FRAMES; f++) {
    int start = f * FRAME_STEP;
    float frame[FRAME_LENGTH];
    bool useRealAudio = (f < validFrames);

    for (int i = 0; i < FRAME_LENGTH; i++) {
      frame[i] = (useRealAudio && (start + i < AUDIO_BUFFER_SIZE)) ? audioBuffer[start + i] : 0.0f;
    }

    applyHammingWindow(frame, FRAME_LENGTH);

    for (int i = 0; i < FFT_SIZE; i++) {
      vReal[i] = (i < FRAME_LENGTH) ? frame[i] : 0.0;
      vImag[i] = 0.0;
    }

    FFT.compute(FFT_FORWARD);
    FFT.complexToMagnitude();

    float melE[MEL_FILTERS];

    for (int m = 0; m < MEL_FILTERS; m++) {
      float sum = 0.0f;
      for (int k = 0; k <= FFT_SIZE / 2; k++) {
        sum += (float)vReal[k] * melBank[m][k];
      }
      melE[m] = logf(sum + 1e-6f);
    }

    for (int c = 0; c < MFCC_FEATURES; c++) {
      float val = 0.0f;
      for (int m = 0; m < MEL_FILTERS; m++) {
        val += melE[m] * cosf((PI * c * (m + 0.5f)) / MEL_FILTERS);
      }
      mfccMatrix[f * MFCC_FEATURES + c] = val;
    }
  }
}

float hzToMel(float hz) {
  return 2595.0f * log10f(1.0f + hz / 700.0f);
}

float melToHz(float mel) {
  return 700.0f * (powf(10.0f, mel / 2595.0f) - 1.0f);
}

void applyHammingWindow(float *frame, int len) {
  for (int i = 0; i < len; i++) {
    frame[i] *= (0.54f - 0.46f * cosf((2.0f * PI * i) / (len - 1)));
  }
}