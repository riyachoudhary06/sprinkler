"""
sensors/ph_sensor.py
Reads soil pH via analog pH module connected to ADS1115 ADC (channel A0).

Wiring:
  pH module AOUT → ADS1115 A0
  ADS1115 VDD    → Pi 3.3V
  ADS1115 GND    → Pi GND
  ADS1115 SCL    → Pi GPIO 3 (SCL)
  ADS1115 SDA    → Pi GPIO 2 (SDA)

Calibration:
  Use pH 4.0 and pH 7.0 buffer solutions.
  Adjust PH_SLOPE and PH_OFFSET in .env until readings match.
"""
import logging
import Adafruit_ADS1x15

log = logging.getLogger(__name__)

GAIN    = 1          # ±4.096 V range  →  1 bit = 0.125 mV
CHANNEL = 0          # ADS1115 channel A0


class PhSensor:
    def __init__(self, slope: float = 3.5, offset: float = 0.0, bus: int = 1):
        self.slope  = slope
        self.offset = offset
        self.adc    = Adafruit_ADS1x15.ADS1115(busnum=bus)
        log.info(f"PhSensor init: slope={slope} offset={offset}")

    def read(self) -> float:
        """
        Return pH (0.0–14.0).
        Returns -1.0 if the read fails.
        """
        try:
            raw     = self.adc.read_adc(CHANNEL, gain=GAIN)
            voltage = raw * (4.096 / 32767.0)
            ph      = 7.0 + ((2.5 - voltage) * self.slope) + self.offset
            ph      = round(max(0.0, min(14.0, ph)), 2)
            log.debug(f"pH: raw={raw} V={voltage:.3f} pH={ph}")
            return ph
        except Exception as e:
            log.error(f"PhSensor.read() error: {e}")
            return -1.0
