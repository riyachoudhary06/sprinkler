/**
 * led_control.ino — RGB status LED management
 * 
 * States:
 *   "idle"  — green LED  — system running, pump off
 *   "spray" — blue LED   — pump active
 *   "error" — red LED    — WiFi/MQTT fault
 */

#include <Arduino.h>
#include "config.h"

void setupLeds() {
    pinMode(PIN_LED_IDLE,  OUTPUT);
    pinMode(PIN_LED_SPRAY, OUTPUT);
    pinMode(PIN_LED_ERROR, OUTPUT);
    // All off at start
    digitalWrite(PIN_LED_IDLE,  LOW);
    digitalWrite(PIN_LED_SPRAY, LOW);
    digitalWrite(PIN_LED_ERROR, LOW);
    Serial.printf("LEDs setup: idle=%d spray=%d error=%d\n",
                  PIN_LED_IDLE, PIN_LED_SPRAY, PIN_LED_ERROR);
}

void setLedState(const String& state) {
    digitalWrite(PIN_LED_IDLE,  state == "idle"  ? HIGH : LOW);
    digitalWrite(PIN_LED_SPRAY, state == "spray" ? HIGH : LOW);
    digitalWrite(PIN_LED_ERROR, state == "error" ? HIGH : LOW);
    Serial.printf("[LED] state → %s\n", state.c_str());
}

void blinkLed(int pin, int times, int on_ms, int off_ms) {
    for (int i = 0; i < times; i++) {
        digitalWrite(pin, HIGH);
        delay(on_ms);
        digitalWrite(pin, LOW);
        if (i < times - 1) delay(off_ms);
    }
}
