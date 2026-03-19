/**
 * flow_meter.ino — YF-S201 Hall-effect flow meter
 * 
 * The YF-S201 outputs ~450 pulses per litre.
 * An ISR counts rising edges on PIN_FLOW_METER.
 * flowMeterLoop() is called every iteration of loop()
 * to compute flow rate (L/min) from pulse count per second.
 * 
 * Wiring:
 *   Red   → 5V
 *   Black → GND
 *   Yellow → PIN_FLOW_METER (with 10kΩ pull-up to 3.3V)
 */

#include <Arduino.h>
#include "config.h"

volatile uint32_t _pulseCount    = 0;
static   uint32_t _lastPulseSnap = 0;
static   unsigned long _lastFlowTime = 0;
static   float    _flowRateLPM   = 0.0f;
static   float    _totalLitres   = 0.0f;

// ISR — keep it minimal
void IRAM_ATTR _flowISR() {
    _pulseCount++;
}

void setupFlowMeter() {
    pinMode(PIN_FLOW_METER, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_FLOW_METER), _flowISR, RISING);
    _lastFlowTime = millis();
    Serial.printf("Flow meter setup: PIN=%d  %.0f pulses/L\n",
                  PIN_FLOW_METER, FLOW_PULSES_PER_LITRE);
}

/**
 * Call every loop() iteration.
 * Every 1000 ms, snapshot pulse count, compute flow rate & total volume.
 */
void flowMeterLoop() {
    unsigned long now = millis();
    if (now - _lastFlowTime < 1000) return;

    // Atomic snapshot
    noInterrupts();
    uint32_t snap = _pulseCount;
    _pulseCount   = 0;
    interrupts();

    float elapsed_min = (now - _lastFlowTime) / 60000.0f;
    _flowRateLPM  = (snap / FLOW_PULSES_PER_LITRE) / elapsed_min;
    _totalLitres += (snap / FLOW_PULSES_PER_LITRE);
    _lastFlowTime = now;
}

float getFlowRateLPM() {
    return _flowRateLPM;
}

float getTotalLitres() {
    return _totalLitres;
}

void resetFlowMeter() {
    noInterrupts();
    _pulseCount = 0;
    interrupts();
    _totalLitres  = 0.0f;
    _flowRateLPM  = 0.0f;
    _lastFlowTime = millis();
}
