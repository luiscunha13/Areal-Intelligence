from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from ...core.database import SessionLocal
from ...models import MarketRegime, MacroFeature
from ...services.regime import classify_regime_v2, generate_drivers_explanation

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/current")
def current_regime(db: Session = Depends(get_db)):
    """Get the latest market regime classification, scores, and driver explanations."""
    mr = db.query(MarketRegime).order_by(MarketRegime.date.desc()).first()
    if not mr:
        raise HTTPException(status_code=404, detail="No market regime computed yet.")

    scores = {
        "growth": mr.growth_score,
        "inflation": mr.inflation_score,
        "rates": mr.rates_score,
        "liquidity": mr.liquidity_score,
        "credit": mr.credit_score,
        "risk": mr.risk_score,
        "overall": mr.overall_score,
    }

    target_prior_date = mr.date - timedelta(days=90)
    prior_mf = (
        db.query(MacroFeature)
        .filter(MacroFeature.feature_date <= target_prior_date)
        .order_by(MacroFeature.feature_date.desc())
        .first()
    )
    delta_g = mr.growth_score - (prior_mf.growth_score if prior_mf else mr.growth_score)
    delta_i = mr.inflation_score - (prior_mf.inflation_score if prior_mf else mr.inflation_score)

    classification = classify_regime_v2(
        scores=scores,
        delta_growth=delta_g,
        delta_inflation=delta_i,
        methodology_version="2.0",
    )
    classification["date"] = mr.date.isoformat()

    # Fix 3: Regime Duration tracking
    all_recent = (
        db.query(MarketRegime)
        .order_by(MarketRegime.date.desc())
        .limit(365)
        .all()
    )
    current_regime_label = mr.regime
    regime_start_date = mr.date
    for r in all_recent:
        if r.regime == current_regime_label:
            regime_start_date = r.date
        else:
            break
    regime_duration_days = (mr.date - regime_start_date).days + 1
    classification["regime_duration_days"] = regime_duration_days
    classification["regime_started"] = regime_start_date.isoformat()

    # Compute historical avg regime duration
    all_regime_rows = db.query(MarketRegime).order_by(MarketRegime.date.asc()).all()
    regime_periods = []
    if all_regime_rows:
        cur = all_regime_rows[0].regime
        start = all_regime_rows[0].date
        for r in all_regime_rows[1:]:
            if r.regime != cur:
                regime_periods.append((r.date - start).days + 1)
                cur = r.regime
                start = r.date
        regime_periods.append((all_regime_rows[-1].date - start).days + 1)
    avg_regime_duration = round(sum(regime_periods) / len(regime_periods)) if regime_periods else None
    classification["avg_regime_duration_days"] = avg_regime_duration

    # Fix 2: 30-day prev dimension scores for trend arrows
    prior_30d_date = mr.date - timedelta(days=30)
    prior_30d = (
        db.query(MarketRegime)
        .filter(MarketRegime.date <= prior_30d_date)
        .order_by(MarketRegime.date.desc())
        .first()
    )
    if prior_30d:
        classification["prev_dimensions"] = {
            "growth": prior_30d.growth_score,
            "inflation": prior_30d.inflation_score,
            "rates": prior_30d.rates_score,
            "liquidity": prior_30d.liquidity_score,
            "credit": prior_30d.credit_score,
            "risk": prior_30d.risk_score,
        }
    else:
        classification["prev_dimensions"] = None

    # Fix 5: ETF proxy mappings for asset tilt chips
    ETF_PROXY_MAP = {
        "Growth Equities": {"etf": "QQQ", "name": "Nasdaq 100"},
        "Small Caps": {"etf": "IWM", "name": "Russell 2000"},
        "High-Yield Credit": {"etf": "HYG", "name": "iShares HY Bond"},
        "Commodities": {"etf": "DJP", "name": "Bloomberg Commodity"},
        "Value Equities": {"etf": "VTV", "name": "Vanguard Value"},
        "Cyclicals": {"etf": "XLI", "name": "Industrials ETF"},
        "TIPS": {"etf": "TIP", "name": "iShares TIPS Bond"},
        "Gold": {"etf": "GLD", "name": "SPDR Gold"},
        "Short Duration Treasuries": {"etf": "SHY", "name": "1-3Y Treasuries"},
        "Short/Intermediate Treasuries (2Y-5Y)": {"etf": "IEI", "name": "3-7Y Treasuries"},
        "Duration / Treasuries": {"etf": "TLT", "name": "20Y+ Treasuries"},
        "Long Duration Bonds": {"etf": "TLT", "name": "20Y+ Treasuries"},
        "Long Duration Treasuries (20Y+)": {"etf": "TLT", "name": "20Y+ Treasuries"},
        "Quality Defensives": {"etf": "SPLV", "name": "Low Volatility"},
        "Cash": {"etf": "BIL", "name": "T-Bill / Cash"},
        "USD": {"etf": "UUP", "name": "USD Index"},
        "TIPS / Gold": {"etf": "IAU", "name": "Gold / TIPS"},
        "Quality Cyclicals": {"etf": "XLI", "name": "Industrials ETF"},
        "Speculative High-Beta": {"etf": "SPHB", "name": "High Beta"},
        "Adding New Risk Exposure": {"etf": None, "name": "Avoid New Risk"},
        "Speculative Growth": {"etf": "ARKK", "name": "Disruptive Growth"},
        "Long-Duration Growth Equities": {"etf": "QQQ", "name": "Nasdaq 100"},
        "Duration & Growth Equities": {"etf": "QQQ", "name": "Growth Equities"},
        "High-Beta Equities": {"etf": "SPHB", "name": "High Beta"},
    }
    classification["favored_assets_with_etf"] = [
        {**ETF_PROXY_MAP.get(a, {"etf": None, "name": a}), "label": a}
        for a in classification.get("favored_assets", [])
    ]
    classification["avoid_assets_with_etf"] = [
        {**ETF_PROXY_MAP.get(a, {"etf": None, "name": a}), "label": a}
        for a in classification.get("avoid_assets", [])
    ]

    return classification


