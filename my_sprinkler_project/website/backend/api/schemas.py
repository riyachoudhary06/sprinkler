"""
api/schemas.py — Pydantic models for request validation and response serialization.
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ── Sensor ────────────────────────────────────────────────────────────────────

class SensorReadingOut(BaseModel):
    id:           int
    ph:           Optional[float]
    moisture:     Optional[float]
    nitrogen:     Optional[float]
    phosphorus:   Optional[float]
    potassium:    Optional[float]
    temperature:  Optional[float]
    humidity:     Optional[float]
    light_lux:    Optional[float]
    recorded_at:  datetime

    class Config:
        from_attributes = True


# ── Disease ───────────────────────────────────────────────────────────────────

class DiseaseResultOut(BaseModel):
    id:             int
    disease:        str
    confidence:     Optional[float]
    severity:       Optional[str]
    affected_area:  Optional[float]
    recommendation: Optional[str]
    pesticide:      Optional[str]
    dosage_ml:      Optional[float]
    image_path:     Optional[str]
    sensor_context: Optional[dict]
    gemini_error:   Optional[str]
    recorded_at:    datetime

    class Config:
        from_attributes = True


# ── Motor ─────────────────────────────────────────────────────────────────────

class MotorCommandIn(BaseModel):
    dosage_ml: float = Field(default=0.0, ge=0, le=200, description="Spray dosage in ml/m²")
    trigger:   str   = Field(default="manual")

class MotorEventOut(BaseModel):
    id:           int
    event_type:   str
    trigger:      Optional[str]
    dosage_ml:    Optional[float]
    flow_litres:  Optional[float]
    duration_sec: Optional[int]
    recorded_at:  datetime

    class Config:
        from_attributes = True


# ── Logs ──────────────────────────────────────────────────────────────────────

class LogOut(BaseModel):
    id:         int
    level:      str
    message:    str
    source:     Optional[str]
    extra:      Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Mode ──────────────────────────────────────────────────────────────────────

class ModeIn(BaseModel):
    mode: str = Field(..., pattern="^(auto|manual)$")

class ModeOut(BaseModel):
    mode:       str
    updated_at: Optional[datetime]


# ── Thresholds ────────────────────────────────────────────────────────────────

class ThresholdIn(BaseModel):
    sensor: str
    min:    float
    max:    float


# ── Alerts ────────────────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    sensor:    str
    value:     float
    type:      str
    threshold: float
