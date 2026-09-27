import pandas as pd
import numpy as np

def compute_sector_features(sector_returns_df: pd.DataFrame, benchmark_returns_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Computes technical trend, momentum, volatility, drawdown, continuous trend score,
    rolling SPY correlation, and constituent breadth for a sector ETF.
    """
    df = sector_returns_df.copy().sort_values("date").reset_index(drop=True)
    price_col = "adjusted_close" if "adjusted_close" in df.columns else "close"

    # Momentum
    df["momentum_1m"] = df["return_1m"]
    df["momentum_3m"] = df["return_3m"]
    df["momentum_6m"] = df["return_6m"]
    df["momentum_12m"] = df["return_12m"]

    # Moving Averages
    df["sma_20"] = df[price_col].rolling(window=20).mean()
    df["sma_50"] = df[price_col].rolling(window=50).mean()
    df["sma_100"] = df[price_col].rolling(window=100).mean()
    df["sma_200"] = df[price_col].rolling(window=200).mean()

    # 200D slope (pct change of SMA200 over 20 trading days)
    df["slope_200d"] = df["sma_200"].pct_change(20)

    # Factor E: Continuous Trend Distance Score (0-100 scale)
    dist_200 = np.where(df["sma_200"] > 0, (df[price_col] - df["sma_200"]) / df["sma_200"], 0.0)
    dist_50 = np.where(df["sma_50"] > 0, (df[price_col] - df["sma_50"]) / df["sma_50"], 0.0)
    slope_200 = df["slope_200d"].fillna(0.0)

    score_200 = np.clip((dist_200 + 0.20) / 0.40, 0.0, 1.0) * 100.0
    score_50 = np.clip((dist_50 + 0.10) / 0.20, 0.0, 1.0) * 100.0
    score_slope = np.clip((slope_200 + 0.05) / 0.10, 0.0, 1.0) * 100.0

    df["trend_score_continuous"] = 0.40 * score_200 + 0.30 * score_50 + 0.30 * score_slope

    # Volatility (annualized std of daily returns)
    daily_ret = df[price_col].pct_change(1)
    df["volatility_20d"] = daily_ret.rolling(window=20).std() * np.sqrt(252)
    df["volatility_60d"] = daily_ret.rolling(window=60).std() * np.sqrt(252)

    # Drawdown & distance from high
    running_max = df[price_col].cummax()
    df["drawdown"] = (df[price_col] / running_max) - 1.0
    high_52w = df[price_col].rolling(window=252, min_periods=21).max()
    df["distance_from_high"] = (df[price_col] / high_52w) - 1.0

    # Volume ratio
    if "volume" in df.columns and df["volume"].notnull().any():
        vol_sma20 = df["volume"].rolling(window=20).mean()
        df["volume_ratio"] = np.where(vol_sma20 > 0, df["volume"] / vol_sma20, 1.0)
    else:
        df["volume_ratio"] = 1.0

    # Rolling Correlation to SPY benchmark
    if benchmark_returns_df is not None and not benchmark_returns_df.empty:
        bmk_df = benchmark_returns_df.copy().sort_values("date").set_index("date")
        bmk_price_col = "adjusted_close" if "adjusted_close" in bmk_df.columns else "close"
        bmk_daily_ret = bmk_df[bmk_price_col].pct_change(1)

        temp_df = pd.DataFrame({"s_ret": daily_ret.values, "date": df["date"]}).set_index("date")
        joined_ret = temp_df.join(bmk_daily_ret.rename("b_ret"))

        rolling_corr = joined_ret["s_ret"].rolling(window=60, min_periods=20).corr(joined_ret["b_ret"])
        df["correlation_spy"] = rolling_corr.values
    else:
        df["correlation_spy"] = 0.85

    # Constituent Breadth Fallback (Factor D)
    # 0.5 * (% constituents > SMA50) + 0.5 * (% constituents > SMA200)
    # Default ETF-level signal: 100 if > both, 50 if > one, 0 if < both
    above_50 = (df[price_col] > df["sma_50"]).astype(float)
    above_200 = (df[price_col] > df["sma_200"]).astype(float)
    df["breadth_sma"] = 50.0 * above_50 + 50.0 * above_200

    return df