@router.get("/history")
def regime_history(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get historical market regime trajectory."""
    rows = db.query(MarketRegime).order_by(MarketRegime.date.desc()).limit(limit).all()
    out = []
    for r in reversed(rows):
        out.append(
            {
                "date": r.date.isoformat(),
                "regime": r.regime,
                "overall_score": r.overall_score,
                "confidence": r.confidence,
                "dimensions": {
                    "growth": r.growth_score,
                    "inflation": r.inflation_score,
                    "rates": r.rates_score,
                    "liquidity": r.liquidity_score,
                    "credit": r.credit_score,
                    "risk": r.risk_score,
                },
            }
        )
    return out


@router.get("/{target_date}")
def get_regime_at_date(target_date: date, db: Session = Depends(get_db)):
    """Get market regime classification for a specific historical date."""
    mr = (
        db.query(MarketRegime)
        .filter(MarketRegime.date <= target_date)
        .order_by(MarketRegime.date.desc())
        .first()
    )
    if not mr:
        raise HTTPException(status_code=404, detail=f"No regime data available for date {target_date}")

    scores = {
        "growth": mr.growth_score,
        "inflation": mr.inflation_score,
        "rates": mr.rates_score,
        "liquidity": mr.liquidity_score,
        "credit": mr.credit_score,
        "risk": mr.risk_score,
        "overall": mr.overall_score,
    }
    target_prior_date = mr.date - timedelta(days=90)
    prior_mf = (
        db.query(MacroFeature)
        .filter(MacroFeature.feature_date <= target_prior_date)
        .order_by(MacroFeature.feature_date.desc())
        .first()
    )
    delta_g = mr.growth_score - (prior_mf.growth_score if prior_mf else mr.growth_score)
    delta_i = mr.inflation_score - (prior_mf.inflation_score if prior_mf else mr.inflation_score)

    classification = classify_regime_v2(
        scores=scores,
        delta_growth=delta_g,
        delta_inflation=delta_i,
        methodology_version="2.0",
    )
    classification["date"] = mr.date.isoformat()
    return classification
