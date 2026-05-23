#include <Arduino.h>
#include <Wire.h>
#include <math.h>
#include <string.h>
#include <WiFi.h>
// AWS REMOVED: #include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <HTTPClient.h>
#include "driver/i2s.h"
#include "esp_heap_caps.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include <time.h>
#include <MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <MAX30105.h>
#include <heartRate.h>

// =========================
// WIFI / AWS IOT 
// =========================
const char* ssid = "Note 10";
const char* password = "23456789";

const char* mqtt_server = "10.184.183.100";
const int mqtt_port = 1883;
const char* mqtt_client_id = "ESP32_001";
const char* mqtt_topic = "babyband/01/data";
const char* audio_post_url = "http://10.184.183.100:8000/predict";
const uint32_t audio_post_timeout_ms = 15000;
const uint32_t wifi_connect_timeout_ms = 10000;
const uint32_t mqtt_connect_timeout_ms = 5000;

// Amazon Root CA
/* AWS REMOVED: 
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
-----END CERTIFICATE-----
)EOF";

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
-----END CERTIFICATE-----
)KEY";

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
-----END RSA PRIVATE KEY-----
)KEY";
*/

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
#define VAD_FRAME_MS      20
#define VAD_FRAME_SAMPLES ((SAMPLE_RATE * VAD_FRAME_MS) / 1000)
#define PRE_TRIGGER_SECONDS 2
#define POST_TRIGGER_SECONDS 1
#define FULL_AUDIO_SECONDS 3
#define PRE_TRIGGER_SAMPLES (SAMPLE_RATE * PRE_TRIGGER_SECONDS)
#define POST_TRIGGER_SAMPLES (SAMPLE_RATE * POST_TRIGGER_SECONDS)
#define FULL_AUDIO_SAMPLES (SAMPLE_RATE * FULL_AUDIO_SECONDS)
#define PCM_BYTES_PER_SAMPLE 2

// =========================
// THRESHOLDS / INTERVALS
// =========================
#define ENERGY_THRESHOLD  7000
#define ZCR_MIN           35
#define ZCR_MAX           110
#define CRY_COUNT_TRIGGER 12
#define CRY_COOLDOWN_MS   8000
#define PEAK_THRESHOLD    14000
#define MOVEMENT_THRESHOLD 0.15f

const unsigned long MOTION_INTERVAL = 200;
const unsigned long ENV_INTERVAL    = 2000;
const unsigned long HEART_INTERVAL  = 40;
const unsigned long STATUS_PUBLISH_INTERVAL = 10000;

const float MOTION_THRESHOLD = 0.18f;
const float MOTION_BASELINE_ALPHA = 0.95f;
const long  FINGER_IR_THRESHOLD = 7000;

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

// =========================
// MQTT / WIFI OBJECTS
// =========================
// AWS REMOVED: WiFiClientSecure net;
WiFiClient espClient;
PubSubClient client(espClient);

// =========================
// DATA STRUCTURE
// =========================
struct SensorData {
  float meanMag;
  float varianceMag;
  int spikeCount;
  bool motionDetected;

  float heartRateAvg;
  float heartRateVariance;
  bool fingerDetected;
  bool heartRateValid;

  float temperatureAvg;
  float humidityAvg;
  bool envValid;

  unsigned long timestamp;
};

SensorData dataPacket;

// =========================
// AUDIO BUFFERS
// =========================
int16_t* circularBuffer = nullptr;
int16_t* audioClipBuffer = nullptr;
size_t circularWriteIndex = 0;
size_t circularSamplesWritten = 0;
static int16_t vadFrame[VAD_FRAME_SAMPLES];
SemaphoreHandle_t i2sMutex = nullptr;
SemaphoreHandle_t audioClipMutex = nullptr;
volatile bool audioCaptureInProgress = false;
volatile bool audioUploadInProgress = false;
int cryCount = 0;
TaskHandle_t audioCaptureTaskHandle = nullptr;
TaskHandle_t audioUploadTaskHandle = nullptr;
unsigned long lastCryTrigger = 0;

