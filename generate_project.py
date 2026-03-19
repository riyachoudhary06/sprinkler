"""
generate_project.py
Run this script once to scaffold the full Intelligent Pesticide Sprinkling System project.

Usage:
    python generate_project.py
    python generate_project.py --root ./my_project   # custom output directory
"""

import os
import argparse

# ──────────────────────────────────────────────
# BOILERPLATE CONTENT FOR EACH FILE
# ──────────────────────────────────────────────

FILES = {

    # ╔══════════════════════════════════════════╗
    # ║           RASPBERRY PI                   ║
    # ╚══════════════════════════════════════════╝

    "raspberry_pi/.env": """\
# Raspberry Pi environment variables
GEMINI_API_KEY=your_gemini_api_key_here
MQTT_BROKER_IP=192.168.1.100
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
SENSOR_POLL_INTERVAL=5       # seconds between sensor reads
INFERENCE_INTERVAL=30        # seconds between disease scans
LOG_LEVEL=INFO
""",

    "raspberry_pi/requirements.txt": """\
paho-mqtt>=1.6.1
google-generativeai>=0.5.0
Adafruit-ADS1x15>=1.0.2
adafruit-circuitpython-dht>=3.7.0
smbus2>=0.4.2
RPi.GPIO>=0.7.1
picamera2>=0.3.12
Pillow>=10.0.0
python-dotenv>=1.0.0
pyserial>=3.5
""",

    "raspberry_pi/main.py": """\
\"\"\"
main.py — Raspberry Pi orchestrator
Starts all threads: sensor polling, camera stream, MQTT, OLED display.
\"\"\"
import time
import threading
import logging
from utils.config import Config
from utils.logger import setup_logger
from sensors.sensor_manager import SensorManager
from camera.camera_stream import CameraStream
from inference.disease_detector import DiseaseDetector
from mqtt.publisher import Publisher
from mqtt.subscriber import Subscriber
from display.oled_display import OledDisplay

setup_logger()
log = logging.getLogger(__name__)

def main():
    log.info("Booting Pesticide Sprinkling System...")
    cfg = Config()

    publisher  = Publisher(cfg)
    subscriber = Subscriber(cfg, publisher)
    sensors    = SensorManager(cfg, publisher)
    camera     = CameraStream(cfg)
    detector   = DiseaseDetector(cfg, publisher)
    display    = OledDisplay(cfg)

    threads = [
        threading.Thread(target=subscriber.start,     daemon=True, name="MQTT-Sub"),
        threading.Thread(target=sensors.start_loop,   daemon=True, name="Sensors"),
        threading.Thread(target=camera.start,         daemon=True, name="Camera"),
        threading.Thread(target=detector.start_loop,  daemon=True, name="Inference"),
        threading.Thread(target=display.start_loop,   daemon=True, name="Display"),
    ]

    for t in threads:
        t.start()
        log.info(f"Started thread: {t.name}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutdown requested.")

if __name__ == "__main__":
    main()
""",

    # ── sensors ──────────────────────────────────

    "raspberry_pi/sensors/ph_sensor.py": """\
\"\"\"
ph_sensor.py — Read soil pH via ADS1115 ADC (analog).
Typical wiring: pH module OUT → ADS1115 A0 → Pi via I2C.
\"\"\"
import Adafruit_ADS1x15
import logging

log = logging.getLogger(__name__)

GAIN = 1          # ±4.096 V range
PH_OFFSET = 0.0   # calibrate per probe
PH_SLOPE  = 3.5   # calibrate per probe

class PhSensor:
    def __init__(self):
        self.adc = Adafruit_ADS1x15.ADS1115()

    def read(self) -> float:
        \"\"\"Return pH value (0–14). Returns -1.0 on error.\"\"\"
        try:
            raw = self.adc.read_adc(0, gain=GAIN)
            voltage = raw * 4.096 / 32767
            ph = 7.0 + (2.5 - voltage) * PH_SLOPE + PH_OFFSET
            ph = round(max(0.0, min(14.0, ph)), 2)
            log.debug(f"pH raw={raw} voltage={voltage:.3f} pH={ph}")
            return ph
        except Exception as e:
            log.error(f"PhSensor read error: {e}")
            return -1.0
""",

    "raspberry_pi/sensors/moisture_sensor.py": """\
\"\"\"
moisture_sensor.py — Capacitive soil moisture via ADS1115 channel 1.
Returns moisture percentage (0–100%).
\"\"\"
import Adafruit_ADS1x15
import logging

log = logging.getLogger(__name__)

GAIN       = 1
DRY_VALUE  = 26000   # raw ADC value in dry soil  (calibrate)
WET_VALUE  = 13000   # raw ADC value in wet soil  (calibrate)

class MoistureSensor:
    def __init__(self):
        self.adc = Adafruit_ADS1x15.ADS1115()

    def read(self) -> float:
        \"\"\"Return soil moisture percentage (0–100). Returns -1 on error.\"\"\"
        try:
            raw = self.adc.read_adc(1, gain=GAIN)
            pct = (DRY_VALUE - raw) / (DRY_VALUE - WET_VALUE) * 100
            pct = round(max(0.0, min(100.0, pct)), 1)
            log.debug(f"Moisture raw={raw} pct={pct}%")
            return pct
        except Exception as e:
            log.error(f"MoistureSensor read error: {e}")
            return -1.0
""",

    "raspberry_pi/sensors/npk_sensor.py": """\
\"\"\"
npk_sensor.py — RS485 Modbus RTU NPK sensor reader.
Typical baud: 4800. Adjust PORT and SLAVE_ADDR per your sensor.
\"\"\"
import serial
import logging

log = logging.getLogger(__name__)

PORT       = "/dev/ttyUSB0"
BAUD       = 4800
SLAVE_ADDR = 0x01

# Modbus read-holding-registers request for N, P, K (3 registers from 0x0000)
NPK_CMD = bytes([SLAVE_ADDR, 0x03, 0x00, 0x00, 0x00, 0x03, 0x05, 0xCB])

class NpkSensor:
    def __init__(self):
        self.ser = serial.Serial(PORT, BAUD, timeout=1)

    def read(self) -> dict:
        \"\"\"Return {'N': int, 'P': int, 'K': int} in mg/kg. Empty dict on error.\"\"\"
        try:
            self.ser.write(NPK_CMD)
            response = self.ser.read(11)
            if len(response) < 9:
                raise ValueError(f"Short response: {response.hex()}")
            n = (response[3] << 8) | response[4]
            p = (response[5] << 8) | response[6]
            k = (response[7] << 8) | response[8]
            result = {"N": n, "P": p, "K": k}
            log.debug(f"NPK: {result}")
            return result
        except Exception as e:
            log.error(f"NpkSensor read error: {e}")
            return {}
""",

    "raspberry_pi/sensors/humidity_sensor.py": """\
\"\"\"
humidity_sensor.py — DHT22 temperature and humidity.
GPIO pin is configured in config.py.
\"\"\"
import adafruit_dht
import board
import logging

log = logging.getLogger(__name__)

class HumiditySensor:
    def __init__(self, pin=board.D4):
        self.device = adafruit_dht.DHT22(pin)

    def read(self) -> dict:
        \"\"\"Return {'temperature': float, 'humidity': float}. Empty dict on error.\"\"\"
        try:
            temp = self.device.temperature
            humi = self.device.humidity
            result = {"temperature": round(temp, 1), "humidity": round(humi, 1)}
            log.debug(f"DHT22: {result}")
            return result
        except Exception as e:
            log.warning(f"HumiditySensor read error (transient ok): {e}")
            return {}
""",

    "raspberry_pi/sensors/light_sensor.py": """\
\"\"\"
light_sensor.py — BH1750 ambient light sensor via I2C.
Returns lux value. Useful for correlating disease risk with light conditions.
\"\"\"
import smbus2
import time
import logging

log = logging.getLogger(__name__)

BH1750_ADDR = 0x23
CONTINUOUS_HIGH_RES = 0x10

class LightSensor:
    def __init__(self, bus_number=1):
        self.bus = smbus2.SMBus(bus_number)
        self.bus.write_byte(BH1750_ADDR, CONTINUOUS_HIGH_RES)
        time.sleep(0.2)

    def read(self) -> float:
        \"\"\"Return ambient light in lux. Returns -1 on error.\"\"\"
        try:
            data = self.bus.read_i2c_block_data(BH1750_ADDR, CONTINUOUS_HIGH_RES, 2)
            lux = round((data[0] << 8 | data[1]) / 1.2, 1)
            log.debug(f"Light: {lux} lux")
            return lux
        except Exception as e:
            log.error(f"LightSensor read error: {e}")
            return -1.0
""",

    "raspberry_pi/sensors/sensor_manager.py": """\
\"\"\"
sensor_manager.py — Polls all sensors on a fixed interval and publishes to MQTT.
\"\"\"
import time
import json
import logging
from sensors.ph_sensor       import PhSensor
from sensors.moisture_sensor import MoistureSensor
from sensors.npk_sensor      import NpkSensor
from sensors.humidity_sensor import HumiditySensor
from sensors.light_sensor    import LightSensor

log = logging.getLogger(__name__)

class SensorManager:
    def __init__(self, cfg, publisher):
        self.cfg       = cfg
        self.publisher = publisher
        self.ph        = PhSensor()
        self.moisture  = MoistureSensor()
        self.npk       = NpkSensor()
        self.humidity  = HumiditySensor()
        self.light     = LightSensor()

    def read_all(self) -> dict:
        npk  = self.npk.read()
        dht  = self.humidity.read()
        data = {
            "ph":          self.ph.read(),
            "moisture":    self.moisture.read(),
            "nitrogen":    npk.get("N", -1),
            "phosphorus":  npk.get("P", -1),
            "potassium":   npk.get("K", -1),
            "temperature": dht.get("temperature", -1),
            "humidity":    dht.get("humidity", -1),
            "light_lux":   self.light.read(),
            "timestamp":   time.time(),
        }
        return data

    def start_loop(self):
        log.info("Sensor loop started.")
        while True:
            try:
                data = self.read_all()
                self.publisher.publish("pi/sensors/all", json.dumps(data))
                log.info(f"Sensors published: {data}")
            except Exception as e:
                log.error(f"Sensor loop error: {e}")
            time.sleep(self.cfg.SENSOR_POLL_INTERVAL)
""",

    # ── camera ───────────────────────────────────

    "raspberry_pi/camera/camera_stream.py": """\
\"\"\"
camera_stream.py — MJPEG HTTP stream via picamera2.
Stream accessible at http://<pi-ip>:8080/stream.
\"\"\"
import io
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

log = logging.getLogger(__name__)
STREAM_PORT = 8080

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class StreamHandler(BaseHTTPRequestHandler):
    output = None

    def do_GET(self):
        if self.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
            self.end_headers()
            try:
                while True:
                    with StreamHandler.output.condition:
                        StreamHandler.output.condition.wait()
                        frame = StreamHandler.output.frame
                    self.wfile.write(b"--FRAME\r\nContent-Type: image/jpeg\r\n\r\n")
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
            except Exception:
                pass
        else:
            self.send_error(404)

    def log_message(self, *args):
        pass  # suppress access logs

class CameraStream:
    def __init__(self, cfg):
        self.cfg    = cfg
        self.output = StreamingOutput()
        StreamHandler.output = self.output

    def start(self):
        log.info(f"Camera stream starting on port {STREAM_PORT}...")
        cam = Picamera2()
        config = cam.create_video_configuration(main={"size": (640, 480)})
        cam.configure(config)
        cam.start_recording(JpegEncoder(), FileOutput(self.output))
        server = HTTPServer(("", STREAM_PORT), StreamHandler)
        log.info(f"Stream live at http://0.0.0.0:{STREAM_PORT}/stream")
        server.serve_forever()
""",

    "raspberry_pi/camera/capture.py": """\
\"\"\"
capture.py — Take a still snapshot from picamera2 and save to disk.
\"\"\"
import time
import os
import logging
from picamera2 import Picamera2

log = logging.getLogger(__name__)
SAVE_DIR = "/home/pi/captures"

def capture_image() -> str:
    \"\"\"Capture a JPEG, save it, return the file path.\"\"\"
    os.makedirs(SAVE_DIR, exist_ok=True)
    filename = os.path.join(SAVE_DIR, f"capture_{int(time.time())}.jpg")
    cam = Picamera2()
    cam.start()
    time.sleep(0.5)           # let exposure settle
    cam.capture_file(filename)
    cam.stop()
    log.info(f"Image captured: {filename}")
    return filename
""",

    "raspberry_pi/camera/preprocess.py": """\
\"\"\"
preprocess.py — Resize and base64-encode a captured image for Gemini API.
\"\"\"
import base64
import logging
from PIL import Image

log = logging.getLogger(__name__)
TARGET_SIZE  = (768, 768)   # Gemini Vision recommended max
JPEG_QUALITY = 85

def preprocess_image(image_path: str) -> str:
    \"\"\"Return base64-encoded JPEG string ready for Gemini API.\"\"\"
    try:
        img = Image.open(image_path).convert("RGB")
        img.thumbnail(TARGET_SIZE, Image.LANCZOS)
        from io import BytesIO
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY)
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        log.debug(f"Preprocessed {image_path} → {len(encoded)} chars b64")
        return encoded
    except Exception as e:
        log.error(f"Preprocess error: {e}")
        return ""
""",

    # ── inference ────────────────────────────────

    "raspberry_pi/inference/gemini_client.py": """\
\"\"\"
gemini_client.py — Send a base64 image to Gemini Vision API.
Returns a structured dict with disease info.
\"\"\"
import json
import logging
import google.generativeai as genai
from inference.prompt_builder import build_prompt

log = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        log.info("Gemini client initialised (gemini-1.5-flash)")

    def analyze(self, b64_image: str, sensor_context: dict) -> dict:
        \"\"\"
        Send image + sensor data to Gemini.
        Returns dict:
            {
                "disease":         str,   # e.g. "Leaf Blight"
                "confidence":      float, # 0.0–1.0
                "severity":        str,   # "low" | "medium" | "high"
                "affected_area":   float, # percentage of leaf area affected
                "recommendation":  str,   # human-readable advice
                "pesticide":       str,   # recommended pesticide name
                "dosage_ml":       float, # suggested spray volume per m²
                "error":           str    # non-empty if API call failed
            }
        \"\"\"
        try:
            prompt = build_prompt(sensor_context)
            image_part = {
                "mime_type": "image/jpeg",
                "data": b64_image
            }
            response = self.model.generate_content([prompt, image_part])
            raw = response.text.strip()

            # strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            result = json.loads(raw)
            result.setdefault("error", "")
            log.info(f"Gemini result: {result}")
            return result

        except json.JSONDecodeError as e:
            log.error(f"Gemini JSON parse error: {e} | raw: {response.text[:200]}")
            return {"error": "json_parse_failed", "disease": "unknown"}
        except Exception as e:
            log.error(f"Gemini API error: {e}")
            return {"error": str(e), "disease": "unknown"}
""",

    "raspberry_pi/inference/prompt_builder.py": """\
\"\"\"
prompt_builder.py — Construct structured Gemini Vision prompts.
Injects sensor context so Gemini can cross-reference environmental data.
\"\"\"

def build_prompt(sensor_context: dict) -> str:
    ph        = sensor_context.get("ph",          "N/A")
    moisture  = sensor_context.get("moisture",    "N/A")
    humidity  = sensor_context.get("humidity",    "N/A")
    temp      = sensor_context.get("temperature", "N/A")
    nitrogen  = sensor_context.get("nitrogen",    "N/A")
    phosphorus= sensor_context.get("phosphorus",  "N/A")
    potassium = sensor_context.get("potassium",   "N/A")
    light_lux = sensor_context.get("light_lux",   "N/A")

    prompt = f\"\"\"You are a precision agriculture plant pathologist AI.

Analyze the provided plant image and the following environmental sensor readings:
- Soil pH:          {ph}
- Soil Moisture:    {moisture}%
- Air Humidity:     {humidity}%
- Air Temperature:  {temp}°C
- Nitrogen (N):     {nitrogen} mg/kg
- Phosphorus (P):   {phosphorus} mg/kg
- Potassium (K):    {potassium} mg/kg
- Ambient Light:    {light_lux} lux

Return ONLY a valid JSON object with these exact keys (no markdown, no extra text):
{{
  "disease":        "<name of disease or 'healthy'>",
  "confidence":     <float 0.0 to 1.0>,
  "severity":       "<low|medium|high|none>",
  "affected_area":  <float percentage 0–100>,
  "recommendation": "<one sentence action advice>",
  "pesticide":      "<recommended pesticide or 'none'>",
  "dosage_ml":      <recommended spray ml per square meter, 0 if healthy>
}}
\"\"\"
    return prompt
""",

    "raspberry_pi/inference/disease_detector.py": """\
\"\"\"
disease_detector.py — Orchestrates capture → preprocess → Gemini → publish.
Runs on its own thread at INFERENCE_INTERVAL seconds.
\"\"\"
import time
import json
import logging
from camera.capture          import capture_image
from camera.preprocess       import preprocess_image
from inference.gemini_client import GeminiClient
from inference.dosage_calculator import calculate_dosage

log = logging.getLogger(__name__)

class DiseaseDetector:
    def __init__(self, cfg, publisher):
        self.cfg        = cfg
        self.publisher  = publisher
        self.gemini     = GeminiClient(api_key=cfg.GEMINI_API_KEY)
        self.last_sensors = {}   # updated externally by SensorManager if needed

    def run_once(self) -> dict:
        img_path  = capture_image()
        b64_image = preprocess_image(img_path)
        if not b64_image:
            log.warning("Empty image, skipping inference.")
            return {}

        result = self.gemini.analyze(b64_image, self.last_sensors)
        if result.get("error"):
            log.warning(f"Gemini returned error: {result['error']}")
            return result

        result["dosage_ml"] = calculate_dosage(result)
        result["image_path"] = img_path
        result["timestamp"]  = time.time()

        self.publisher.publish("pi/inference/result", json.dumps(result))
        log.info(f"Inference published: disease={result.get('disease')} "
                 f"severity={result.get('severity')} dosage={result.get('dosage_ml')} ml")
        return result

    def start_loop(self):
        log.info("Disease detection loop started.")
        while True:
            try:
                self.run_once()
            except Exception as e:
                log.error(f"Detector loop error: {e}")
            time.sleep(self.cfg.INFERENCE_INTERVAL)
""",

    "raspberry_pi/inference/dosage_calculator.py": """\
\"\"\"
dosage_calculator.py — Map Gemini severity + affected_area → spray volume (ml/m²).
Adjust thresholds based on your specific pesticide and crop.
\"\"\"
import logging

log = logging.getLogger(__name__)

# Base dose in ml per m² per severity level
BASE_DOSE = {
    "none":   0,
    "low":    10,
    "medium": 25,
    "high":   50,
}

def calculate_dosage(gemini_result: dict) -> float:
    \"\"\"Return recommended spray volume in ml per m².\"\"\"
    if gemini_result.get("disease", "healthy").lower() == "healthy":
        return 0.0

    severity     = gemini_result.get("severity", "low").lower()
    affected_pct = gemini_result.get("affected_area", 10.0)
    base         = BASE_DOSE.get(severity, 10)

    # Scale proportionally with affected area (10% area = base, 100% = 2× base)
    scale  = 1.0 + (affected_pct / 100.0)
    dosage = round(base * scale, 1)

    log.debug(f"Dosage calc: severity={severity} area={affected_pct}% → {dosage} ml/m²")
    return dosage
""",

    # ── mqtt ─────────────────────────────────────

    "raspberry_pi/mqtt/publisher.py": """\
\"\"\"
publisher.py — MQTT client for publishing Pi data to the broker.
\"\"\"
import paho.mqtt.client as mqtt
import logging

log = logging.getLogger(__name__)

class Publisher:
    def __init__(self, cfg):
        self.cfg    = cfg
        self.client = mqtt.Client(client_id="pi-publisher")
        if cfg.MQTT_USERNAME:
            self.client.username_pw_set(cfg.MQTT_USERNAME, cfg.MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.connect(cfg.MQTT_BROKER_IP, cfg.MQTT_PORT, keepalive=60)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            log.info("Publisher connected to MQTT broker.")
        else:
            log.error(f"Publisher MQTT connect failed rc={rc}")

    def publish(self, topic: str, payload: str, qos: int = 1):
        result = self.client.publish(topic, payload, qos=qos)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            log.warning(f"Publish failed on topic {topic}: rc={result.rc}")
""",

    "raspberry_pi/mqtt/subscriber.py": """\
\"\"\"
subscriber.py — Subscribe to server commands (mode, manual spray trigger).
\"\"\"
import json
import paho.mqtt.client as mqtt
import logging

log = logging.getLogger(__name__)

SUBSCRIPTIONS = [
    "server/mode",
    "server/motor/cmd",
]

class Subscriber:
    def __init__(self, cfg, publisher):
        self.cfg       = cfg
        self.publisher = publisher
        self.mode      = "auto"   # "auto" | "manual"
        self.client    = mqtt.Client(client_id="pi-subscriber")
        if cfg.MQTT_USERNAME:
            self.client.username_pw_set(cfg.MQTT_USERNAME, cfg.MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            for topic in SUBSCRIPTIONS:
                self.client.subscribe(topic, qos=1)
                log.info(f"Subscribed to {topic}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            log.info(f"Received [{msg.topic}]: {payload}")
            if msg.topic == "server/mode":
                self.mode = payload.get("mode", "auto")
                log.info(f"Mode changed to: {self.mode}")
        except Exception as e:
            log.error(f"Subscriber message error: {e}")

    def start(self):
        self.client.connect(self.cfg.MQTT_BROKER_IP, self.cfg.MQTT_PORT, keepalive=60)
        log.info("Subscriber loop started.")
        self.client.loop_forever()
""",

    # ── display ──────────────────────────────────

    "raspberry_pi/display/oled_display.py": """\
\"\"\"
oled_display.py — SSD1306 128×64 OLED via I2C.
Shows: IP address, current mode, last sensor readings, last disease result.
\"\"\"
import time
import socket
import logging

log = logging.getLogger(__name__)

try:
    import board
    import busio
    import adafruit_ssd1306
    from PIL import Image, ImageDraw, ImageFont
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False
    log.warning("OLED libraries not found; display disabled.")

WIDTH, HEIGHT = 128, 64

class OledDisplay:
    def __init__(self, cfg):
        self.cfg    = cfg
        self.display = None
        if OLED_AVAILABLE:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.display = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)
                self.display.fill(0)
                self.display.show()
            except Exception as e:
                log.error(f"OLED init error: {e}")

    def _get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "no network"

    def show(self, lines: list):
        if not self.display:
            return
        img  = Image.new("1", (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(img)
        for i, line in enumerate(lines[:5]):
            draw.text((0, i * 12), str(line), font=None, fill=255)
        self.display.image(img)
        self.display.show()

    def start_loop(self):
        log.info("OLED display loop started.")
        while True:
            try:
                ip = self._get_ip()
                self.show([
                    f"IP: {ip}",
                    f"Mode: {self.cfg.MODE}",
                    "Status: OK",
                ])
            except Exception as e:
                log.error(f"Display loop error: {e}")
            time.sleep(10)
""",

    # ── utils ────────────────────────────────────

    "raspberry_pi/utils/config.py": """\
\"\"\"
config.py — Load all configuration from .env file.
\"\"\"
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY       = os.getenv("GEMINI_API_KEY", "")
    MQTT_BROKER_IP       = os.getenv("MQTT_BROKER_IP", "localhost")
    MQTT_PORT            = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME        = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD        = os.getenv("MQTT_PASSWORD", "")
    SENSOR_POLL_INTERVAL = int(os.getenv("SENSOR_POLL_INTERVAL", 5))
    INFERENCE_INTERVAL   = int(os.getenv("INFERENCE_INTERVAL", 30))
    LOG_LEVEL            = os.getenv("LOG_LEVEL", "INFO")
    MODE                 = "auto"   # runtime mutable
""",

    "raspberry_pi/utils/logger.py": """\
\"\"\"
logger.py — Configure rotating file + console logging.
\"\"\"
import logging
import logging.handlers
import os

LOG_DIR  = "/home/pi/logs"
LOG_FILE = os.path.join(LOG_DIR, "pesticide_system.log")

def setup_logger(level: str = "INFO"):
    os.makedirs(LOG_DIR, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.addHandler(file_handler)
    root.addHandler(console_handler)
""",

    # ╔══════════════════════════════════════════╗
    # ║              WEBSITE BACKEND             ║
    # ╚══════════════════════════════════════════╝

    "website/backend/main.py": """\
\"\"\"
main.py — FastAPI application entrypoint.
\"\"\"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes_sensors  import router as sensors_router
from api.routes_camera   import router as camera_router
from api.routes_disease  import router as disease_router
from api.routes_motor    import router as motor_router
from api.routes_logs     import router as logs_router
from api.routes_mode     import router as mode_router
from services.mqtt_bridge import start_mqtt_bridge
from db.database import init_db
import threading

app = FastAPI(title="Pesticide Sprinkling System API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sensors_router,  prefix="/sensors")
app.include_router(camera_router,   prefix="/camera")
app.include_router(disease_router,  prefix="/disease")
app.include_router(motor_router,    prefix="/motor")
app.include_router(logs_router,     prefix="/logs")
app.include_router(mode_router,     prefix="/mode")

@app.on_event("startup")
async def startup():
    init_db()
    threading.Thread(target=start_mqtt_bridge, daemon=True).start()

@app.get("/health")
def health():
    return {"status": "ok"}
""",

    "website/backend/config.py": """\
\"\"\"
config.py — Backend configuration from environment.
\"\"\"
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MQTT_BROKER_IP  = os.getenv("MQTT_BROKER_IP", "localhost")
    MQTT_PORT       = int(os.getenv("MQTT_PORT", 1883))
    DATABASE_URL    = os.getenv("DATABASE_URL", "sqlite:///./pesticide.db")
    SECRET_KEY      = os.getenv("SECRET_KEY", "changeme")

settings = Settings()
""",

    "website/backend/db/database.py": """\
\"\"\"
database.py — SQLAlchemy session setup.
\"\"\"
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

engine       = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base         = declarative_base()

def init_db():
    from db import models  # noqa: ensure models are registered
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",

    "website/backend/db/models.py": """\
\"\"\"
models.py — SQLAlchemy ORM models.
\"\"\"
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from db.database import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id          = Column(Integer, primary_key=True, index=True)
    ph          = Column(Float)
    moisture    = Column(Float)
    nitrogen    = Column(Float)
    phosphorus  = Column(Float)
    potassium   = Column(Float)
    temperature = Column(Float)
    humidity    = Column(Float)
    light_lux   = Column(Float)
    recorded_at = Column(DateTime, server_default=func.now())

class DiseaseResult(Base):
    __tablename__ = "disease_results"
    id            = Column(Integer, primary_key=True, index=True)
    disease       = Column(String(128))
    confidence    = Column(Float)
    severity      = Column(String(32))
    affected_area = Column(Float)
    recommendation= Column(Text)
    pesticide     = Column(String(128))
    dosage_ml     = Column(Float)
    image_path    = Column(String(256))
    recorded_at   = Column(DateTime, server_default=func.now())

class Log(Base):
    __tablename__ = "logs"
    id         = Column(Integer, primary_key=True, index=True)
    level      = Column(String(16))
    message    = Column(Text)
    source     = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())

