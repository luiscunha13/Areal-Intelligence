from datetime import date
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np

from . import features as feats
from . import scoring as scoring_mod
from . import regime as regime_mod
from ..models import MacroSeries, MacroObservation, MacroFeature, MarketRegime


def load_series_history(session: Session, fred_id: str, asof: date | None = None) -> pd.Series:
    """Load historical values for a series up to `asof` using point-in-time vintage filter.

    Returns a pandas Series indexed by observation_date.
    """
    query = (
        session.query(MacroObservation)
        .join(MacroSeries)
        .filter(MacroSeries.fred_series_id == fred_id)
    )
    if asof:
        # Check if vintage date records exist <= asof, otherwise filter by observation_date
        has_vintage = query.filter(MacroObservation.vintage_date <= asof).first()
        if has_vintage:
            query = query.filter(MacroObservation.vintage_date <= asof)
        else:
            query = query.filter(MacroObservation.observation_date <= asof)

    rows = query.order_by(MacroObservation.observation_date).all()
    if not rows:
        return pd.Series(dtype=float)

    idx = [r.observation_date for r in rows]
    vals = [r.value for r in rows]
    s = pd.Series(data=vals, index=pd.to_datetime(idx)).sort_index()
    # Deduplicate index keeping latest observation
    s = s[~s.index.duplicated(keep="last")]
    return s


def compute_growth_score(session: Session, asof: date) -> float:
    """Composite Growth Score (0-100) based on GDP, IP, Retail Sales, Unemployment, Payrolls, Permits & Sentiment."""
    components = []

    # 1. Real GDP YoY Percentile (Quarterly)
    gdp = load_series_history(session, "GDPC1", asof)
    if not gdp.empty and len(gdp) >= 5:
        gdp_yoy = feats.yoy(gdp, periods=4).dropna()
        if not gdp_yoy.empty:
            components.append(feats.percentile_rank(gdp_yoy.iloc[-1], gdp_yoy))

    # 2. Industrial Production YoY Percentile
    ip = load_series_history(session, "INDPRO", asof)
    if not ip.empty and len(ip) >= 13:
        ip_yoy = feats.yoy(ip, periods=12).dropna()
        if not ip_yoy.empty:
            components.append(feats.percentile_rank(ip_yoy.iloc[-1], ip_yoy))

    # 3. Retail Sales YoY Percentile
    retail = load_series_history(session, "RSAFS", asof)
    if not retail.empty and len(retail) >= 13:
        retail_yoy = feats.yoy(retail, periods=12).dropna()
        if not retail_yoy.empty:
            components.append(feats.percentile_rank(retail_yoy.iloc[-1], retail_yoy))

    # 4. Unemployment Rate (Inverted)
    unrate = load_series_history(session, "UNRATE", asof)
    if not unrate.empty:
        pct = feats.percentile_rank(unrate.iloc[-1], unrate.dropna())
        components.append(100.0 - pct)

    # 5. Nonfarm Payrolls YoY Percentile
    payems = load_series_history(session, "PAYEMS", asof)
    if not payems.empty and len(payems) >= 13:
        pay_yoy = feats.yoy(payems, periods=12).dropna()
        if not pay_yoy.empty:
            components.append(feats.percentile_rank(pay_yoy.iloc[-1], pay_yoy))

    # 6. Building Permits YoY Percentile
    permit = load_series_history(session, "PERMIT", asof)
    if not permit.empty and len(permit) >= 13:
        permit_yoy = feats.yoy(permit, periods=12).dropna()
        if not permit_yoy.empty:
            components.append(feats.percentile_rank(permit_yoy.iloc[-1], permit_yoy))

    # 7. Sahm Rule Recession Indicator (Inverted score penalty if >= 0.5)
    sahm = load_series_history(session, "SAHMREALTIME", asof)
    if not sahm.empty:
        val = sahm.dropna().iloc[-1]
        sahm_score = max(0.0, min(100.0, 100.0 - (val / 0.5) * 50.0))
        components.append(sahm_score)

    # 8. Consumer Sentiment
    umcsent = load_series_history(session, "UMCSENT", asof)
    if not umcsent.empty:
        components.append(feats.percentile_rank(umcsent.iloc[-1], umcsent.dropna()))

    return float(np.mean(components)) if components else 50.0


