"""
api/routes_sensors.py
GET  /sensors/latest          — most recent sensor reading
GET  /sensors/history         — paginated time-series (limit, offset, hours)
GET  /sensors/stats           — min/avg/max per field over last N hours
GET  /sensors/alerts          — current out-of-range values
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import SensorReading
from api.schemas import SensorReadingOut

router = APIRouter()

SENSOR_FIELDS = ["ph", "moisture", "nitrogen", "phosphorus", "potassium",
                 "temperature", "humidity", "light_lux"]

THRESHOLDS = {
    "ph":          (5.5,  7.5),
    "moisture":    (40.0, 80.0),
    "humidity":    (30.0, 90.0),
    "temperature": (15.0, 35.0),
}


@router.get("/latest", response_model=Optional[SensorReadingOut])
def get_latest(db: Session = Depends(get_db)):
    """Return the most recent sensor reading."""
    return db.query(SensorReading).order_by(SensorReading.id.desc()).first()


@router.get("/history", response_model=list[SensorReadingOut])
def get_history(
    limit:  int = Query(default=100, ge=1,  le=1000),
    offset: int = Query(default=0,   ge=0),
    hours:  int = Query(default=24,  ge=1,  le=720),
    db: Session = Depends(get_db),
):
    """Return time-series sensor readings for the last `hours` hours."""
    since = datetime.utcnow() - timedelta(hours=hours)
    return (
        db.query(SensorReading)
        .filter(SensorReading.recorded_at >= since)
        .order_by(SensorReading.recorded_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/stats")
def get_stats(
    hours: int = Query(default=24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    """Return min/avg/max for each sensor field over the last `hours` hours."""
    since = datetime.utcnow() - timedelta(hours=hours)
    stats = {}
    for field in SENSOR_FIELDS:
        col = getattr(SensorReading, field)
        row = (
            db.query(
                func.min(col).label("min"),
                func.avg(col).label("avg"),
                func.max(col).label("max"),
                func.count(col).label("count"),
            )
            .filter(SensorReading.recorded_at >= since)
            .filter(col.isnot(None))
            .first()
        )
        stats[field] = {
            "min":   round(row.min, 2)  if row.min is not None else None,
            "avg":   round(row.avg, 2)  if row.avg is not None else None,
            "max":   round(row.max, 2)  if row.max is not None else None,
            "count": row.count,
        }
    return {"hours": hours, "stats": stats}


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    """Return alert status based on the latest sensor reading."""
    latest = db.query(SensorReading).order_by(SensorReading.id.desc()).first()
    if not latest:
        return {"alerts": [], "latest": None}

    alerts = []
    for sensor, (lo, hi) in THRESHOLDS.items():
        val = getattr(latest, sensor)
        if val is None or val < 0:
            continue
        if val < lo:
            alerts.append({"sensor": sensor, "value": val, "type": "below_threshold", "threshold": lo})
        elif val > hi:
            alerts.append({"sensor": sensor, "value": val, "type": "above_threshold", "threshold": hi})

    return {"alerts": alerts, "count": len(alerts), "latest_at": latest.recorded_at}
