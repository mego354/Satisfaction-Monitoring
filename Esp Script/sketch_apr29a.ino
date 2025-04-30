// {"timestamp": "32767","heartRate": 42.83,"spo2": 100.00,"avgHeartRate": 58}
// {"timestamp": "37450","heartRate": 107.14,"spo2": 100.00,"avgHeartRate": 85}
// {"timestamp": "46975","heartRate": 41.67,"spo2": 0.00,"avgHeartRate": 70}
// {"timestamp": "51738","heartRate": 44.09,"spo2": 90.93,"avgHeartRate": 58}
// {"timestamp": "54580","heartRate": 83.22,"spo2": 95.72,"avgHeartRate": 68}


#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <WiFi.h> 
#include <HTTPClient.h>

// Wi-Fi Credentials
const char* ssid = "HUAWEI nova 9";
const char* password = "100010000";

// Replace with your PC's local IP
const char* serverUrl = "http://192.168.43.75:4000/health_data";


MAX30105 particleSensor;

const byte RATE_SIZE = 4; // For heart rate averaging
byte rates[RATE_SIZE]; // Array of heart rates
byte rateSpot = 0;
long lastBeat = 0; // Time at which the last beat occurred

float beatsPerMinute;
int beatAvg;
float spo2 = 0; // SpO2 value
float ratio;

// Buffers for AC/DC moving average
const int BUFFER_SIZE = 10;
long irBuffer[BUFFER_SIZE], redBuffer[BUFFER_SIZE];
int bufferIndex = 0;
long irDC = 0, redDC = 0, irAC = 0, redAC = 0;

// JSON formatting function for a single reading
String formatJson(float heartRate, float spo2Value, int avgBPM, unsigned long timestamp) {
  String json = "{";
  json += "\"timestamp\": \"" + String(timestamp) + "\",";
  json += "\"heartRate\": " + String(heartRate, 2) + ",";
  json += "\"spo2\": " + String(spo2Value, 2) + ",";
  json += "\"avgHeartRate\": " + String(avgBPM);
  json += "}";
  return json;
}

// Function to send JSON to the API endpoint
void sendToServer(float bpm, float spo2Val, int avgBPM, unsigned long timestamp) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String jsonPayload = formatJson(bpm, spo2Val, avgBPM, timestamp);

    int httpCode = http.POST(jsonPayload);
    if (httpCode > 0) {
      Serial.println("POST response code: " + String(httpCode));
    } else {
      Serial.println("POST failed: " + http.errorToString(httpCode));
    }
    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("Starting MAX30102 detection...");

  Wire.begin(); // Initialize I2C

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");

  // Initialize MAX30102
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("MAX30102 NOT found. Please check wiring!");
    while (1);
  } else {
    Serial.println("MAX30102 FOUND!");
  }

  Serial.println("Place your index finger on the sensor with steady pressure.");

  // Configure sensor
  particleSensor.setup(); // Default settings
  particleSensor.setPulseAmplitudeRed(0x1F); // Increased for better signal
  particleSensor.setPulseAmplitudeIR(0x1F); // Increased for better signal
  particleSensor.setPulseAmplitudeGreen(0); // Turn off green LED
}

void loop() {
  long irValue = particleSensor.getIR();
  long redValue = particleSensor.getRed();

  // Check if finger is present
  if (irValue < 50000) {
    Serial.print("IR=");
    Serial.print(irValue);
    Serial.println(" No finger?");
    spo2 = 0;
    beatsPerMinute = 0;
    beatAvg = 0;
    return; // Skip calculations
  }

  // Heart rate calculation
  if (checkForBeat(irValue) == true) {
    long delta = millis() - lastBeat;
    lastBeat = millis();
    beatsPerMinute = 60 / (delta / 1000.0);

    // Only process valid BPM (> 40 and < 255)
    if (beatsPerMinute > 40 && beatsPerMinute < 255) {
      rates[rateSpot++] = (byte)beatsPerMinute;
      rateSpot %= RATE_SIZE;
      beatAvg = 0;
      for (byte x = 0; x < RATE_SIZE; x++)
        beatAvg += rates[x];
      beatAvg /= RATE_SIZE;

      // Calculate SpO2 (only if signal is valid)
      if (irDC > 10000 && redDC > 10000 && abs(irAC) > 50 && abs(redAC) > 50) {
        ratio = (float)(redAC * irDC) / (float)(irAC * redDC);
        spo2 = 110.0 - 25.0 * ratio;
        if (spo2 >= 100) spo2 = 100;
        if (spo2 < 90) spo2 = 50; // Filter out unrealistically low SpO2
      } else {
        spo2 = 95; // Invalid SpO2
      }

      // Output JSON for this reading
      Serial.println("Reading JSON:");
      String json = formatJson(beatsPerMinute, spo2, beatAvg, millis());
      Serial.println(json);
      sendToServer(beatsPerMinute, spo2, beatAvg, millis());
    }
  }

  // AC/DC separation with moving average
  irBuffer[bufferIndex] = irValue;
  redBuffer[bufferIndex] = redValue;
  bufferIndex = (bufferIndex + 1) % BUFFER_SIZE;

  // Calculate DC (moving average)
  irDC = 0;
  redDC = 0;
  for (int i = 0; i < BUFFER_SIZE; i++) {
    irDC += irBuffer[i];
    redDC += redBuffer[i];
  }
  irDC /= BUFFER_SIZE;
  redDC /= BUFFER_SIZE;

  // Calculate AC
  irAC = irValue - irDC;
  redAC = redValue - redDC;

  // Print real-time results
  Serial.print("IR=");
  Serial.print(irValue);
  Serial.print(", Red=");
  Serial.print(redValue);
  Serial.print(", BPM=");
  Serial.print(beatsPerMinute);
  Serial.print(", Avg BPM=");
  Serial.print(beatAvg);
  Serial.print(", SpO2=");
  Serial.print(spo2);
  Serial.println("%");
}