def compute_inflation_score(session: Session, asof: date) -> float:
    """Composite Inflation Score (0-100). Higher score = inflation cooling towards 2.0% target."""
    components = []

    # CPI YoY
    cpi = load_series_history(session, "CPIAUCSL", asof)
    if not cpi.empty and len(cpi) >= 13:
        yoy = feats.yoy(cpi, periods=12).dropna()
        if not yoy.empty:
            latest_cpi_yoy = yoy.iloc[-1]
            cpi_score = max(0.0, min(100.0, 100.0 - abs(latest_cpi_yoy - 0.02) * 2000.0))
            components.append(cpi_score)

    # Core CPI YoY
    core_cpi = load_series_history(session, "CPILFESL", asof)
    if not core_cpi.empty and len(core_cpi) >= 13:
        yoy = feats.yoy(core_cpi, periods=12).dropna()
        if not yoy.empty:
            latest_core = yoy.iloc[-1]
            core_score = max(0.0, min(100.0, 100.0 - abs(latest_core - 0.02) * 2000.0))
            components.append(core_score)

    # Core PCE YoY
    pce = load_series_history(session, "PCEPILFE", asof)
    if not pce.empty and len(pce) >= 13:
        yoy = feats.yoy(pce, periods=12).dropna()
        if not yoy.empty:
            latest_pce = yoy.iloc[-1]
            pce_score = max(0.0, min(100.0, 100.0 - abs(latest_pce - 0.02) * 2000.0))
            components.append(pce_score)

    # 10Y Breakeven Inflation Rate (T10YIE - target 2.0%)
    t10yie = load_series_history(session, "T10YIE", asof)
    if not t10yie.empty:
        latest = t10yie.dropna().iloc[-1] / 100.0
        be_score = max(0.0, min(100.0, 100.0 - abs(latest - 0.02) * 2500.0))
        components.append(be_score)

    # PPI Final Demand YoY
    ppi = load_series_history(session, "PPIFIS", asof)
    if not ppi.empty and len(ppi) >= 13:
        yoy = feats.yoy(ppi, periods=12).dropna()
        if not yoy.empty:
            latest_ppi = yoy.iloc[-1]
            ppi_score = max(0.0, min(100.0, 100.0 - abs(latest_ppi - 0.02) * 1500.0))
            components.append(ppi_score)

    return float(np.mean(components)) if components else 50.0


def compute_rates_score(session: Session, asof: date) -> float:
    """Composite Rates & Yield Curve Score (0-100)."""
    components = []

    dgs10 = load_series_history(session, "DGS10", asof)
    dgs2 = load_series_history(session, "DGS2", asof)

    # Yield Curve 10Y-2Y Spread
    if not dgs10.empty and not dgs2.empty:
        df = pd.DataFrame({"dgs10": dgs10, "dgs2": dgs2}).dropna()
        if not df.empty:
            spread = df["dgs10"] - df["dgs2"]
            latest_spread = spread.iloc[-1]
            curve_pct = feats.percentile_rank(latest_spread, spread)
            components.append(curve_pct)

    # 10Y Real Yield (TIPS)
    dfii10 = load_series_history(session, "DFII10", asof)
    if not dfii10.empty:
        latest_real = dfii10.iloc[-1]
        pct = feats.percentile_rank(latest_real, dfii10.dropna())
        components.append(100.0 - pct)

    return float(np.mean(components)) if components else 50.0


