import logging
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

# Sector Mapping
SECTOR_NAME_MAP = {
    1: "Technology",
    2: "Healthcare",
    3: "Financials",
    4: "Consumer Cyclical",
    5: "Communication",
    6: "Industrials",
    7: "Consumer Staples",
    8: "Energy",
    9: "Utilities",
    10: "Real Estate",
    11: "Basic Materials"
}

def calculate_macro_regime_fit(
    regime_name: str,
    sector_name: str,
    quality_score: float,
    valuation_score: float,
    growth_score: float
) -> Dict[str, Any]:
    """
    Computes Macro Regime Sensitivity and Fit Score (0-100) based on macro environment & stock factors.
    """
    reg_upper = (regime_name or "").upper()
    sec_upper = (sector_name or "").upper()

    regime_fit_score = 50.0  # Base neutral
    reasons = []

    # 1. Goldilocks / Growth Expansion Regime
    if "GOLDILOCKS" in reg_upper or "EXPANSION" in reg_upper:
        if sec_upper in ["TECHNOLOGY", "FINANCIALS", "INDUSTRIALS"]:
            regime_fit_score += 25.0
            reasons.append("High sector beta aligns with Goldilocks economic expansion.")
        if growth_score >= 70.0:
            regime_fit_score += 15.0
            reasons.append("High earnings growth rate thrives in accommodative macro conditions.")
        if quality_score >= 75.0:
            regime_fit_score += 10.0
            reasons.append("Institutional quality balance sheet provides structural growth tailwinds.")

    # 2. Reflation / Inflationary Boom Regime
    elif "REFLATION" in reg_upper or "INFLATION" in reg_upper:
        if sec_upper in ["ENERGY", "BASIC MATERIALS", "FINANCIALS"]:
            regime_fit_score += 30.0
            reasons.append("Natural resource / financial sector provides inflation hedge.")
        if valuation_score >= 70.0:
            regime_fit_score += 15.0
            reasons.append("Low duration / attractive valuation protects against rising discount rates.")

    # 3. Stagflation / Tightening Regime
    elif "STAGFLATION" in reg_upper:
        if sec_upper in ["ENERGY", "CONSUMER STAPLES", "HEALTHCARE"]:
            regime_fit_score += 25.0
            reasons.append("Defensive inelastic demand sector insulates cash flows.")
        if quality_score >= 80.0:
            regime_fit_score += 20.0
            reasons.append("Ultra-high ROIC and balance sheet liquidity withstand margin compression.")

    # 4. Deflation / Contraction / Recession Regime
    elif "DEFLATION" in reg_upper or "CONTRACTION" in reg_upper or "RECESSION" in reg_upper:
        if sec_upper in ["CONSUMER STAPLES", "HEALTHCARE", "UTILITIES"]:
            regime_fit_score += 30.0
            reasons.append("Non-cyclical defensive earnings profile favored during contraction.")
        if valuation_score >= 75.0 and quality_score >= 75.0:
            regime_fit_score += 15.0
            reasons.append("High FCF yield & low debt insulate against credit tightening.")

    # Fallback default boost for general strong quality
    else:
        if quality_score >= 80.0:
            regime_fit_score += 15.0
            reasons.append("Strong quality fundamentals provide resilience across macro regimes.")

    regime_fit_score = round(min(100.0, max(10.0, regime_fit_score)), 1)
    
    return {
        "regime_fit_score": regime_fit_score,
        "reasons": reasons
    }

def evaluate_macro_sector_candidate(
    stock_scores: Dict[str, float],
    sector_score: float,
    sector_name: str,
    regime_name: str
) -> Dict[str, Any]:
    """
    Synthesizes Stock Score, Sector Leadership Score, and Macro Regime Fit into a unified
    Macro-Sector Investment Candidate evaluation.
    """
    stock_score = stock_scores.get("overall_score", 50.0)
    quality = stock_scores.get("quality_score", 50.0)
    valuation = stock_scores.get("valuation_score", 50.0)
    growth = stock_scores.get("growth_score", 50.0)

    # Calculate Macro Regime Fit
    reg_fit = calculate_macro_regime_fit(regime_name, sector_name, quality, valuation, growth)
    macro_fit_score = reg_fit["regime_fit_score"]

    # Composite Candidate Score Formula:
    # 50% Stock Score + 30% Sector Rotation Score + 20% Macro Regime Fit Score
    composite_candidate_score = round(
        0.50 * stock_score + 0.30 * sector_score + 0.20 * macro_fit_score, 1
    )

    # Classification Category
    if composite_candidate_score >= 80.0:
        category = "Prime Opportunity"
    elif composite_candidate_score >= 70.0:
        category = "High Conviction"
    elif composite_candidate_score >= 55.0:
        category = "Tactical Watchlist"
    else:
        category = "Underweight / Avoid"

    explanations = reg_fit["reasons"]
    if sector_score >= 75.0:
        explanations.append(f"Sector '{sector_name}' exhibits strong leadership momentum (Score: {sector_score:.1f}/100).")
    elif sector_score < 45.0:
        explanations.append(f"Sector '{sector_name}' is currently in a weakening/lagging quadrant (Score: {sector_score:.1f}/100).")

    return {
        "composite_candidate_score": composite_candidate_score,
        "stock_score": stock_score,
        "sector_score": sector_score,
        "macro_fit_score": macro_fit_score,
        "active_regime": regime_name,
        "category": category,
        "explanations": explanations
    }
