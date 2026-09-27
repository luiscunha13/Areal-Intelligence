import pandas as pd
from backend.app.services.earnings_surprise import (
    compute_sector_earnings_surprises,
    compute_cross_sector_surprise_scores
)

def test_compute_sector_earnings_surprises():
    df = pd.DataFrame([
        {"ticker": "AAPL", "eps_surprise_pct": 0.08},
        {"ticker": "MSFT", "eps_surprise_pct": 0.05},
    ])
    res = compute_sector_earnings_surprises(df)
    assert "eps_surprise_pct" in res
    assert res["eps_surprise_pct"] > 0

def test_compute_cross_sector_surprise_scores():
    surprises = {
        "XLK": 0.08,
        "XLE": -0.02,
        "XLF": 0.03
    }
    scores = compute_cross_sector_surprise_scores(surprises)
    assert len(scores) == 3
    assert scores["XLK"] > scores["XLE"]
