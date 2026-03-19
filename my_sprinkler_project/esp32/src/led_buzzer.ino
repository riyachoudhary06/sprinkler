/**
 * led_buzzer.ino — Passive buzzer control via ledc PWM
 * 
 * Wiring:
 *   Buzzer + → PIN_BUZZER
 *   Buzzer − → GND
 */

#include <Arduino.h>
#include "config.h"

#define BUZZER_CHANNEL 0
#define BUZZER_RESOLUTION 8    // 8-bit duty cycle

void setupBuzzer() {
    if (!BUZZER_ENABLED) return;
    ledcSetup(BUZZER_CHANNEL, 1000, BUZZER_RESOLUTION);
    ledcAttachPin(PIN_BUZZER, BUZZER_CHANNEL);
    Serial.printf("Buzzer setup: PIN=%d\n", PIN_BUZZER);
}

/**
 * Emit a tone at `freq` Hz for `duration_ms` milliseconds.
 * Non-blocking variant uses a flag — for now uses blocking delay
 * since beeps are very short and called only on state changes.
 */
void beep(int freq, int duration_ms) {
    if (!BUZZER_ENABLED) return;
    ledcWriteTone(BUZZER_CHANNEL, freq);
    delay(duration_ms);
    ledcWriteTone(BUZZER_CHANNEL, 0);
}

void beepPattern(int* freqs, int* durations, int count) {
    for (int i = 0; i < count; i++) {
        beep(freqs[i], durations[i]);
        if (i < count - 1) delay(80);
    }
}