// =========================
// TIMERS
// =========================
unsigned long lastMotionRead = 0;
unsigned long lastEnvRead = 0;
unsigned long lastHeartRead = 0;
unsigned long lastStatusPublish = 0;
unsigned long lastMqttReconnectAttempt = 0;
const unsigned long MQTT_RECONNECT_INTERVAL = 15000;  // 15s between reconnect attempts

// =========================
// MOTION BASELINE
// =========================
bool motionBaselineReady = false;
float motionBaseX = 0.0f;
float motionBaseY = 0.0f;
float motionBaseZ = 1.0f;

// =========================
// HEART VARIABLES
// =========================
unsigned long lastBeatTime = 0;

// =========================
// 10-SECOND AVERAGE WINDOWS
// =========================
float envTempSum = 0.0f;
float envHumiditySum = 0.0f;
int envSampleCount = 0;

float heartBpmSum = 0.0f;
float heartBpmSumSq = 0.0f;
int heartBpmCount = 0;

float motionMagSum = 0.0f;
float motionMagSumSq = 0.0f;
int motionMagCount = 0;
int motionSpikeCount = 0;

// =========================
// FUNCTION DECLARATIONS
// =========================
void initPacket();
void initI2CBus();
void initMPU6050();
void initBME280();
void initMAX30102();
void initAudioCapture();
void setupI2S();
bool readI2SSamplesRaw(int16_t* dest, size_t sampleCount);
void writeCircularBuffer(const int16_t* samples, size_t sampleCount);
void extractBufferedAudio(int16_t* dest, size_t sampleCount);
bool captureFutureAudio(int16_t* dest, size_t sampleCount);
float computeEnergy(const int16_t* frame, size_t len);
int computeZCR(const int16_t* frame, size_t len);
void runVAD();
void audioCaptureTask(void* param);
void audioUploadTask(void* param);
bool uploadAudioHTTP(const int16_t* pcm, size_t sampleCount);

void setupWiFi();
void setupMQTT();
void reconnectMQTT();
bool connectMQTT();
void connectWiFi();

bool publishMessage(const String& payload);

void readMotionSensor();
void readEnvironmentSensor();
void readHeartRateSensor();
void readVitals(unsigned long now);
void publishVitalsMQTT(unsigned long now);

void updateAverageSnapshot();
void resetAverageWindows();

String buildStatusPayload();

// =========================
// SETUP
// =========================
void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("===== SMART BABY BAND LOCAL MQTT START =====");

  initPacket();
  initI2CBus();
  initMPU6050();
  initBME280();
  initMAX30102();
  initAudioCapture();

  setupWiFi();
  setupMQTT();

  Serial.println("===== SYSTEM READY =====");
}

// =========================
// LOOP
// =========================
void loop() {
  unsigned long now = millis();

  reconnectMQTT();
  client.loop();

  readVitals(now);
  runVAD();
  publishVitalsMQTT(now);
}

// =========================
// WIFI / MQTT
// =========================
void setupWiFi() {
  connectWiFi();

  if (WiFi.status() == WL_CONNECTED) {
    // UTC+5 (Pakistan Standard Time) = 18000 seconds offset
    configTime(18000, 0, "pool.ntp.org", "time.nist.gov");

    Serial.print("[NTP] Syncing time");
    time_t now = time(nullptr);
    unsigned long start = millis();

    // Wait up to 20 seconds for NTP sync — TLS WILL NOT WORK without correct time
    while (now < 1700000000 && (millis() - start) < 20000) {
      delay(500);
      Serial.print(".");
      now = time(nullptr);
    }

    Serial.println();

    if (now >= 1700000000) {
      struct tm timeinfo;
      localtime_r(&now, &timeinfo);
      Serial.print("[NTP] Time synced: ");
      Serial.println(asctime(&timeinfo));
    } else {
      Serial.println("[NTP] *** TIME SYNC FAILED — TLS/MQTT will not work! ***");
      Serial.print("[NTP] Current time value: ");
      Serial.println((unsigned long)now);
    }
  }
}