class SystemMode(Base):
    __tablename__ = "system_mode"
    id      = Column(Integer, primary_key=True)
    mode    = Column(String(16), default="auto")
    updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
""",

    "website/backend/services/mqtt_bridge.py": """\
\"\"\"
mqtt_bridge.py — Subscribe to Pi topics and write data to the database.
\"\"\"
import json
import logging
import paho.mqtt.client as mqtt
from db.database import SessionLocal
from db.models   import SensorReading, DiseaseResult, Log
from config      import settings

log = logging.getLogger(__name__)

TOPICS = [
    ("pi/sensors/all",       1),
    ("pi/inference/result",  1),
    ("pi/logs",              1),
    ("esp32/status",         0),
    ("esp32/flow",           0),
]

def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        db      = SessionLocal()
        if msg.topic == "pi/sensors/all":
            db.add(SensorReading(**{k: payload.get(k) for k in
                ["ph","moisture","nitrogen","phosphorus","potassium",
                 "temperature","humidity","light_lux"]}))
        elif msg.topic == "pi/inference/result":
            db.add(DiseaseResult(**{k: payload.get(k) for k in
                ["disease","confidence","severity","affected_area",
                 "recommendation","pesticide","dosage_ml","image_path"]}))
        elif msg.topic == "pi/logs":
            db.add(Log(level=payload.get("level","INFO"),
                       message=payload.get("message",""),
                       source="pi"))
        db.commit()
        db.close()
    except Exception as e:
        log.error(f"MQTT bridge error [{msg.topic}]: {e}")

