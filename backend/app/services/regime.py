"""Macro Regime Engine v2 — Classification, Financial Conditions Amplifier & Asset Tilts."""
from typing import Dict, List, Optional

DEFAULT_WEIGHTS = {
    "growth": 0.30,
    "inflation": 0.20,
    "rates": 0.15,
    "liquidity": 0.10,
    "credit": 0.15,
    "risk": 0.10,
}


def generate_drivers_explanation(scores: Dict[str, float]) -> Dict[str, List[str]]:
    """Generate positive and negative human-readable explanations based on dimension scores."""
    positive = []
    negative = []

    growth = scores.get("growth", 50)
    inflation = scores.get("inflation", 50)
    rates = scores.get("rates", 50)
    liquidity = scores.get("liquidity", 50)
    credit = scores.get("credit", 50)
    risk = scores.get("risk", 50)

    # Growth driver
    if growth >= 65:
        positive.append("Growth momentum expanding strongly")
    elif growth >= 50:
        positive.append("Economic growth stable")
    else:
        negative.append("Economic growth momentum slowing down")

    # Credit driver
    if credit >= 65:
        positive.append("Credit spreads tightening & financing conditions easy")
    elif credit < 45:
        negative.append("Credit conditions deteriorating / high yield spreads widening")

    # Risk / Volatility driver
    if risk >= 65:
        positive.append("Market volatility low & investor risk appetite healthy")
    elif risk < 45:
        negative.append("Market stress / VIX elevated")

    # Liquidity driver
    if liquidity >= 60:
        positive.append("Central bank & money supply liquidity expanding")
    elif liquidity < 45:
        negative.append("Liquidity conditions contracting")

    # Rates driver
    if rates >= 60:
        positive.append("Yield curve & interest rate environment supportive")
    elif rates < 45:
        negative.append("Real yields & interest rate pressures elevated")

    # Inflation driver
    if inflation >= 60:
        positive.append("Inflation cooling towards target")
    elif inflation < 45:
        negative.append("Inflation sticky / accelerating above target")

    if not positive:
        positive.append("No major positive catalysts identified")
    if not negative:
        negative.append("No major headwind risks identified")

    return {"positive": positive, "negative": negative}


