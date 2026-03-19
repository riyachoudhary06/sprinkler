#pragma once

// ── Topics ESP32 subscribes to ────────────────────────────────────────────────
#define TOPIC_MOTOR_CMD     "server/motor/cmd"    // {"cmd":"on","dosage_ml":25}
#define TOPIC_MODE          "server/mode"          // {"mode":"auto"}
#define TOPIC_DISPLAY_CMD   "esp32/display"        // {"line1":"...","line2":"...","line3":"..."}

// ── Topics ESP32 publishes ────────────────────────────────────────────────────
#define TOPIC_STATUS        "esp32/status"         // heartbeat + state
#define TOPIC_FLOW          "esp32/flow"           // spray session summary
#define TOPIC_ACK           "esp32/ack"            // command acknowledgement
