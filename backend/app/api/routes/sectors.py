import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict

from backend.app.core.database import get_db
from backend.app.models.sector import Sector
from backend.app.models.sector_return import SectorReturn
from backend.app.models.sector_feature import SectorFeature
from backend.app.models.sector_score import SectorScore
from backend.app.models.market_regime import MarketRegime
from backend.app.models.company import Company

from backend.app.schemas.sector import (
    SectorResponse,
    SectorRankingResponse,
    SectorRankingItem,
    SectorScoresSchema,
    SectorPerformanceItem,
    TailCoordinate,
)
from backend.app.services.sector_ranking import generate_sector_explanations

router = APIRouter(prefix="/api/sectors", tags=["sectors"])

@router.get("", response_model=List[SectorResponse])
def get_all_sectors(level: Optional[int] = Query(None, description="Filter by universe level: 1 (Sectors), 2 (Industry Groups)"), db: Session = Depends(get_db)):
    """List all sector & industry group ETF proxies."""
    query = db.query(Sector).filter(Sector.symbol != "SPY")
    if level is not None:
        query = query.filter(Sector.level == level)
    sectors = query.all()
    return sectors

@router.get("/ranking", response_model=SectorRankingResponse)
def get_sector_ranking(level: Optional[int] = Query(None, description="Filter rankings by level: 1 (Sectors), 2 (Industry Groups)"), db: Session = Depends(get_db)):
    """Get current institutional sector & industry group rankings, composite scores, fundamental metrics, RRG ratios, macro betas, and tails."""
    latest_score = db.query(SectorScore.date).order_by(SectorScore.date.desc()).first()
    if not latest_score:
        raise HTTPException(status_code=404, detail="No sector scores found.")

    score_date = latest_score.date

    latest_regime = db.query(MarketRegime).order_by(MarketRegime.date.desc()).first()
    active_regime_name = latest_regime.regime if latest_regime else "Neutral / Transition"

    score_query = db.query(SectorScore).filter(SectorScore.date == score_date).order_by(SectorScore.rank)
    scores = score_query.all()

    rankings = []
    for sc in scores:
        sector = db.query(Sector).filter(Sector.id == sc.sector_id).first()
        if not sector or sector.symbol == "SPY":
            continue

        if level is not None and sector.level != level:
            continue

        feat = db.query(SectorFeature).filter(
            SectorFeature.sector_id == sc.sector_id
        ).order_by(SectorFeature.date.desc()).first()

        scores_dict = {
            "momentum_score": sc.momentum_score or 50.0,
            "relative_strength_score": sc.relative_strength_score or 50.0,
            "trend_score": sc.trend_score or 50.0,
            "regime_fit_score": sc.regime_fit_score or 50.0,
            "risk_score": sc.risk_score or 50.0,
            "breadth_score": sc.breadth_score or 50.0,
            "fundamental_score": sc.fundamental_score or 50.0,
            "surprise_score": sc.surprise_score or 50.0,
        }

        feat_dict = {
            "momentum_1m": feat.momentum_1m if feat else 0.0,
            "relative_strength_1m": feat.relative_strength_1m if feat else 0.0,
        }

        why = generate_sector_explanations(scores_dict, feat_dict)

        tails_data = []
        if sc.tails:
            try:
                raw_tails = json.loads(sc.tails)
                tails_data = [TailCoordinate(**t) for t in raw_tails]
            except Exception:
                tails_data = []

        rankings.append(SectorRankingItem(
            symbol=sector.symbol,
            name=sector.name,
            gics_code=sector.gics_code,
            level=sector.level or 1,
            category=sector.category,
            rank=sc.rank or 1,
            rank_change=sc.rank_change or 0,
            overall_score=sc.overall_score,
            scores=SectorScoresSchema(
                momentum=sc.momentum_score or 50.0,
                relative_strength=sc.relative_strength_score or 50.0,
                trend=sc.trend_score or 50.0,
                regime_fit=sc.regime_fit_score or 50.0,
                risk=sc.risk_score or 50.0,
                breadth=sc.breadth_score or 50.0,
                fundamental=sc.fundamental_score or 50.0,
                surprise=sc.surprise_score or 50.0,
            ),
            rs_ratio=sc.rs_ratio or 100.0,
            rs_momentum=sc.rs_momentum or 100.0,
            rs_ratio_strategic=sc.rs_ratio_strategic or 100.0,
            rs_momentum_strategic=sc.rs_momentum_strategic or 100.0,
            pe_ratio_ttm=feat.pe_ratio_ttm if feat else None,
            pe_percentile_5y=feat.pe_percentile_5y if feat else None,
            quality_flag=feat.quality_flag if feat else "Clean growth",
            eps_growth_yoy=feat.eps_growth_yoy if feat else None,
            revenue_growth_yoy=feat.revenue_growth_yoy if feat else None,
            eps_surprise_pct=feat.eps_surprise_pct if feat else None,
            beta_growth=feat.beta_growth if feat else None,
            beta_inflation=feat.beta_inflation if feat else None,
            beta_fca=feat.beta_fca if feat else None,
            tails=tails_data,
            classification=sc.classification or "NEUTRAL",
            why=why,
        ))

    return SectorRankingResponse(
        date=score_date,
        active_regime=active_regime_name,
        rankings=rankings,
    )