def start_mqtt_bridge():
    client = mqtt.Client(client_id="backend-bridge")
    client.on_message = _on_message
    client.connect(settings.MQTT_BROKER_IP, settings.MQTT_PORT)
    for topic, qos in TOPICS:
        client.subscribe(topic, qos)
        log.info(f"Bridge subscribed: {topic}")
    log.info("MQTT bridge running.")
    client.loop_forever()
""",

    "website/backend/services/alert_service.py": """\
\"\"\"
alert_service.py — Check sensor readings against thresholds and emit alerts.
\"\"\"
import logging

log = logging.getLogger(__name__)

THRESHOLDS = {
    "ph":       (5.5, 7.5),
    "moisture": (20,  80),
    "humidity": (30,  90),
}

def check_alerts(sensor_data: dict) -> list:
    alerts = []
    for key, (low, high) in THRESHOLDS.items():
        val = sensor_data.get(key)
        if val is None:
            continue
        if val < low:
            alerts.append({"sensor": key, "value": val, "type": "below_threshold", "threshold": low})
        elif val > high:
            alerts.append({"sensor": key, "value": val, "type": "above_threshold", "threshold": high})
    if alerts:
        log.warning(f"Alerts triggered: {alerts}")
    return alerts
""",

    "website/backend/api/routes_sensors.py": """\
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db.models   import SensorReading

