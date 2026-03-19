/**
 * wifi_mqtt.ino — WiFi connection + MQTT client management
 * 
 * Handles:
 *   - WiFi connection with retry
 *   - MQTT connect / subscribe / reconnect
 *   - Incoming message dispatch → command_handler
 *   - Status + flow publishing helpers
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"
#include "topics.h"

// ── Externals ─────────────────────────────────────────────────────────────────
extern String g_mode;
extern String g_disease;
extern String g_severity;
extern float  g_dosage_ml;
extern bool   isMotorRunning();
extern float  getTotalLitres();
extern float  getFlowRateLPM();
extern void   handleCommand(const String& topic, const JsonDocument& doc);

// ── Clients ───────────────────────────────────────────────────────────────────
WiFiClient   wifiClient;
PubSubClient mqttClient(wifiClient);

// ─────────────────────────────────────────────────────────────────────────────

static void _mqttCallback(char* topic, byte* payload, unsigned int length) {
    String t = String(topic);
    String raw;
    raw.reserve(length);
    for (unsigned int i = 0; i < length; i++) raw += (char)payload[i];

    Serial.printf("[MQTT] ← [%s] %s\n", topic, raw.c_str());

    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, raw);
    if (err) {
        Serial.printf("[MQTT] JSON parse error: %s\n", err.c_str());
        return;
    }
    handleCommand(t, doc);
}

static void _connectWifi() {
    Serial.printf("Connecting to WiFi: %s", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    int tries = 0;
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        if (++tries > 40) {
            Serial.println("\nWiFi timeout — restarting...");
            ESP.restart();
        }
    }
    Serial.printf("\nWiFi connected: %s\n", WiFi.localIP().toString().c_str());
}

static void _connectMqtt() {
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(_mqttCallback);
    mqttClient.setBufferSize(1024);   // larger than default 256

    Serial.printf("Connecting MQTT to %s:%d", MQTT_BROKER, MQTT_PORT);
    while (!mqttClient.connected()) {
        bool ok = (strlen(MQTT_USERNAME) > 0)
            ? mqttClient.connect(MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD)
            : mqttClient.connect(MQTT_CLIENT_ID);

        if (ok) {
            Serial.println("\nMQTT connected.");
            mqttClient.subscribe(TOPIC_MOTOR_CMD,   1);
            mqttClient.subscribe(TOPIC_MODE,         1);
            mqttClient.subscribe(TOPIC_DISPLAY_CMD,  1);
            Serial.println("Subscribed to all topics.");
        } else {
            Serial.printf(" rc=%d — retry in 3s\n", mqttClient.state());
            delay(MQTT_RECONNECT_DELAY_MS);
        }
    }
}

// ── Public API ────────────────────────────────────────────────────────────────

void setupWifiMqtt() {
    _connectWifi();
    _connectMqtt();
}

void mqttLoop() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WiFi] Disconnected — reconnecting...");
        _connectWifi();
    }
    if (!mqttClient.connected()) {
        Serial.println("[MQTT] Disconnected — reconnecting...");
        _connectMqtt();
    }
    mqttClient.loop();
}

bool mqttConnected() {
    return mqttClient.connected();
}

void publishStatus() {
    StaticJsonDocument<256> doc;
    doc["running"]        = isMotorRunning();
    doc["mode"]           = g_mode;
    doc["flow_lpm"]       = getFlowRateLPM();
    doc["total_litres"]   = getTotalLitres();
    doc["wifi_rssi"]      = WiFi.RSSI();
    doc["free_heap"]      = ESP.getFreeHeap();
    doc["uptime_ms"]      = millis();

    char buf[256];
    serializeJson(doc, buf);
    mqttClient.publish(TOPIC_STATUS, buf, false);
    Serial.printf("[MQTT] → status published\n");
}

void publishFlow() {
    StaticJsonDocument<128> doc;
    doc["total_litres"] = getTotalLitres();
    doc["flow_lpm"]     = getFlowRateLPM();
    doc["uptime_ms"]    = millis();

    char buf[128];
    serializeJson(doc, buf);
    mqttClient.publish(TOPIC_FLOW, buf, false);
}

void publishAck(const String& cmd, bool success, const String& note = "") {
    StaticJsonDocument<128> doc;
    doc["cmd"]     = cmd;
    doc["success"] = success;
    if (note.length()) doc["note"] = note;
    char buf[128];
    serializeJson(doc, buf);
    mqttClient.publish(TOPIC_ACK, buf, false);
}
