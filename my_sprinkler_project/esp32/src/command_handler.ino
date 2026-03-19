/**
 * command_handler.ino — Parse and dispatch incoming MQTT JSON commands
 * 
 * Called by wifi_mqtt.ino's _mqttCallback for every incoming message.
 * Dispatches to motor_control, led_control, display_tft based on topic.
 */

#include <Arduino.h>
#include <ArduinoJson.h>
#include "topics.h"

// Externals
extern String g_mode;
extern String g_disease;
extern String g_severity;
extern float  g_dosage_ml;
extern void motorOn(float dosage_ml, String trigger);
extern void motorOff(String trigger);
extern void setLedState(const String& state);
extern void updateDisplay(const String& l1, const String& l2, const String& l3);
extern void beep(int freq, int ms);
extern void publishAck(const String& cmd, bool success, const String& note);

// ─────────────────────────────────────────────────────────────────────────────

void handleCommand(const String& topic, const JsonDocument& doc) {

    // ── server/motor/cmd ──────────────────────────────────────────────────────
    if (topic == TOPIC_MOTOR_CMD) {
        String cmd     = doc["cmd"]     | "off";
        float  dosage  = doc["dosage_ml"] | 0.0f;
        String trigger = doc["trigger"]  | "manual";

        Serial.printf("[CMD] motor/%s  dosage=%.1f  trigger=%s\n",
                      cmd.c_str(), dosage, trigger.c_str());

        if (cmd == "on") {
            motorOn(dosage, trigger);
        } else if (cmd == "off") {
            motorOff(trigger);
        } else {
            Serial.printf("[CMD] Unknown motor cmd: %s\n", cmd.c_str());
            publishAck(cmd, false, "unknown_cmd");
        }
    }

    // ── server/mode ───────────────────────────────────────────────────────────
    else if (topic == TOPIC_MODE) {
        String newMode = doc["mode"] | "auto";
        g_mode = newMode;
        Serial.printf("[CMD] Mode → %s\n", newMode.c_str());
        updateDisplay("Mode: " + newMode, g_disease, "Sev: " + g_severity);

        // If switching to auto, ensure motor is off (safety)
        // (motor is controlled by server in auto mode; ESP32 just executes)
    }

    // ── esp32/display ─────────────────────────────────────────────────────────
    else if (topic == TOPIC_DISPLAY_CMD) {
        String l1 = doc["line1"] | "";
        String l2 = doc["line2"] | "";
        String l3 = doc["line3"] | "";
        updateDisplay(l1, l2, l3);
        Serial.printf("[CMD] Display updated: %s | %s | %s\n",
                      l1.c_str(), l2.c_str(), l3.c_str());
    }

    else {
        Serial.printf("[CMD] Unhandled topic: %s\n", topic.c_str());
    }
}
