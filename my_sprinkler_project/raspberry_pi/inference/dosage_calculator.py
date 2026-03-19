"""
inference/dosage_calculator.py
Maps Gemini's disease severity + affected_area percentage
to a recommended spray volume in ml/m².

Override Gemini's own dosage suggestion with calibrated field values.
"""
import logging

log = logging.getLogger(__name__)

# Base spray dose (ml/m²) per severity level
BASE_DOSE: dict[str, float] = {
    "none":   0.0,
    "low":    10.0,
    "medium": 25.0,
    "high":   50.0,
}

# Hard cap to prevent over-spraying
MAX_DOSE: float = 100.0


def calculate_dosage(gemini_result: dict) -> float:
    """
    Calculate spray volume in ml/m².

    Formula:
        dose = BASE_DOSE[severity] × (1 + affected_area / 100)

    Example:
        severity=medium, affected_area=40%  →  25 × 1.40 = 35.0 ml/m²
        severity=high,   affected_area=80%  →  50 × 1.80 = 90.0 ml/m²

    Returns 0.0 if disease is 'healthy' or severity is 'none'.
    """
    disease  = gemini_result.get("disease", "healthy").lower().strip()
    severity = gemini_result.get("severity", "none").lower().strip()
    area     = float(gemini_result.get("affected_area") or 0.0)

    if disease == "healthy" or severity == "none":
        return 0.0

    base   = BASE_DOSE.get(severity, 10.0)
    scale  = 1.0 + (area / 100.0)
    dosage = round(min(base * scale, MAX_DOSE), 1)

    log.debug(
        f"Dosage: disease={disease} severity={severity} "
        f"area={area}% base={base} → {dosage} ml/m²"
    )
    return dosage