@router.get("/{symbol}")
def get_sector_detail(
    symbol: str, 
    limit: int = Query(default=100, ge=1, le=5000),
    db: Session = Depends(get_db)
):
    """Get detailed sector/industry profile, sub-scores, fundamentals, macro sensitivities, and constituent companies."""
    sector = db.query(Sector).filter(Sector.symbol == symbol.upper()).first()
    if not sector:
        raise HTTPException(status_code=404, detail=f"Sector '{symbol}' not found")

    latest_score = db.query(SectorScore).filter(SectorScore.sector_id == sector.id).order_by(SectorScore.date.desc()).first()
    feat = db.query(SectorFeature).filter(SectorFeature.sector_id == sector.id).order_by(SectorFeature.date.desc()).first()
    
    limit_num = limit if isinstance(limit, int) else getattr(limit, "default", 100)
    comp_query = db.query(Company).filter(Company.sector_id == sector.id, Company.is_active == True)
    total_count = comp_query.count()
    companies = (
        comp_query
        .order_by(Company.market_cap.desc().nullslast())
        .limit(limit_num)
        .all()
    )

    if not companies and sector.category:
        parent_sector = db.query(Sector).filter(
            Sector.category == sector.category,
            Sector.level == 1
        ).first()
        if parent_sector:
            comp_query = db.query(Company).filter(Company.sector_id == parent_sector.id, Company.is_active == True)
            total_count = comp_query.count()
            companies = (
                comp_query
                .order_by(Company.market_cap.desc().nullslast())
                .limit(limit_num)
                .all()
            )

    tails_data = []
    if latest_score and latest_score.tails:
        try:
            tails_data = json.loads(latest_score.tails)
        except Exception:
            tails_data = []

    scores_dict = {
        "momentum_score": latest_score.momentum_score or 50.0,
        "relative_strength_score": latest_score.relative_strength_score or 50.0,
        "trend_score": latest_score.trend_score or 50.0,
        "regime_fit_score": latest_score.regime_fit_score or 50.0,
        "risk_score": latest_score.risk_score or 50.0,
        "breadth_score": latest_score.breadth_score or 50.0,
        "fundamental_score": latest_score.fundamental_score or 50.0,
        "surprise_score": latest_score.surprise_score or 50.0,
    } if latest_score else {}

    feat_dict = {
        "momentum_1m": feat.momentum_1m if feat else 0.0,
        "relative_strength_1m": feat.relative_strength_1m if feat else 0.0,
    }

    why = generate_sector_explanations(scores_dict, feat_dict) if scores_dict else []

    return {
        "id": sector.id,
        "symbol": sector.symbol,
        "name": sector.name,
        "gics_code": sector.gics_code,
        "level": sector.level or 1,
        "category": sector.category,
        "description": sector.description or f"{sector.name} ETF Proxy",
        "why": why,
        "total_companies": total_count,
        "latest_score": {
            "overall_score": latest_score.overall_score if latest_score else 50.0,
            "rank": latest_score.rank if latest_score else 1,
            "classification": latest_score.classification if latest_score else "NEUTRAL",
            "rs_ratio": latest_score.rs_ratio if latest_score else 100.0,
            "rs_momentum": latest_score.rs_momentum if latest_score else 100.0,
            "pe_ratio_ttm": feat.pe_ratio_ttm if feat else None,
            "pe_percentile_5y": feat.pe_percentile_5y if feat else None,
            "quality_flag": feat.quality_flag if feat else "Clean growth",
            "eps_growth_yoy": feat.eps_growth_yoy if feat else None,
            "revenue_growth_yoy": feat.revenue_growth_yoy if feat else None,
            "eps_surprise_pct": feat.eps_surprise_pct if feat else None,
            "sensitivities": {
                "beta_growth": feat.beta_growth if feat else None,
                "beta_inflation": feat.beta_inflation if feat else None,
                "beta_fca": feat.beta_fca if feat else None,
            },
            "tails": tails_data,
            "scores": {
                "momentum": latest_score.momentum_score if latest_score else 50.0,
                "relative_strength": latest_score.relative_strength_score if latest_score else 50.0,
                "trend": latest_score.trend_score if latest_score else 50.0,
                "regime_fit": latest_score.regime_fit_score if latest_score else 50.0,
                "risk": latest_score.risk_score if latest_score else 50.0,
                "breadth": latest_score.breadth_score if latest_score else 50.0,
                "fundamental": latest_score.fundamental_score if latest_score else 50.0,
                "surprise": latest_score.surprise_score if latest_score else 50.0,
            } if latest_score else {}
        },
        "companies": [
            {
                "id": c.id,
                "ticker": c.ticker,
                "company_name": c.company_name,
                "exchange": c.exchange,
                "market_cap": c.market_cap,
            }
            for c in companies
        ]
    }

