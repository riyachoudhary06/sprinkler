"""
api/routes_disease.py
GET  /disease/latest          — most recent Gemini inference result
GET  /disease/predictions     — paginated history of all predictions
GET  /disease/summary         — count by disease name / severity
DELETE /disease/{id}          — remove a specific result
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import DiseaseResult
from api.schemas import DiseaseResultOut

router = APIRouter()


@router.get("/latest", response_model=Optional[DiseaseResultOut])
def get_latest(db: Session = Depends(get_db)):
    """Return the most recent disease inference result."""
    return db.query(DiseaseResult).order_by(DiseaseResult.id.desc()).first()


@router.get("/predictions", response_model=list[DiseaseResultOut])
def get_predictions(
    limit:    int           = Query(default=50, ge=1, le=500),
    offset:   int           = Query(default=0,  ge=0),
    hours:    int           = Query(default=168, ge=1, le=2160),  # default 7 days
    severity: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Return paginated disease prediction history."""
    since = datetime.utcnow() - timedelta(hours=hours)
    q = (
        db.query(DiseaseResult)
        .filter(DiseaseResult.recorded_at >= since)
    )
    if severity:
        q = q.filter(DiseaseResult.severity == severity)
    return q.order_by(DiseaseResult.id.desc()).offset(offset).limit(limit).all()


@router.get("/summary")
def get_summary(
    hours: int = Query(default=168, ge=1, le=2160),
    db: Session = Depends(get_db),
):
    """Return counts grouped by disease name and by severity."""
    since = datetime.utcnow() - timedelta(hours=hours)

    by_disease = (
        db.query(DiseaseResult.disease, func.count(DiseaseResult.id).label("count"))
        .filter(DiseaseResult.recorded_at >= since)
        .group_by(DiseaseResult.disease)
        .all()
    )
    by_severity = (
        db.query(DiseaseResult.severity, func.count(DiseaseResult.id).label("count"))
        .filter(DiseaseResult.recorded_at >= since)
        .group_by(DiseaseResult.severity)
        .all()
    )
    return {
        "hours":       hours,
        "by_disease":  [{"disease": r.disease, "count": r.count}  for r in by_disease],
        "by_severity": [{"severity": r.severity, "count": r.count} for r in by_severity],
    }


@router.get("/{result_id}", response_model=DiseaseResultOut)
def get_by_id(result_id: int, db: Session = Depends(get_db)):
    row = db.query(DiseaseResult).filter(DiseaseResult.id == result_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")
    return row


@router.delete("/{result_id}")
def delete_result(result_id: int, db: Session = Depends(get_db)):
    row = db.query(DiseaseResult).filter(DiseaseResult.id == result_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")
    db.delete(row)
    db.commit()
    return {"deleted": result_id}
