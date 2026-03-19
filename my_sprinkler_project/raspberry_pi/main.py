"""
main.py — Raspberry Pi System Orchestrator
Intelligent Pesticide Sprinkling System

Starts all threads:
  • Sensor polling     (SensorManager)
  • MJPEG camera stream (CameraStream)
  • Disease detection  (DiseaseDetector)
  • MQTT publisher     (Publisher)
  • MQTT subscriber    (Subscriber)
  • OLED display       (OledDisplay)

All threads are daemon threads — they die automatically when the main thread exits.
"""
import time
import signal
import threading
import logging

from utils.logger import setup_logger
from utils.config import Config
from mqtt.publisher  import Publisher
from mqtt.subscriber import Subscriber
from sensors.sensor_manager import SensorManager
from camera.camera_stream   import CameraStream
from inference.disease_detector import DiseaseDetector
from display.oled_display   import OledDisplay

setup_logger()
log = logging.getLogger(__name__)

_shutdown = threading.Event()


def _handle_signal(sig, frame):
    log.info(f"Signal {sig} received — shutting down...")
    _shutdown.set()


def main():
    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    log.info("═" * 50)
    log.info("  Agri-Watch Pesticide System — Pi Node")
    log.info("═" * 50)

    cfg = Config()
    cfg.validate()

    # Build components (order matters — publisher must exist before others)
    publisher  = Publisher(cfg)
    subscriber = Subscriber(cfg, publisher)
    sensors    = SensorManager(cfg, publisher)
    camera     = CameraStream(cfg)
    detector   = DiseaseDetector(cfg, publisher, sensors)
    display    = OledDisplay(cfg)

    threads = [
        threading.Thread(target=subscriber.start,       daemon=True, name="MQTT-Sub"),
        threading.Thread(target=sensors.start_loop,     daemon=True, name="Sensors"),
        threading.Thread(target=camera.start,           daemon=True, name="Camera"),
        threading.Thread(target=detector.start_loop,    daemon=True, name="Inference"),
        threading.Thread(target=display.start_loop,     daemon=True, name="Display"),
    ]

    for t in threads:
        t.start()
        log.info(f"  ✓ Thread started: {t.name}")

    log.info("All threads running. Press Ctrl+C to stop.")

    # Keep main thread alive; check every second for shutdown signal
    while not _shutdown.is_set():
        time.sleep(1)

    log.info("Shutdown complete.")


if __name__ == "__main__":
    main()