void setupMQTT() {
  // AWS REMOVED: net.setCACert(AMAZON_ROOT_CA);
  // AWS REMOVED: net.setCertificate(DEVICE_CERT);
  // AWS REMOVED: net.setPrivateKey(DEVICE_PRIVATE_KEY);

  client.setServer(mqtt_server, mqtt_port);
  client.setBufferSize(1024);

  connectMQTT();
}

void reconnectMQTT() {
  // Don't attempt reconnect if already connected
  if (client.connected()) return;

  // Non-blocking: only attempt every MQTT_RECONNECT_INTERVAL
  unsigned long now = millis();
  if (now - lastMqttReconnectAttempt < MQTT_RECONNECT_INTERVAL) return;
  lastMqttReconnectAttempt = now;

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[MQTT] WiFi lost. Reconnecting...");
    connectWiFi();
    if (WiFi.status() != WL_CONNECTED) return;
  }

  connectMQTT();
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  // WiFi.config with INADDR_NONE sets an invalid static IP, causing connection timeouts.
  // We'll rely on the hotspot's DHCP for IP and DNS.
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - start) < wifi_connect_timeout_ms) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected via DHCP.");
    
    // Override the network-provided DNS with Google Public DNS (8.8.8.8)
    // We do this by re-applying the DHCP-assigned IP, Gateway, and Subnet as static
    IPAddress ip = WiFi.localIP();
    IPAddress gw = WiFi.gatewayIP();
    IPAddress sn = WiFi.subnetMask();
    IPAddress dns1(8, 8, 8, 8);
    IPAddress dns2(8, 8, 4, 4);
    WiFi.config(ip, gw, sn, dns1, dns2);

    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("DNS: ");
    Serial.println(WiFi.dnsIP(0));
  } else {
    Serial.print("WiFi connect timeout after ");
    Serial.print(wifi_connect_timeout_ms);
    Serial.println(" ms");
  }
}

bool connectMQTT() {
  // --- Verify system time before TLS ---
  /* AWS REMOVED: TLS Time Check
  // WiFiClientSecure validates the server certificate against the system clock.
  // If time is still at epoch (1970), TLS handshake silently fails → rc=-1.
  if (now < 1770000000) { // Must be after Feb 2026 because certificate was issued in April 2026
    Serial.print("[MQTT] Clock not valid for certs (epoch=");
    Serial.print((unsigned long)now);
    Serial.println("). Retrying NTP...");
    configTime(18000, 0, "pool.ntp.org", "time.nist.gov");
    unsigned long start = millis();
    while (time(nullptr) < 1770000000 && (millis() - start) < 10000) {
      delay(500);
    }
    now = time(nullptr);
    if (now < 1770000000) {
      Serial.println("[MQTT] NTP still failed. Skipping MQTT attempt.");
      return false;
    }
  }
  */
  time_t now = time(nullptr);
  
  struct tm timeinfo;
  localtime_r(&now, &timeinfo);
  Serial.print("[MQTT] Current Time: ");
  Serial.print(asctime(&timeinfo));

  // Single non-blocking attempt (no while-loop)
  // The backoff timer in reconnectMQTT() handles retry spacing
  Serial.print("[MQTT] Connecting to Local Mosquitto Broker...");

  if (client.connect(mqtt_client_id)) {
    Serial.println("connected!");
    return true;
  }

  Serial.print("failed, rc=");
  Serial.print(client.state());
  Serial.print(" (");
  switch (client.state()) {
    case -4: Serial.print("TIMEOUT"); break;
    case -3: Serial.print("LOST_CONNECTION"); break;
    case -2: Serial.print("CONNECT_FAILED"); break;
    case -1: Serial.print("DISCONNECTED"); break;
    case  1: Serial.print("BAD_PROTOCOL"); break;
    case  2: Serial.print("BAD_CLIENT_ID"); break;
    case  3: Serial.print("UNAVAILABLE"); break;
    case  4: Serial.print("BAD_CREDENTIALS"); break;
    case  5: Serial.print("UNAUTHORIZED"); break;
    default: Serial.print("UNKNOWN"); break;
  }
  Serial.println("). Will retry in 15s.");

  return false;
}

