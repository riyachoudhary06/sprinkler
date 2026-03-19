"""
sensors/npk_sensor.py
RS485 Modbus RTU NPK sensor reader.

Typical sensor: JXBS-3001-NPK or similar 5-pin RS485 type.

Wiring (via RS485-to-USB adapter):
  Sensor A+ → RS485 adapter A
  Sensor B- → RS485 adapter B
  Sensor VCC → 12V supply
  Sensor GND → GND

Modbus frame for reading N, P, K (3 registers from address 0x0000):
  [ADDR][FC=0x03][REG_HI][REG_LO][COUNT_HI][COUNT_LO][CRC_LO][CRC_HI]
"""
import time
import struct
import logging
import serial

log = logging.getLogger(__name__)

SLAVE_ADDR = 0x01
FUNC_CODE  = 0x03
START_REG  = 0x0000
NUM_REGS   = 0x0003   # N, P, K


def _crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack("<H", crc)


class NpkSensor:
    REQUEST = bytes([SLAVE_ADDR, FUNC_CODE, 0x00, 0x00, 0x00, 0x03])

    def __init__(self, cfg):
        self.ser = serial.Serial(
            port=cfg.NPK_SERIAL_PORT,
            baudrate=cfg.NPK_BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
        )
        self._cmd = self.REQUEST + _crc16(self.REQUEST)
        log.info(f"NpkSensor init: port={cfg.NPK_SERIAL_PORT} baud={cfg.NPK_BAUD_RATE}")

    def read(self) -> dict:
        """
        Return dict {"N": int, "P": int, "K": int} in mg/kg.
        Returns {} on error.
        """
        try:
            self.ser.reset_input_buffer()
            self.ser.write(self._cmd)
            time.sleep(0.1)
            response = self.ser.read(11)

            if len(response) < 9:
                raise ValueError(f"Short response ({len(response)} bytes): {response.hex()}")

            n = (response[3] << 8) | response[4]
            p = (response[5] << 8) | response[6]
            k = (response[7] << 8) | response[8]
            result = {"N": n, "P": p, "K": k}
            log.debug(f"NPK: {result}")
            return result
        except Exception as e:
            log.error(f"NpkSensor.read() error: {e}")
            return {}
