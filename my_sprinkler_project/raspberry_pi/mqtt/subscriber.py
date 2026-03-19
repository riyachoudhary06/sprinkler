"""
mqtt/subscriber.py
Subscribes to server commands and updates Pi state accordingly.

Topics handled:
  server/mode          → update Config.mode ("auto" | "manual")
  server/motor/cmd     → forwarded to ESP32 (Pi is pass-through in auto mode)
  server/camera/capture → triggers immediate inference cycle
"""
import json
import logging
import paho.mqtt.client as mqtt

log = logging.getLogger(__name__)

SUBSCRIPTIONS = [
    ("server/mode",           1),
    ("server/motor/cmd",      1),
    ("server/camera/capture", 1),
]


class Subscriber:
    def __init__(self, cfg, publisher):
        self.cfg       = cfg
        self.publisher = publisher
        # Will be set by main.py after detector is created
        self._detector = None

        self.client = mqtt.Client(
            client_id=f"{cfg.MQTT_CLIENT_ID}-sub",
            clean_session=True,
        )
        if cfg.MQTT_USERNAME:
            self.client.username_pw_set(cfg.MQTT_USERNAME, cfg.MQTT_PASSWORD)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def set_detector(self, detector):
        """Inject DiseaseDetector reference after construction."""
        self._detector = detector

    def start(self):
        log.info(f"Subscriber connecting to {self.cfg.MQTT_BROKER_IP}:{self.cfg.MQTT_PORT}")
        self.client.connect(self.cfg.MQTT_BROKER_IP, self.cfg.MQTT_PORT, keepalive=60)
        self.client.loop_forever()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            log.info("Subscriber connected.")
            for topic, qos in SUBSCRIPTIONS:
                client.subscribe(topic, qos)
                log.info(f"  Subscribed → {topic}")
        else:
            log.error(f"Subscriber connect failed: rc={rc}")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            log.warning(f"Non-JSON on {topic}: {msg.payload[:80]}")
            return

        log.debug(f"Received [{topic}]: {payload}")

        if topic == "server/mode":
            new_mode = payload.get("mode", "auto")
            self.cfg.mode = new_mode
            log.info(f"Mode updated to: {new_mode}")

        elif topic == "server/motor/cmd":
            # Pi logs the command; ESP32 executes it directly via its own subscription
            log.info(f"Motor command observed: {payload.get('cmd')} dosage={payload.get('dosage_ml')}")

        elif topic == "server/camera/capture":
            log.info("On-demand capture requested by server.")
            if self._detector:
                self._detector.trigger_now()
            else:
                log.warning("Detector not available yet — ignoring capture request.")
