# ESP32 Controller

Handles: pump relay, status LEDs, TFT display, flow meter.
Communicates with the Pi and backend server via MQTT.

## Setup
1. Install PlatformIO (VSCode extension or CLI)
2. Edit `include/config.h` — set WiFi credentials and MQTT broker IP
3. Configure TFT_eSPI `User_Setup.h` for your specific TFT module
4. `pio run --target upload`
