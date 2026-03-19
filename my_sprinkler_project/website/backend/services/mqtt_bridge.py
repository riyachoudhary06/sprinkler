"""
services/mqtt_bridge.py
Subscribes to all Raspberry Pi and ESP32 MQTT topics.
Persists incoming data to the database and triggers alert checks.
"""
import json
import logging
import threading
from datetime import datetime

import paho.mqtt.client as mqtt

from db.database import SessionLocal
from db.models import SensorReading, DiseaseResult, MotorEvent, SystemLog
from services.alert_service import AlertService

log = logging.getLogger(__name__)

# Topics the backend subscribes to
SUBSCRIPTIONS = [
    ("pi/sensors/all",      1),
    ("pi/inference/result", 1),
    ("pi/logs",             1),
    ("esp32/status",        0),
    ("esp32/flow",          0),
]


class MQTTBridge:
    def __init__(self, settings):
        self.settings      = settings
        self.alert_service = AlertService(settings)
        self._connected    = False
        self._stop_event   = threading.Event()

        self.client = mqtt.Client(
            client_id=f"{settings.MQTT_CLIENT_ID}-bridge",
            clean_session=True,
        )
        if settings.MQTT_USERNAME:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        self.client.on_connect    = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message    = self._on_message

    # ── connection ────────────────────────────────────────────────────────────

    def start(self):
        log.info(f"MQTT bridge connecting to {self.settings.MQTT_BROKER_IP}:{self.settings.MQTT_PORT}")
        try:
            self.client.connect(
                self.settings.MQTT_BROKER_IP,
                self.settings.MQTT_PORT,
                keepalive=60,
            )
            self.client.loop_forever()
        except Exception as e:
            log.error(f"MQTT bridge fatal error: {e}")

    def stop(self):
        self._stop_event.set()
        self.client.disconnect()
        log.info("MQTT bridge stopped.")

    def is_connected(self) -> bool:
        return self._connected

    def publish(self, topic: str, payload: str | dict, qos: int = 1):
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        result = self.client.publish(topic, payload, qos=qos)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            log.warning(f"Publish failed on '{topic}': rc={result.rc}")

    # ── callbacks ─────────────────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            log.info("MQTT bridge connected.")
            for topic, qos in SUBSCRIPTIONS:
                client.subscribe(topic, qos)
                log.info(f"  Subscribed → {topic}")
        else:
            log.error(f"MQTT bridge connect failed: rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            log.warning(f"MQTT bridge disconnected unexpectedly: rc={rc}. Will auto-reconnect.")

    def _on_message(self, client, userdata, msg):
        topic   = msg.topic
        raw     = msg.payload.decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            log.warning(f"Non-JSON payload on {topic}: {raw[:100]}")
            return

        try:
            if topic == "pi/sensors/all":
                self._handle_sensors(payload)
            elif topic == "pi/inference/result":
                self._handle_inference(payload)
            elif topic == "pi/logs":
                self._handle_pi_log(payload)
            elif topic == "esp32/status":
                self._handle_esp_status(payload)
            elif topic == "esp32/flow":
                self._handle_esp_flow(payload)
        except Exception as e:
            log.error(f"Error handling [{topic}]: {e}", exc_info=True)

    # ── handlers ──────────────────────────────────────────────────────────────

    def _handle_sensors(self, payload: dict):
        db = SessionLocal()
        try:
            row = SensorReading(
                ph           = payload.get("ph"),
                moisture     = payload.get("moisture"),
                nitrogen     = payload.get("nitrogen"),
                phosphorus   = payload.get("phosphorus"),
                potassium    = payload.get("potassium"),
                temperature  = payload.get("temperature"),
                humidity     = payload.get("humidity"),
                light_lux    = payload.get("light_lux"),
                pi_timestamp = payload.get("timestamp"),
            )
            db.add(row)
            db.commit()
            log.debug(f"Sensor reading saved: pH={payload.get('ph')} moisture={payload.get('moisture')}")

            # check alert thresholds
            alerts = self.alert_service.check(payload)
            if alerts:
                for alert in alerts:
                    db.add(SystemLog(
                        level="WARN",
                        message=f"Threshold alert: {alert['sensor']} = {alert['value']} ({alert['type']})",
                        source="alert_service",
                        extra=alert,
                    ))
                db.commit()
        finally:
            db.close()

    def _handle_inference(self, payload: dict):
        db = SessionLocal()
        try:
            row = DiseaseResult(
                disease        = payload.get("disease", "unknown"),
                confidence     = payload.get("confidence"),
                severity       = payload.get("severity"),
                affected_area  = payload.get("affected_area"),
                recommendation = payload.get("recommendation"),
                pesticide      = payload.get("pesticide"),
                dosage_ml      = payload.get("dosage_ml"),
                image_path     = payload.get("image_path"),
                sensor_context = payload.get("sensor_context"),
                gemini_error   = payload.get("error") or None,
            )
            db.add(row)

            # Log the event
            db.add(SystemLog(
                level="INFO",
                message=(
                    f"Gemini inference: {payload.get('disease', 'unknown')} "
                    f"({int((payload.get('confidence') or 0)*100)}% conf, "
                    f"severity={payload.get('severity')})"
                ),
                source="disease_detector",
                extra={"dosage_ml": payload.get("dosage_ml")},
            ))
            db.commit()
            log.info(f"Disease result saved: {payload.get('disease')}")

            # Auto-spray in auto mode if disease detected
            if payload.get("disease", "").lower() != "healthy" and self._get_mode(db) == "auto":
                dosage = payload.get("dosage_ml", 0)
                if dosage > 0:
                    self.publish("server/motor/cmd", {"cmd": "on", "dosage_ml": dosage, "trigger": "auto_disease"})
                    log.info(f"Auto-spray triggered: {dosage} ml/m²")
        finally:
            db.close()

    def _handle_pi_log(self, payload: dict):
        db = SessionLocal()
        try:
            db.add(SystemLog(
                level   = payload.get("level", "INFO"),
                message = payload.get("message", ""),
                source  = payload.get("source", "pi"),
                extra   = payload.get("extra"),
            ))
            db.commit()
        finally:
            db.close()

    def _handle_esp_status(self, payload: dict):
        log.debug(f"ESP32 status: {payload}")
        # Could update a status table or in-memory state here

    def _handle_esp_flow(self, payload: dict):
        """ESP32 reports total flow after a spray session ends."""
        db = SessionLocal()
        try:
            flow_litres  = payload.get("total_litres", 0)
            duration_sec = payload.get("duration_sec", 0)
            # Update the most recent motor ON event with actual flow
            event = (
                db.query(MotorEvent)
                .filter(MotorEvent.event_type.in_(["on", "auto_on"]))
                .order_by(MotorEvent.id.desc())
                .first()
            )
            if event:
                event.flow_litres  = flow_litres
                event.duration_sec = duration_sec
                db.commit()
            log.info(f"Flow data saved: {flow_litres} L over {duration_sec}s")
        finally:
            db.close()

    def _get_mode(self, db) -> str:
        from db.models import SystemConfig
        cfg = db.query(SystemConfig).filter(SystemConfig.key == "mode").first()
        return cfg.value if cfg else "auto"
