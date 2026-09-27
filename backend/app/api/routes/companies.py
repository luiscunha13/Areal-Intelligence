import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.core.database import get_db
from backend.app.models.company import Company
from backend.app.models.stock_score import StockScore
from backend.app.models.stock_price import StockPrice
from backend.app.models.financial_metric import FinancialMetric
from backend.app.models.company_snapshot import CompanySnapshot
from backend.app.schemas.company import CompanyBase, CompanyDetailResponse

def safe_float(val: Optional[float]) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val

router = APIRouter(prefix="/api/companies", tags=["Companies & Stock Intelligence"])

@router.get("", response_model=List[CompanyBase])
def list_companies(
    sector_id: Optional[int] = Query(None),
    industry_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(default=1000, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    """List equities with optional sector, industry, or ticker search filter."""
    query = db.query(Company).filter(Company.is_active == True)
    if sector_id:
        query = query.filter(Company.sector_id == sector_id)
    if industry_id:
        query = query.filter(Company.industry_id == industry_id)
    if search:
        s = f"%{search.upper()}%"
        query = query.filter((Company.ticker.ilike(s)) | (Company.company_name.ilike(s)))

    return query.order_by(Company.ticker).limit(limit).all()

@router.get("/rankings")
def get_stock_rankings(
    sector_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(default=1000, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    """Get overall stock rankings across all active US & Global equities using materialized snapshots."""
    query = db.query(CompanySnapshot)

    if sector_id:
        query = query.filter(CompanySnapshot.sector_id == sector_id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((CompanySnapshot.ticker.ilike(s)) | (CompanySnapshot.company_name.ilike(s)))

    results = query.order_by(CompanySnapshot.rank.asc()).limit(limit).all()

    rankings = []
    for sn in results:
        rankings.append({
            "company_id": sn.company_id,
            "ticker": sn.ticker,
            "company_name": sn.company_name,
            "sector_id": sn.sector_id,
            "market_cap": safe_float(sn.market_cap),
            "close_price": safe_float(sn.close_price),
            "rank": sn.rank,
            "overall_score": safe_float(sn.overall_score),
            "quality_score": safe_float(sn.quality_score),
            "growth_score": safe_float(sn.growth_score),
            "valuation_score": safe_float(sn.valuation_score),
            "earnings_score": safe_float(sn.earnings_score),
            "technical_score": safe_float(sn.technical_score),
            "relative_strength_score": safe_float(sn.relative_strength_score),
            "revenue": safe_float(sn.revenue),
            "net_income": safe_float(sn.net_income),
            "eps": safe_float(sn.eps),
            "pe_ratio": safe_float(sn.pe_ratio),
            "revenue_growth_yoy": safe_float(sn.revenue_growth_yoy),
            "gross_margin": safe_float(sn.gross_margin),
        })

    return {"rankings": rankings, "total": len(rankings)}

@router.get("/{ticker}", response_model=CompanyDetailResponse)
def get_company_detail(ticker: str, db: Session = Depends(get_db)):
    """Get detailed profile, latest market price, financial metrics, and stock score with autonomous on-the-fly lookup."""
    tk = ticker.upper().strip()
    company = db.query(Company).filter(Company.ticker == tk).first()
    if not company:
        # Autonomous On-the-Fly Lookup via SEC EDGAR directory
        try:
            import urllib.request
            import json
            from backend.app.models.sector import Sector
            from scripts.sync_autonomous_universe import classify_sector_by_title

            url = "https://www.sec.gov/files/company_tickers.json"
            req = urllib.request.Request(url, headers={"User-Agent": "MacroAnalysisEngine/1.0 (admin@analysis.com)"})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                matching_title = None
                for item in data.values():
                    if item.get("ticker", "").upper() == tk:
                        matching_title = item.get("title", tk).title()
                        break
                
                title = matching_title or f"{tk} Inc."
                sec_sym = classify_sector_by_title(title)
                sector_obj = db.query(Sector).filter(Sector.symbol == sec_sym).first()
                sec_id = sector_obj.id if sector_obj else 2

                company = Company(
                    ticker=tk,
                    company_name=title,
                    exchange="NASDAQ/NYSE",
                    sector_id=sec_id,
                    is_active=True
                )
                db.add(company)
                db.commit()
                db.refresh(company)
        except Exception:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    latest_score = (
        db.query(StockScore)
        .filter(StockScore.company_id == company.id)
        .order_by(StockScore.date.desc())
        .first()
    )

    latest_price = (
        db.query(StockPrice)
        .filter(StockPrice.company_id == company.id)
        .order_by(StockPrice.date.desc())
        .first()
    )

    latest_financials = (
        db.query(FinancialMetric)
        .filter(FinancialMetric.company_id == company.id)
        .order_by(FinancialMetric.period_end.desc())
        .first()
    )

    # 4. Fetch Macro & Sector Synergy Context
    from backend.app.models.sector import Sector
    from backend.app.models.sector_score import SectorScore
    from backend.app.models.market_regime import MarketRegime
    from backend.app.services.macro_sector_synergy import evaluate_macro_sector_candidate

    sector_obj = db.query(Sector).filter(Sector.id == company.sector_id).first() if company.sector_id else None
    sector_name = sector_obj.name if sector_obj else "General"

    latest_sec_score_obj = (
        db.query(SectorScore)
        .filter(SectorScore.sector_id == company.sector_id)
        .order_by(SectorScore.date.desc())
        .first()
    ) if company.sector_id else None
    sector_score_val = latest_sec_score_obj.overall_score if latest_sec_score_obj else 75.0

    active_regime_obj = db.query(MarketRegime).order_by(MarketRegime.date.desc()).first()
    regime_name = active_regime_obj.regime if active_regime_obj else "Goldilocks"

    stock_scores_dict = {
        "overall_score": latest_score.overall_score if latest_score else 50.0,
        "quality_score": latest_score.quality_score if latest_score else 50.0,
        "growth_score": latest_score.growth_score if latest_score else 50.0,
        "valuation_score": latest_score.valuation_score if latest_score else 50.0,
    }

    synergy_res = evaluate_macro_sector_candidate(
        stock_scores=stock_scores_dict,
        sector_score=sector_score_val,
        sector_name=sector_name,
        regime_name=regime_name
    )

    return CompanyDetailResponse(
        id=company.id,
        ticker=company.ticker,
        company_name=company.company_name,
        legal_name=company.legal_name,
        exchange=company.exchange,
        country=company.country,
        currency=company.currency,
        sector_id=company.sector_id,
        industry_id=company.industry_id,
        market_cap=company.market_cap,
        is_active=company.is_active,
        first_seen=company.first_seen,
        last_seen=company.last_seen,
        industry=company.industry,
        sector_name=sector_name,
        sector_score=safe_float(sector_score_val),
        active_regime=regime_name,
        macro_fit_score=safe_float(synergy_res["macro_fit_score"]),
        composite_candidate_score=safe_float(synergy_res["composite_candidate_score"]),
        candidate_category=synergy_res["category"],
        thesis_explanations=synergy_res["explanations"],
        latest_score=latest_score,
        latest_price=latest_price,
        latest_financials=latest_financials
    )