bool publishMessage(const String& payload) {
  if (!client.connected()) {
    Serial.println("[MQTT] Not connected, skipping publish");
    return false;
  }
  bool ok = client.publish(mqtt_topic, payload.c_str());
  if (!ok) {
    Serial.println("[MQTT] Publish failed");
  }
  return ok;
}

// =========================
// INITIALIZATION
// =========================
void initPacket() {
  dataPacket.meanMag = 0.0f;
  dataPacket.varianceMag = 0.0f;
  dataPacket.spikeCount = 0;
  dataPacket.motionDetected = false;

  dataPacket.heartRateAvg = 0.0f;
  dataPacket.heartRateVariance = 0.0f;
  dataPacket.fingerDetected = false;
  dataPacket.heartRateValid = false;

  dataPacket.temperatureAvg = 0.0f;
  dataPacket.humidityAvg = 0.0f;
  dataPacket.envValid = false;

  dataPacket.timestamp = 0;
}

void initI2CBus() {
  Wire.begin(I2C_SDA, I2C_SCL);
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

void initMAX30102() {
  Serial.println("Initializing MAX30102...");

  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30102 not detected!");
    maxReady = false;
    return;
  }

  byte ledBrightness = 90;
  byte sampleAverage = 4;
  byte ledMode = 2;
  int sampleRate = 100;
  int pulseWidth = 411;
  int adcRange = 4096;

  particleSensor.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange);
  particleSensor.setPulseAmplitudeRed(0x24);
  particleSensor.setPulseAmplitudeIR(0x24);
  particleSensor.setPulseAmplitudeGreen(0);

  maxReady = true;
  Serial.println("MAX30102 connected.");
}

void initAudioCapture() {
  Serial.println("Initializing audio capture...");
  if (!psramFound()) {
    Serial.println("PSRAM NOT FOUND");
    while (1);
  }

  size_t circular_bytes = FULL_AUDIO_SAMPLES * sizeof(int16_t);
  circularBuffer = (int16_t*) heap_caps_malloc(circular_bytes, MALLOC_CAP_SPIRAM);
  audioClipBuffer = (int16_t*) heap_caps_malloc(circular_bytes, MALLOC_CAP_SPIRAM);

  if (!circularBuffer || !audioClipBuffer) {
    Serial.println("Audio buffer allocation failed");
    while (1);
  }

  memset(circularBuffer, 0, circular_bytes);
  circularWriteIndex = 0;
  circularSamplesWritten = 0;

  i2sMutex = xSemaphoreCreateMutex();
  if (!i2sMutex) {
    Serial.println("I2S mutex allocation failed");
    while (1);
  }

  audioClipMutex = xSemaphoreCreateMutex();
  if (!audioClipMutex) {
    Serial.println("Audio clip mutex allocation failed");
    while (1);
  }

  setupI2S();
  Serial.println("Audio capture ready.");
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

  if (heartBpmCount > 0) {
    dataPacket.heartRateAvg = heartBpmSum / heartBpmCount;
    dataPacket.heartRateVariance = (heartBpmSumSq / heartBpmCount) - (dataPacket.heartRateAvg * dataPacket.heartRateAvg);
    dataPacket.heartRateValid = true;
  } else {
    dataPacket.heartRateAvg = 0.0f;
    dataPacket.heartRateVariance = 0.0f;
    dataPacket.heartRateValid = false;
  }

  if (motionMagCount > 0) {
    dataPacket.meanMag = motionMagSum / motionMagCount;
    dataPacket.varianceMag = (motionMagSumSq / motionMagCount) - (dataPacket.meanMag * dataPacket.meanMag);
    dataPacket.spikeCount = motionSpikeCount;
    dataPacket.motionDetected = (motionSpikeCount > 0);
  } else {
    dataPacket.meanMag = 0.0f;
    dataPacket.varianceMag = 0.0f;
    dataPacket.spikeCount = 0;
    dataPacket.motionDetected = false;
  }
}

