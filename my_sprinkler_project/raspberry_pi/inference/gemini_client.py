"""
inference/gemini_client.py
Sends a base64-encoded JPEG to the Gemini Vision API and parses the
structured JSON response for plant disease analysis.
"""
import json
import logging
import re
import google.generativeai as genai

from inference.prompt_builder import build_prompt

log = logging.getLogger(__name__)

REQUIRED_KEYS = {"disease", "confidence", "severity", "affected_area",
                 "recommendation", "pesticide", "dosage_ml"}


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        log.info(f"GeminiClient init: model={model}")

    def analyze(self, b64_image: str, sensor_context: dict) -> dict:
        """
        Send image + sensor context to Gemini.

        Returns a dict with these keys (all always present):
            disease, confidence, severity, affected_area,
            recommendation, pesticide, dosage_ml, error
        """
        default = {
            "disease": "unknown", "confidence": 0.0, "severity": "none",
            "affected_area": 0.0, "recommendation": "", "pesticide": "none",
            "dosage_ml": 0.0, "error": "",
        }

        if not b64_image:
            default["error"] = "empty_image"
            return default

        try:
            prompt = build_prompt(sensor_context)
            image_part = {
                "mime_type": "image/jpeg",
                "data": b64_image,
            }
            response = self.model.generate_content(
                [prompt, image_part],
                generation_config={"temperature": 0.1},   # low temp for deterministic JSON
            )
            raw = response.text.strip()
            result = self._parse(raw)
            result.setdefault("error", "")

            # Validate required keys
            missing = REQUIRED_KEYS - result.keys()
            if missing:
                log.warning(f"Gemini response missing keys: {missing}")
                for k in missing:
                    result[k] = default[k]

            log.info(
                f"Gemini: disease={result['disease']} "
                f"conf={result['confidence']:.2f} "
                f"severity={result['severity']} "
                f"dosage={result['dosage_ml']} ml/m²"
            )
            return result

        except Exception as e:
            log.error(f"GeminiClient.analyze() error: {e}", exc_info=True)
            default["error"] = str(e)
            return default

    @staticmethod
    def _parse(raw: str) -> dict:
        """
        Extract JSON from the raw Gemini response.
        Handles markdown code fences gracefully.
        """
        # Strip ```json ... ``` or ``` ... ``` fences
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())

        # Extract the first {...} block in case there's surrounding prose
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON object found in response: {raw[:200]}")

        return json.loads(match.group())