router = APIRouter(tags=["Sensors"])

@router.get("/latest")
def get_latest(db: Session = Depends(get_db)):
    row = db.query(SensorReading).order_by(SensorReading.id.desc()).first()
    return row

@router.get("/history")
def get_history(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(SensorReading).order_by(SensorReading.id.desc()).limit(limit).all()
""",

    "website/backend/api/routes_disease.py": """\
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db.models   import DiseaseResult

router = APIRouter(tags=["Disease"])

@router.get("/predictions")
def get_predictions(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(DiseaseResult).order_by(DiseaseResult.id.desc()).limit(limit).all()

@router.get("/latest")
def get_latest_prediction(db: Session = Depends(get_db)):
    return db.query(DiseaseResult).order_by(DiseaseResult.id.desc()).first()
""",

    "website/backend/api/routes_motor.py": """\
import json
import paho.mqtt.publish as publish
from fastapi import APIRouter
from config  import settings

router = APIRouter(tags=["Motor"])

@router.post("/on")
def motor_on(dosage_ml: float = 0):
    publish.single("server/motor/cmd",
                   json.dumps({"cmd": "on", "dosage_ml": dosage_ml}),
                   hostname=settings.MQTT_BROKER_IP)
    return {"status": "motor_on", "dosage_ml": dosage_ml}

@router.post("/off")
def motor_off():
    publish.single("server/motor/cmd",
                   json.dumps({"cmd": "off"}),
                   hostname=settings.MQTT_BROKER_IP)
    return {"status": "motor_off"}
""",

    "website/backend/api/routes_camera.py": """\
from fastapi import APIRouter

router = APIRouter(tags=["Camera"])

@router.get("/stream-url")
def stream_url():
    # Returns URL pointing to Pi's MJPEG stream
    return {"url": "http://raspberrypi.local:8080/stream"}
""",

    "website/backend/api/routes_logs.py": """\
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db.models   import Log

router = APIRouter(tags=["Logs"])

@router.get("/")
def get_logs(limit: int = 200, db: Session = Depends(get_db)):
    return db.query(Log).order_by(Log.id.desc()).limit(limit).all()
""",

    "website/backend/api/routes_mode.py": """\
import json
import paho.mqtt.publish as publish
from fastapi import APIRouter
from config  import settings

router = APIRouter(tags=["Mode"])

_current_mode = {"mode": "auto"}

@router.get("/")
def get_mode():
    return _current_mode

@router.post("/{mode}")
def set_mode(mode: str):
    if mode not in ("auto", "manual"):
        return {"error": "mode must be 'auto' or 'manual'"}
    _current_mode["mode"] = mode
    publish.single("server/mode", json.dumps({"mode": mode}),
                   hostname=settings.MQTT_BROKER_IP)
    return {"mode": mode}
""",

    "website/backend/requirements.txt": """\
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.0
paho-mqtt>=1.6.1
python-dotenv>=1.0.0
Pillow>=10.0.0
""",

    "website/.env": """\
MQTT_BROKER_IP=192.168.1.100
MQTT_PORT=1883
DATABASE_URL=sqlite:///./pesticide.db
SECRET_KEY=change_this_in_production
""",

    # ╔══════════════════════════════════════════╗
    # ║           WEBSITE FRONTEND               ║
    # ╚══════════════════════════════════════════╝

    "website/frontend/package.json": """\
{
  "name": "pesticide-dashboard",
  "version": "0.1.0",
  "scripts": {
    "dev":   "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react":         "^18.2.0",
    "react-dom":     "^18.2.0",
    "react-router-dom": "^6.22.0",
    "mqtt":          "^5.5.0",
    "axios":         "^1.6.0",
    "recharts":      "^2.12.0",
    "zustand":       "^4.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.2.0"
  }
}
""",

    "website/frontend/src/main.jsx": """\
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
""",

    "website/frontend/src/App.jsx": """\
import React from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import HomePage      from './pages/HomePage'
import SensorsPage   from './pages/SensorsPage'
import CameraPage    from './pages/CameraPage'
import DiseasePage   from './pages/DiseasePage'
import MotorPage     from './pages/MotorPage'
import LogsPage      from './pages/LogsPage'
import SettingsPage  from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <nav style={{ display:'flex', gap:16, padding:'12px 24px',
                    background:'#1a1a2e', color:'#fff' }}>
        {['/', '/sensors', '/camera', '/disease',
          '/motor', '/logs', '/settings'].map((path, i) => (
          <NavLink key={path} to={path}
            style={({ isActive }) => ({ color: isActive ? '#4FC3F7' : '#ccc',
                                        textDecoration:'none', fontSize:14 })}>
            {['Dashboard','Sensors','Camera','Disease',
              'Motor','Logs','Settings'][i]}
          </NavLink>
        ))}
      </nav>
      <Routes>
        <Route path="/"          element={<HomePage />} />
        <Route path="/sensors"   element={<SensorsPage />} />
        <Route path="/camera"    element={<CameraPage />} />
        <Route path="/disease"   element={<DiseasePage />} />
        <Route path="/motor"     element={<MotorPage />} />
        <Route path="/logs"      element={<LogsPage />} />
        <Route path="/settings"  element={<SettingsPage />} />
      </Routes>
    </BrowserRouter>
  )
}
""",

    # pages (stubs)
    "website/frontend/src/pages/HomePage.jsx":     "import React from 'react'\nimport Dashboard from '../components/Dashboard'\nexport default function HomePage() { return <Dashboard /> }\n",
    "website/frontend/src/pages/SensorsPage.jsx":  "import React from 'react'\nexport default function SensorsPage() { return <div><h2>Sensors</h2></div> }\n",
    "website/frontend/src/pages/CameraPage.jsx":   "import React from 'react'\nimport CameraFeed from '../components/CameraFeed'\nexport default function CameraPage() { return <CameraFeed /> }\n",
    "website/frontend/src/pages/DiseasePage.jsx":  "import React from 'react'\nimport DiseasePanel from '../components/DiseasePanel'\nexport default function DiseasePage() { return <DiseasePanel /> }\n",
    "website/frontend/src/pages/MotorPage.jsx":    "import React from 'react'\nimport MotorControl from '../components/MotorControl'\nexport default function MotorPage() { return <MotorControl /> }\n",
    "website/frontend/src/pages/LogsPage.jsx":     "import React from 'react'\nimport LogViewer from '../components/LogViewer'\nexport default function LogsPage() { return <LogViewer /> }\n",
    "website/frontend/src/pages/SettingsPage.jsx": "import React from 'react'\nexport default function SettingsPage() { return <div><h2>Settings</h2><p>Configure MQTT, thresholds, Gemini key.</p></div> }\n",

    # components (stubs)
    "website/frontend/src/components/Dashboard.jsx": """\