void resetAverageWindows() {
  envTempSum = 0.0f;
  envHumiditySum = 0.0f;
  envSampleCount = 0;

  heartBpmSum = 0.0f;
  heartBpmSumSq = 0.0f;
  heartBpmCount = 0;

  motionMagSum = 0.0f;
  motionMagSumSq = 0.0f;
  motionMagCount = 0;
  motionSpikeCount = 0;
}

// =========================
// SENSOR READ FUNCTIONS
// =========================
void readMotionSensor() {
  if (!mpuReady) return;

  int16_t ax, ay, az;
  mpu.getAcceleration(&ax, &ay, &az);

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

  motionMagSum += motionScore;
  motionMagSumSq += (motionScore * motionScore);
  motionMagCount++;
  
  if (motionScore > MOVEMENT_THRESHOLD) {
    motionSpikeCount++;
  }

  motionBaseX = (MOTION_BASELINE_ALPHA * motionBaseX) + ((1.0f - MOTION_BASELINE_ALPHA) * accel_x);
  motionBaseY = (MOTION_BASELINE_ALPHA * motionBaseY) + ((1.0f - MOTION_BASELINE_ALPHA) * accel_y);
  motionBaseZ = (MOTION_BASELINE_ALPHA * motionBaseZ) + ((1.0f - MOTION_BASELINE_ALPHA) * accel_z);
}

void readEnvironmentSensor() {
  if (!bmeReady) {
    dataPacket.envValid = false;
    return;
  }

  float temperature = bme.readTemperature();
  float humidity = bme.readHumidity();

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
  if (!maxReady) {
    dataPacket.fingerDetected = false;
    dataPacket.heartRateAvg = 0.0f;
    dataPacket.heartRateValid = false;
    return;
  }

  long irValue = particleSensor.getIR();
  dataPacket.fingerDetected = (irValue > FINGER_IR_THRESHOLD);

  if (!dataPacket.fingerDetected) {
    heartBpmSum = 0.0f;
    heartBpmSumSq = 0.0f;
    heartBpmCount = 0;
    lastBeatTime = 0;
    updateAverageSnapshot();
    return;
  }

  if (checkForBeat(irValue)) {
    unsigned long now = millis();

    if (lastBeatTime > 0) {
      unsigned long delta = now - lastBeatTime;

      if (delta > 0) {
        float bpm = 60.0f / (delta / 1000.0f);

        if (bpm > 40.0f && bpm < 220.0f) {
          heartBpmSum += bpm;
          heartBpmSumSq += (bpm * bpm);
          heartBpmCount++;
        }
      }
    }

    lastBeatTime = now;
  }

  updateAverageSnapshot();
}