@router.get("/{symbol}/performance", response_model=List[SectorPerformanceItem])
def get_sector_performance(symbol: str, limit: int = 60, db: Session = Depends(get_db)):
    """Get multi-period return history for a sector/industry."""
    sector = db.query(Sector).filter(Sector.symbol == symbol.upper()).first()
    if not sector:
        raise HTTPException(status_code=404, detail=f"Sector {symbol} not found.")

    returns = db.query(SectorReturn).filter(
        SectorReturn.sector_id == sector.id
    ).order_by(SectorReturn.date.desc()).limit(limit).all()

    return [SectorPerformanceItem(
        date=r.date,
        return_1d=r.return_1d,
        return_5d=r.return_5d,
        return_1m=r.return_1m,
        return_3m=r.return_3m,
        return_6m=r.return_6m,
        return_12m=r.return_12m,
    ) for r in reversed(returns)]


@router.get("/{symbol}/rank-history")
def get_sector_rank_history(symbol: str, limit: int = Query(default=30, ge=5, le=365), db: Session = Depends(get_db)):
    """Get historical rank and score trajectory for a sector — powers rank sparklines."""
    sector = db.query(Sector).filter(Sector.symbol == symbol.upper()).first()
    if not sector:
        raise HTTPException(status_code=404, detail=f"Sector {symbol} not found.")

    rows = (
        db.query(SectorScore)
        .filter(SectorScore.sector_id == sector.id)
        .order_by(SectorScore.date.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "date": r.date.isoformat(),
            "rank": r.rank,
            "overall_score": round(r.overall_score, 1) if r.overall_score else None,
            "classification": r.classification,
        }
        for r in reversed(rows)
    ]


@router.get("/analytics/regime-alpha-matrix")
def get_regime_alpha_matrix(db: Session = Depends(get_db)):
    """Compute per-sector average performance during each macro regime quadrant.
    Returns a matrix: {regime_quadrant -> {sector_symbol -> avg_1m_return, avg_3m_return, count}}.
    Powers Fix 5 — regime x sector alpha insights.
    """
    import re

    regimes = db.query(MarketRegime).order_by(MarketRegime.date.asc()).all()
    sectors = db.query(Sector).filter(Sector.symbol != "SPY", Sector.level == 1).all()

    def extract_quadrant(regime_str: str) -> str:
        for q in ["Goldilocks", "Overheat", "Slowdown", "Stagflation"]:
            if q.lower() in regime_str.lower():
                return q
        return "Neutral"

    # Build regime date ranges
    regime_windows = []
    for i, r in enumerate(regimes):
        start_date = r.date
        end_date = regimes[i + 1].date if i + 1 < len(regimes) else r.date
        regime_windows.append({
            "quadrant": extract_quadrant(r.regime),
            "regime": r.regime,
            "start": start_date,
            "end": end_date,
        })

    matrix: Dict[str, Dict[str, dict]] = {}
    for sector in sectors:
        for window in regime_windows:
            q = window["quadrant"]
            if q not in matrix:
                matrix[q] = {}
            if sector.symbol not in matrix[q]:
                matrix[q][sector.symbol] = {"sum_1m": 0.0, "sum_3m": 0.0, "count": 0}

            # Find closest sector return in that regime window
            ret = (
                db.query(SectorReturn)
                .filter(
                    SectorReturn.sector_id == sector.id,
                    SectorReturn.date >= window["start"],
                    SectorReturn.date <= window["end"],
                )
                .order_by(SectorReturn.date.desc())
                .first()
            )
            if ret and ret.return_1m is not None:
                matrix[q][sector.symbol]["sum_1m"] += ret.return_1m * 100
                matrix[q][sector.symbol]["sum_3m"] += (ret.return_3m or 0) * 100
                matrix[q][sector.symbol]["count"] += 1

    # Compute averages and build clean output
    result = {}
    for quadrant, sectors_data in matrix.items():
        result[quadrant] = {}
        for sym, agg in sectors_data.items():
            n = agg["count"]
            if n > 0:
                result[quadrant][sym] = {
                    "avg_1m_return": round(agg["sum_1m"] / n, 2),
                    "avg_3m_return": round(agg["sum_3m"] / n, 2),
                    "count": n,
                }
    return result