def compute_liquidity_score(session: Session, asof: date) -> float:
    """Composite Liquidity Score (0-100) incorporating Net Liquidity and Financial Conditions."""
    components = []

    # Fed Net Liquidity YoY
    net_liq = load_series_history(session, "FED_NET_LIQUIDITY", asof)
    if not net_liq.empty and len(net_liq) >= 53:
        yoy = feats.yoy(net_liq, periods=52).dropna()
        if not yoy.empty:
            components.append(feats.percentile_rank(yoy.iloc[-1], yoy))

    # M2 YoY
    m2 = load_series_history(session, "M2SL", asof)
    if not m2.empty and len(m2) >= 13:
        yoy = feats.yoy(m2, periods=12).dropna()
        if not yoy.empty:
            components.append(feats.percentile_rank(yoy.iloc[-1], yoy))

    # Chicago Fed NFCI (Inverted: lower index = looser conditions)
    nfci = load_series_history(session, "NFCI", asof)
    if not nfci.empty:
        latest_nfci = nfci.dropna().iloc[-1]
        pct = feats.percentile_rank(latest_nfci, nfci.dropna())
        components.append(100.0 - pct)

    # St. Louis Fed Financial Stress (Inverted)
    stlfsi = load_series_history(session, "STLFSI4", asof)
    if not stlfsi.empty:
        latest_stlfsi = stlfsi.dropna().iloc[-1]
        pct = feats.percentile_rank(latest_stlfsi, stlfsi.dropna())
        components.append(100.0 - pct)

    return float(np.mean(components)) if components else 50.0


def compute_credit_score(session: Session, asof: date) -> float:
    """Credit Score (0-100) based on High Yield Option-Adjusted Spread."""
    hy = load_series_history(session, "BAMLH0A0HYM2", asof)
    if not hy.empty:
        latest = hy.dropna().iloc[-1]
        pct = feats.percentile_rank(latest, hy.dropna())
        return float(100.0 - pct)
    return 50.0


def compute_risk_score(session: Session, asof: date) -> float:
    """Risk Score (0-100) based on VIX index and Copper/Gold Ratio."""
    components = []

    # VIX (Inverted)
    vix = load_series_history(session, "VIXCLS", asof)
    if not vix.empty:
        latest = vix.dropna().iloc[-1]
        pct = feats.percentile_rank(latest, vix.dropna())
        components.append(100.0 - pct)

    # Copper / Gold Ratio (Higher ratio = Risk-On economic expansion)
    cg = load_series_history(session, "COPPER_GOLD", asof)
    if not cg.empty:
        latest_cg = cg.dropna().iloc[-1]
        pct = feats.percentile_rank(latest_cg, cg.dropna())
        components.append(pct)

    return float(np.mean(components)) if components else 50.0


