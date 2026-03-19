"""
sensors/sensor_manager.py
Polls all sensors on a fixed interval, aggregates readings,
publishes to MQTT topic pi/sensors/all, and keeps the latest
reading in memory so DiseaseDetector can embed context in prompts.
"""
import json
import time
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

        # Lazy-init sensors; failures are caught per-sensor so one broken
        # sensor doesn't kill the whole system.
        self._ph       = self._init(PhSensor)
        self._moisture = self._init(MoistureSensor, cfg)
        self._npk      = self._init(NpkSensor, cfg)
        self._humidity = self._init(HumiditySensor, cfg)
        self._light    = self._init(LightSensor, cfg)

        # Latest reading kept in memory for inference context
        self.latest: dict = {}

    def _init(self, cls, *args):
        try:
            return cls(*args)
        except Exception as e:
            log.error(f"Failed to init {cls.__name__}: {e}")
            return None

    def _safe_read(self, sensor, method="read"):
        if sensor is None:
            return None
        try:
            return getattr(sensor, method)()
        except Exception as e:
            log.warning(f"{sensor.__class__.__name__} read error: {e}")
            return None

    def read_all(self) -> dict:
        npk = self._safe_read(self._npk) or {}
        dht = self._safe_read(self._humidity) or {}

        data = {
            "ph":          self._safe_read(self._ph),
            "moisture":    self._safe_read(self._moisture),
            "nitrogen":    npk.get("N"),
            "phosphorus":  npk.get("P"),
            "potassium":   npk.get("K"),
            "temperature": dht.get("temperature"),
            "humidity":    dht.get("humidity"),
            "light_lux":   self._safe_read(self._light),
            "timestamp":   time.time(),
        }
        # Filter out None for cleaner MQTT payload
        return {k: v for k, v in data.items() if v is not None}

    def start_loop(self):
        log.info(f"Sensor loop started — polling every {self.cfg.SENSOR_POLL_INTERVAL}s")
        while True:
            try:
                self.latest = self.read_all()
                self.publisher.publish("pi/sensors/all", json.dumps(self.latest))
                log.debug(f"Sensors: {self.latest}")
            except Exception as e:
                log.error(f"Sensor loop error: {e}", exc_info=True)
            time.sleep(self.cfg.SENSOR_POLL_INTERVAL)
