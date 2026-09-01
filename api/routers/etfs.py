"""
api/routers/etfs.py
────────────────────
ETF Analysis API — full ETF universe with detail pages.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.database import get_db

router = APIRouter()


@router.get("/")
def list_etfs(
    category: Optional[str] = Query(None, description="sector | factor | fixed_income | international | commodity | real_estate | thematic | volatility | multi_asset"),
    sub_category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all catalog ETFs, optionally filtered by category."""
    sql = "SELECT * FROM etfs WHERE is_active = true"
    params = {}
    if category:
        sql += " AND category = :category"
        params["category"] = category
    if sub_category:
        sql += " AND sub_category = :sub_category"
        params["sub_category"] = sub_category
    sql += " ORDER BY category, sub_category, ticker"
    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """Return distinct ETF categories with counts."""
    rows = db.execute(text("""
        SELECT category, COUNT(*) as count
        FROM etfs WHERE is_active = true
        GROUP BY category
        ORDER BY category
    """)).mappings().all()
    return [dict(r) for r in rows]


@router.get("/scores")
def get_etf_scores(
    category: Optional[str] = Query(None),
    as_of: Optional[date] = Query(None),
    limit: int = Query(100, le=200),
    db: Session = Depends(get_db),
):
    """
    Return ETF composite scores with rankings.
    Default: latest available date, all categories.
    """
    date_clause = """
        AND es.date = (SELECT MAX(date) FROM etf_scores)
    """ if not as_of else "AND es.date = :as_of"

    cat_clause = "AND e.category = :category" if category else ""

    params: dict = {"limit": limit}
    if as_of:
        params["as_of"] = as_of
    if category:
        params["category"] = category

    rows = db.execute(text(f"""
        SELECT
            es.ticker,
            es.date,
            es.momentum_1m,
            es.momentum_3m,
            es.momentum_6m,
            es.momentum_12m,
            es.sharpe_1y,
            es.volatility_1y,
            es.max_drawdown_1y,
            es.beta_vs_spy,
            es.corr_vs_spy,
            es.sortino_ratio,
            es.composite_score,
            es.rank_overall,
            es.rank_category,
            e.name,
            e.category,
            e.sub_category,
            e.benchmark,
            e.expense_ratio,
            p.close as latest_price,
            p.high as high_52w,
            p.low  as low_52w
        FROM etf_scores es
        JOIN etfs e ON e.ticker = es.ticker
        LEFT JOIN LATERAL (
            SELECT close, high, low FROM prices
            WHERE ticker = es.ticker
            ORDER BY date DESC LIMIT 1
        ) p ON true
        WHERE 1=1
        {date_clause}
        {cat_clause}
        ORDER BY es.composite_score DESC
        LIMIT :limit
    """), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{ticker}/related")
def get_related_etfs(
    ticker: str,
    limit: int = Query(8, le=20),
    db: Session = Depends(get_db),
):
    """Return ETFs in the same category, ordered by composite score."""
    category = db.execute(
        text("SELECT category FROM etfs WHERE ticker = :ticker"),
        {"ticker": ticker.upper()}
    ).scalar()

    if not category:
        return []

    rows = db.execute(text("""
        SELECT
            es.ticker,
            es.composite_score,
            es.rank_overall,
            es.momentum_1m,
            es.momentum_3m,
            es.momentum_6m,
            es.momentum_12m,
            es.sharpe_1y,
            es.volatility_1y,
            e.name,
            e.category,
            e.expense_ratio
        FROM etf_scores es
        JOIN etfs e ON e.ticker = es.ticker
        WHERE e.category = :category
          AND es.ticker != :ticker
          AND es.date = (SELECT MAX(date) FROM etf_scores)
        ORDER BY es.composite_score DESC
        LIMIT :limit
    """), {"category": category, "ticker": ticker.upper(), "limit": limit}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{ticker}/holdings")
def get_etf_holdings(
    ticker: str,
    db: Session = Depends(get_db),
):
    """Return latest top holdings for an ETF (if available)."""
    rows = db.execute(text("""
        SELECT rank, symbol, name, weight_pct, holding_date
        FROM etf_holdings
        WHERE etf_ticker = :ticker
          AND holding_date = (
              SELECT MAX(holding_date) FROM etf_holdings WHERE etf_ticker = :ticker
          )
        ORDER BY rank ASC
    """), {"ticker": ticker.upper()}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{ticker}/scores/history")
def get_etf_score_history(
    ticker: str,
    limit: int = Query(252, le=1000),
    db: Session = Depends(get_db),
):
    """Return score history for a single ETF."""
    rows = db.execute(text("""
        SELECT date, composite_score, rank_overall, rank_category,
               momentum_1m, momentum_3m, momentum_6m, momentum_12m,
               sharpe_1y, volatility_1y, max_drawdown_1y, beta_vs_spy,
               corr_vs_spy, sortino_ratio
        FROM etf_scores WHERE ticker = :ticker
        ORDER BY date DESC LIMIT :limit
    """), {"ticker": ticker, "limit": limit}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{ticker}")
def get_etf_detail(ticker: str, db: Session = Depends(get_db)):
    """Full ETF detail — catalog info + latest score + recent price history."""
    catalog = db.execute(
        text("SELECT * FROM etfs WHERE ticker = :ticker"),
        {"ticker": ticker.upper()}
    ).mappings().first()

    if not catalog:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"ETF {ticker} not found in catalog")

    # Latest score with risk metrics
    score = db.execute(text("""
        SELECT * FROM etf_scores WHERE ticker = :ticker
        ORDER BY date DESC LIMIT 1
    """), {"ticker": ticker.upper()}).mappings().first()

    # 1Y price history (most recent first for chart)
    prices = db.execute(text("""
        SELECT date, open, high, low, close, adj_close, volume
        FROM prices WHERE ticker = :ticker
        ORDER BY date ASC LIMIT 252
    """), {"ticker": ticker.upper()}).mappings().all()

    return {
        "catalog": dict(catalog),
        "score": dict(score) if score else None,
        "prices": [dict(p) for p in prices],
    }
