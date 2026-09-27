import pandas as pd
import numpy as np

def compute_relative_strength(
    sector_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Computes Dual-Horizon Relative Rotation Graph (RRG) factors:
      1. Tactical (50d smoothing, 14d momentum)
      2. Strategic (260d / 52-week smoothing, 65d / 13-week momentum)
    """
    s_df = sector_df.copy().sort_values("date").set_index("date")
    b_df = benchmark_df.copy().sort_values("date").set_index("date")

    price_s = s_df["adjusted_close"] if "adjusted_close" in s_df.columns else s_df["close"]
    price_b = b_df["adjusted_close"] if "adjusted_close" in b_df.columns else b_df["close"]

    # Align dates
    merged_prices = pd.DataFrame({"price_s": price_s, "price_b": price_b}).dropna()
    ratio = merged_prices["price_s"] / merged_prices["price_b"]

    # 1. Tactical Horizon (50d SMA, 14d momentum)
    ratio_sma_50 = ratio.rolling(window=50, min_periods=1).mean()
    raw_rs_ratio_50 = 100.0 * (ratio / ratio_sma_50)
    rs_ratio_lagged_50 = raw_rs_ratio_50.shift(14)
    raw_rs_mom_50 = 100.0 * (raw_rs_ratio_50 / np.where(rs_ratio_lagged_50 > 0, rs_ratio_lagged_50, 100.0))

    # 2. Strategic Horizon (260d SMA, 65d momentum)
    ratio_sma_260 = ratio.rolling(window=260, min_periods=1).mean()
    raw_rs_ratio_260 = 100.0 * (ratio / ratio_sma_260)
    rs_ratio_lagged_260 = raw_rs_ratio_260.shift(65)
    raw_rs_mom_260 = 100.0 * (raw_rs_ratio_260 / np.where(rs_ratio_lagged_260 > 0, rs_ratio_lagged_260, 100.0))

    # Fill NaN
    raw_rs_ratio_50 = raw_rs_ratio_50.fillna(100.0)
    raw_rs_mom_50 = raw_rs_mom_50.fillna(100.0)
    raw_rs_ratio_260 = raw_rs_ratio_260.fillna(100.0)
    raw_rs_mom_260 = raw_rs_mom_260.fillna(100.0)

    # Join back to s_df
    s_df["rs_ratio"] = raw_rs_ratio_50
    s_df["rs_momentum"] = raw_rs_mom_50
    s_df["rs_ratio_strategic"] = raw_rs_ratio_260
    s_df["rs_momentum_strategic"] = raw_rs_mom_260

    # Standard multi-period relative strength returns
    if all(col in b_df.columns for col in ["return_1m", "return_3m", "return_6m", "return_12m"]):
        b_rets = b_df[["return_1m", "return_3m", "return_6m", "return_12m"]]
        joined = s_df.join(b_rets, rsuffix="_bmk")
        s_df["relative_strength_1m"] = joined.get("return_1m", 0.0) - joined.get("return_1m_bmk", 0.0)
        s_df["relative_strength_3m"] = joined.get("return_3m", 0.0) - joined.get("return_3m_bmk", 0.0)
        s_df["relative_strength_6m"] = joined.get("return_6m", 0.0) - joined.get("return_6m_bmk", 0.0)
        s_df["relative_strength_12m"] = joined.get("return_12m", 0.0) - joined.get("return_12m_bmk", 0.0)
    else:
        s_df["relative_strength_1m"] = 0.0
        s_df["relative_strength_3m"] = 0.0
        s_df["relative_strength_6m"] = 0.0
        s_df["relative_strength_12m"] = 0.0

    return s_df.reset_index()
