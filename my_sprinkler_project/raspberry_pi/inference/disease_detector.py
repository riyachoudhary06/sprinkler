"""
inference/disease_detector.py
Orchestrates the full disease detection pipeline:
  capture → preprocess → Gemini API → dosage calc → MQTT publish

Runs on its own thread at INFERENCE_INTERVAL seconds.
Also listens for on-demand capture commands from MQTT subscriber.
"""
import json
import time
import logging
import threading

from camera.capture             import capture_image
from camera.preprocess          import preprocess_image
from inference.gemini_client    import GeminiClient
from inference.dosage_calculator import calculate_dosage

log = logging.getLogger(__name__)


class DiseaseDetector:
    def __init__(self, cfg, publisher, sensor_manager):
        self.cfg            = cfg
        self.publisher      = publisher
        self.sensor_manager = sensor_manager   # for live sensor context
        self.gemini         = GeminiClient(api_key=cfg.GEMINI_API_KEY, model=cfg.GEMINI_MODEL)
        self._manual_trigger = threading.Event()   # set by Subscriber for on-demand runs

    # ── public API ────────────────────────────────────────────────────────────

    def trigger_now(self):
        """Called by MQTT subscriber when server/camera/capture is received."""
        self._manual_trigger.set()

    def start_loop(self):
        log.info(f"Disease detection loop: every {self.cfg.INFERENCE_INTERVAL}s")
        while True:
            try:
                self._run_once()
            except Exception as e:
                log.error(f"Detector loop error: {e}", exc_info=True)

            # Wait for interval OR a manual trigger, whichever comes first
            triggered = self._manual_trigger.wait(timeout=self.cfg.INFERENCE_INTERVAL)
            if triggered:
                self._manual_trigger.clear()
                log.info("Manual capture triggered.")

    # ── internals ─────────────────────────────────────────────────────────────

    def _run_once(self) -> dict:
        log.info("Starting inference cycle...")

        # 1. Capture
        try:
            img_path = capture_image(
                self.cfg.CAPTURE_DIR,
                self.cfg.CAPTURE_WIDTH,
                self.cfg.CAPTURE_HEIGHT,
            )
        except RuntimeError as e:
            log.error(f"Capture failed: {e}")
            self._publish_error(str(e))
            return {}

        # 2. Preprocess
        b64_image = preprocess_image(img_path)
        if not b64_image:
            log.error("Preprocessing returned empty image — skipping inference.")
            return {}

        # 3. Gemini inference
        sensor_ctx = dict(self.sensor_manager.latest)   # snapshot at time of capture
        result     = self.gemini.analyze(b64_image, sensor_ctx)

        # 4. Recalculate dosage with our own formula (overrides Gemini's suggestion)
        result["dosage_ml"]      = calculate_dosage(result)
        result["image_path"]     = img_path
        result["sensor_context"] = sensor_ctx
        result["timestamp"]      = time.time()

        # 5. Publish
        self.publisher.publish("pi/inference/result", json.dumps(result))

        if result.get("error"):
            log.warning(f"Inference published with error: {result['error']}")
        else:
            log.info(
                f"Inference published → disease={result.get('disease')} "
                f"severity={result.get('severity')} dosage={result.get('dosage_ml')} ml/m²"
            )
        return result

    def _publish_error(self, error_msg: str):
        self.publisher.publish("pi/inference/result", json.dumps({
            "disease":    "unknown",
            "confidence": 0.0,
            "severity":   "none",
            "dosage_ml":  0.0,
            "error":      error_msg,
            "timestamp":  time.time(),
        }))
