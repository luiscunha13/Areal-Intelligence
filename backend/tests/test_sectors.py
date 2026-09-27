import pandas as pd
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.sector_returns import compute_sector_returns
from backend.app.services.relative_strength import compute_relative_strength
from backend.app.services.sector_scoring import compute_cross_sector_scores

client = TestClient(app)

def test_compute_sector_returns():
    dates = pd.date_range("2024-01-01", periods=30, freq="B")
    prices = [100.0 + i * 0.5 for i in range(30)]
    df = pd.DataFrame({"date": dates.date, "adjusted_close": prices})

    res = compute_sector_returns(df)

    assert "return_1d" in res.columns
    assert "return_5d" in res.columns
    assert "return_1m" in res.columns
    assert pd.notnull(res["return_1d"].iloc[1])

def test_compute_relative_strength_rrg():
    dates = pd.date_range("2024-01-01", periods=30, freq="B")
    s_prices = [100.0 + i * 1.0 for i in range(30)]
    b_prices = [100.0 + i * 0.2 for i in range(30)]

    s_df = compute_sector_returns(pd.DataFrame({"date": dates.date, "adjusted_close": s_prices}))
    b_df = compute_sector_returns(pd.DataFrame({"date": dates.date, "adjusted_close": b_prices}))

    rs_df = compute_relative_strength(s_df, b_df)

    assert "rs_ratio" in rs_df.columns
    assert "rs_momentum" in rs_df.columns
    assert pd.notnull(rs_df["rs_ratio"].iloc[-1])
    assert pd.notnull(rs_df["rs_momentum"].iloc[-1])

def test_compute_sector_scoring_rrg():
    features_today = {
        "XLK": pd.Series({
            "adjusted_close": 200.0, "sma_50": 190.0, "sma_200": 170.0, "slope_200d": 0.05,
            "rs_ratio": 105.2, "rs_momentum": 102.1,
            "trend_score_continuous": 85.0, "breadth_sma": 80.0, "correlation_spy": 0.88,
            "volatility_20d": 0.14, "drawdown": -0.02
        }),
        "XLE": pd.Series({
            "adjusted_close": 80.0, "sma_50": 85.0, "sma_200": 90.0, "slope_200d": -0.02,
            "rs_ratio": 94.5, "rs_momentum": 96.0,
            "trend_score_continuous": 20.0, "breadth_sma": 10.0, "correlation_spy": 0.50,
            "volatility_20d": 0.25, "drawdown": -0.15
        }),
    }

    regime_fit = {"XLK": 90.0, "XLE": 20.0}

    results = compute_cross_sector_scores(features_today, regime_fit)

    assert len(results) == 2
    xlk = next(r for r in results if r["symbol"] == "XLK")
    xle = next(r for r in results if r["symbol"] == "XLE")

    assert xlk["rank"] == 1
    assert xlk["overall_score"] > xle["overall_score"]
    assert xlk["classification"] == "LEADING"
    assert xle["classification"] == "LAGGING"

def test_sectors_api_endpoints():
    response = client.get("/api/sectors")
    assert response.status_code == 200
    sectors = response.json()
    assert isinstance(sectors, list)

    ranking_res = client.get("/api/sectors/ranking")
    assert ranking_res.status_code in [200, 404]
