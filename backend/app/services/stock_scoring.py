import pandas as pd
import numpy as np
import math
from typing import Dict, List, Any, Optional

STOCK_SCORE_WEIGHTS = {
    "quality": 0.25,
    "growth": 0.20,
    "valuation": 0.20,
    "earnings": 0.15,
    "technical": 0.10,
    "relative_strength": 0.10,
}

def sigmoid_normalize(series: pd.Series, invert: bool = False, min_score: float = 10.0, max_score: float = 100.0) -> pd.Series:
    """
    Normalizes a numerical series cross-sectionally using Z-Score -> Sigmoid transform.
    Missing NaN values are filled with population median (yielding a neutral 50.0 Z-score)
    so missing metrics don't break composite score computation.
    """
    clean_s = series.dropna()
    if len(clean_s) <= 1 or clean_s.std() == 0:
        return pd.Series(50.0, index=series.index)

    median = clean_s.median()
    filled_s = series.fillna(median)
    
    mean = clean_s.mean()
    std = clean_s.std()
    
    # Calculate Z-score
    z = (filled_s - mean) / (std + 1e-8)
    if invert:
        z = -z

    # Sigmoid mapping to 0-100
    sigmoid_vals = 100.0 / (1.0 + np.exp(-z))
    
    # Bound within range
    return sigmoid_vals.clip(lower=min_score, upper=max_score).round(1)

