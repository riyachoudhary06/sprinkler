/**
 * main.ino — Agri-Watch ESP32 (USB Serial mode)
 *
 * WiFi and MQTT are REMOVED.
 * All communication is over USB serial to the Raspberry Pi.
 * Pi handles WiFi, MQTT, and cloud connectivity.
 */

#include <Arduino.h>
#include "config.h"

extern void setupSerial();
extern void serialLoop();
extern void setupMotor();
extern void setupLeds();
extern void setupDisplay();
extern void setupFlowMeter();
extern void setupBuzzer();
extern void publishStatus();
extern void publishFlow();
extern void checkMotorSafetyTimeout();
extern void flowMeterLoop();
extern void updateDisplay(const String&, const String&, const String&);
extern void setLedState(const String&);
extern void beep(int, int);

String g_mode      = "auto";
String g_disease   = "—";
String g_severity  = "none";
float  g_dosage_ml = 0.0f;

unsigned long g_lastStatusMs = 0;
unsigned long g_lastFlowMs   = 0;
unsigned long g_lastDisplayMs = 0;

void setup() {
  setupSerial();      // USB serial — must be first
  setupLeds();
  setLedState("idle");
  setupMotor();
  setupBuzzer();
  setupFlowMeter();
  setupDisplay();

  updateDisplay("AGRI-WATCH", "USB Serial Mode", "Waiting for Pi...");
  beep(1000, 100);

  Serial.println("{\"type\":\"ready\",\"msg\":\"ESP32 setup complete\"}");
}

void loop() {
  serialLoop();                 // read + dispatch Pi commands
  checkMotorSafetyTimeout();    // hard safety cutoff
  flowMeterLoop();              // accumulate pulse count

  unsigned long now = millis();

  if (now - g_lastStatusMs >= STATUS_PUBLISH_INTERVAL_MS) {
    publishStatus();            // sends JSON line to Pi via Serial
    g_lastStatusMs = now;
  }
  if (now - g_lastFlowMs >= FLOW_REPORT_INTERVAL_MS) {
    publishFlow();
    g_lastFlowMs = now;
  }
  if (now - g_lastDisplayMs >= DISPLAY_UPDATE_INTERVAL_MS) {
    // Refresh TFT with current state
    extern bool isMotorRunning();
    extern float getFlowRateLPM();
    extern float getTotalLitres();
    if (isMotorRunning()) {
      updateDisplay(
        "SPRAYING",
        "Flow: " + String(getFlowRateLPM(), 2) + " L/min",
        "Total: "  + String(getTotalLitres(), 3) + " L"
      );
    } else {
      updateDisplay(
        "Mode: " + g_mode,
        g_disease == "—" ? "Idle" : g_disease,
        "Sev: " + g_severity
      );
    }
    g_lastDisplayMs = now;
  }

  delay(10);
}
