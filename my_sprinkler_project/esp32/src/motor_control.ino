/**
 * motor_control.ino — Pump relay control
 * 
 * Manages the 12V diaphragm pump via a relay module.
 * Enforces a hard safety timeout to prevent over-spraying.
 */

#include <Arduino.h>
#include "config.h"

extern void setLedState(const String& state);
extern void beep(int freq, int ms);
extern void resetFlowMeter();
extern void publishAck(const String& cmd, bool success, const String& note);

// ── State ─────────────────────────────────────────────────────────────────────
static bool          _motorRunning   = false;
static unsigned long _motorStartTime = 0;
static float         _targetDosage   = 0.0f;
static String        _trigger        = "manual";

// ─────────────────────────────────────────────────────────────────────────────

void setupMotor() {
    pinMode(PIN_PUMP_RELAY, OUTPUT);
    digitalWrite(PIN_PUMP_RELAY, RELAY_OFF);
    _motorRunning = false;
    Serial.printf("Motor setup: PIN=%d  RELAY_ON=%d\n", PIN_PUMP_RELAY, RELAY_ON);
}

void motorOn(float dosage_ml, String trigger) {
    if (_motorRunning) {
        Serial.println("[Motor] Already running — ignoring ON command.");
        publishAck("on", false, "already_running");
        return;
    }
    digitalWrite(PIN_PUMP_RELAY, RELAY_ON);
    _motorRunning   = true;
    _motorStartTime = millis();
    _targetDosage   = dosage_ml;
    _trigger        = trigger;

    resetFlowMeter();
    setLedState("spray");
    beep(800, 150);

    Serial.printf("[Motor] ON — dosage=%.1f ml/m²  trigger=%s\n",
                  dosage_ml, trigger.c_str());
    publishAck("on", true);
}

void motorOff(String trigger) {
    if (!_motorRunning) {
        Serial.println("[Motor] Already off.");
        publishAck("off", false, "already_off");
        return;
    }
    digitalWrite(PIN_PUMP_RELAY, RELAY_OFF);
    _motorRunning = false;

    setLedState("idle");
    beep(500, 100);

    unsigned long dur = (millis() - _motorStartTime) / 1000;
    Serial.printf("[Motor] OFF — trigger=%s  duration=%lus\n",
                  trigger.c_str(), dur);
    publishAck("off", true);
}

void checkMotorSafetyTimeout() {
    if (!_motorRunning) return;
    if (millis() - _motorStartTime >= MAX_SPRAY_DURATION_MS) {
        Serial.println("[Motor] SAFETY TIMEOUT — forcing off.");
        motorOff("safety_timeout");
        beep(300, 500);   // long warning beep
    }
}

bool isMotorRunning() {
    return _motorRunning;
}

float getTargetDosage() {
    return _targetDosage;
}

unsigned long getMotorRuntime() {
    if (!_motorRunning) return 0;
    return (millis() - _motorStartTime) / 1000;
}
