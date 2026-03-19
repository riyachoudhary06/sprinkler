#pragma once

// ── WiFi ──────────────────────────────────────────────────────────────────────
#define WIFI_SSID        "YOUR_WIFI_SSID"
#define WIFI_PASS        "YOUR_WIFI_PASSWORD"

// ── MQTT ──────────────────────────────────────────────────────────────────────
#define MQTT_BROKER      "192.168.1.100"
#define MQTT_PORT        1883
#define MQTT_CLIENT_ID   "agriwatch-esp32"
#define MQTT_USERNAME    ""               // leave empty if no auth
#define MQTT_PASSWORD    ""

// ── Pin Definitions ───────────────────────────────────────────────────────────
// Pump relay (active HIGH — change to LOW if your relay board is active-low)
#define PIN_PUMP_RELAY   26
#define RELAY_ON         HIGH
#define RELAY_OFF        LOW

// Status LEDs (common-cathode)
#define PIN_LED_IDLE     18   // green  — system running, no spray
#define PIN_LED_SPRAY    19   // blue   — pump active
#define PIN_LED_ERROR    21   // red    — MQTT/WiFi fault

// Flow meter (YF-S201 or similar Hall-effect pulse sensor)
#define PIN_FLOW_METER   34   // INPUT_PULLUP; connect sensor OUT here
#define FLOW_PULSES_PER_LITRE  450.0f   // YF-S201 spec: ~450 pulses/litre

// TFT display (ST7735 / ILI9341 — configure TFT_eSPI User_Setup.h separately)
#define PIN_TFT_CS       5
#define PIN_TFT_DC       4
#define PIN_TFT_RST      22
#define PIN_TFT_MOSI     23
#define PIN_TFT_SCLK     18   // Note: shared with LED_IDLE if using SPI LCD

// Buzzer (optional, for alarm)
#define PIN_BUZZER       25
#define BUZZER_ENABLED   true

// ── Timing ────────────────────────────────────────────────────────────────────
#define STATUS_PUBLISH_INTERVAL_MS   5000    // publish esp32/status every 5s
#define FLOW_REPORT_INTERVAL_MS     10000    // publish esp32/flow every 10s
#define DISPLAY_UPDATE_INTERVAL_MS   3000    // refresh TFT every 3s
#define MQTT_RECONNECT_DELAY_MS      3000    // wait between reconnect attempts

// ── Safety ────────────────────────────────────────────────────────────────────
#define MAX_SPRAY_DURATION_MS   300000   // 5 minutes hard cap — auto-off
