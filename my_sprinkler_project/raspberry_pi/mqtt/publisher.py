"""
mqtt/publisher.py
Thread-safe MQTT publisher with automatic reconnection.
"""
import json
import logging
import threading
import paho.mqtt.client as mqtt

log = logging.getLogger(__name__)


class Publisher:
    def __init__(self, cfg):
        self.cfg   = cfg
        self._lock = threading.Lock()

        self.client = mqtt.Client(
            client_id=f"{cfg.MQTT_CLIENT_ID}-pub",
            clean_session=True,
        )
        if cfg.MQTT_USERNAME:
            self.client.username_pw_set(cfg.MQTT_USERNAME, cfg.MQTT_PASSWORD)

        self.client.on_connect    = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        self._connect()
        self.client.loop_start()   # background network thread

    def _connect(self):
        try:
            self.client.connect(self.cfg.MQTT_BROKER_IP, self.cfg.MQTT_PORT, keepalive=60)
            log.info(f"Publisher connecting to {self.cfg.MQTT_BROKER_IP}:{self.cfg.MQTT_PORT}")
        except Exception as e:
            log.error(f"Publisher connect error: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            log.info("Publisher connected to broker.")
        else:
            log.error(f"Publisher connect failed: rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            log.warning(f"Publisher disconnected (rc={rc}) — paho will auto-reconnect.")

    def publish(self, topic: str, payload: str | dict, qos: int = 1) -> bool:
        """
        Publish a message. Thread-safe.
        payload can be a string or a dict (will be JSON-serialised).
        Returns True on success, False on failure.
        """
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        with self._lock:
            result = self.client.publish(topic, payload, qos=qos)

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            log.warning(f"Publish failed on '{topic}': rc={result.rc}")
            return False
        return True

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