import React, { useEffect, useState } from 'react'
import axios from 'axios'
import SensorCard   from './SensorCard'
import DiseasePanel from './DiseasePanel'
import ModeToggle   from './ModeToggle'

const API = 'http://localhost:8000'

export default function Dashboard() {
  const [sensors, setSensors] = useState(null)
  const [disease, setDisease] = useState(null)

  useEffect(() => {
    const fetch = () => {
      axios.get(`${API}/sensors/latest`).then(r => setSensors(r.data))
      axios.get(`${API}/disease/latest`).then(r => setDisease(r.data))
    }
    fetch()
    const id = setInterval(fetch, 5000)
    return () => clearInterval(id)
  }, [])

  return (
    <div style={{ padding: 24 }}>
      <h1>Pesticide System Dashboard</h1>
      <ModeToggle />
      <SensorCard data={sensors} />
      <DiseasePanel data={disease} />
    </div>
  )
}
""",

    "website/frontend/src/components/SensorCard.jsx": """\
import React from 'react'
export default function SensorCard({ data }) {
  if (!data) return <p>Loading sensors...</p>
  const fields = ['ph','moisture','nitrogen','phosphorus','potassium','temperature','humidity','light_lux']
  return (
    <div style={{ display:'flex', gap:12, flexWrap:'wrap', margin:'16px 0' }}>
      {fields.map(f => (
        <div key={f} style={{ background:'#f0f4ff', borderRadius:8, padding:'12px 16px', minWidth:120 }}>
          <div style={{ fontSize:11, color:'#666', textTransform:'uppercase' }}>{f.replace('_',' ')}</div>
          <div style={{ fontSize:22, fontWeight:600 }}>{data[f] ?? '—'}</div>
        </div>
      ))}
    </div>
  )
}
""",

    "website/frontend/src/components/DiseasePanel.jsx": """\
