# 🌿 Agri-Watch — Intelligent Pesticide Sprinkling System

> IoT precision-agriculture platform combining Raspberry Pi sensor nodes,
> Gemini Vision AI disease detection, ESP32 actuator control, and a
> real-time React dashboard.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         WEBSITE                                 │
│   React Dashboard  ←→  FastAPI Backend  ←→  SQLite / Postgres  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ MQTT (broker: Mosquitto)
              ┌────────────────┴────────────────┐
              │                                 │
┌─────────────▼──────────────┐    ┌─────────────▼──────────────┐
│       RASPBERRY PI         │    │          ESP32             │
│                            │    │                            │
│  Sensors (pH, NPK,         │    │  Pump relay               │
│  moisture, DHT22, BH1750)  │    │  Status LEDs              │
│  Pi Camera v2 (stream)     │    │  TFT display              │
│  Gemini Vision API         │    │  YF-S201 flow meter       │
│  OLED display (SSD1306)    │    │  Buzzer                   │
└────────────────────────────┘    └────────────────────────────┘
```

### MQTT Topic Map

| Topic                  | Direction          | Payload                                      |
|------------------------|--------------------|----------------------------------------------|
| `pi/sensors/all`       | Pi → Backend       | JSON: pH, moisture, NPK, temp, humidity, lux |
| `pi/inference/result`  | Pi → Backend       | JSON: disease, confidence, severity, dosage  |
| `pi/logs`              | Pi → Backend       | JSON: level, message, source                 |
| `server/motor/cmd`     | Backend → ESP32    | JSON: cmd (on/off), dosage_ml, trigger       |
| `server/mode`          | Backend → All      | JSON: mode (auto/manual)                     |
| `server/camera/capture`| Backend → Pi       | JSON: cmd, ts                                |
| `esp32/status`         | ESP32 → Backend    | JSON: running, flow_lpm, wifi_rssi           |
| `esp32/flow`           | ESP32 → Backend    | JSON: total_litres, duration_sec             |
| `esp32/ack`            | ESP32 → Backend    | JSON: cmd, success, note                     |

---

## Project Structure

```
agriwatch/
├── website/
│   ├── frontend/                 React 18 + Vite dashboard
│   │   └── src/
│   │       ├── components/       Dashboard, SensorCard, DiseasePanel, ...
│   │       ├── pages/            7 pages (Dashboard, Sensors, Camera, ...)
│   │       ├── hooks/            useMQTT, useSensors, useCamera
│   │       └── store/            Zustand global state
│   └── backend/                  FastAPI server
│       ├── api/                  6 route modules
│       ├── db/                   SQLAlchemy models + session
│       └── services/             MQTT bridge + alert service
│
├── raspberry_pi/
│   ├── sensors/                  pH, moisture, NPK, DHT22, BH1750
│   ├── camera/                   MJPEG stream, capture, preprocess
│   ├── inference/                Gemini client, prompt builder, dosage calc
│   ├── mqtt/                     Publisher + Subscriber
│   ├── display/                  SSD1306 OLED
│   └── utils/                    Config, logger
│
└── esp32/
    ├── src/                      Arduino .ino files
    └── include/                  config.h, topics.h
```

---

## Quickstart

### 1. Prerequisites

- Raspberry Pi 4 (or 3B+) running Raspberry Pi OS Bullseye+
- ESP32 DevKit v1
- Python 3.11+ on the backend machine
- Node.js 18+ for the frontend
- PlatformIO for the ESP32
- Mosquitto MQTT broker (can run on the Pi or backend machine)

### 2. MQTT Broker (Mosquitto)

Install on Raspberry Pi or backend server:

```bash
sudo apt install mosquitto mosquitto-clients -y
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Test it works
mosquitto_pub -t test/hello -m "world"
mosquitto_sub -t test/hello
```

### 3. Raspberry Pi

```bash
# Clone / copy raspberry_pi/ folder to the Pi
cd raspberry_pi

# Install system dependencies first
sudo apt install python3-pip python3-venv libatlas-base-dev -y
sudo pip3 install --break-system-packages -r requirements.txt

# Enable I2C and Serial in raspi-config
sudo raspi-config
# → Interface Options → I2C → Enable
# → Interface Options → Serial Port → Enable (no login shell)

# Configure environment
cp .env.example .env
nano .env     # ← set GEMINI_API_KEY and MQTT_BROKER_IP

# Run (auto-start on boot via systemd below)
python main.py
```

**Auto-start with systemd:**

```ini
# /etc/systemd/system/agriwatch.service
[Unit]
Description=Agri-Watch Pi Node
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/agriwatch/raspberry_pi
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable agriwatch
sudo systemctl start agriwatch
sudo journalctl -u agriwatch -f   # live logs
```

### 4. Backend Server

```bash
cd website/backend

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
nano .env     # ← set MQTT_BROKER_IP

# Run development server
uvicorn main:app --reload --port 8000

# Run production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

API docs auto-generated at: `http://localhost:8000/docs`

### 5. Frontend Dashboard

```bash
cd website/frontend

npm install

# Create .env.local
echo "VITE_API_URL=http://localhost:8000" > .env.local
echo "VITE_STREAM_URL=http://raspberrypi.local:8080/stream" >> .env.local

npm run dev      # development (http://localhost:5173)
npm run build    # production build → dist/
```

### 6. ESP32

```bash
cd esp32

# Install PlatformIO CLI or use VSCode PlatformIO extension
pip install platformio

# Edit config before flashing
nano include/config.h     # ← set WIFI_SSID, WIFI_PASS, MQTT_BROKER

# IMPORTANT: configure TFT_eSPI for your display
# Edit ~/.platformio/packages/framework-arduinoespressif32/
#   libraries/TFT_eSPI/User_Setup.h
# Set your driver (ST7735, ILI9341, etc.) and pin assignments.

# Build and flash
pio run --target upload

# Monitor serial output
pio device monitor
```

