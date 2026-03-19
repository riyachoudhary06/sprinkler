"""
api/routes_camera.py
GET  /camera/stream-url       — return MJPEG stream URL
POST /camera/capture          — trigger Pi to take a snapshot via MQTT
GET  /camera/captures         — list saved capture files
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import paho.mqtt.publish as mqtt_publish
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import settings
from db.database import get_db
from db.models import SystemLog

log = logging.getLogger(__name__)
router = APIRouter()

# Captures directory (should match Pi's SAVE_DIR via shared mount or SCP)
CAPTURES_DIR = Path("/captures")


@router.get("/stream-url")
def get_stream_url():
    """Return the MJPEG stream URL hosted by the Raspberry Pi."""
    return {
        "url":        f"http://{settings.PI_HOST}:8080/stream",
        "host":       settings.PI_HOST,
        "port":       8080,
        "format":     "MJPEG",
        "resolution": "640x480",
    }


@router.post("/capture")
def trigger_capture(db: Session = Depends(get_db)):
    """
    Send an MQTT command to the Pi to take a snapshot immediately.
    The Pi will save to disk and publish the path back via pi/inference/result.
    """
    try:
        mqtt_publish.single(
            "server/camera/capture",
            json.dumps({"cmd": "capture", "ts": datetime.utcnow().isoformat()}),
            hostname=settings.MQTT_BROKER_IP,
            port=settings.MQTT_PORT,
            qos=1,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MQTT broker unreachable: {e}")

    db.add(SystemLog(
        level="INFO",
        message="Manual capture triggered via API",
        source="routes_camera",
    ))
    db.commit()

    log.info("Camera capture triggered.")
    return {"status": "capture_triggered", "timestamp": datetime.utcnow().isoformat()}


@router.get("/captures")
def list_captures(limit: int = 20):
    """
    List the most recent capture image files.
    Returns filenames only; actual images served by the Pi's HTTP server or shared mount.
    """
    if not CAPTURES_DIR.exists():
        return {"captures": [], "note": "Capture directory not mounted"}

    files = sorted(CAPTURES_DIR.glob("*.jpg"), key=lambda f: f.stat().st_mtime, reverse=True)
    return {
        "captures": [
            {
                "filename": f.name,
                "size_kb":  round(f.stat().st_size / 1024, 1),
                "captured_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            }
            for f in files[:limit]
        ],
        "total": len(files),
    }