import React from 'react'
export default function DiseasePanel({ data }) {
  if (!data) return <p>No prediction yet.</p>
  const color = { low:'#4CAF50', medium:'#FF9800', high:'#F44336', none:'#9E9E9E' }
  return (
    <div style={{ background:'#fff8e1', borderRadius:8, padding:16, margin:'16px 0' }}>
      <h3>Latest Disease Detection</h3>
      <p><b>Disease:</b> {data.disease}</p>
      <p><b>Confidence:</b> {(data.confidence * 100).toFixed(1)}%</p>
      <p><b>Severity:</b> <span style={{ color: color[data.severity] }}>{data.severity}</span></p>
      <p><b>Affected area:</b> {data.affected_area}%</p>
      <p><b>Pesticide:</b> {data.pesticide}</p>
      <p><b>Dosage:</b> {data.dosage_ml} ml/m²</p>
      <p><i>{data.recommendation}</i></p>
    </div>
  )
}
""",

    "website/frontend/src/components/CameraFeed.jsx": """\
import React from 'react'
const STREAM = 'http://raspberrypi.local:8080/stream'
export default function CameraFeed() {
  return (
    <div style={{ padding:24 }}>
      <h2>Live Camera Feed</h2>
      <img src={STREAM} alt="Live feed"
           style={{ width:'100%', maxWidth:640, borderRadius:8, border:'1px solid #ddd' }} />
    </div>
  )
}
""",

    "website/frontend/src/components/MotorControl.jsx": """\
import React, { useState } from 'react'
import axios from 'axios'
const API = 'http://localhost:8000'
export default function MotorControl() {
  const [dosage, setDosage] = useState(20)
  const on  = () => axios.post(`${API}/motor/on?dosage_ml=${dosage}`)
  const off = () => axios.post(`${API}/motor/off`)
  return (
    <div style={{ padding:24 }}>
      <h2>Motor Control</h2>
      <label>Dosage (ml/m²): <input type="number" value={dosage}
        onChange={e => setDosage(e.target.value)} style={{ width:80 }} /></label>
      <br /><br />
      <button onClick={on}  style={{ background:'#4CAF50', color:'#fff', padding:'8px 20px', marginRight:12 }}>Spray ON</button>
      <button onClick={off} style={{ background:'#F44336', color:'#fff', padding:'8px 20px' }}>Spray OFF</button>
    </div>
  )
}
""",

    "website/frontend/src/components/ModeToggle.jsx": """\
