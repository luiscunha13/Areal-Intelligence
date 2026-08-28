"""
api/routers/stocks.py
──────────────────────
Stock Screener + Detail API.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.database import get_db

router = APIRouter()


@router.get("/")
def list_stocks(
    sector: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by ticker or name"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """List active stocks with optional sector/search filter."""
    sql = "SELECT ticker, name, sector, industry, market_cap_tier, exchange FROM stocks WHERE is_active = true"
    params: dict = {"limit": limit, "offset": offset}

    if sector:
        sql += " AND sector = :sector"
        params["sector"] = sector
    if search:
        sql += " AND (ticker ILIKE :search OR name ILIKE :search)"
        params["search"] = f"%{search}%"

    sql += " ORDER BY ticker LIMIT :limit OFFSET :offset"
    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/screener")
def screener(
    sector: Optional[str] = Query(None),
    classification: Optional[str] = Query(None, description="leading | improving | weakening | lagging"),
    min_score: Optional[float] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """
    Multi-factor stock screener — returns latest scored stocks with filters.
    """
    clauses = ["ss.date = (SELECT MAX(date) FROM stock_scores)"]
    params: dict = {"limit": limit}

    if sector:
        clauses.append("s.sector = :sector")
        params["sector"] = sector
    if classification:
        clauses.append("ss.classification = :classification")
        params["classification"] = classification
    if min_score is not None:
        clauses.append("ss.composite_score >= :min_score")
        params["min_score"] = min_score

    where = " AND ".join(clauses)

    rows = db.execute(text(f"""
        SELECT
            ss.ticker,
            ss.date,
            ss.composite_score,
            ss.momentum_score,
            ss.trend_score,
            ss.quality_score,
            ss.value_score,
            ss.classification,
            ss.rank_overall,
            ss.rank_sector,
            s.name,
            s.sector,
            s.industry,
            p.close  as latest_price,
            ss.pe_ratio,
            ss.pb_ratio,
            ss.roe,
            ss.ret_1m,
            ss.ret_3m,
            ss.ret_12m
        FROM stock_scores ss
        JOIN stocks s ON s.ticker = ss.ticker
        LEFT JOIN LATERAL (
            SELECT close FROM prices
            WHERE ticker = ss.ticker
            ORDER BY date DESC LIMIT 1
        ) p ON true
        WHERE {where}
        ORDER BY ss.composite_score DESC
        LIMIT :limit
    """), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/sectors")
def get_stock_sectors(db: Session = Depends(get_db)):
    """Return distinct sectors with stock counts."""
    rows = db.execute(text("""
        SELECT sector, COUNT(*) as count
        FROM stocks WHERE is_active = true AND sector IS NOT NULL
        GROUP BY sector ORDER BY sector
    """)).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{ticker}")
def get_stock_detail(ticker: str, db: Session = Depends(get_db)):
    """Full stock detail — metadata + latest score + price history + fundamentals."""
    stock = db.execute(
        text("SELECT * FROM stocks WHERE ticker = :ticker"),
        {"ticker": ticker.upper()}
    ).mappings().first()

    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    score = db.execute(text("""
        SELECT * FROM stock_scores WHERE ticker = :ticker
        ORDER BY date DESC LIMIT 1
    """), {"ticker": ticker.upper()}).mappings().first()

    prices = db.execute(text("""
        SELECT date, open, high, low, close, adj_close, volume
        FROM prices WHERE ticker = :ticker
        ORDER BY date DESC LIMIT 252
    """), {"ticker": ticker.upper()}).mappings().all()

    fundamentals = db.execute(text("""
        SELECT * FROM financial_metrics WHERE ticker = :ticker
        ORDER BY period_end DESC LIMIT 4
    """), {"ticker": ticker.upper()}).mappings().all()

    return {
        "stock": dict(stock),
        "score": dict(score) if score else None,
        "prices": [dict(p) for p in prices],
        "fundamentals": [dict(f) for f in fundamentals],
    }


@router.get("/{ticker}/score/history")
def get_score_history(
    ticker: str,
    limit: int = Query(252, le=1000),
    db: Session = Depends(get_db),
):
    """Return score history for a single stock."""
    rows = db.execute(text("""
        SELECT date, composite_score, momentum_score, trend_score,
               quality_score, value_score, classification,
               rank_overall, rank_sector
        FROM stock_scores WHERE ticker = :ticker
        ORDER BY date DESC LIMIT :limit
    """), {"ticker": ticker.upper(), "limit": limit}).mappings().all()
    return [dict(r) for r in rows]
