"""
inference/prompt_builder.py
Builds a structured Gemini Vision prompt that embeds live sensor context.
The prompt instructs Gemini to return a strict JSON object — no markdown,
no prose — so the response can be reliably parsed.
"""


def build_prompt(sensor_context: dict) -> str:
    """
    Build a plant pathology prompt with embedded sensor readings.

    sensor_context keys (all optional, show 'N/A' if missing):
        ph, moisture, humidity, temperature, nitrogen, phosphorus, potassium, light_lux
    """
    def _fmt(key: str, decimals: int = 1) -> str:
        val = sensor_context.get(key)
        if val is None or (isinstance(val, float) and val < 0):
            return "N/A"
        return f"{round(val, decimals)}"

    prompt = f"""\
You are an expert plant pathologist AI integrated into an IoT precision-agriculture system.

Analyse the attached image of a plant leaf/crop together with the current field sensor data:

  Soil pH          : {_fmt('ph', 2)}
  Soil Moisture    : {_fmt('moisture')}%
  Air Humidity     : {_fmt('humidity')}%
  Air Temperature  : {_fmt('temperature')}°C
  Nitrogen (N)     : {_fmt('nitrogen', 0)} mg/kg
  Phosphorus (P)   : {_fmt('phosphorus', 0)} mg/kg
  Potassium (K)    : {_fmt('potassium', 0)} mg/kg
  Ambient Light    : {_fmt('light_lux', 0)} lux

Task:
1. Identify the most likely plant disease visible in the image (or classify as "healthy").
2. Estimate the severity and the percentage of visible leaf area affected.
3. Recommend the most appropriate registered pesticide or treatment.
4. Suggest a spray dosage in ml per m² appropriate for the severity.

Return ONLY a valid JSON object — no markdown fences, no explanatory text, no trailing commas:
{{
  "disease":        "<disease name or 'healthy'>",
  "confidence":     <float 0.0–1.0>,
  "severity":       "<none|low|medium|high>",
  "affected_area":  <float 0–100>,
  "recommendation": "<one concise action sentence>",
  "pesticide":      "<pesticide name or 'none'>",
  "dosage_ml":      <float ml per m², 0 if healthy>
}}
"""
    return prompt
