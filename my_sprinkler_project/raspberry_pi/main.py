"""
main.py — Raspberry Pi System Orchestrator
ESP32 is connected via USB cable — serial_controller handles all ESP32 comms.
WiFi/MQTT is only used for Pi ↔ backend server communication.
"""
import time
import signal
import threading
import logging

from utils.logger           import setup_logger
from utils.config           import Config
from mqtt.publisher         import Publisher
from mqtt.subscriber        import Subscriber
from sensors.sensor_manager import SensorManager
from camera.camera_stream   import CameraStream
from inference.disease_detector import DiseaseDetector
from display.oled_display   import OledDisplay
from serial_controller      import SerialController

setup_logger()
log = logging.getLogger(__name__)

_shutdown = threading.Event()


def _handle_signal(sig, frame):
    log.info(f"Signal {sig} — shutting down...")
    _shutdown.set()


def main():
    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    log.info("═" * 50)
    log.info("  Agri-Watch Pi Node  (ESP32 via USB Serial)")
    log.info("═" * 50)

    cfg = Config()
    cfg.validate()

    # ── MQTT (Pi ↔ Backend server) ─────────────────────────────────────────
    publisher  = Publisher(cfg)
    subscriber = Subscriber(cfg, publisher)

    # ── USB Serial (Pi ↔ ESP32) ────────────────────────────────────────────
    serial_ctrl = SerialController(cfg, publisher)
    subscriber.set_serial_controller(serial_ctrl)

    # ── Sensors + Camera + Inference ───────────────────────────────────────
    sensors  = SensorManager(cfg, publisher)
    camera   = CameraStream(cfg)
    detector = DiseaseDetector(cfg, publisher, sensors)
    display  = OledDisplay(cfg)

    # Wire detector into subscriber for on-demand captures
    subscriber.set_detector(detector)

    # ── Start all threads ──────────────────────────────────────────────────
    threads = [
        threading.Thread(target=subscriber.start,         daemon=True, name="MQTT-Sub"),
        threading.Thread(target=sensors.start_loop,       daemon=True, name="Sensors"),
        threading.Thread(target=camera.start,             daemon=True, name="Camera"),
        threading.Thread(target=detector.start_loop,      daemon=True, name="Inference"),
        threading.Thread(target=display.start_loop,       daemon=True, name="Display"),
        threading.Thread(target=serial_ctrl.start_listener, daemon=True, name="Serial-RX"),
    ]

    for t in threads:
        t.start()
        log.info(f"  ✓ {t.name}")

    # Send initial state to ESP32
    if serial_ctrl.is_connected():
        serial_ctrl.send_mode(cfg.mode)
        serial_ctrl.update_display("Agri-Watch", f"Mode: {cfg.mode}", "Booted OK")
        log.info("Initial state sent to ESP32 over serial.")
    else:
        log.warning("ESP32 serial not connected — check USB cable and port.")

    log.info("All threads running. Ctrl+C to stop.")
    while not _shutdown.is_set():
        time.sleep(1)

    serial_ctrl.stop()
    log.info("Shutdown complete.")


if __name__ == "__main__":
    main()