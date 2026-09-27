import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.entry_timing import (
    calculate_entry_subscores,
    calculate_composite_entry_score,
    detect_entry_setups,
    calculate_entry_zone,
)

client = TestClient(app)

def test_calculate_entry_subscores():
    subscores = calculate_entry_subscores(
        price=100.0,
        sma20=98.0,
        sma50=95.0,
        sma200=85.0,
        rsi14=55.0,
        atr14=2.5,
        high_52w=105.0,
        low_52w=80.0,
        valuation_score=60.0,
        days_to_earnings=30
    )

    assert "trend_score" in subscores
    assert subscores["trend_score"] == 90.0
    assert subscores["momentum_score"] == 90.0
    assert subscores["extension_score"] == 70.0
    assert subscores["event_risk_score"] == 95.0

def test_calculate_composite_entry_score():
    subscores = {
        "trend_score": 90.0,
        "momentum_score": 90.0,
        "extension_score": 95.0,
        "support_resistance_score": 88.0,
        "valuation_context_score": 70.0,
        "event_risk_score": 95.0,
    }
    score, status = calculate_composite_entry_score(subscores)
    assert score >= 85.0
    assert status == "EXCELLENT"

def test_detect_entry_setups():
    setups = detect_entry_setups(
        price=100.0,
        sma20=99.0,
        sma50=96.0,
        sma200=85.0,
        rsi14=54.0,
        atr14=2.5,
        high_52w=101.0
    )
    assert len(setups) >= 1
    setup_types = [s["setup_type"] for s in setups]
    assert "TREND_PULLBACK" in setup_types or "BREAKOUT" in setup_types

def test_calculate_entry_zone():
    ez = calculate_entry_zone(price=100.0, atr14=2.0, sma50=95.0)
    assert ez["current_price"] == 100.0
    assert ez["entry_zone_low"] < ez["current_price"]
    assert ez["invalidation_price"] < ez["entry_zone_low"]
    assert ez["risk_reward_ratio"] > 1.5

def test_api_entry_ranking():
    response = client.get("/api/entry/ranking")
    assert response.status_code == 200
    data = response.json()
    assert "entry_opportunities" in data
    assert len(data["entry_opportunities"]) > 0

def test_api_company_entry_detail():
    response = client.get("/api/entry/company/NVDA")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "NVDA"
    assert "entry_score" in data
    assert "entry_zone" in data
