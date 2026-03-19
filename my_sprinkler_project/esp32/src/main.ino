/**
 * main.ino — Agri-Watch ESP32 Controller
 * 
 * Handles: pump relay, status LEDs, TFT display, flow meter, buzzer.
 * Communicates with the backend server via MQTT over WiFi.
 * 
 * Startup sequence:
 *   1. Init Serial
 *   2. Init LEDs, motor, buzzer, display
 *   3. Connect WiFi
 *   4. Connect MQTT + subscribe
 *   5. Attach flow meter ISR
 *   6. Enter main loop
 */

#include <Arduino.h>
#include "config.h"
#include "topics.h"

// Forward declarations (defined in other .ino files)
void setupWifiMqtt();
void mqttLoop();
bool mqttConnected();

void setupMotor();
void motorOn(float dosage_ml, String trigger);
void motorOff(String trigger);
void checkMotorSafetyTimeout();
bool isMotorRunning();

void setupLeds();
void setLedState(const String& state);

void setupDisplay();
void updateDisplay(const String& l1, const String& l2, const String& l3);
void displayLoop();

void setupFlowMeter();
void flowMeterLoop();
float getTotalLitres();
float getFlowRateLPM();
void resetFlowMeter();

void setupBuzzer();
void beep(int freq, int duration_ms);

void publishStatus();
void publishFlow();

// ── Globals shared across files ───────────────────────────────────────────────
String g_mode       = "auto";     // "auto" | "manual"
String g_disease    = "—";
String g_severity   = "none";
float  g_dosage_ml  = 0.0f;

unsigned long g_lastStatusPublish = 0;
unsigned long g_lastFlowPublish   = 0;
unsigned long g_lastDisplayUpdate = 0;

// ─────────────────────────────────────────────────────────────────────────────

void setup() {
    Serial.begin(115200);
    delay(200);
    Serial.println("\n\n══ Agri-Watch ESP32 Controller ══");

    setupLeds();
    setLedState("error");          // red while connecting

    setupMotor();
    setupBuzzer();
    setupFlowMeter();
    setupDisplay();
    updateDisplay("AGRI-WATCH", "Connecting WiFi...", "");

    setupWifiMqtt();               // blocks until WiFi + MQTT connected

    setLedState("idle");
    updateDisplay("AGRI-WATCH", "Mode: " + g_mode, "MQTT: OK");
    beep(1000, 100);
    Serial.println("Setup complete.");
}

void loop() {
    mqttLoop();                    // keep MQTT alive, dispatch callbacks
    checkMotorSafetyTimeout();     // hard-off after MAX_SPRAY_DURATION_MS
    flowMeterLoop();               // accumulate pulse count into litres

    unsigned long now = millis();

    // Publish heartbeat status
    if (now - g_lastStatusPublish >= STATUS_PUBLISH_INTERVAL_MS) {
        publishStatus();
        g_lastStatusPublish = now;
    }

    // Publish flow data
    if (now - g_lastFlowPublish >= FLOW_REPORT_INTERVAL_MS) {
        if (isMotorRunning()) publishFlow();
        g_lastFlowPublish = now;
    }

    // Refresh TFT display
    if (now - g_lastDisplayUpdate >= DISPLAY_UPDATE_INTERVAL_MS) {
        if (isMotorRunning()) {
            updateDisplay(
                "SPRAYING",
                "Flow: " + String(getFlowRateLPM(), 2) + " L/min",
                "Total: " + String(getTotalLitres(), 3) + " L"
            );
        } else {
            updateDisplay(
                "Mode: " + g_mode,
                g_disease == "—" ? "No detection" : g_disease,
                "Sev: " + g_severity
            );
        }
        g_lastDisplayUpdate = now;
    }

    delay(10);
}
