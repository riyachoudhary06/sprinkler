"""
utils/config.py — Load all Pi configuration from .env
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)


class Config:
    # Gemini
    GEMINI_API_KEY:      str   = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL:        str   = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # MQTT
    MQTT_BROKER_IP:      str   = os.getenv("MQTT_BROKER_IP", "localhost")
    MQTT_PORT:           int   = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME:       str   = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD:       str   = os.getenv("MQTT_PASSWORD", "")
    MQTT_CLIENT_ID:      str   = os.getenv("MQTT_CLIENT_ID", "agriwatch-pi")

    # Intervals
    SENSOR_POLL_INTERVAL:  int = int(os.getenv("SENSOR_POLL_INTERVAL", 5))
    INFERENCE_INTERVAL:    int = int(os.getenv("INFERENCE_INTERVAL", 30))
    DISPLAY_UPDATE_INTERVAL:int= int(os.getenv("DISPLAY_UPDATE_INTERVAL", 10))

    # Camera
    CAPTURE_DIR:         str   = os.getenv("CAPTURE_DIR", "/home/pi/captures")
    STREAM_PORT:         int   = int(os.getenv("STREAM_PORT", 8080))
    CAPTURE_WIDTH:       int   = int(os.getenv("CAPTURE_WIDTH", 1280))
    CAPTURE_HEIGHT:      int   = int(os.getenv("CAPTURE_HEIGHT", 960))
    STREAM_WIDTH:        int   = int(os.getenv("STREAM_WIDTH", 640))
    STREAM_HEIGHT:       int   = int(os.getenv("STREAM_HEIGHT", 480))

    # Sensors
    ADS1115_I2C_BUS:     int   = int(os.getenv("ADS1115_I2C_BUS", 1))
    DHT_GPIO_PIN:        int   = int(os.getenv("DHT_GPIO_PIN", 4))
    NPK_SERIAL_PORT:     str   = os.getenv("NPK_SERIAL_PORT", "/dev/ttyUSB0")
    NPK_BAUD_RATE:       int   = int(os.getenv("NPK_BAUD_RATE", 4800))
    BH1750_I2C_BUS:      int   = int(os.getenv("BH1750_I2C_BUS", 1))

    # pH calibration
    PH_SLOPE:            float = float(os.getenv("PH_SLOPE", 3.5))
    PH_OFFSET:           float = float(os.getenv("PH_OFFSET", 0.0))

    # Moisture calibration
    MOISTURE_DRY_RAW:    int   = int(os.getenv("MOISTURE_DRY_RAW", 26000))
    MOISTURE_WET_RAW:    int   = int(os.getenv("MOISTURE_WET_RAW", 13000))

    # Logging
    LOG_LEVEL:           str   = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR:             str   = os.getenv("LOG_DIR", "/home/pi/logs")

    # Runtime mutable state (not from env)
    mode: str = "auto"

    def validate(self):
        """Warn about missing critical config values at startup."""
        if not self.GEMINI_API_KEY:
            log.warning("GEMINI_API_KEY is not set — disease detection will fail.")
        if self.MQTT_BROKER_IP == "localhost":
            log.warning("MQTT_BROKER_IP is 'localhost' — ensure broker is running locally.")
        log.info(f"Config loaded: broker={self.MQTT_BROKER_IP} poll={self.SENSOR_POLL_INTERVAL}s infer={self.INFERENCE_INTERVAL}s")