---

## Sensor Wiring

### Raspberry Pi GPIO

| Sensor         | Interface | Pi Pins                          |
|----------------|-----------|----------------------------------|
| ADS1115 (pH + moisture) | I2C | GPIO 2 (SDA), GPIO 3 (SCL), 3.3V, GND |
| DHT22          | 1-Wire    | GPIO 4, 3.3V, GND (10kΩ pull-up) |
| BH1750 (light) | I2C       | GPIO 2 (SDA), GPIO 3 (SCL), 3.3V, GND |
| NPK sensor     | RS485 USB | /dev/ttyUSB0 (via RS485-USB adapter) |
| SSD1306 OLED   | I2C       | GPIO 2 (SDA), GPIO 3 (SCL), 3.3V, GND |
| Pi Camera v2   | CSI       | Camera connector                 |

### ESP32

| Device            | ESP32 Pin       | Notes                     |
|-------------------|-----------------|---------------------------|
| Pump relay IN     | GPIO 26         | Active HIGH (configurable)|
| LED idle (green)  | GPIO 18         | 220Ω series resistor      |
| LED spray (blue)  | GPIO 19         | 220Ω series resistor      |
| LED error (red)   | GPIO 21         | 220Ω series resistor      |
| Flow meter OUT    | GPIO 34         | 10kΩ pull-up to 3.3V      |
| Buzzer +          | GPIO 25         | Passive buzzer            |
| TFT (SPI)         | See config.h    | Configure TFT_eSPI        |

---

## Configuration Reference

### raspberry_pi/.env

| Variable                | Default         | Description                          |
|-------------------------|-----------------|--------------------------------------|
| `GEMINI_API_KEY`        | —               | Google AI Studio API key (required)  |
| `GEMINI_MODEL`          | gemini-1.5-flash| Model name                           |
| `MQTT_BROKER_IP`        | localhost        | Mosquitto broker address             |
| `SENSOR_POLL_INTERVAL`  | 5               | Seconds between sensor reads         |
| `INFERENCE_INTERVAL`    | 30              | Seconds between disease scans        |
| `PH_SLOPE`              | 3.5             | pH probe calibration slope           |
| `PH_OFFSET`             | 0.0             | pH probe calibration offset          |
| `MOISTURE_DRY_RAW`      | 26000           | ADC reading in dry air               |
| `MOISTURE_WET_RAW`      | 13000           | ADC reading fully in water           |

### website/backend/.env

| Variable          | Default      | Description                     |
|-------------------|--------------|---------------------------------|
| `MQTT_BROKER_IP`  | localhost     | Mosquitto broker address        |
| `DATABASE_URL`    | sqlite:///./agriwatch.db | DB connection string |
| `PH_MIN/MAX`      | 5.5 / 7.5    | Alert threshold for pH          |
| `MOISTURE_MIN/MAX`| 40 / 80      | Alert threshold for moisture %  |

---

## API Endpoints

```
GET  /sensors/latest          Latest sensor reading
GET  /sensors/history         Time-series (limit, offset, hours)
GET  /sensors/stats           Min/avg/max per field
GET  /sensors/alerts          Current out-of-range values

GET  /disease/latest          Most recent Gemini result
GET  /disease/predictions     Paginated history
GET  /disease/summary         Grouped counts by disease/severity

POST /motor/on                Turn pump on (manual mode only)
POST /motor/off               Turn pump off
GET  /motor/status            Current motor state + mode
GET  /motor/stats             Total spray volume today/week

GET  /mode/                   Get current mode
POST /mode/                   Set mode {"mode": "auto"|"manual"}

GET  /logs/                   Filterable system logs
GET  /logs/export             Download as CSV
DELETE /logs/clear            Clear logs older than N days

GET  /camera/stream-url       Pi MJPEG stream URL
POST /camera/capture          Trigger immediate snapshot

GET  /health                  System health + MQTT status
```

---

## Calibration Guide

### pH Probe
1. Prepare pH 4.0 and pH 7.0 buffer solutions.
2. Immerse probe in pH 7.0 → note voltage reading in logs.
3. Immerse probe in pH 4.0 → note voltage reading.
4. Calculate: `PH_SLOPE = (4.0 - 7.0) / (V_pH4 - V_pH7)`
5. Set `PH_OFFSET` to fine-tune until display reads exactly 7.0 in pH 7.0 buffer.

### Soil Moisture Sensor
1. Hold sensor in open air → note ADS1115 raw value → set `MOISTURE_DRY_RAW`.
2. Submerge sensor in water → note raw value → set `MOISTURE_WET_RAW`.

### NPK Sensor
- Adjust `NPK_SERIAL_PORT` to match your RS485-USB adapter (run `ls /dev/ttyUSB*`).
- Adjust `NPK_BAUD_RATE` to match your sensor's spec (common: 4800 or 9600).

---

## Tech Stack

| Component    | Technologies                                                  |
|--------------|---------------------------------------------------------------|
| Frontend     | React 18, Vite, Recharts, Zustand, MQTT.js, Axios, Syne + Space Mono fonts |
| Backend      | FastAPI, SQLAlchemy, Paho-MQTT, Pydantic v2, SQLite/PostgreSQL|
| Raspberry Pi | Python 3.11, picamera2, google-generativeai, Adafruit libs    |
| ESP32        | Arduino framework, PubSubClient, ArduinoJson, TFT_eSPI        |
| Broker       | Mosquitto MQTT                                                |
| AI           | Gemini 1.5 Flash (Vision API)                                 |

---

## License

MIT — National Institute of Technology Hamirpur · Team OJAS · 2025