import React, { useState } from 'react'
import axios from 'axios'
const API = 'http://localhost:8000'
export default function ModeToggle() {
  const [mode, setMode] = useState('auto')
  const toggle = () => {
    const next = mode === 'auto' ? 'manual' : 'auto'
    axios.post(`${API}/mode/${next}`).then(() => setMode(next))
  }
  return (
    <div style={{ margin:'8px 0' }}>
      <span>Mode: <b>{mode.toUpperCase()}</b></span>
      <button onClick={toggle} style={{ marginLeft:12, padding:'4px 16px' }}>Switch</button>
    </div>
  )
}
""",

    "website/frontend/src/components/LogViewer.jsx": """\
import React, { useEffect, useState } from 'react'
import axios from 'axios'
const API = 'http://localhost:8000'
export default function LogViewer() {
  const [logs, setLogs] = useState([])
  useEffect(() => {
    axios.get(`${API}/logs/?limit=100`).then(r => setLogs(r.data))
  }, [])
  return (
    <div style={{ padding:24 }}>
      <h2>System Logs</h2>
      <div style={{ fontFamily:'monospace', fontSize:12, maxHeight:400,
                    overflowY:'auto', background:'#111', color:'#0f0', padding:12 }}>
        {logs.map((l, i) => <div key={i}>[{l.level}] {l.message}</div>)}
      </div>
    </div>
  )
}
""",

    "website/frontend/src/components/AlertBanner.jsx": """\
import React from 'react'
export default function AlertBanner({ alerts = [] }) {
  if (!alerts.length) return null
  return (
    <div style={{ background:'#fff3cd', border:'1px solid #ffc107',
                  borderRadius:6, padding:'10px 16px', margin:'8px 0' }}>
      {alerts.map((a, i) => (
        <div key={i}>⚠️ {a.sensor} is {a.type.replace('_',' ')} ({a.value})</div>
      ))}
    </div>
  )
}
""",

    "website/frontend/src/components/SensorChart.jsx": """\
import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
export default function SensorChart({ data = [], field = 'ph' }) {
  return (
    <LineChart width={600} height={250} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="recorded_at" hide />
      <YAxis />
      <Tooltip />
      <Legend />
      <Line type="monotone" dataKey={field} stroke="#8884d8" dot={false} />
    </LineChart>
  )
}
""",

    "website/frontend/src/components/ScheduleManager.jsx": """\
import React, { useState } from 'react'
export default function ScheduleManager() {
  const [time, setTime]   = useState('06:00')
  const [dose, setDose]   = useState(20)
  const save = () => alert(`Schedule saved: ${time} @ ${dose} ml/m²`)
  return (
    <div style={{ padding:24 }}>
      <h2>Spray Schedule</h2>
      <label>Time: <input type="time" value={time} onChange={e => setTime(e.target.value)} /></label>
      <br /><br />
      <label>Dosage (ml/m²): <input type="number" value={dose} onChange={e => setDose(e.target.value)} /></label>
      <br /><br />
      <button onClick={save}>Save Schedule</button>
    </div>
  )
}
""",

    "website/frontend/src/services/api.js": """\
import axios from 'axios'
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const api  = axios.create({ baseURL: BASE })
export default api
""",

    "website/frontend/src/store/index.js": """\
import { create } from 'zustand'
export const useStore = create((set) => ({
  mode:    'auto',
  sensors: null,
  disease: null,
  alerts:  [],
  setMode:    (mode)    => set({ mode }),
  setSensors: (sensors) => set({ sensors }),
  setDisease: (disease) => set({ disease }),
  setAlerts:  (alerts)  => set({ alerts }),
}))
""",

    "website/frontend/src/hooks/useMQTT.js": """\
import { useEffect } from 'react'
import mqtt from 'mqtt'
export function useMQTT(broker, topics, onMessage) {
  useEffect(() => {
    const client = mqtt.connect(broker)
    client.on('connect', () => topics.forEach(t => client.subscribe(t)))
    client.on('message', (topic, payload) => onMessage(topic, payload.toString()))
    return () => client.end()
  }, [broker])
}
""",

    "website/frontend/src/hooks/useSensors.js": """\
import { useEffect } from 'react'
import api from '../services/api'
import { useStore } from '../store'
export function useSensors(interval = 5000) {
  const setSensors = useStore(s => s.setSensors)
  useEffect(() => {
    const fetch = () => api.get('/sensors/latest').then(r => setSensors(r.data))
    fetch()
    const id = setInterval(fetch, interval)
    return () => clearInterval(id)
  }, [])
}
""",

    "website/frontend/src/hooks/useCamera.js": """\
export function useCamera() {
  const streamUrl = import.meta.env.VITE_STREAM_URL || 'http://raspberrypi.local:8080/stream'
  return { streamUrl }
}
""",

    "website/frontend/vite.config.js": """\
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://localhost:8000' } }
})
""",

    "website/README.md": """\
# Intelligent Pesticide Sprinkling System — Website

## Stack
- **Frontend**: React 18 + Vite + Recharts + Zustand + MQTT.js
- **Backend**: FastAPI + SQLAlchemy + Paho-MQTT

## Quick Start

### Backend
```bash
cd website/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd website/frontend
npm install
npm run dev
```
""",

    # ╔══════════════════════════════════════════╗
    # ║                 ESP32                    ║
    # ╚══════════════════════════════════════════╝

    "esp32/include/config.h": """\
#pragma once
#define WIFI_SSID       "YOUR_WIFI_SSID"
#define WIFI_PASS       "YOUR_WIFI_PASSWORD"
#define MQTT_BROKER     "192.168.1.100"
#define MQTT_PORT       1883

// Pin definitions
#define PIN_PUMP_RELAY  26
#define PIN_LED_IDLE    18
#define PIN_LED_SPRAY   19
#define PIN_LED_ERROR   21
#define PIN_FLOW_METER  34    // YF-S201 pulse input
#define PIN_TFT_CS      5
#define PIN_TFT_RST     22
#define PIN_TFT_DC      4
""",

    "esp32/include/topics.h": """\
#pragma once
#define TOPIC_MOTOR_CMD   "server/motor/cmd"
#define TOPIC_MODE        "server/mode"
#define TOPIC_STATUS      "esp32/status"
#define TOPIC_FLOW        "esp32/flow"
#define TOPIC_DISPLAY     "esp32/display"
""",

    "esp32/src/main.ino": """\
#include "config.h"
#include "topics.h"

void setup() {
  Serial.begin(115200);
  setupWifiMqtt();
  setupMotor();
  setupLeds();
  setupDisplay();
  setupFlowMeter();
  Serial.println("ESP32 ready.");
}

void loop() {
  mqttLoop();          // keep connection alive, handle callbacks
  updateFlowMeter();   // accumulate pulse count
  delay(10);
}
""",

    "esp32/src/wifi_mqtt.ino": """\
