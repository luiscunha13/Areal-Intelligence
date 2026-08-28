"""
api/routers/macro.py
─────────────────────
Macro indicators API — replaces the old /api/macro routes.
All data served from pre-computed production tables.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.database import get_db

router = APIRouter()


@router.get("/series")
def list_series(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
):
    """List all active macro series from the catalog."""
    sql = "SELECT series_id, name, category, frequency, unit, display_color FROM macro_series WHERE is_active = true"
    params = {}
    if category:
        sql += " AND category = :category"
        params["category"] = category
    sql += " ORDER BY category, name"
    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/series/{series_id}")
def get_series_detail(series_id: str, db: Session = Depends(get_db)):
    """Get catalog metadata for a single series."""
    row = db.execute(
        text("SELECT * FROM macro_series WHERE series_id = :sid"),
        {"sid": series_id}
    ).mappings().first()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Series {series_id} not found")
    return dict(row)


@router.get("/series/{series_id}/observations")
def get_observations(
    series_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(500, le=5000),
    db: Session = Depends(get_db),
):
    """
    Return time-series observations for a single macro series.
    Includes computed features (MoM, YoY, z-score, trend) when available.
    """
    sql = """
        SELECT
            o.date,
            o.value,
            f.value_mom_1m,
            f.value_mom_3m,
            f.value_yoy,
            f.z_score_2y,
            f.z_score_5y,
            f.trend
        FROM macro_observations o
        LEFT JOIN macro_features f
            ON f.series_id = o.series_id AND f.date = o.date
        WHERE o.series_id = :sid
    """
    params: dict = {"sid": series_id}
    if start_date:
        sql += " AND o.date >= :start_date"
        params["start_date"] = start_date
    if end_date:
        sql += " AND o.date <= :end_date"
        params["end_date"] = end_date
    sql += " ORDER BY o.date DESC LIMIT :limit"
    params["limit"] = limit

    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/regime")
def get_regime(
    limit: int = Query(252, le=2000),
    db: Session = Depends(get_db),
):
    """Return market regime history (most recent first)."""
    rows = db.execute(text("""
        SELECT
            date, quadrant, growth_momentum, inflation_momentum,
            fca_score, policy_stance, confidence, scoring_version
        FROM market_regimes
        ORDER BY date DESC
        LIMIT :limit
    """), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/regime/current")
def get_current_regime(db: Session = Depends(get_db)):
    """Return the most recent regime classification."""
    row = db.execute(text("""
        SELECT *
        FROM market_regimes
        ORDER BY date DESC
        LIMIT 1
    """)).mappings().first()
    return dict(row) if row else {}


@router.get("/features/{series_id}")
def get_features(
    series_id: str,
    limit: int = Query(252, le=2000),
    db: Session = Depends(get_db),
):
    """Return computed features (z-scores, momentum) for a series."""
    rows = db.execute(text("""
        SELECT *
        FROM macro_features
        WHERE series_id = :sid
        ORDER BY date DESC
        LIMIT :limit
    """), {"sid": series_id, "limit": limit}).mappings().all()
    return [dict(r) for r in rows]
