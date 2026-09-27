import pandas as pd
import numpy as np
from backend.app.services.regime_fit import (
    fit_macro_sensitivity_regression,
    compute_rolling_regime_fit_scores
)

def test_fit_macro_sensitivity_regression():
    dates = pd.date_range("2023-01-01", periods=24, freq="ME")
    sector_returns = pd.DataFrame({"date": dates, "return_1m": np.random.normal(0.01, 0.03, 24)})
    macro_mom = pd.DataFrame({
        "date": dates,
        "growth_momentum": np.random.normal(0.5, 0.1, 24),
        "inflation_momentum": np.random.normal(0.0, 0.05, 24),
        "fca_amplifier": np.random.normal(0.0, 0.02, 24),
    })

    res = fit_macro_sensitivity_regression(sector_returns, macro_mom, lookback_months=24)
    assert "alpha" in res
    assert "beta_growth" in res
    assert "beta_inflation" in res
    assert "beta_fca" in res

def test_compute_rolling_regime_fit_scores():
    dates = pd.date_range("2023-01-01", periods=24, freq="ME")
    map_returns = {
        "XLK": pd.DataFrame({"date": dates, "return_1m": np.random.normal(0.02, 0.04, 24)}),
        "XLE": pd.DataFrame({"date": dates, "return_1m": np.random.normal(-0.01, 0.05, 24)}),
    }
    macro_mom = pd.DataFrame({
        "date": dates,
        "growth_momentum": np.random.normal(0.5, 0.1, 24),
        "inflation_momentum": np.random.normal(0.0, 0.05, 24),
        "fca_amplifier": np.random.normal(0.0, 0.02, 24),
    })

    active_vec = {"growth_momentum": 0.6, "inflation_momentum": 0.1, "fca_amplifier": -0.05}
    scores, sens = compute_rolling_regime_fit_scores(map_returns, macro_mom, active_vec, lookback_months=24)
    
    assert "XLK" in scores
    assert "XLE" in scores
    assert 0 <= scores["XLK"] <= 100
    assert "beta_growth" in sens["XLK"]