#include <WiFi.h>
#include <PubSubClient.h>
#include "config.h"
#include "topics.h"

WiFiClient   wifiClient;
PubSubClient mqttClient(wifiClient);

void mqttCallback(char* topic, byte* payload, unsigned int len) {
  String msg = "";
  for (unsigned int i = 0; i < len; i++) msg += (char)payload[i];
  handleCommand(String(topic), msg);
}

void setupWifiMqtt() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\\nWiFi connected: " + WiFi.localIP().toString());

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  reconnectMqtt();
}

void reconnectMqtt() {
  while (!mqttClient.connected()) {
    if (mqttClient.connect("esp32-controller")) {
      mqttClient.subscribe(TOPIC_MOTOR_CMD);
      mqttClient.subscribe(TOPIC_MODE);
      mqttClient.subscribe(TOPIC_DISPLAY);
      Serial.println("MQTT connected.");
    } else {
      delay(2000);
    }
  }
}

void mqttLoop() {
  if (!mqttClient.connected()) reconnectMqtt();
  mqttClient.loop();
}
""",

    "esp32/src/motor_control.ino": """\
#include <Arduino.h>
#include "config.h"

bool motorRunning = false;

void setupMotor() {
  pinMode(PIN_PUMP_RELAY, OUTPUT);
  digitalWrite(PIN_PUMP_RELAY, LOW);
}

void motorOn() {
  digitalWrite(PIN_PUMP_RELAY, HIGH);
  motorRunning = true;
  setLedState("spray");
  Serial.println("Motor ON");
}

void motorOff() {
  digitalWrite(PIN_PUMP_RELAY, LOW);
  motorRunning = false;
  setLedState("idle");
  Serial.println("Motor OFF");
}
""",

    "esp32/src/led_control.ino": """\
#include <Arduino.h>
#include "config.h"

void setupLeds() {
  pinMode(PIN_LED_IDLE,  OUTPUT);
  pinMode(PIN_LED_SPRAY, OUTPUT);
  pinMode(PIN_LED_ERROR, OUTPUT);
  setLedState("idle");
}

void setLedState(String state) {
  digitalWrite(PIN_LED_IDLE,  state == "idle"  ? HIGH : LOW);
  digitalWrite(PIN_LED_SPRAY, state == "spray" ? HIGH : LOW);
  digitalWrite(PIN_LED_ERROR, state == "error" ? HIGH : LOW);
}
""",

    "esp32/src/display_tft.ino": """\
// TFT display using TFT_eSPI library (configure User_Setup.h separately)
#include <TFT_eSPI.h>
TFT_eSPI tft;

void setupDisplay() {
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1);
  tft.drawString("Booting...", 10, 10, 2);
}

void updateDisplay(String line1, String line2, String line3) {
  tft.fillScreen(TFT_BLACK);
  tft.drawString(line1, 10, 10, 2);
  tft.drawString(line2, 10, 35, 2);
  tft.drawString(line3, 10, 60, 2);
}
""",

    "esp32/src/flow_meter.ino": """\
#include <Arduino.h>
#include "config.h"

volatile long pulseCount = 0;
float totalLitres = 0.0;

void IRAM_ATTR flowISR() { pulseCount++; }

void setupFlowMeter() {
  pinMode(PIN_FLOW_METER, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_FLOW_METER), flowISR, FALLING);
}

// Call every second from loop to accumulate litres
void updateFlowMeter() {
  static unsigned long lastTime = 0;
  unsigned long now = millis();
  if (now - lastTime >= 1000) {
    // YF-S201: ~7.5 pulses per second per litre/min
    float flowRate  = (pulseCount / 7.5);   // L/min
    totalLitres    += flowRate / 60.0;       // L this second
    pulseCount      = 0;
    lastTime        = now;
  }
}

float getTotalLitres() { return totalLitres; }
""",

    "esp32/src/command_handler.ino": """\
#include <Arduino.h>
#include <ArduinoJson.h>
#include "topics.h"

void handleCommand(String topic, String payload) {
  StaticJsonDocument<256> doc;
  deserializeJson(doc, payload);

  if (topic == TOPIC_MOTOR_CMD) {
    String cmd = doc["cmd"] | "off";
    if (cmd == "on")  motorOn();
    else              motorOff();
  }
  else if (topic == TOPIC_MODE) {
    String mode = doc["mode"] | "auto";
    Serial.println("Mode: " + mode);
    updateDisplay("Mode: " + mode, motorRunning ? "Spraying" : "Idle",
                  "Flow: " + String(getTotalLitres(), 2) + " L");
  }
  else if (topic == TOPIC_DISPLAY) {
    String l1 = doc["line1"] | "";
    String l2 = doc["line2"] | "";
    String l3 = doc["line3"] | "";
    updateDisplay(l1, l2, l3);
  }
}
""",

    "esp32/platformio.ini": """\
[env:esp32dev]
platform   = espressif32
board      = esp32dev
framework  = arduino
lib_deps   =
    knolleary/PubSubClient @ ^2.8
    bblanchon/ArduinoJson  @ ^6.21.0
    bodmer/TFT_eSPI        @ ^2.5.0
monitor_speed = 115200
""",

    "esp32/README.md": """\
# ESP32 Controller

Handles: pump relay, status LEDs, TFT display, flow meter.
Communicates with the Pi and backend server via MQTT.

## Setup
1. Install PlatformIO (VSCode extension or CLI)
2. Edit `include/config.h` — set WiFi credentials and MQTT broker IP
3. Configure TFT_eSPI `User_Setup.h` for your specific TFT module
4. `pio run --target upload`
""",
}

# ──────────────────────────────────────────────
# GENERATOR
# ──────────────────────────────────────────────

def generate(root: str):
    created_dirs  = 0
    created_files = 0

    for rel_path, content in FILES.items():
        full_path = os.path.join(root, rel_path)
        dir_path  = os.path.dirname(full_path)

        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"  📁  {dir_path}")
            created_dirs += 1

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅  {full_path}")
        created_files += 1

    print()
    print(f"Done! Created {created_dirs} directories and {created_files} files under '{root}'")
    print()
    print("Next steps:")
    print("  1. cd raspberry_pi  →  pip install -r requirements.txt")
    print("  2. Edit raspberry_pi/.env  →  add your GEMINI_API_KEY and MQTT_BROKER_IP")
    print("  3. cd website/backend  →  pip install -r requirements.txt && uvicorn main:app --reload")
    print("  4. cd website/frontend →  npm install && npm run dev")
    print("  5. Open esp32/ in PlatformIO, edit include/config.h, then upload to board")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold Pesticide Sprinkling System project")
    parser.add_argument("--root", default="./pesticide_system",
                        help="Root directory to generate into (default: ./pesticide_system)")
    args = parser.parse_args()
    print(f"\n🌱  Generating project in: {args.root}\n")
    generate(args.root)