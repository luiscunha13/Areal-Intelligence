import pandas as pd
from backend.app.services.sector_fundamentals import (
    compute_sector_fundamental_metrics,
    compute_historical_pe_percentile,
    compute_cross_sector_fundamental_scores
)

def test_compute_sector_fundamental_metrics():
    df = pd.DataFrame([
        {"ticker": "AAPL", "revenue_growth_yoy": 0.10, "eps_growth_yoy": 0.12, "operating_margin": 0.30, "prev_operating_margin": 0.28, "pe_ratio": 25.0},
        {"ticker": "MSFT", "revenue_growth_yoy": 0.15, "eps_growth_yoy": 0.18, "operating_margin": 0.42, "prev_operating_margin": 0.40, "pe_ratio": 30.0},
    ])
    
    res = compute_sector_fundamental_metrics(df)
    assert res["quality_flag"] == "Clean growth"
    assert res["revenue_growth_yoy"] > 0
    assert res["pe_ratio_ttm"] > 0

def test_compute_historical_pe_percentile():
    hist_pes = [15.0, 18.0, 20.0, 22.0, 25.0, 30.0]
    percentile = compute_historical_pe_percentile(20.0, hist_pes)
    assert 40.0 <= percentile <= 60.0

def test_compute_cross_sector_fundamental_scores():
    today = {
        "XLK": {"eps_growth_yoy": 0.15, "revenue_growth_yoy": 0.12, "margin_trend": 0.02, "capex_growth_yoy": 0.10, "pe_ratio_ttm": 28.0},
        "XLE": {"eps_growth_yoy": -0.05, "revenue_growth_yoy": -0.02, "margin_trend": -0.01, "capex_growth_yoy": 0.01, "pe_ratio_ttm": 12.0},
    }
    
    res = compute_cross_sector_fundamental_scores(today)
    assert len(res) == 2
    assert res["XLK"]["fundamental_score"] > res["XLE"]["fundamental_score"]
