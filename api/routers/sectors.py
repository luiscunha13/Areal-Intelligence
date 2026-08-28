"""
api/routers/sectors.py
───────────────────────
Sector Rotation Engine API.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.database import get_db

router = APIRouter()


@router.get("/")
def list_sectors(db: Session = Depends(get_db)):
    """List all GICS sectors with their ETF mapping."""
    rows = db.execute(text(
        "SELECT * FROM sectors WHERE is_active = true ORDER BY name"
    )).mappings().all()
    return [dict(r) for r in rows]


@router.get("/scores")
def get_sector_scores(
    horizon: str = Query("tactical_50d", description="tactical_50d | strategic_260d"),
    as_of: Optional[date] = Query(None, description="Scores as of date (default: latest)"),
    db: Session = Depends(get_db),
):
    """
    Return sector RRG scores for all 11 GICS sectors.
    Returns the latest available scores if as_of is not specified.
    """
    if as_of:
        date_filter = "AND ss.date = :as_of"
        params = {"horizon": horizon, "as_of": as_of}
    else:
        # Get the latest date available for this horizon
        date_filter = """
            AND ss.date = (
                SELECT MAX(date) FROM sector_scores
                WHERE horizon = :horizon
            )
        """
        params = {"horizon": horizon}

    rows = db.execute(text(f"""
        SELECT
            ss.ticker,
            ss.date,
            ss.horizon,
            ss.rs_ratio,
            ss.rs_momentum,
            ss.rrg_quadrant,
            ss.composite_score,
            ss.rank,
            s.name as sector_name
        FROM sector_scores ss
        LEFT JOIN sectors s ON s.etf_ticker = ss.ticker
        WHERE ss.horizon = :horizon
        {date_filter}
        ORDER BY ss.composite_score DESC
    """), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/scores/{ticker}/history")
def get_sector_score_history(
    ticker: str,
    horizon: str = Query("tactical_50d"),
    limit: int = Query(252, le=1000),
    db: Session = Depends(get_db),
):
    """Return RRG score history for a single sector ETF."""
    rows = db.execute(text("""
        SELECT date, horizon, rs_ratio, rs_momentum, rrg_quadrant, composite_score, rank
        FROM sector_scores
        WHERE ticker = :ticker AND horizon = :horizon
        ORDER BY date DESC
        LIMIT :limit
    """), {"ticker": ticker, "horizon": horizon, "limit": limit}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/prices/{ticker}")
def get_sector_prices(
    ticker: str,
    limit: int = Query(260, le=1000),
    db: Session = Depends(get_db),
):
    """Return raw price history for a sector ETF."""
    rows = db.execute(text("""
        SELECT date, open, high, low, close, adj_close, volume
        FROM prices
        WHERE ticker = :ticker
        ORDER BY date DESC
        LIMIT :limit
    """), {"ticker": ticker, "limit": limit}).mappings().all()
    return [dict(r) for r in rows]
