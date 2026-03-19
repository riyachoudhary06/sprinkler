"""
sensors/light_sensor.py
BH1750 ambient light sensor via I2C.

Wiring:
  BH1750 VCC → 3.3V
  BH1750 GND → GND
  BH1750 SCL → GPIO 3 (SCL)
  BH1750 SDA → GPIO 2 (SDA)
  BH1750 ADD → GND (I2C address 0x23) or 3.3V (address 0x5C)
"""
import time
import logging
import smbus2

log = logging.getLogger(__name__)

ADDR_LOW  = 0x23   # ADD pin → GND
ADDR_HIGH = 0x5C   # ADD pin → VCC
CMD_CONT_HIGH_RES = 0x10


class LightSensor:
    def __init__(self, cfg):
        self.bus  = smbus2.SMBus(cfg.BH1750_I2C_BUS)
        self.addr = ADDR_LOW
        self.bus.write_byte(self.addr, CMD_CONT_HIGH_RES)
        time.sleep(0.18)   # measurement time
        log.info(f"LightSensor init: I2C bus={cfg.BH1750_I2C_BUS} addr=0x{self.addr:02X}")

    def read(self) -> float:
        """
        Return ambient light in lux.
        Returns -1.0 on error.
        """
        try:
            data = self.bus.read_i2c_block_data(self.addr, CMD_CONT_HIGH_RES, 2)
            lux  = round((data[0] << 8 | data[1]) / 1.2, 1)
            log.debug(f"Light: {lux} lux")
            return lux
        except Exception as e:
            log.error(f"LightSensor.read() error: {e}")
            return -1.0
