"""
sensors/humidity_sensor.py
DHT22 temperature + humidity sensor.

Wiring:
  DHT22 VCC → 3.3V or 5V
  DHT22 GND → GND
  DHT22 DATA → GPIO pin (default 4, configurable via DHT_GPIO_PIN in .env)
  Pull-up: 10kΩ resistor between VCC and DATA
"""
import logging
import board
import adafruit_dht

log = logging.getLogger(__name__)

_PIN_MAP = {
    4: board.D4, 17: board.D17, 27: board.D27, 22: board.D22,
    5: board.D5,  6: board.D6,  13: board.D13, 19: board.D19,
}


class HumiditySensor:
    def __init__(self, cfg):
        pin = _PIN_MAP.get(cfg.DHT_GPIO_PIN, board.D4)
        self.device = adafruit_dht.DHT22(pin, use_pulseio=False)
        log.info(f"HumiditySensor init: GPIO{cfg.DHT_GPIO_PIN}")

    def read(self) -> dict:
        """
        Return {"temperature": float (°C), "humidity": float (%)}.
        Returns {} on error. DHT22 occasionally fails — this is normal.
        """
        try:
            temp = self.device.temperature
            humi = self.device.humidity
            if temp is None or humi is None:
                raise ValueError("DHT22 returned None")
            result = {"temperature": round(temp, 1), "humidity": round(humi, 1)}
            log.debug(f"DHT22: {result}")
            return result
        except Exception as e:
            # DHT22 read failures are transient and expected ~5% of the time
            log.debug(f"HumiditySensor transient error (normal): {e}")
            return {}
