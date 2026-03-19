"""
db/models.py — SQLAlchemy ORM models.

Tables:
  sensor_readings  — time-series from Pi sensor manager
  disease_results  — Gemini Vision API inference results
  motor_events     — spray start/stop events with flow data
  system_logs      — structured log messages from Pi and backend
  system_config    — key-value store for runtime config (mode, thresholds)
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, Float, String, Text, Boolean, DateTime, JSON, Index
)

from db.database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id            = Column(Integer, primary_key=True, index=True)
    ph            = Column(Float, nullable=True)
    moisture      = Column(Float, nullable=True)   # %
    nitrogen      = Column(Float, nullable=True)   # mg/kg
    phosphorus    = Column(Float, nullable=True)   # mg/kg
    potassium     = Column(Float, nullable=True)   # mg/kg
    temperature   = Column(Float, nullable=True)   # °C
    humidity      = Column(Float, nullable=True)   # %
    light_lux     = Column(Float, nullable=True)   # lux
    pi_timestamp  = Column(Float, nullable=True)   # unix ts from Pi
    recorded_at   = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_sensor_readings_recorded_at", "recorded_at"),
    )


class DiseaseResult(Base):
    __tablename__ = "disease_results"

    id             = Column(Integer, primary_key=True, index=True)
    disease        = Column(String(128), nullable=False, default="unknown")
    confidence     = Column(Float, nullable=True)         # 0.0–1.0
    severity       = Column(String(32), nullable=True)    # none/low/medium/high
    affected_area  = Column(Float, nullable=True)         # %
    recommendation = Column(Text, nullable=True)
    pesticide      = Column(String(128), nullable=True)
    dosage_ml      = Column(Float, nullable=True)         # ml/m²
    image_path     = Column(String(256), nullable=True)
    sensor_context = Column(JSON, nullable=True)          # snapshot of sensor values at time of inference
    gemini_error   = Column(String(256), nullable=True)   # populated if API failed
    recorded_at    = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_disease_results_recorded_at", "recorded_at"),
    )


class MotorEvent(Base):
    __tablename__ = "motor_events"

    id            = Column(Integer, primary_key=True, index=True)
    event_type    = Column(String(16), nullable=False)    # "on" | "off" | "auto_on" | "auto_off"
    trigger       = Column(String(32), nullable=True)     # "manual" | "schedule" | "auto_disease"
    dosage_ml     = Column(Float, nullable=True)
    flow_litres   = Column(Float, nullable=True)          # populated when motor stops
    duration_sec  = Column(Integer, nullable=True)        # populated when motor stops
    recorded_at   = Column(DateTime, default=datetime.utcnow, index=True)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id          = Column(Integer, primary_key=True, index=True)
    level       = Column(String(16), nullable=False, default="INFO")   # DEBUG/INFO/WARN/ERROR
    message     = Column(Text, nullable=False)
    source      = Column(String(64), nullable=True)     # e.g. "sensor_manager", "disease_detector"
    extra       = Column(JSON, nullable=True)            # any structured metadata
    created_at  = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_system_logs_level", "level"),
        Index("ix_system_logs_created_at", "created_at"),
    )


class SystemConfig(Base):
    __tablename__ = "system_config"

    id          = Column(Integer, primary_key=True)
    key         = Column(String(64), unique=True, nullable=False, index=True)
    value       = Column(Text, nullable=False)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
