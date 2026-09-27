import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

def fit_macro_sensitivity_regression(
    sector_returns_df: pd.DataFrame,
    macro_momentum_df: pd.DataFrame,
    lookback_months: int = 36
) -> Dict[str, Any]:
    """
    Fits rolling 24-36 month multivariate linear regression for sector monthly returns
    against Macro Growth Momentum (dG), Inflation Momentum (dI), and Financial Conditions Amplifier (dFCA).
    
    Model: R_s(t) = alpha + beta_growth * dG(t) + beta_inflation * dI(t) + beta_fca * dFCA(t) + eps
    
    Returns:
      - alpha: float
      - beta_growth: float
      - beta_inflation: float
      - beta_fca: float
      - r_squared: float
    """
    if sector_returns_df.empty or macro_momentum_df.empty:
        return {"alpha": 0.0, "beta_growth": 0.5, "beta_inflation": 0.0, "beta_fca": -0.2, "r_squared": 0.0}

    s_df = sector_returns_df.copy()
    m_df = macro_momentum_df.copy()

    s_df["date"] = pd.to_datetime(s_df["date"]).dt.to_period("M")
    m_df["date"] = pd.to_datetime(m_df["date"]).dt.to_period("M")

    merged = pd.merge(s_df, m_df, on="date", how="inner").dropna()
    merged = merged.tail(lookback_months)

    if len(merged) < 12:
        return {"alpha": 0.0, "beta_growth": 0.5, "beta_inflation": 0.0, "beta_fca": -0.2, "r_squared": 0.0}

    y = merged["return_1m"].values
    
    # Construct feature matrix X with intercept
    dg = merged["growth_momentum"].values if "growth_momentum" in merged.columns else np.zeros(len(y))
    di = merged["inflation_momentum"].values if "inflation_momentum" in merged.columns else np.zeros(len(y))
    dfca = merged["fca_amplifier"].values if "fca_amplifier" in merged.columns else np.zeros(len(y))

    X = np.column_stack([np.ones(len(y)), dg, di, dfca])

    try:
        # Solve OLS via least-squares
        beta, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
        alpha, b_g, b_i, b_fca = beta[0], beta[1], beta[2], beta[3]

        # Calculate R-squared
        y_pred = X @ beta
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        ss_res = np.sum((y - y_pred) ** 2)
        r2 = 1.0 - (ss_res / (ss_tot + 1e-8)) if ss_tot > 0 else 0.0

        return {
            "alpha": float(alpha),
            "beta_growth": round(float(b_g), 4),
            "beta_inflation": round(float(b_i), 4),
            "beta_fca": round(float(b_fca), 4),
            "r_squared": round(float(max(0.0, r2)), 4)
        }
    except Exception:
        return {"alpha": 0.0, "beta_growth": 0.5, "beta_inflation": 0.0, "beta_fca": -0.2, "r_squared": 0.0}

def compute_rolling_regime_fit_scores(
    sector_returns_map: Dict[str, pd.DataFrame],
    macro_momentum_df: pd.DataFrame,
    current_regime_vector: Dict[str, float],
    lookback_months: int = 36
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
    """
    Computes regression-based expected excess returns and converts them into
    cross-sectional Sigmoid normalized Regime Fit Scores (0-100) across all sectors.
    
    Returns:
      - regime_fit_scores: Dict[symbol, score_0_to_100]
      - sector_sensitivities: Dict[symbol, Dict[alpha, beta_growth, beta_inflation, beta_fca]]
    """
    symbols = list(sector_returns_map.keys())
    if not symbols:
        return {}, {}

    dg_active = current_regime_vector.get("growth_momentum", 0.5)
    di_active = current_regime_vector.get("inflation_momentum", 0.0)
    dfca_active = current_regime_vector.get("fca_amplifier", 0.0)

    expected_returns = {}
    sensitivities = {}

    for sym, s_df in sector_returns_map.items():
        if sym == "SPY": continue
        res = fit_macro_sensitivity_regression(s_df, macro_momentum_df, lookback_months=lookback_months)
        sensitivities[sym] = res

        # Expected excess return equation
        exp_ret = res["alpha"] + (res["beta_growth"] * dg_active) + (res["beta_inflation"] * di_active) + (res["beta_fca"] * dfca_active)
        expected_returns[sym] = exp_ret

    # Cross-Sectional Z-score -> Sigmoid Normalization
    ret_series = pd.Series(expected_returns)
    if len(ret_series) <= 1 or ret_series.std() == 0:
        fit_scores = {sym: 50.0 for sym in symbols if sym != "SPY"}
    else:
        z = (ret_series - ret_series.mean()) / (ret_series.std() + 1e-8)
        sigmoid_vals = 100.0 / (1.0 + np.exp(-z))
        fit_scores = {sym: round(float(sigmoid_vals[sym]), 1) for sym in ret_series.index}

    return fit_scores, sensitivities
