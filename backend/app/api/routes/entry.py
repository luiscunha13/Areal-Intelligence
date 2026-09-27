from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.core.database import get_db
from backend.app.models.company import Company
from backend.app.models.stock_score import StockScore
from backend.app.models.entry_score import EntryScore
from backend.app.models.entry_setup import EntrySetup
from backend.app.models.entry_zone import EntryZone

router = APIRouter(prefix="/api/entry", tags=["Entry Timing Engine"])

@router.get("/ranking")
def get_entry_rankings(
    setup_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get market-wide ranked entry timing opportunities."""
    query = (
        db.query(Company, EntryScore, EntryZone)
        .join(EntryScore, Company.id == EntryScore.company_id)
        .join(EntryZone, Company.id == EntryZone.company_id)
        .filter(Company.is_active == True)
    )

    if search:
        s = f"%{search.upper()}%"
        query = query.filter((Company.ticker.like(s)) | (Company.company_name.ilike(s)))

    results = query.order_by(EntryScore.entry_score.desc()).limit(limit).all()

    opportunities = []
    for comp, es, ez in results:
        # Fetch setup info
        setups = db.query(EntrySetup).filter(
            EntrySetup.company_id == comp.id,
            EntrySetup.date == es.date
        ).all()

        stock_score_obj = db.query(StockScore).filter(
            StockScore.company_id == comp.id
        ).order_by(StockScore.date.desc()).first()

        opportunities.append({
            "company_id": comp.id,
            "ticker": comp.ticker,
            "company_name": comp.company_name,
            "stock_score": stock_score_obj.overall_score if stock_score_obj else 75.0,
            "entry_score": es.entry_score,
            "status": es.status,
            "confidence": es.confidence,
            "current_price": ez.current_price,
            "entry_zone": {
                "low": ez.entry_zone_low,
                "high": ez.entry_zone_high
            },
            "invalidation_price": ez.invalidation_price,
            "target_price": ez.reference_target_price,
            "risk_reward_ratio": ez.risk_reward_ratio,
            "setups": [s.setup_type for s in setups],
            "event_risk": es.event_risk_level,
        })

    return {"entry_opportunities": opportunities}

@router.get("/company/{ticker}")
def get_company_entry_detail(ticker: str, db: Session = Depends(get_db)):
    """Get detailed Entry Timing report for a specific ticker."""
    comp = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    latest_es = db.query(EntryScore).filter(EntryScore.company_id == comp.id).order_by(EntryScore.date.desc()).first()
    latest_ez = db.query(EntryZone).filter(EntryZone.company_id == comp.id).order_by(EntryZone.date.desc()).first()
    setups = db.query(EntrySetup).filter(EntrySetup.company_id == comp.id).order_by(EntrySetup.date.desc()).all()
    stock_score_obj = db.query(StockScore).filter(StockScore.company_id == comp.id).order_by(StockScore.date.desc()).first()

    if not latest_es or not latest_ez:
        raise HTTPException(status_code=404, detail=f"Entry timing metrics not yet calculated for '{ticker}'.")

    return {
        "ticker": comp.ticker,
        "company_name": comp.company_name,
        "stock_score": stock_score_obj.overall_score if stock_score_obj else 75.0,
        "entry_score": latest_es.entry_score,
        "status": latest_es.status,
        "confidence": latest_es.confidence,
        "subscores": {
            "trend_score": latest_es.trend_score,
            "momentum_score": latest_es.momentum_score,
            "extension_score": latest_es.extension_score,
            "support_resistance_score": latest_es.support_resistance_score,
            "valuation_context_score": latest_es.valuation_context_score,
            "event_risk_score": latest_es.event_risk_score,
        },
        "entry_zone": {
            "current_price": latest_ez.current_price,
            "entry_zone_low": latest_ez.entry_zone_low,
            "entry_zone_high": latest_ez.entry_zone_high,
            "invalidation_price": latest_ez.invalidation_price,
            "target_price": latest_ez.reference_target_price,
            "risk_reward_ratio": latest_ez.risk_reward_ratio,
        },
        "setups": [
            {
                "setup_type": s.setup_type,
                "signal_strength": s.signal_strength,
                "description": s.description
            } for s in setups
        ],
        "event_risk": latest_es.event_risk_level,
    }
