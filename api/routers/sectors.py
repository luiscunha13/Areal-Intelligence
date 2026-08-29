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


QUADRANT_REGIME_FIT = {
    "reflation": {
        "XLK": 92, "XLC": 88, "XLY": 85, "XLF": 84, "XLI": 82, "XLB": 72, "XLV": 65, "VNQ": 60, "XLRE": 60, "XLP": 55, "XLE": 50, "XLU": 45,
        "ARKK": 90, "ARKW": 88, "BOTZ": 86, "AIQ": 88, "CLOU": 85, "FINX": 82, "DRIV": 80, "PAVE": 82, "ICLN": 75, "CIBR": 85, "HACK": 85
    },
    "goldilocks": {
        "XLK": 95, "XLC": 92, "XLY": 88, "XLF": 82, "XLI": 80, "XLV": 70, "XLB": 65, "VNQ": 60, "XLRE": 60, "XLP": 50, "XLE": 45, "XLU": 40,
        "ARKK": 95, "ARKW": 94, "BOTZ": 92, "AIQ": 94, "CLOU": 90, "FINX": 88, "DRIV": 85, "PAVE": 80, "ICLN": 80, "CIBR": 90, "HACK": 90
    },
    "overheat": {
        "XLE": 95, "XLB": 90, "XLI": 82, "XLF": 80, "XLP": 65, "XLV": 60, "XLC": 55, "XLK": 50, "XLY": 50, "VNQ": 45, "XLRE": 45, "XLU": 40,
        "PAVE": 88, "ICLN": 70, "ARKK": 35, "ARKW": 35, "BOTZ": 45, "AIQ": 45, "CLOU": 40, "FINX": 45, "CIBR": 60
    },
    "slowdown": {
        "XLV": 92, "XLP": 90, "XLU": 88, "XLC": 75, "VNQ": 70, "XLRE": 70, "XLF": 60, "XLK": 55, "XLI": 50, "XLY": 45, "XLB": 45, "XLE": 40,
        "CIBR": 80, "HACK": 80, "CLOU": 65, "ARKK": 45, "ARKW": 45, "BOTZ": 50, "AIQ": 55, "FINX": 50
    },
    "stagflation": {
        "XLE": 95, "XLB": 90, "XLP": 82, "XLV": 78, "XLU": 75, "XLI": 60, "XLF": 50, "XLC": 50, "VNQ": 45, "XLRE": 45, "XLK": 40, "XLY": 35,
        "PAVE": 70, "CIBR": 65, "HACK": 65, "ICLN": 50, "ARKK": 25, "ARKW": 25, "BOTZ": 30, "AIQ": 35, "CLOU": 30, "FINX": 30
    }
}

def _enrich_sector_score(r: dict, active_quadrant: str = "reflation") -> dict:
    if not r:
        return {}
    d = dict(r)
    rs = float(d.get("rs_ratio") or 100.0)
    mom = float(d.get("rs_momentum") or 100.0)
    
    rel_strength_score = round(min(98.0, max(20.0, (rs - 90.0) * 4.5)), 1)
    momentum_score = round(min(98.0, max(20.0, (mom - 90.0) * 4.5)), 1)
    trend_score = round(min(98.0, max(20.0, rel_strength_score * 0.55 + momentum_score * 0.45)), 1)
    
    ticker = (d.get("ticker") or d.get("symbol") or "").upper()
    quad_map = QUADRANT_REGIME_FIT.get(active_quadrant.lower(), QUADRANT_REGIME_FIT["reflation"])
    regime_fit_score = quad_map.get(ticker, 75)

    risk_score = round(min(98.0, max(30.0, 100.0 - abs(mom - 100.0) * 2.5)), 1)
    # breadth_estimate and surprise_estimate are RS-derived approximations (no constituent or earnings data)
    breadth_estimate = round(min(98.0, max(30.0, rel_strength_score * 0.6 + 35.0)), 1)
    fundamental_score = round(min(98.0, max(30.0, trend_score * 0.5 + regime_fit_score * 0.5)), 1)
    surprise_estimate = round(min(98.0, max(30.0, momentum_score * 0.45 + 40.0)), 1)

    overall_sc = round(min(98.0, max(20.0, (rel_strength_score * 0.3 + momentum_score * 0.3 + trend_score * 0.2 + regime_fit_score * 0.2))), 1)

    d["raw_composite_score"] = float(d.get("composite_score") or 0)
    d["composite_score"] = overall_sc
    d["overall_score"] = overall_sc
    d["scores"] = {
        "relative_strength": rel_strength_score,
        "momentum": momentum_score,
        "trend": trend_score,
        "regime_fit": regime_fit_score,
        "risk": risk_score,
        "breadth_estimate": breadth_estimate,
        "fundamental": fundamental_score,
        "surprise_estimate": surprise_estimate,
    }
    d["classification"] = (d.get("rrg_quadrant") or "leading").upper()
    return d


