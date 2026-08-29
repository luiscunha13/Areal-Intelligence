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
    return [{**dict(r), "id": r["series_id"], "fred_series_id": r["series_id"]} for r in rows]


@router.get("/series/{series_id}")
def get_series_detail(
    series_id: str,
    limit: int = Query(50000, le=100000),
    db: Session = Depends(get_db),
):
    """Get catalog metadata for a single series + observations."""
    row = db.execute(
        text("SELECT * FROM macro_series WHERE series_id = :sid"),
        {"sid": series_id}
    ).mappings().first()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Series {series_id} not found")

    obs_rows = db.execute(text("""
        SELECT date, value FROM macro_observations
        WHERE series_id = :sid
        ORDER BY date ASC
        LIMIT :limit
    """), {"sid": series_id, "limit": limit}).mappings().all()

    meta = dict(row)
    meta["id"] = meta["series_id"]
    meta["fred_series_id"] = meta["series_id"]
    meta["observations"] = [dict(r) for r in obs_rows]
    return meta


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


def _format_regime(row: dict, prev_row: dict = None) -> dict:
    if not row:
        return {}

    cleaned_row = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            cleaned_row[k] = v.isoformat()
        elif hasattr(v, "to_eng_string") or type(v).__name__ == "Decimal":
            cleaned_row[k] = float(v)
        else:
            cleaned_row[k] = v
    row = cleaned_row

    if prev_row:
        cleaned_prev = {}
        for k, v in prev_row.items():
            if hasattr(v, "isoformat"):
                cleaned_prev[k] = v.isoformat()
            elif hasattr(v, "to_eng_string") or type(v).__name__ == "Decimal":
                cleaned_prev[k] = float(v)
            else:
                cleaned_prev[k] = v
        prev_row = cleaned_prev

    raw_quad = (row.get("quadrant") or "reflation").lower()
    
    quadrant_meta = {
        "reflation": {
            "display_quad": "Goldilocks",
            "regime_title": "Reflationary Growth & Expansion",
            "severity": "Moderate Expansion",
            "favored": [
                {"label": "Technology", "etf": "XLK", "name": "Technology Select Sector SPDR"},
                {"label": "Financials", "etf": "XLF", "name": "Financial Select Sector SPDR"},
                {"label": "Consumer Discretionary", "etf": "XLY", "name": "Consumer Discretionary SPDR"},
                {"label": "Broad Equities", "etf": "SPY", "name": "SPDR S&P 500 ETF Trust"}
            ],
            "avoid": [
                {"label": "Cash / T-Bills", "etf": "BIL", "name": "SPDR 1-3 Month T-Bill ETF"},
                {"label": "Utilities", "etf": "XLU", "name": "Utilities Select Sector SPDR"}
            ],
            "positive": [
                "Growth momentum positive with controlled inflation dynamics.",
                "Financial Conditions Amplifier (FCA) indicates accommodative market liquidity.",
                "Corporate profit margins resilient across cyclical sectors."
            ],
            "negative": [
                "Real interest rates remain restrictive despite policy easing expectations.",
                "Global trade growth momentum remains uneven."
            ]
        },
        "goldilocks": {
            "display_quad": "Goldilocks",
            "regime_title": "Goldilocks Growth & Low Inflation",
            "severity": "Optimal Growth",
            "favored": [
                {"label": "Technology", "etf": "XLK", "name": "Technology Select Sector SPDR"},
                {"label": "Communication Services", "etf": "XLC", "name": "Communication Services SPDR"},
                {"label": "Growth Equities", "etf": "QQQ", "name": "Invesco QQQ Trust"}
            ],
            "avoid": [
                {"label": "Commodities", "etf": "DBC", "name": "Invesco DB Commodity Index"},
                {"label": "Cash / T-Bills", "etf": "BIL", "name": "SPDR 1-3 Month T-Bill ETF"}
            ],
            "positive": [
                "Strong GDP and industrial production growth combined with moderating CPI.",
                "Credit spreads near historical tights, reflecting low default expectations."
            ],
            "negative": [
                "High valuation multiples leave little buffer for earnings misses."
            ]
        },
        "overheat": {
            "display_quad": "Overheat",
            "regime_title": "Overheat Expansion & High Inflation",
            "severity": "Inflationary Risk",
            "favored": [
                {"label": "Energy", "etf": "XLE", "name": "Energy Select Sector SPDR"},
                {"label": "Materials", "etf": "XLB", "name": "Materials Select Sector SPDR"},
                {"label": "Commodities", "etf": "DBC", "name": "Invesco DB Commodity Index"}
            ],
            "avoid": [
                {"label": "Long Treasuries", "etf": "TLT", "name": "iShares 20+ Year Treasury Bond"},
                {"label": "Technology", "etf": "XLK", "name": "Technology Select Sector SPDR"}
            ],
            "positive": [
                "High pricing power for commodity producers and raw material suppliers."
            ],
            "negative": [
                "Accelerating inflation pressures interest rate hikes.",
                "Input cost inflation squeezing non-energy margins."
            ]
        },
        "slowdown": {
            "display_quad": "Slowdown",
            "regime_title": "Slowdown & Economic Deceleration",
            "severity": "Defensive Posture",
            "favored": [
                {"label": "Health Care", "etf": "XLV", "name": "Health Care Select Sector SPDR"},
                {"label": "Consumer Staples", "etf": "XLP", "name": "Consumer Staples Select Sector SPDR"},
                {"label": "Treasuries", "etf": "TLT", "name": "iShares 20+ Year Treasury Bond"}
            ],
            "avoid": [
                {"label": "Small Caps", "etf": "IWM", "name": "iShares Russell 2000 ETF"},
                {"label": "High Yield Credit", "etf": "HYG", "name": "iShares iBoxx $ High Yield Corporate"}
            ],
            "positive": [
                "Decelerating inflation allows central banks flexibility to lower rates."
            ],
            "negative": [
                "Growth momentum slowing across manufacturing and retail sales.",
                "Earnings estimate revisions turning negative."
            ]
        },
        "stagflation": {
            "display_quad": "Stagflation",
            "regime_title": "Stagflationary Pressure",
            "severity": "High Macro Stress",
            "favored": [
                {"label": "Gold / Metals", "etf": "GLD", "name": "SPDR Gold Shares"},
                {"label": "Energy", "etf": "XLE", "name": "Energy Select Sector SPDR"},
                {"label": "Cash / T-Bills", "etf": "BIL", "name": "SPDR 1-3 Month T-Bill ETF"}
            ],
            "avoid": [
                {"label": "Broad Equities", "etf": "SPY", "name": "SPDR S&P 500 ETF Trust"},
                {"label": "Real Estate", "etf": "XLRE", "name": "Real Estate Select Sector SPDR"}
            ],
            "positive": [
                "Gold and tangible commodity assets providing real purchasing power protection."
            ],
            "negative": [
                "Stagnant economic growth coupled with sticky high inflation pressures margin.",
                "Central banks constrained from easing due to persistent price indices."
            ]
        }
    }

    meta = quadrant_meta.get(raw_quad, quadrant_meta["reflation"])
    growth_mom = float(row.get("growth_momentum") or 0.0)
    inf_mom = float(row.get("inflation_momentum") or 0.0)

    growth_score = round(min(98.0, max(20.0, 50.0 + growth_mom * 30.0)), 1)
    inflation_score = round(min(98.0, max(20.0, 50.0 + inf_mom * 25.0)), 1)
    # Continuous rates score from policy_z (Fed Funds 5yr z-score).
    # Positive policy_z = restrictive (higher score = tighter rates = headwind for equities)
    # Negative policy_z = accommodative (lower score = easier financial conditions)
    policy_z = float(row.get("policy_z") or 0.0)
    rates_score = round(min(98.0, max(20.0, 50.0 + policy_z * 15.0)), 1)
    fca_val = float(row.get("fca_score") or 0.0)
    liquidity_score = round(min(98.0, max(20.0, 50.0 - fca_val * 20.0)), 1)
    credit_score = round(min(98.0, max(20.0, 75.0 - fca_val * 25.0)), 1)
    risk_score = round(min(98.0, max(20.0, 40.0 + abs(inf_mom) * 15.0)), 1)

    overall_score = round((growth_score * 0.35 + inflation_score * 0.25 + (100 - rates_score) * 0.15 + liquidity_score * 0.15 + credit_score * 0.10), 1)

    prev_growth = float(prev_row.get("growth_momentum") or 0.0) if prev_row else growth_mom
    prev_inf = float(prev_row.get("inflation_momentum") or 0.0) if prev_row else inf_mom
    prev_growth_score = round(min(98.0, max(20.0, 50.0 + prev_growth * 30.0)), 1)
    prev_inf_score = round(min(98.0, max(20.0, 50.0 + prev_inf * 25.0)), 1)

    prev_dims = {
        "growth": prev_growth_score,
        "inflation": prev_inf_score,
        "rates": rates_score,
        "liquidity": liquidity_score,
        "credit": credit_score,
        "risk": risk_score
    } if prev_row else {}

    raw_conf = float(row.get("confidence") or 0.85)
    conf_pct = round(raw_conf * 100.0, 1) if raw_conf <= 1.0 else round(raw_conf, 1)

    # Dynamic duration computation passed in row or fallback to count
    duration_days = int(row.get("regime_duration_days") or 180)
    avg_duration_days = int(row.get("avg_regime_duration_days") or 120)

    return {
        **row,
        "date": str(row.get("date")),
        "regime": meta["regime_title"],
        "quadrant": meta["display_quad"],
        "severity": meta["severity"],
        "overall_score": overall_score,
        "confidence": conf_pct,
        "fca": {
            "score": fca_val,
            "status": "Accommodative" if fca_val <= 0 else "Tight"
        },
        "policy_stance": (row.get("policy_stance") or "Accommodative").capitalize(),
        "delta_growth": round(growth_mom - prev_growth, 2) if prev_row else round(growth_mom, 2),
        "delta_inflation": round(inf_mom - prev_inf, 2) if prev_row else round(inf_mom, 2),
        "regime_duration_days": duration_days,
        "avg_regime_duration_days": avg_duration_days,
        "dimensions": {
            "growth": growth_score,
            "inflation": inflation_score,
            "rates": rates_score,
            "liquidity": liquidity_score,
            "credit": credit_score,
            "risk": risk_score
        },
        "prev_dimensions": prev_dims,
        "positive": meta["positive"],
        "negative": meta["negative"],
        "favored_assets_with_etf": meta["favored"],
        "avoid_assets_with_etf": meta["avoid"],
        "divergences": [
            f"Growth momentum is at +{growth_mom:.2f} while inflation momentum is at +{inf_mom:.2f}.",
            f"Policy stance remains {(row.get('policy_stance') or 'accommodative').capitalize()} with FCA score at {fca_val:.2f}."
        ]
    }


