"""
api/routes_motor.py
POST /motor/on            — turn pump on (manual mode)
POST /motor/off           — turn pump off
GET  /motor/status        — current motor state
GET  /motor/history       — paginated motor events
GET  /motor/stats         — total spray today / this week
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import paho.mqtt.publish as mqtt_publish
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from db.database import get_db
from db.models import MotorEvent, SystemConfig, SystemLog
from api.schemas import MotorCommandIn, MotorEventOut

log = logging.getLogger(__name__)
router = APIRouter()

# In-memory motor state (also stored in DB via events)
_motor_state = {"running": False, "started_at": None, "dosage_ml": 0.0}


def _publish(topic: str, payload: dict):
    try:
        mqtt_publish.single(
            topic,
            json.dumps(payload),
            hostname=settings.MQTT_BROKER_IP,
            port=settings.MQTT_PORT,
            qos=1,
        )
    except Exception as e:
        log.error(f"MQTT publish error on '{topic}': {e}")
        raise HTTPException(status_code=503, detail=f"MQTT broker unreachable: {e}")


def _get_mode(db: Session) -> str:
    cfg = db.query(SystemConfig).filter(SystemConfig.key == "mode").first()
    return cfg.value if cfg else "auto"


@router.post("/on")
def motor_on(cmd: MotorCommandIn, db: Session = Depends(get_db)):
    """Turn the spray pump ON. Only allowed in manual mode."""
    mode = _get_mode(db)
    if mode != "manual":
        raise HTTPException(
            status_code=403,
            detail=f"Motor can only be manually controlled in 'manual' mode. Current mode: '{mode}'."
        )
    if _motor_state["running"]:
        return {"status": "already_running", "started_at": _motor_state["started_at"]}

    _publish("server/motor/cmd", {"cmd": "on", "dosage_ml": cmd.dosage_ml, "trigger": cmd.trigger})

    _motor_state.update({"running": True, "started_at": datetime.utcnow().isoformat(), "dosage_ml": cmd.dosage_ml})

    event = MotorEvent(event_type="on", trigger=cmd.trigger, dosage_ml=cmd.dosage_ml)
    db.add(event)
    db.add(SystemLog(level="INFO", message=f"Motor ON — dosage={cmd.dosage_ml} ml/m² trigger={cmd.trigger}", source="routes_motor"))
    db.commit()

    log.info(f"Motor ON: dosage={cmd.dosage_ml} ml/m²")
    return {"status": "motor_on", "dosage_ml": cmd.dosage_ml, "started_at": _motor_state["started_at"]}


@router.post("/off")
def motor_off(db: Session = Depends(get_db)):
    """Turn the spray pump OFF."""
    _publish("server/motor/cmd", {"cmd": "off"})

    _motor_state.update({"running": False, "started_at": None, "dosage_ml": 0.0})

    event = MotorEvent(event_type="off", trigger="manual")
    db.add(event)
    db.add(SystemLog(level="INFO", message="Motor OFF", source="routes_motor"))
    db.commit()

    log.info("Motor OFF")
    return {"status": "motor_off"}


@router.get("/status")
def motor_status(db: Session = Depends(get_db)):
    """Return current motor state and mode."""
    return {
        "running":    _motor_state["running"],
        "started_at": _motor_state["started_at"],
        "dosage_ml":  _motor_state["dosage_ml"],
        "mode":       _get_mode(db),
    }


@router.get("/history", response_model=list[MotorEventOut])
def motor_history(
    limit:  int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0,  ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(MotorEvent)
        .order_by(MotorEvent.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/stats")
def motor_stats(db: Session = Depends(get_db)):
    """Total spray volume today and this week."""
    now   = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week  = now - timedelta(days=7)

    def _sum(since):
        r = (
            db.query(func.sum(MotorEvent.flow_litres))
            .filter(MotorEvent.event_type.in_(["off", "auto_off"]))
            .filter(MotorEvent.recorded_at >= since)
            .scalar()
        )
        return round(r or 0.0, 3)

    def _count(since):
        return (
            db.query(func.count(MotorEvent.id))
            .filter(MotorEvent.event_type.in_(["on", "auto_on"]))
            .filter(MotorEvent.recorded_at >= since)
            .scalar() or 0
        )

    return {
        "today":       {"litres": _sum(today),   "sessions": _count(today)},
        "this_week":   {"litres": _sum(week),    "sessions": _count(week)},
    }
