"""
serial_controller.py
Manages communication between the Raspberry Pi and ESP32
over a USB serial cable (Pi USB-A → ESP32 USB micro/C).

Protocol: newline-delimited JSON  (one JSON object per line)

Pi → ESP32 commands:
  {"cmd":"on",   "dosage_ml":25.0, "trigger":"manual"}
  {"cmd":"off"}
  {"cmd":"mode", "mode":"auto"}
  {"cmd":"display", "line1":"...", "line2":"...", "line3":"..."}
  {"cmd":"ping"}

ESP32 → Pi messages:
  {"type":"status", "running":true, "flow_lpm":1.8, "total_litres":0.42}
  {"type":"flow",   "total_litres":0.42, "duration_sec":14}
  {"type":"ack",    "cmd":"on", "success":true}
  {"type":"pong"}

The listener thread reads ESP32 responses and publishes them
to MQTT so the backend receives flow/status data normally.
"""
import json
import time
import logging
import threading
import serial
import serial.tools.list_ports

log = logging.getLogger(__name__)

# Default USB serial port — Pi enumerates ESP32 as /dev/ttyUSB0 or /dev/ttyACM0
DEFAULT_PORT = "/dev/ttyUSB0"
BAUD_RATE    = 115200
TIMEOUT      = 2    # seconds


def _find_esp32_port() -> str:
    """
    Auto-detect the ESP32 serial port.
    Looks for CP210x (most common ESP32 USB-UART chip) or CH340.
    Falls back to DEFAULT_PORT if not found.
    """
    for port in serial.tools.list_ports.comports():
        desc = (port.description or "").lower()
        if any(k in desc for k in ["cp210", "ch340", "ch341", "silicon labs", "uart"]):
            log.info(f"Auto-detected ESP32 on: {port.device} ({port.description})")
            return port.device
    log.warning(f"ESP32 not auto-detected — using default: {DEFAULT_PORT}")
    return DEFAULT_PORT


class SerialController:
    def __init__(self, cfg, publisher):
        self.cfg       = cfg
        self.publisher = publisher
        self._ser      = None
        self._lock     = threading.Lock()
        self._running  = False

        port = getattr(cfg, "ESP32_SERIAL_PORT", None) or _find_esp32_port()
        try:
            self._ser = serial.Serial(
                port=port,
                baudrate=BAUD_RATE,
                timeout=TIMEOUT,
            )
            time.sleep(2)   # wait for ESP32 to reset after serial connect
            self._ser.reset_input_buffer()
            log.info(f"Serial connection open: {port} @ {BAUD_RATE}")
        except serial.SerialException as e:
            log.error(f"Failed to open serial port {port}: {e}")
            self._ser = None

    # ── public commands ───────────────────────────────────────────────────────

    def motor_on(self, dosage_ml: float, trigger: str = "manual"):
        self._send({"cmd": "on", "dosage_ml": round(dosage_ml, 1), "trigger": trigger})

    def motor_off(self):
        self._send({"cmd": "off"})

    def send_mode(self, mode: str):
        self._send({"cmd": "mode", "mode": mode})

    def update_display(self, line1: str, line2: str = "", line3: str = ""):
        self._send({"cmd": "display", "line1": line1, "line2": line2, "line3": line3})

    def ping(self) -> bool:
        self._send({"cmd": "ping"})
        return True

    def is_connected(self) -> bool:
        return self._ser is not None and self._ser.is_open

    # ── listener thread ───────────────────────────────────────────────────────

    def start_listener(self):
        """
        Start background thread that reads lines from ESP32
        and forwards them to MQTT so backend receives them normally.
        """
        self._running = True
        t = threading.Thread(target=self._listen_loop, daemon=True, name="Serial-Listener")
        t.start()
        log.info("Serial listener thread started.")

    def stop(self):
        self._running = False
        if self._ser and self._ser.is_open:
            self._ser.close()
            log.info("Serial port closed.")

    # ── internals ─────────────────────────────────────────────────────────────

    def _send(self, obj: dict):
        if not self.is_connected():
            log.warning(f"Serial not connected — cannot send: {obj}")
            return
        line = json.dumps(obj) + "\n"
        try:
            with self._lock:
                self._ser.write(line.encode("utf-8"))
            log.debug(f"Serial → ESP32: {line.strip()}")
        except serial.SerialException as e:
            log.error(f"Serial write error: {e}")

    def _listen_loop(self):
        """Read JSON lines from ESP32, publish to MQTT."""
        log.info("Serial listener running...")
        while self._running:
            if not self.is_connected():
                time.sleep(2)
                continue
            try:
                raw = self._ser.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                log.debug(f"Serial ← ESP32: {line}")

                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    log.warning(f"Non-JSON from ESP32: {line[:80]}")
                    continue

                self._handle_esp_message(msg)

            except serial.SerialException as e:
                log.error(f"Serial read error: {e}")
                time.sleep(1)
            except Exception as e:
                log.error(f"Listener unexpected error: {e}", exc_info=True)

    def _handle_esp_message(self, msg: dict):
        """Route ESP32 messages to the appropriate MQTT topic."""
        msg_type = msg.get("type", "")

        if msg_type == "status":
            # Publish as esp32/status — backend bridge handles it
            self.publisher.publish("esp32/status", json.dumps(msg))

        elif msg_type == "flow":
            # Publish as esp32/flow — backend updates motor event with actual litres
            self.publisher.publish("esp32/flow", json.dumps(msg))

        elif msg_type == "ack":
            # Log acknowledgements
            cmd     = msg.get("cmd", "?")
            success = msg.get("success", False)
            note    = msg.get("note", "")
            log.info(f"ESP32 ACK: cmd={cmd} success={success} {note}")
            self.publisher.publish("esp32/ack", json.dumps(msg))

        elif msg_type == "pong":
            log.debug("ESP32 pong received.")

        elif msg_type == "log":
            # ESP32 can send log messages
            log.info(f"[ESP32] {msg.get('message', '')}")

        else:
            log.debug(f"Unhandled ESP32 message type '{msg_type}': {msg}")