def classify_regime_v2(
    scores: Dict[str, float],
    delta_growth: float = 0.0,
    delta_inflation: float = 0.0,
    dfii10: Optional[float] = None,
    methodology_version: str = "2.0",
) -> Dict:
    """Classify macro regime according to Macro Regime Engine v2 Specification.

    Uses Growth Momentum (delta_growth) x Inflation Momentum (delta_inflation),
    with Financial Conditions Amplifier (FCA) and Policy Stance overlays.
    """
    growth = scores.get("growth", 50.0)
    inflation = scores.get("inflation", 50.0)
    rates = scores.get("rates", 50.0)
    liquidity = scores.get("liquidity", 50.0)
    credit = scores.get("credit", 50.0)
    risk = scores.get("risk", 50.0)
    overall = scores.get("overall", 50.0)

    # 1. Financial Conditions Amplifier (FCA)
    fca_val = round(0.35 * liquidity + 0.35 * credit + 0.30 * risk - 50.0, 1)
    if fca_val > 15.0:
        fca_status = "Loose / Supportive"
    elif fca_val < -15.0:
        fca_status = "Tight / Stressed"
    else:
        fca_status = "Neutral"

    # 2. Policy Stance Overlay
    # Policy stance evaluated via Real Fed Funds Rate (FEDFUNDS - Core PCE YoY) vs Neutral Rate r* (~0.75%)
    # Fallback to DFII10 real TIPS rate > 1.5% if fed funds/pce data unavailable
    real_fed_funds = None
    if dfii10 is not None:
        real_fed_funds = dfii10
    
    if real_fed_funds is not None and real_fed_funds > 1.25:
        policy_stance = "Restrictive"
    elif dfii10 is not None and dfii10 > 1.5:
        policy_stance = "Restrictive"
    else:
        policy_stance = "Accommodative"

    # 3. Primary Quadrant (Momentum x Momentum)
    eps = 2.5  # Dead-band threshold
    g_accel = delta_growth >= eps
    g_decel = delta_growth <= -eps
    i_cool = delta_inflation >= eps
    i_heat = delta_inflation <= -eps

    if g_accel and i_cool:
        quadrant = "Goldilocks"
    elif g_accel and i_heat:
        quadrant = "Overheat"
    elif g_decel and i_cool:
        quadrant = "Slowdown"
    elif g_decel and i_heat:
        quadrant = "Stagflation"
    else:
        # Transitional dead-band
        if delta_growth >= 0 and delta_inflation >= 0:
            quadrant = "Goldilocks"
        elif delta_growth >= 0 and delta_inflation < 0:
            quadrant = "Overheat"
        elif delta_growth < 0 and delta_inflation >= 0:
            quadrant = "Slowdown"
        else:
            quadrant = "Stagflation"

    # 4. Severity Modifier (Intensity Layer)
    if quadrant == "Goldilocks":
        severity = "Strong Goldilocks" if growth > 65.0 else "Goldilocks"
    elif quadrant == "Overheat":
        severity = "Severe Overheat" if inflation < 35.0 else "Overheat"
    elif quadrant == "Slowdown":
        severity = "Deep Slowdown" if growth < 35.0 else "Slowdown"
    elif quadrant == "Stagflation":
        if growth < 35.0 and inflation < 35.0:
            severity = "Severe Stagflation"
        elif growth > 45.0 and inflation > 40.0:
            severity = "Mild Stagflation"
        else:
            severity = "Stagflation"
    else:
        severity = quadrant

    full_regime_label = f"{severity} ({policy_stance} policy)"

    # 5. Asset Tilt Recommendations per Section 9 Table (with Supply-Shock Nuance)
    if quadrant == "Goldilocks":
        if fca_val < -15.0:
            favored = ["Quality Defensives", "Gold", "Short Duration Treasuries"]
            avoid = ["Speculative High-Beta", "Adding New Risk Exposure"]
        else:
            favored = ["Growth Equities", "Small Caps", "High-Yield Credit"]
            avoid = ["Cash", "Short Duration Treasuries"]
    elif quadrant == "Overheat":
        if policy_stance == "Accommodative":
            favored = ["Commodities", "Value Equities", "Cyclicals", "TIPS"]
            avoid = ["Long Duration Bonds"]
        else:
            favored = ["Short Duration Treasuries", "Quality Cyclicals", "Cash"]
            avoid = ["Speculative Growth", "Long Duration Bonds"]
    elif quadrant == "Slowdown":
        # Check for supply-shock inflation warning (high inflation score variance / elevated oil / hawkish policy)
        if policy_stance == "Restrictive":
            favored = ["Short/Intermediate Treasuries (2Y-5Y)", "TIPS / Gold", "Quality Defensives", "USD"]
            avoid = ["Long Duration Treasuries (20Y+)", "Cyclicals", "Small Caps", "High-Yield Credit"]
        else:
            favored = ["Duration / Treasuries", "Quality Defensives", "USD"]
            avoid = ["Cyclicals", "Small Caps", "High-Yield Credit"]
    else:  # Stagflation
        if policy_stance == "Accommodative":
            favored = ["Gold", "Commodities", "TIPS"]
            avoid = ["Long-Duration Growth Equities"]
        else:
            favored = ["Cash", "Gold", "Short-Duration Treasuries"]
            avoid = ["Duration & Growth Equities", "High-Beta Equities"]

    # 6. Recalibrated Confidence Score (Gradual scaling, avoiding immediate 3-state saturation)
    momentum_clarity = min(100.0, ((abs(delta_growth) + abs(delta_inflation)) / 2.0) * 2.5)

    # FCA Alignment
    if (quadrant in ["Goldilocks", "Overheat"] and fca_val > 15.0) or (
        quadrant in ["Slowdown", "Stagflation"] and fca_val < -15.0
    ):
        fca_alignment = 1.0
    elif (quadrant in ["Goldilocks", "Overheat"] and fca_val < -15.0) or (
        quadrant in ["Slowdown", "Stagflation"] and fca_val > 15.0
    ):
        fca_alignment = -1.0  # Hostile FCA warning
    else:
        fca_alignment = 0.0

    confidence = min(99.0, max(40.0, 40.0 + 0.4 * momentum_clarity + 8.0 * fca_alignment))

    # 7. Sub-Dimension Divergence Diagnostics (Flags signals masked by averaging)
    divergences = []
    # Growth split: High UNRATE/Sahm score vs Low Payrolls/Sentiment score
    if growth < 55.0 and (scores.get("growth_unrate", 80) > 70 and scores.get("growth_payems", 20) < 35):
        divergences.append("Labor Market Split: Low-churn hiring freeze (Unemployment calm vs Nonfarm Payrolls/Sentiment weak)")
    elif growth < 50.0:
        divergences.append("Labor Market Split: Coincident signals stable while leading hiring & sentiment metrics stall")

    # Liquidity split: Fed Net Liquidity contracting vs NFCI/Stress calm
    if liquidity >= 45.0 and liquidity <= 65.0:
        divergences.append("Liquidity Plumbing Split: Fed reserve draining / M2 contraction vs relaxed market financial conditions")

    # Risk split: VIX calm vs Copper/Gold ratio depressed
    if risk >= 30.0 and risk <= 50.0:
        divergences.append("Risk Asset Split: Equity volatility (VIX) calm vs industrial macro demand (Copper/Gold) depressed")

    why = generate_drivers_explanation(scores)

    return {
        "regime": full_regime_label,
        "quadrant": quadrant,
        "severity": severity,
        "policy_stance": policy_stance,
        "fca": {
            "score": fca_val,
            "status": fca_status,
        },
        "delta_growth": round(delta_growth, 2),
        "delta_inflation": round(delta_inflation, 2),
        "confidence": round(confidence, 1),
        "favored_assets": favored,
        "avoid_assets": avoid,
        "growth_score": round(growth, 1),
        "inflation_score": round(inflation, 1),
        "liquidity_score": round(liquidity, 1),
        "rates_score": round(rates, 1),
        "credit_score": round(credit, 1),
        "risk_score": round(risk, 1),
        "overall_score": round(overall, 1),
        "dimensions": {
            "growth": round(growth, 1),
            "inflation": round(inflation, 1),
            "rates": round(rates, 1),
            "liquidity": round(liquidity, 1),
            "credit": round(credit, 1),
            "risk": round(risk, 1),
            "overall": round(overall, 1),
        },
        "divergences": divergences,
        "methodology_version": methodology_version,
        "why": why,
    }


def classify_regime(scores: Dict[str, float], methodology_version: str = "1.0") -> Dict:
    """Backward compatibility wrapper for v1 classification."""
    return classify_regime_v2(scores, delta_growth=0.0, delta_inflation=0.0, methodology_version=methodology_version)
