import pandas as pd
from backend.app.services import features


def test_yoy_and_momentum():
    dates = pd.date_range("2020-01-01", periods=30, freq="ME")
    vals = pd.Series([100 + i for i in range(30)], index=dates)

    yoy = features.yoy(vals, periods=12)
    assert round(float(yoy.dropna().iloc[0]), 6) == round((vals.iloc[12] / vals.iloc[0] - 1), 6)

    mom = features.momentum(vals, periods=12)
    assert not mom.dropna().empty


def test_percentile_rank_and_rolling():
    s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    p = features.percentile_rank(10, s[:-1])
    assert int(p) == 100

    r = features.rolling_percentile(s, window=5)
    assert r.isna().sum() >= 4


def test_yield_curve_spread():
    dgs10 = pd.Series([4.2, 4.3, 4.1])
    dgs2 = pd.Series([3.8, 3.9, 4.0])
    spread = features.yield_curve_spread(dgs10, dgs2)
    assert round(float(spread.iloc[0]), 2) == 0.4