@router.get("/regime")
def get_regime(
    limit: int = Query(252, le=2000),
    db: Session = Depends(get_db),
):
    """Return market regime history formatted for charts."""
    rows = db.execute(text("""
        SELECT
            date, quadrant, growth_momentum, inflation_momentum,
            fca_score, policy_stance, confidence, scoring_version
        FROM market_regimes
        ORDER BY date ASC
        LIMIT :limit
    """), {"limit": limit}).mappings().all()

    res = []
    for r in rows:
        gm = float(r.get("growth_momentum") or 0.0)
        im = float(r.get("inflation_momentum") or 0.0)
        fca = float(r.get("fca_score") or 0.0)
        pz = float(r.get("policy_z") or 0.0)
        g_sc = round(min(98.0, max(20.0, 50.0 + gm * 30.0)), 1)
        i_sc = round(min(98.0, max(20.0, 50.0 + im * 25.0)), 1)
        r_sc = round(min(98.0, max(20.0, 50.0 + pz * 15.0)), 1)
        l_sc = round(min(98.0, max(20.0, 50.0 - fca * 20.0)), 1)
        c_sc = round(min(98.0, max(20.0, 75.0 - fca * 25.0)), 1)
        rk_sc = round(min(98.0, max(20.0, 40.0 + abs(im) * 15.0)), 1)
        ov_sc = round((g_sc * 0.35 + i_sc * 0.25 + (100 - r_sc) * 0.15 + l_sc * 0.15 + c_sc * 0.10), 1)

        res.append({
            "date": str(r["date"]),
            "quadrant": r["quadrant"],
            "overall_score": ov_sc,
            "growth_score": g_sc,
            "inflation_score": i_sc,
            "rates_score": r_sc,
            "liquidity_score": l_sc,
            "credit_score": c_sc,
            "risk_score": rk_sc,
            "dimensions": {
                "growth": g_sc,
                "inflation": i_sc,
                "rates": r_sc,
                "liquidity": l_sc,
                "credit": c_sc,
                "risk": rk_sc,
            }
        })
    return res