def calculate_cross_sectional_stock_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes cross-sectionally normalized stock sub-scores (0-100) across a cohort/universe of companies.
    """
    res = df.copy()
    
    # 1. Quality Subscore Factors
    q_roic = sigmoid_normalize(res.get("roic", pd.Series(np.nan, index=res.index)))
    q_roe = sigmoid_normalize(res.get("roe", pd.Series(np.nan, index=res.index)))
    q_op_margin = sigmoid_normalize(res.get("operating_margin", pd.Series(np.nan, index=res.index)))
    q_fcf_margin = sigmoid_normalize(res.get("fcf_margin", pd.Series(np.nan, index=res.index)))
    q_dte = sigmoid_normalize(res.get("debt_to_equity", pd.Series(np.nan, index=res.index)), invert=True)

    res["quality_score"] = (0.25 * q_roic + 0.25 * q_roe + 0.20 * q_op_margin + 0.15 * q_fcf_margin + 0.15 * q_dte).round(1)

    # 2. Growth Subscore Factors
    g_rev = sigmoid_normalize(res.get("revenue_growth_yoy", pd.Series(np.nan, index=res.index)))
    g_eps = sigmoid_normalize(res.get("eps_growth_yoy", pd.Series(np.nan, index=res.index)))
    g_fcf = sigmoid_normalize(res.get("fcf_growth_yoy", pd.Series(np.nan, index=res.index)))

    res["growth_score"] = (0.40 * g_rev + 0.35 * g_eps + 0.25 * g_fcf).round(1)

    # 3. Valuation Subscore Factors (Cheaper = Inverted Z-Score = Higher Score)
    v_pe = sigmoid_normalize(res.get("pe_ratio", pd.Series(np.nan, index=res.index)), invert=True)
    v_fwd_pe = sigmoid_normalize(res.get("forward_pe", pd.Series(np.nan, index=res.index)), invert=True)
    v_ev_ebitda = sigmoid_normalize(res.get("ev_to_ebitda", pd.Series(np.nan, index=res.index)), invert=True)
    v_fcf_yield = sigmoid_normalize(res.get("fcf_yield", pd.Series(np.nan, index=res.index)))

    res["valuation_score"] = (0.30 * v_pe + 0.30 * v_fwd_pe + 0.20 * v_ev_ebitda + 0.20 * v_fcf_yield).round(1)

    # 4. Earnings Subscore Factors
    e_eps_surp = sigmoid_normalize(res.get("eps_surprise_pct", pd.Series(np.nan, index=res.index)))
    e_rev_surp = sigmoid_normalize(res.get("revenue_surprise_pct", pd.Series(np.nan, index=res.index)))

    res["earnings_score"] = (0.60 * e_eps_surp + 0.40 * e_rev_surp).round(1)

    # 5. Technical Subscore Factors
    close = res.get("close", pd.Series(np.nan, index=res.index))
    sma50 = res.get("sma_50", pd.Series(np.nan, index=res.index))
    sma200 = res.get("sma_200", pd.Series(np.nan, index=res.index))
    rsi = res.get("rsi_14", pd.Series(np.nan, index=res.index))

    dist_sma200 = sigmoid_normalize((close - sma200) / (sma200 + 1e-8))
    dist_sma50 = sigmoid_normalize((close - sma50) / (sma50 + 1e-8))
    rsi_score = sigmoid_normalize(rsi)

    res["technical_score"] = (0.40 * dist_sma200 + 0.35 * dist_sma50 + 0.25 * rsi_score).round(1)

    # 6. Relative Strength Subscore Factors
    rs_sp500 = sigmoid_normalize(res.get("relative_strength_sp500", pd.Series(np.nan, index=res.index)))
    rs_sec = sigmoid_normalize(res.get("relative_strength_sector", pd.Series(np.nan, index=res.index)))

    res["relative_strength_score"] = (0.60 * rs_sp500 + 0.40 * rs_sec).round(1)

    # 7. Composite Score Calculation
    res["overall_score"] = (
        STOCK_SCORE_WEIGHTS["quality"] * res["quality_score"] +
        STOCK_SCORE_WEIGHTS["growth"] * res["growth_score"] +
        STOCK_SCORE_WEIGHTS["valuation"] * res["valuation_score"] +
        STOCK_SCORE_WEIGHTS["earnings"] * res["earnings_score"] +
        STOCK_SCORE_WEIGHTS["technical"] * res["technical_score"] +
        STOCK_SCORE_WEIGHTS["relative_strength"] * res["relative_strength_score"]
    ).round(1)

    return res

def calculate_stock_subscores(metrics: Dict[str, Any], price_features: Dict[str, Any]) -> Dict[str, float]:
    """
    Wrapper for single-company score calculation when raw metrics & price features are provided.
    Evaluates against population baseline context.
    """
    single_df = pd.DataFrame([{
        "roic": metrics.get("roic"),
        "roe": metrics.get("roe"),
        "operating_margin": metrics.get("operating_margin"),
        "fcf_margin": metrics.get("fcf_margin"),
        "debt_to_equity": metrics.get("debt_to_equity"),
        "revenue_growth_yoy": metrics.get("revenue_growth_yoy"),
        "eps_growth_yoy": metrics.get("eps_growth_yoy"),
        "fcf_growth_yoy": metrics.get("fcf_growth_yoy"),
        "pe_ratio": metrics.get("pe_ratio"),
        "forward_pe": metrics.get("forward_pe"),
        "ev_to_ebitda": metrics.get("ev_to_ebitda"),
        "fcf_yield": metrics.get("fcf_yield"),
        "eps_surprise_pct": metrics.get("eps_surprise_pct"),
        "revenue_surprise_pct": metrics.get("revenue_surprise_pct"),
        "close": price_features.get("close"),
        "sma_50": price_features.get("sma_50"),
        "sma_200": price_features.get("sma_200"),
        "rsi_14": price_features.get("rsi_14"),
        "relative_strength_sp500": price_features.get("relative_strength_sp500"),
        "relative_strength_sector": price_features.get("relative_strength_sector"),
    }]).astype(float)

    baseline = pd.DataFrame([{
        "roic": 0.12, "roe": 0.15, "operating_margin": 0.15, "fcf_margin": 0.12, "debt_to_equity": 0.8,
        "revenue_growth_yoy": 0.08, "eps_growth_yoy": 0.10, "fcf_growth_yoy": 0.08,
        "pe_ratio": 22.0, "forward_pe": 18.0, "ev_to_ebitda": 14.0, "fcf_yield": 0.04,
        "eps_surprise_pct": 0.05, "revenue_surprise_pct": 0.02,
        "close": 100.0, "sma_50": 95.0, "sma_200": 90.0, "rsi_14": 55.0,
        "relative_strength_sp500": 0.0, "relative_strength_sector": 0.0
    }]).astype(float)

    combined = pd.concat([single_df, baseline], ignore_index=True)
    scored = calculate_cross_sectional_stock_scores(combined)
    row = scored.iloc[0]

    return {
        "quality_score": float(row["quality_score"]),
        "growth_score": float(row["growth_score"]),
        "valuation_score": float(row["valuation_score"]),
        "earnings_score": float(row["earnings_score"]),
        "technical_score": float(row["technical_score"]),
        "relative_strength_score": float(row["relative_strength_score"]),
        "overall_score": float(row["overall_score"]),
    }