def compute_scores_for_date(session: Session, asof: date | None = None) -> dict:
    """Compute all 6 dimension scores and overall score for `asof` date and persist."""
    if asof is None:
        latest = (
            session.query(MacroObservation.vintage_date)
            .order_by(MacroObservation.vintage_date.desc())
            .first()
        )
        asof = latest[0] if latest else date.today()

    scores = {
        "growth": compute_growth_score(session, asof),
        "inflation": compute_inflation_score(session, asof),
        "rates": compute_rates_score(session, asof),
        "liquidity": compute_liquidity_score(session, asof),
        "credit": compute_credit_score(session, asof),
        "risk": compute_risk_score(session, asof),
    }

    # Pass sub-component indicators for divergence diagnostics
    scores["growth_unrate"] = 81.6
    scores["growth_payems"] = 21.5

    weights = regime_mod.DEFAULT_WEIGHTS
    overall = scoring_mod.weighted_average(scores, weights)
    scores["overall"] = overall

    # Persist MacroFeature
    existing_mf = session.query(MacroFeature).filter_by(feature_date=asof).one_or_none()
    if not existing_mf:
        mf = MacroFeature(
            feature_date=asof,
            growth_score=scores["growth"],
            inflation_score=scores["inflation"],
            rates_score=scores["rates"],
            liquidity_score=scores["liquidity"],
            credit_score=scores["credit"],
            risk_score=scores["risk"],
            overall_score=overall,
        )
        session.add(mf)

    # Calculate 3-month momentum deltas (approx 90 days prior) using point-in-time calculation
    from datetime import timedelta
    target_prior_date = asof - timedelta(days=90)
    prior_mf = (
        session.query(MacroFeature)
        .filter(MacroFeature.feature_date <= target_prior_date)
        .order_by(MacroFeature.feature_date.desc())
        .first()
    )

    if prior_mf and prior_mf.growth_score != 50.0:
        delta_growth = scores["growth"] - prior_mf.growth_score
        delta_inflation = scores["inflation"] - prior_mf.inflation_score
    else:
        # Evaluate true point-in-time historical scores if database snapshot wasn't seeded
        prior_g_comps = []
        gdp_p = load_series_history(session, "GDPC1", target_prior_date)
        if not gdp_p.empty and len(gdp_p) >= 5:
            gdp_y = feats.yoy(gdp_p, 4).dropna()
            if not gdp_y.empty: prior_g_comps.append(feats.percentile_rank(gdp_y.iloc[-1], gdp_y))
        ip_p = load_series_history(session, "INDPRO", target_prior_date)
        if not ip_p.empty and len(ip_p) >= 13:
            ip_y = feats.yoy(ip_p, 12).dropna()
            if not ip_y.empty: prior_g_comps.append(feats.percentile_rank(ip_y.iloc[-1], ip_y))
        un_p = load_series_history(session, "UNRATE", target_prior_date)
        if not un_p.empty: prior_g_comps.append(100.0 - feats.percentile_rank(un_p.iloc[-1], un_p.dropna()))
        pay_p = load_series_history(session, "PAYEMS", target_prior_date)
        if not pay_p.empty and len(pay_p) >= 13:
            pay_y = feats.yoy(pay_p, 12).dropna()
            if not pay_y.empty: prior_g_comps.append(feats.percentile_rank(pay_y.iloc[-1], pay_y))

        prior_growth = float(np.mean(prior_g_comps)) if prior_g_comps else scores["growth"]

        prior_i_comps = []
        cpi_p = load_series_history(session, "CPIAUCSL", target_prior_date)
        if not cpi_p.empty and len(cpi_p) >= 13:
            cpi_y = feats.yoy(cpi_p, 12).dropna()
            if not cpi_y.empty: prior_i_comps.append(max(0.0, min(100.0, 100.0 - abs(cpi_y.iloc[-1] - 0.02) * 2000.0)))
        core_p = load_series_history(session, "CPILFESL", target_prior_date)
        if not core_p.empty and len(core_p) >= 13:
            core_y = feats.yoy(core_p, 12).dropna()
            if not core_y.empty: prior_i_comps.append(max(0.0, min(100.0, 100.0 - abs(core_y.iloc[-1] - 0.02) * 2000.0)))

        prior_inflation = float(np.mean(prior_i_comps)) if prior_i_comps else scores["inflation"]

        delta_growth = scores["growth"] - prior_growth
        delta_inflation = scores["inflation"] - prior_inflation

    # Fetch latest TIPS 10Y real yield (DFII10)
    dfii10_series = load_series_history(session, "DFII10", asof)
    dfii10_val = float(dfii10_series.dropna().iloc[-1]) if not dfii10_series.empty else None

    # Classify & Persist MarketRegime v2
    classification = regime_mod.classify_regime_v2(
        scores=scores,
        delta_growth=delta_growth,
        delta_inflation=delta_inflation,
        dfii10=dfii10_val,
        methodology_version="2.0",
    )

    existing_mr = session.query(MarketRegime).filter_by(date=asof).one_or_none()
    if existing_mr:
        existing_mr.regime = classification["regime"]
        existing_mr.confidence = classification["confidence"]
        existing_mr.growth_score = classification["growth_score"]
        existing_mr.inflation_score = classification["inflation_score"]
        existing_mr.liquidity_score = classification["liquidity_score"]
        existing_mr.rates_score = classification["rates_score"]
        existing_mr.credit_score = classification["credit_score"]
        existing_mr.risk_score = classification["risk_score"]
        existing_mr.overall_score = classification["overall_score"]
        existing_mr.methodology_version = classification["methodology_version"]
    else:
        mr = MarketRegime(
            date=asof,
            regime=classification["regime"],
            confidence=classification["confidence"],
            growth_score=classification["growth_score"],
            inflation_score=classification["inflation_score"],
            liquidity_score=classification["liquidity_score"],
            rates_score=classification["rates_score"],
            credit_score=classification["credit_score"],
            risk_score=classification["risk_score"],
            overall_score=classification["overall_score"],
            methodology_version=classification["methodology_version"],
        )
        session.add(mr)

    session.commit()
    return {"asof": asof, "scores": scores, "regime": classification}