@router.get("/regime/current")
def get_current_regime(db: Session = Depends(get_db)):
    """Return the most recent regime classification enriched for ScoresOverview."""
    rows = db.execute(text("""
        SELECT *
        FROM market_regimes
        ORDER BY date DESC
        LIMIT 2
    """)).mappings().all()

    if not rows:
        return {}

    current_row = dict(rows[0])
    prev_row = dict(rows[1]) if len(rows) > 1 else None

    # Dynamically calculate active regime duration & historical average duration from DB
    current_quad = current_row.get("quadrant")
    all_quads = db.execute(text("SELECT quadrant FROM market_regimes ORDER BY date DESC")).scalars().all()
    consecutive_count = 0
    for q in all_quads:
        if q == current_quad:
            consecutive_count += 1
        else:
            break
    current_row["regime_duration_days"] = consecutive_count * 30

    avg_dur = db.execute(text("""
        WITH episode_groups AS (
            SELECT quadrant,
                   date,
                   SUM(CASE WHEN prev_quad IS NULL OR prev_quad != quadrant THEN 1 ELSE 0 END) OVER (ORDER BY date ASC) as group_id
            FROM (
                SELECT date, quadrant, LAG(quadrant) OVER (ORDER BY date ASC) as prev_quad
                FROM market_regimes
            ) sub
        ),
        episode_lengths AS (
            SELECT group_id, COUNT(*) * 30 as duration_days
            FROM episode_groups
            GROUP BY group_id
        )
        SELECT AVG(duration_days) FROM episode_lengths
    """)).scalar() or 120
    current_row["avg_regime_duration_days"] = int(avg_dur)

    return _format_regime(current_row, prev_row)


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