@router.get("/scores")
@router.get("/ranking")
def get_sector_scores(
    horizon: str = Query("tactical_50d", description="tactical_50d | strategic_260d"),
    scope: Optional[str] = Query("all", description="all | level1"),
    as_of: Optional[date] = Query(None, description="Scores as of date (default: latest)"),
    db: Session = Depends(get_db),
):
    """
    Return sector/ETF RRG scores across horizons (tactical_50d vs strategic_260d) and scopes.
    """
    h_str = horizon.lower()
    if "strategic" in h_str or "260" in h_str:
        horizon_val = "strategic_260d"
    else:
        horizon_val = "tactical_50d"

    scope_clause = ""
    if scope == "level1":
        scope_clause = "AND ss.ticker IN ('XLK','XLF','XLE','XLV','XLI','XLY','XLP','XLU','XLRE','XLC','XLB')"
    else:
        # All scope returns the 27 Core Sector & Industry/Subsector ETFs
        scope_clause = "AND (e.category IN ('sector', 'thematic') OR ss.ticker IN ('XLK','XLF','XLE','XLV','XLI','XLY','XLP','XLU','XLRE','XLC','XLB','VNQ'))"

    if as_of:
        date_filter = "AND ss.date = :as_of"
        params = {"horizon": horizon_val, "as_of": as_of}
    else:
        date_filter = """
            AND ss.date = (
                SELECT MAX(date) FROM sector_scores
                WHERE horizon = :horizon
            )
        """
        params = {"horizon": horizon_val}

    rows = db.execute(text(f"""
        SELECT
            ss.ticker,
            ss.ticker as symbol,
            ss.date,
            ss.horizon,
            ss.rs_ratio,
            ss.rs_momentum,
            ss.rrg_quadrant,
            ss.rrg_quadrant as quadrant,
            ss.composite_score,
            ss.rank,
            COALESCE(e.name, s.name, ss.ticker) as name,
            COALESCE(s.name, e.category, ss.ticker) as sector_name,
            COALESCE(e.category, 'sector') as category,
            CASE WHEN ss.ticker IN ('XLK','XLF','XLE','XLV','XLI','XLY','XLP','XLU','XLRE','XLC','XLB') THEN 1 ELSE 2 END as level
        FROM sector_scores ss
        LEFT JOIN sectors s ON s.etf_ticker = ss.ticker
        LEFT JOIN etfs e ON e.ticker = ss.ticker
        WHERE ss.horizon = :horizon
        {scope_clause}
        {date_filter}
        ORDER BY ss.composite_score DESC
    """), params).mappings().all()

    active_quad = db.execute(text("SELECT quadrant FROM market_regimes ORDER BY date DESC LIMIT 1")).scalar() or "reflation"
    return [_enrich_sector_score(r, active_quadrant=active_quad) for r in rows]


@router.get("/scores/{ticker}/history")
@router.get("/{ticker}/rank-history")
def get_sector_score_history(
    ticker: str,
    horizon: str = Query("tactical_50d"),
    limit: int = Query(252, le=1000),
    db: Session = Depends(get_db),
):
    """Return RRG score history for a single sector ETF."""
    rows = db.execute(text("""
        SELECT date, horizon, rs_ratio, rs_momentum, rrg_quadrant, rrg_quadrant as quadrant, composite_score, rank
        FROM sector_scores
        WHERE (ticker = :ticker OR ticker = (SELECT etf_ticker FROM sectors WHERE etf_ticker = :ticker OR name = :ticker LIMIT 1))
          AND horizon = :horizon
        ORDER BY date DESC
        LIMIT :limit
    """), {"ticker": ticker.upper(), "horizon": horizon, "limit": limit}).mappings().all()
    return [_enrich_sector_score(r) for r in rows]


@router.get("/{ticker}")
def get_sector_detail(
    ticker: str,
    horizon: str = Query("tactical_50d"),
    db: Session = Depends(get_db)
):
    """Return sector detail and current scores for the requested horizon."""
    sector = db.execute(text(
        "SELECT * FROM sectors WHERE etf_ticker = :ticker OR name ILIKE :ticker"
    ), {"ticker": ticker.upper()}).mappings().first()

    h_val = "strategic_260d" if ("strategic" in horizon.lower() or "260" in horizon.lower()) else "tactical_50d"

    score = db.execute(text("""
        SELECT * FROM sector_scores
        WHERE (ticker = :ticker OR ticker = (SELECT etf_ticker FROM sectors WHERE etf_ticker = :ticker OR name ILIKE :ticker LIMIT 1))
          AND horizon = :horizon
        ORDER BY date DESC LIMIT 1
    """), {"ticker": ticker.upper(), "horizon": h_val}).mappings().first()

    active_quad = db.execute(text("SELECT quadrant FROM market_regimes ORDER BY date DESC LIMIT 1")).scalar() or "reflation"
    enriched_score = _enrich_sector_score(score, active_quadrant=active_quad) if score else None

    return {
        "sector": dict(sector) if sector else {"symbol": ticker.upper(), "name": ticker},
        "score": enriched_score,
        "latest_score": enriched_score
    }


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
