import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

def compute_sector_earnings_surprises(
    company_metrics_df: pd.DataFrame,
    company_weights: Dict[str, float] = None
) -> Dict[str, float]:
    """
    Computes cap-weighted EPS surprise % across sector constituent companies.
    """
    if company_metrics_df.empty or "eps_surprise_pct" not in company_metrics_df.columns:
        return {"eps_surprise_pct": 0.035} # Default +3.5% earnings surprise benchmark

    df = company_metrics_df.copy()
    if company_weights and "ticker" in df.columns:
        df["weight"] = df["ticker"].map(lambda t: company_weights.get(t, 1.0))
    else:
        df["weight"] = 1.0

    valid = df.dropna(subset=["eps_surprise_pct"])
    if valid.empty:
        return {"eps_surprise_pct": 0.035}

    total_w = valid["weight"].sum()
    if total_w == 0:
        total_w = 1.0

    weighted_surprise = (valid["eps_surprise_pct"] * valid["weight"]).sum() / total_w
    return {"eps_surprise_pct": round(float(weighted_surprise), 4)}

def compute_cross_sector_surprise_scores(
    sector_surprises_map: Dict[str, float]
) -> Dict[str, float]:
    """
    Converts raw cap-weighted EPS surprises into a 0-100 continuous score
    via Z-score -> Sigmoid normalization across the universe.
    """
    symbols = list(sector_surprises_map.keys())
    if not symbols:
        return {}

    series = pd.Series(sector_surprises_map)
    clean_s = series.dropna()

    if len(clean_s) <= 1 or clean_s.std() == 0:
        return {sym: 50.0 for sym in symbols}

    mean = clean_s.mean()
    std = clean_s.std()
    z = (series - mean) / (std + 1e-8)
    sigmoid_vals = 100.0 / (1.0 + np.exp(-z))

    return {sym: round(float(sigmoid_vals[sym]), 1) for sym in symbols}
