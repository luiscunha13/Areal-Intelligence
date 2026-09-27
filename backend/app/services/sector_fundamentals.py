import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

def compute_sector_fundamental_metrics(
    company_metrics_df: pd.DataFrame,
    company_weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Aggregates company-level SEC EDGAR financial metrics into sector/industry group fundamental signals.
    
    Returns:
      - eps_growth_yoy (float)
      - revenue_growth_yoy (float)
      - margin_trend (float)
      - quality_flag (str: 'Clean growth', 'Diluted growth', 'Neutral / Contraction')
      - capex_growth_yoy (float)
      - pe_ratio_ttm (float)
    """
    if company_metrics_df.empty:
        return {
            "eps_growth_yoy": 0.05,
            "revenue_growth_yoy": 0.06,
            "margin_trend": 0.005,
            "quality_flag": "Clean growth",
            "capex_growth_yoy": 0.04,
            "pe_ratio_ttm": 22.0,
        }

    df = company_metrics_df.copy()
    if company_weights and "ticker" in df.columns:
        df["weight"] = df["ticker"].map(lambda t: company_weights.get(t, 1.0))
    else:
        df["weight"] = 1.0

    total_weight = df["weight"].sum()
    if total_weight == 0:
        total_weight = 1.0

    # Cap-weighted metrics
    eps_growth = float((df["eps_growth_yoy"] * df["weight"]).sum() / total_weight) if "eps_growth_yoy" in df.columns else 0.05
    rev_growth = float((df["revenue_growth_yoy"] * df["weight"]).sum() / total_weight) if "revenue_growth_yoy" in df.columns else 0.06
    
    if "operating_margin" in df.columns and "prev_operating_margin" in df.columns:
        margin_trend = float(((df["operating_margin"] - df["prev_operating_margin"]) * df["weight"]).sum() / total_weight)
    elif "margin_trend" in df.columns:
        margin_trend = float((df["margin_trend"] * df["weight"]).sum() / total_weight)
    else:
        margin_trend = 0.005

    capex_growth = float((df["capex_growth_yoy"] * df["weight"]).sum() / total_weight) if "capex_growth_yoy" in df.columns else 0.04

    pe_ratio = float((df["pe_ratio"] * df["weight"]).sum() / total_weight) if "pe_ratio" in df.columns else 22.0

    # Quality Flag
    if rev_growth > 0 and margin_trend >= 0:
        quality_flag = "Clean growth"
    elif rev_growth > 0 and margin_trend < 0:
        quality_flag = "Diluted growth"
    else:
        quality_flag = "Neutral / Contraction"

    return {
        "eps_growth_yoy": round(eps_growth, 4),
        "revenue_growth_yoy": round(rev_growth, 4),
        "margin_trend": round(margin_trend, 4),
        "quality_flag": quality_flag,
        "capex_growth_yoy": round(capex_growth, 4),
        "pe_ratio_ttm": round(pe_ratio, 2),
    }

def compute_historical_pe_percentile(current_pe: float, historical_pes: List[float]) -> float:
    """
    Computes percentile rank of current P/E ratio within its 5-10 year historical distribution (0-100%).
    Lower percentile indicates relatively cheaper valuation.
    """
    if not historical_pes:
        return 50.0

    clean_pes = [p for p in historical_pes if pd.notnull(p) and p > 0]
    if not clean_pes:
        return 50.0

    count_below = sum(1 for p in clean_pes if p <= current_pe)
    percentile = (count_below / len(clean_pes)) * 100.0
    return round(float(percentile), 1)

def compute_cross_sector_fundamental_scores(
    sector_fundamentals_today: Dict[str, Dict[str, Any]],
    historical_pe_map: Optional[Dict[str, List[float]]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Computes cross-sectional Z-score -> Sigmoid normalized Growth-Quality composite score (0-100)
    and valuation percentiles across the universe.
    
    Composite Weights:
      - 35% Trailing EPS Growth
      - 35% Revenue Growth & Margin Trend
      - 30% Capex Growth
    """
    symbols = list(sector_fundamentals_today.keys())
    if not symbols:
        return {}

    raw_scores = {}
    pe_percentiles = {}

    for sym, fun in sector_fundamentals_today.items():
        eps_g = fun.get("eps_growth_yoy", 0.05)
        rev_g = fun.get("revenue_growth_yoy", 0.06)
        m_trend = fun.get("margin_trend", 0.005)
        capex_g = fun.get("capex_growth_yoy", 0.04)
        pe_curr = fun.get("pe_ratio_ttm", 22.0)

        # Unblended Growth-Quality raw value
        raw_val = (0.35 * eps_g) + (0.35 * (rev_g + m_trend * 2.0)) + (0.30 * capex_g)
        raw_scores[sym] = raw_val

        hist_pes = (historical_pe_map or {}).get(sym, [])
        pe_percentiles[sym] = compute_historical_pe_percentile(pe_curr, hist_pes)

    # Cross-Sectional Z-Score -> Sigmoid transform
    s_series = pd.Series(raw_scores)
    mean = s_series.mean()
    std = s_series.std()
    if std == 0 or pd.isnull(std):
        z_scores = pd.Series(0.0, index=s_series.index)
    else:
        z_scores = (s_series - mean) / std

    sigmoid_scores = 100.0 / (1.0 + np.exp(-z_scores))

    results = {}
    for sym in symbols:
        fun = sector_fundamentals_today[sym].copy()
        fun["fundamental_score"] = round(float(sigmoid_scores[sym]), 1)
        fun["pe_percentile_5y"] = pe_percentiles.get(sym, 50.0)
        results[sym] = fun

    return results
