"""
config.py — Environment configuration for the backend server.
All values loaded from .env or environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # MQTT
    MQTT_BROKER_IP: str   = os.getenv("MQTT_BROKER_IP", "localhost")
    MQTT_PORT: int        = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME: str    = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD: str    = os.getenv("MQTT_PASSWORD", "")
    MQTT_CLIENT_ID: str   = os.getenv("MQTT_CLIENT_ID", "agriwatch-backend")

    # Database
    DATABASE_URL: str     = os.getenv("DATABASE_URL", "sqlite:///./agriwatch.db")

    # Security
    SECRET_KEY: str       = os.getenv("SECRET_KEY", "change-this-in-production")

    # Pi camera stream
    PI_STREAM_URL: str    = os.getenv("PI_STREAM_URL", "http://raspberrypi.local:8080/stream")
    PI_HOST: str          = os.getenv("PI_HOST", "raspberrypi.local")

    # Alert thresholds
    PH_MIN: float         = float(os.getenv("PH_MIN", 5.5))
    PH_MAX: float         = float(os.getenv("PH_MAX", 7.5))
    MOISTURE_MIN: float   = float(os.getenv("MOISTURE_MIN", 40.0))
    MOISTURE_MAX: float   = float(os.getenv("MOISTURE_MAX", 80.0))
    HUMIDITY_MIN: float   = float(os.getenv("HUMIDITY_MIN", 30.0))
    HUMIDITY_MAX: float   = float(os.getenv("HUMIDITY_MAX", 90.0))
    TEMP_MIN: float       = float(os.getenv("TEMP_MIN", 15.0))
    TEMP_MAX: float       = float(os.getenv("TEMP_MAX", 35.0))


settings = Settings()
