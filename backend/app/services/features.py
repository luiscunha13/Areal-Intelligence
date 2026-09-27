import pandas as pd
import numpy as np


def yoy(series: pd.Series, periods: int = 12) -> pd.Series:
    """Year-over-year percentage change for series.

    For monthly series periods=12, for quarterly periods=4, for weekly periods=52.
    """
    return series.pct_change(periods)


def momentum(series: pd.Series, periods: int = 12) -> pd.Series:
    """Simple momentum: difference between recent YoY and previous YoY.

    momentum[t] = YoY[t] - YoY[t-periods]
    """
    yoy_series = yoy(series, periods=periods)
    return yoy_series - yoy_series.shift(periods)


def three_month_annualized(series: pd.Series) -> pd.Series:
    """Approximate 3-month annualized growth computed from 3-month percentage change."""
    mom3 = series.pct_change(3)
    return (1 + mom3) ** 4 - 1


def six_month_annualized(series: pd.Series) -> pd.Series:
    """6-month annualized growth."""
    mom6 = series.pct_change(6)
    return (1 + mom6) ** 2 - 1


def change(series: pd.Series, periods: int = 1) -> pd.Series:
    """Difference change over N periods."""
    return series - series.shift(periods)


def yield_curve_spread(series_10y: pd.Series, series_2y: pd.Series) -> pd.Series:
    """10Y minus 2Y Yield Curve Spread."""
    return series_10y - series_2y


def moving_average(series: pd.Series, window: int = 20) -> pd.Series:
    """Rolling simple moving average."""
    return series.rolling(window=window).mean()


def percentile_rank(value: float, history: pd.Series) -> float:
    """Return percentile (0-100) of value within history. History may contain NaNs.

    If history is empty or constant, returns 50.0.
    """
    hist = history.dropna()
    if hist.empty:
        return 50.0
    try:
        rank = (hist < value).sum()
        pct = 100.0 * rank / len(hist)
        return float(pct)
    except Exception:
        return 50.0


def rolling_percentile(series: pd.Series, window: int = 252) -> pd.Series:
    """Compute rolling percentile of the current value within the past `window` observations."""
    def _pct(x: pd.Series):
        if len(x) <= 1:
            return np.nan
        v = x.iloc[-1]
        return percentile_rank(v, x[:-1])

    return series.rolling(window).apply(lambda x: _pct(pd.Series(x)), raw=False)


def vix_percentile(series: pd.Series, window: int = 252) -> pd.Series:
    """Convenience wrapper to compute VIX percentile over a rolling window."""
    return rolling_percentile(series, window=window)
