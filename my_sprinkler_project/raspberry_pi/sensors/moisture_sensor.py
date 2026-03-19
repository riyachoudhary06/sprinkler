"""
sensors/moisture_sensor.py
Capacitive soil moisture sensor via ADS1115 channel A1.

Calibration:
  DRY_RAW  — ADC reading with sensor in dry air    (~26000)
  WET_RAW  — ADC reading with sensor fully in water (~13000)
  Set these in .env: MOISTURE_DRY_RAW, MOISTURE_WET_RAW
"""
import logging
import Adafruit_ADS1x15

log = logging.getLogger(__name__)

GAIN    = 1
CHANNEL = 1   # ADS1115 channel A1


class MoistureSensor:
    def __init__(self, cfg):
        self.dry_raw = cfg.MOISTURE_DRY_RAW
        self.wet_raw = cfg.MOISTURE_WET_RAW
        self.adc     = Adafruit_ADS1x15.ADS1115(busnum=cfg.ADS1115_I2C_BUS)
        log.info(f"MoistureSensor init: dry={self.dry_raw} wet={self.wet_raw}")

    def read(self) -> float:
        """
        Return soil moisture percentage (0.0–100.0).
        Returns -1.0 on error.
        """
        try:
            raw  = self.adc.read_adc(CHANNEL, gain=GAIN)
            pct  = (self.dry_raw - raw) / (self.dry_raw - self.wet_raw) * 100.0
            pct  = round(max(0.0, min(100.0, pct)), 1)
            log.debug(f"Moisture: raw={raw} pct={pct}%")
            return pct
        except Exception as e:
            log.error(f"MoistureSensor.read() error: {e}")
            return -1.0
