"""
services/alert_service.py
Checks incoming sensor readings against configured thresholds.
Returns a list of alert dicts for any out-of-range values.
"""
import logging

log = logging.getLogger(__name__)


class AlertService:
    def __init__(self, settings):
        self.thresholds = {
            "ph":          (settings.PH_MIN,       settings.PH_MAX),
            "moisture":    (settings.MOISTURE_MIN,  settings.MOISTURE_MAX),
            "humidity":    (settings.HUMIDITY_MIN,  settings.HUMIDITY_MAX),
            "temperature": (settings.TEMP_MIN,      settings.TEMP_MAX),
        }

    def check(self, sensor_data: dict) -> list[dict]:
        """
        Check sensor_data dict against thresholds.
        Returns list of alert dicts:
            [{"sensor": str, "value": float, "type": "below_threshold"|"above_threshold", "threshold": float}]
        """
        alerts = []
        for sensor, (low, high) in self.thresholds.items():
            value = sensor_data.get(sensor)
            if value is None or value < 0:
                continue  # sensor error value, skip
            if value < low:
                alerts.append({
                    "sensor":    sensor,
                    "value":     value,
                    "type":      "below_threshold",
                    "threshold": low,
                })
                log.warning(f"ALERT: {sensor}={value} below minimum {low}")
            elif value > high:
                alerts.append({
                    "sensor":    sensor,
                    "value":     value,
                    "type":      "above_threshold",
                    "threshold": high,
                })
                log.warning(f"ALERT: {sensor}={value} above maximum {high}")
        return alerts

    def update_threshold(self, sensor: str, low: float, high: float):
        """Update a threshold at runtime."""
        self.thresholds[sensor] = (low, high)
        log.info(f"Threshold updated: {sensor} → [{low}, {high}]")