void readVitals(unsigned long now) {
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

void publishVitalsMQTT(unsigned long now) {
  if (now - lastStatusPublish >= STATUS_PUBLISH_INTERVAL) {
    lastStatusPublish = now;
    dataPacket.timestamp = millis();

    updateAverageSnapshot();

    // --- Print vitals to serial (always, regardless of MQTT status) ---
    Serial.println("──────────── VITALS ────────────");
    Serial.print("  Motion:  meanMag=");
    Serial.print(dataPacket.meanMag, 4);
    Serial.print("  varMag=");
    Serial.print(dataPacket.varianceMag, 4);
    Serial.print("  spikes=");
    Serial.print(dataPacket.spikeCount);
    Serial.print("  detected=");
    Serial.println(dataPacket.motionDetected ? "YES" : "no");

    Serial.print("  Heart:   bpm=");
    Serial.print(dataPacket.heartRateAvg, 1);
    Serial.print("  varBpm=");
    Serial.print(dataPacket.heartRateVariance, 1);
    Serial.print("  finger=");
    Serial.print(dataPacket.fingerDetected ? "YES" : "no");
    Serial.print("  valid=");
    Serial.println(dataPacket.heartRateValid ? "YES" : "no");

    Serial.print("  Env:     temp=");
    Serial.print(dataPacket.temperatureAvg, 1);
    Serial.print("°C  humidity=");
    Serial.print(dataPacket.humidityAvg, 1);
    Serial.print("%  valid=");
    Serial.println(dataPacket.envValid ? "YES" : "no");

    Serial.print("  Sensors: MPU=");
    Serial.print(mpuReady ? "OK" : "FAIL");
    Serial.print("  BME=");
    Serial.print(bmeReady ? "OK" : "FAIL");
    Serial.print("  MAX=");
    Serial.println(maxReady ? "OK" : "FAIL");
    Serial.println("────────────────────────────────");

    String statusPayload = buildStatusPayload();
    if (publishMessage(statusPayload)) {
      Serial.println("[MQTT] Published vitals");
    }

    resetAverageWindows();
  }
}

float computeEnergy(const int16_t* frame, size_t len) {
  if (!frame || len == 0) return 0.0f;
  uint32_t sumAbs = 0;
  for (size_t i = 0; i < len; i++) {
    sumAbs += (uint32_t)abs(frame[i]);
  }
  return (float)sumAbs / (float)len;
}

int computeZCR(const int16_t* frame, size_t len) {
  if (!frame || len < 2) return 0;
  int zcr = 0;
  int prevSign = (frame[0] >= 0) ? 1 : -1;
  for (size_t i = 1; i < len; i++) {
    int sign = (frame[i] >= 0) ? 1 : -1;
    if (sign != prevSign) {
      zcr++;
    }
    prevSign = sign;
  }
  return zcr;
}

void runVAD() {
  if (audioCaptureInProgress || !i2sMutex) {
    return;
  }

  if (xSemaphoreTake(i2sMutex, 0) != pdTRUE) {
    return;
  }

  bool ok = readI2SSamplesRaw(vadFrame, VAD_FRAME_SAMPLES);
  if (!ok) {
    xSemaphoreGive(i2sMutex);
    Serial.println("[VAD] I2S read failed");
    return;
  }

  writeCircularBuffer(vadFrame, VAD_FRAME_SAMPLES);
  xSemaphoreGive(i2sMutex);

  float energy = computeEnergy(vadFrame, VAD_FRAME_SAMPLES);
  int zcr = computeZCR(vadFrame, VAD_FRAME_SAMPLES);
  int16_t peak = 0;
  for (size_t i = 0; i < VAD_FRAME_SAMPLES; i++) {
    int16_t absVal = abs(vadFrame[i]);
    if (absVal > peak) {
      peak = absVal;
    }
  }

  static unsigned long lastVadLog = 0;
  if (millis() - lastVadLog > 500) {
    lastVadLog = millis();
    Serial.print("[VAD] Energy=");
    Serial.print(energy, 1);
    Serial.print(" ZCR=");
    Serial.print(zcr);
    Serial.print(" Count=");
    Serial.println(cryCount);
  }

  bool cryFrame = (energy > ENERGY_THRESHOLD) &&
                  (zcr >= ZCR_MIN && zcr <= ZCR_MAX) &&
                  (peak > PEAK_THRESHOLD);
  if (cryFrame) {
    cryCount++;
  } else if (cryCount > 0) {
    cryCount--;
  }

  if (cryCount >= CRY_COUNT_TRIGGER &&
      (millis() - lastCryTrigger) > CRY_COOLDOWN_MS &&
      !audioCaptureInProgress &&
      !audioUploadInProgress) {
    Serial.println("[VAD] Cry detected");
    cryCount = 0;
    lastCryTrigger = millis();
    audioCaptureInProgress = true;

    BaseType_t created = xTaskCreatePinnedToCore(
      audioCaptureTask,
      "audioCaptureTask",
      8192,
      nullptr,
      1,
      &audioCaptureTaskHandle,
      1
    );

    if (created != pdPASS) {
      Serial.println("[AUDIO] Task create failed");
      audioCaptureInProgress = false;
    }
  }
}

void audioCaptureTask(void* param) {
  (void)param;
  if (!audioClipBuffer || !i2sMutex) {
    Serial.println("[AUDIO] Buffer or mutex missing");
    audioCaptureInProgress = false;
    vTaskDelete(nullptr);
    return;
  }

  Serial.println("[AUDIO] Preparing 3 sec clip");
  if (xSemaphoreTake(i2sMutex, portMAX_DELAY) != pdTRUE) {
    Serial.println("[AUDIO] Failed to lock I2S");
    audioCaptureInProgress = false;
    vTaskDelete(nullptr);
    return;
  }

  if (!audioClipMutex || xSemaphoreTake(audioClipMutex, portMAX_DELAY) != pdTRUE) {
    Serial.println("[AUDIO] Failed to lock clip buffer");
    xSemaphoreGive(i2sMutex);
    audioCaptureInProgress = false;
    vTaskDelete(nullptr);
    return;
  }

  extractBufferedAudio(audioClipBuffer, PRE_TRIGGER_SAMPLES);
  bool ok = captureFutureAudio(audioClipBuffer + PRE_TRIGGER_SAMPLES, POST_TRIGGER_SAMPLES);
  if (ok) {
    writeCircularBuffer(audioClipBuffer + PRE_TRIGGER_SAMPLES, POST_TRIGGER_SAMPLES);
  }
  xSemaphoreGive(audioClipMutex);
  xSemaphoreGive(i2sMutex);

  if (!ok) {
    Serial.println("[AUDIO] Future capture failed");
    audioCaptureInProgress = false;
    vTaskDelete(nullptr);
    return;
  }

  audioUploadInProgress = true;
  BaseType_t created = xTaskCreatePinnedToCore(
    audioUploadTask,
    "audioUploadTask",
    8192,
    nullptr,
    1,
    &audioUploadTaskHandle,
    1
  );

  if (created != pdPASS) {
    Serial.println("[HTTP] Upload task create failed");
    audioUploadInProgress = false;
  }

  audioCaptureInProgress = false;
  vTaskDelete(nullptr);
}

void audioUploadTask(void* param) {
  (void)param;
  if (!audioClipBuffer) {
    Serial.println("[HTTP] Clip buffer missing");
    audioUploadInProgress = false;
    vTaskDelete(nullptr);
    return;
  }

  if (!audioClipMutex || xSemaphoreTake(audioClipMutex, portMAX_DELAY) != pdTRUE) {
    Serial.println("[HTTP] Failed to lock clip buffer");
    audioUploadInProgress = false;
    vTaskDelete(nullptr);
    return;
  }

  if (uploadAudioHTTP(audioClipBuffer, FULL_AUDIO_SAMPLES)) {
    Serial.println("[HTTP] Upload success");
  } else {
    Serial.println("[HTTP] Upload failed");
  }

  xSemaphoreGive(audioClipMutex);

  Serial.println("[HTTP] Upload task exit");
  audioUploadInProgress = false;
  vTaskDelete(nullptr);
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
  json += "\"meanMag\":" + String(dataPacket.meanMag, 4);
  json += ",\"varianceMag\":" + String(dataPacket.varianceMag, 4);
  json += ",\"spikeCount\":" + String(dataPacket.spikeCount);
  json += ",\"detected\":" + String(dataPacket.motionDetected ? "true" : "false");
  json += "}";

  json += ",\"heart\":{";
  json += "\"bpm\":" + String(dataPacket.heartRateAvg, 2);
  json += ",\"varianceBpm\":" + String(dataPacket.heartRateVariance, 2);
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

bool readI2SSamplesRaw(int16_t* dest, size_t sampleCount) {
  if (sampleCount == 0 || !dest) return false;

  size_t bytesRead = 0;
  size_t index = 0;

  while (index < sampleCount) {
    int32_t temp[256];
    esp_err_t err = i2s_read(I2S_PORT, temp, sizeof(temp), &bytesRead, portMAX_DELAY);
    if (err != ESP_OK || bytesRead == 0) {
      return false;
    }

    int samples = bytesRead / sizeof(int32_t);
    for (int i = 0; i < samples && index < sampleCount; i++) {
      int16_t sample16 = (int16_t)(temp[i] >> 8);
      dest[index++] = sample16;
    }
  }

  return true;
}

void writeCircularBuffer(const int16_t* samples, size_t sampleCount) {
  if (!samples || !circularBuffer || sampleCount == 0) return;

  size_t remaining = sampleCount;
  size_t offset = 0;
  while (remaining > 0) {
    size_t space = FULL_AUDIO_SAMPLES - circularWriteIndex;
    size_t chunk = (remaining < space) ? remaining : space;
    memcpy(&circularBuffer[circularWriteIndex], &samples[offset], chunk * sizeof(int16_t));
    circularWriteIndex = (circularWriteIndex + chunk) % FULL_AUDIO_SAMPLES;
    offset += chunk;
    remaining -= chunk;
  }

  if (circularSamplesWritten < FULL_AUDIO_SAMPLES) {
    circularSamplesWritten += sampleCount;
    if (circularSamplesWritten > FULL_AUDIO_SAMPLES) {
      circularSamplesWritten = FULL_AUDIO_SAMPLES;
    }
  }
}

void extractBufferedAudio(int16_t* dest, size_t sampleCount) {
  if (!dest || !circularBuffer || sampleCount == 0) return;

  size_t available = circularSamplesWritten;
  if (available > sampleCount) {
    available = sampleCount;
  }

  size_t missing = sampleCount - available;
  if (missing > 0) {
    memset(dest, 0, missing * sizeof(int16_t));
  }

  if (available == 0) {
    return;
  }

  size_t startIndex = (circularWriteIndex + FULL_AUDIO_SAMPLES - available) % FULL_AUDIO_SAMPLES;
  size_t firstChunk = FULL_AUDIO_SAMPLES - startIndex;
  if (firstChunk > available) {
    firstChunk = available;
  }

  memcpy(dest + missing, &circularBuffer[startIndex], firstChunk * sizeof(int16_t));
  size_t remaining = available - firstChunk;
  if (remaining > 0) {
    memcpy(dest + missing + firstChunk, &circularBuffer[0], remaining * sizeof(int16_t));
  }
}

bool captureFutureAudio(int16_t* dest, size_t sampleCount) {
  if (!dest || sampleCount == 0) return false;
  return readI2SSamplesRaw(dest, sampleCount);
}

bool uploadAudioHTTP(const int16_t* pcm, size_t sampleCount) {
  if (!pcm || sampleCount == 0) return false;
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] WiFi not connected, retrying");
    connectWiFi();
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] WiFi still offline, skipping upload");
    return false;
  }

  HTTPClient http;
  WiFiClient httpClient;

  if (!http.begin(httpClient, audio_post_url)) {
    Serial.println("[HTTP] Begin failed");
    return false;
  }

  http.setTimeout(audio_post_timeout_ms);
  http.addHeader("Content-Type", "application/octet-stream");

  int payload_bytes = (int)(sampleCount * sizeof(int16_t));
  int httpCode = http.POST((uint8_t*)pcm, payload_bytes);

  if (httpCode <= 0) {
    Serial.print("[HTTP] POST error: ");
    Serial.println(http.errorToString(httpCode));
    http.end();
    return false;
  }

  Serial.print("[HTTP] Status: ");
  Serial.println(httpCode);
  String response = http.getString();
  Serial.print("[HTTP] Response: ");
  Serial.println(response);
  http.end();

  return (httpCode >= 200 && httpCode < 300);
}