"""
api/routes_mode.py
GET  /mode         — get current system mode
POST /mode         — set system mode  {"mode": "auto"|"manual"}
"""
import json
import logging
from datetime import datetime

import paho.mqtt.publish as mqtt_publish
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import settings
from db.database import get_db
from db.models import SystemConfig, SystemLog
from api.schemas import ModeIn, ModeOut

log = logging.getLogger(__name__)
router = APIRouter()


def _get_or_create_mode(db: Session) -> SystemConfig:
    cfg = db.query(SystemConfig).filter(SystemConfig.key == "mode").first()
    if not cfg:
        cfg = SystemConfig(key="mode", value="auto")
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


@router.get("/", response_model=ModeOut)
def get_mode(db: Session = Depends(get_db)):
    cfg = _get_or_create_mode(db)
    return ModeOut(mode=cfg.value, updated_at=cfg.updated_at)


@router.post("/", response_model=ModeOut)
def set_mode(body: ModeIn, db: Session = Depends(get_db)):
    cfg = _get_or_create_mode(db)
    old_mode = cfg.value
    cfg.value      = body.mode
    cfg.updated_at = datetime.utcnow()

    db.add(SystemLog(
        level="INFO",
        message=f"Mode changed: {old_mode} → {body.mode}",
        source="routes_mode",
    ))
    db.commit()

    # Broadcast to Pi and ESP32
    try:
        mqtt_publish.single(
            "server/mode",
            json.dumps({"mode": body.mode}),
            hostname=settings.MQTT_BROKER_IP,
            port=settings.MQTT_PORT,
            qos=1,
        )
    except Exception as e:
        log.warning(f"Mode MQTT publish failed: {e}")
        # Don't raise — mode is saved to DB, Pi will pick it up on reconnect

    log.info(f"Mode set to: {body.mode}")
    return ModeOut(mode=body.mode, updated_at=cfg.updated_at)
