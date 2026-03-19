"""
api/routes_logs.py
GET  /logs/            — paginated logs with level + source filtering
GET  /logs/export      — download as CSV
POST /logs/            — create a log entry (from frontend or tests)
DELETE /logs/clear     — clear logs older than N days
"""
import csv
import io
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import SystemLog
from api.schemas import LogOut

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=list[LogOut])
def get_logs(
    limit:   int           = Query(default=100, ge=1,  le=1000),
    offset:  int           = Query(default=0,   ge=0),
    level:   Optional[str] = Query(default=None, description="Filter: DEBUG|INFO|WARN|ERROR"),
    source:  Optional[str] = Query(default=None, description="Filter by source module"),
    hours:   int           = Query(default=24,   ge=1, le=720),
    search:  Optional[str] = Query(default=None, description="Search in message text"),
    db: Session = Depends(get_db),
):
    """Return paginated, filterable system logs."""
    since = datetime.utcnow() - timedelta(hours=hours)
    q = db.query(SystemLog).filter(SystemLog.created_at >= since)

    if level:
        q = q.filter(SystemLog.level == level.upper())
    if source:
        q = q.filter(SystemLog.source.ilike(f"%{source}%"))
    if search:
        q = q.filter(SystemLog.message.ilike(f"%{search}%"))

    return q.order_by(SystemLog.id.desc()).offset(offset).limit(limit).all()


@router.get("/export")
def export_logs(
    hours: int           = Query(default=24, ge=1, le=720),
    level: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Stream logs as a CSV download."""
    since = datetime.utcnow() - timedelta(hours=hours)
    q = db.query(SystemLog).filter(SystemLog.created_at >= since)
    if level:
        q = q.filter(SystemLog.level == level.upper())
    rows = q.order_by(SystemLog.created_at.asc()).all()

    def generate():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "level", "source", "message", "created_at"])
        yield buf.getvalue()
        for r in rows:
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow([r.id, r.level, r.source or "", r.message, r.created_at.isoformat()])
            yield buf.getvalue()

    filename = f"agriwatch_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/", response_model=LogOut, status_code=201)
def create_log(
    level:   str,
    message: str,
    source:  Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Manually create a log entry (useful for frontend-side events)."""
    entry = SystemLog(level=level.upper(), message=message, source=source)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/clear")
def clear_old_logs(
    days: int = Query(default=7, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Delete logs older than `days` days. Returns count deleted."""
    cutoff  = datetime.utcnow() - timedelta(days=days)
    deleted = db.query(SystemLog).filter(SystemLog.created_at < cutoff).delete()
    db.commit()
    log.info(f"Cleared {deleted} log entries older than {days} days.")
    return {"deleted": deleted, "cutoff": cutoff.isoformat()}
