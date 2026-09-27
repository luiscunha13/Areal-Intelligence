import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.stock_scoring import calculate_stock_subscores
from backend.app.services.candidate_engine import evaluate_investment_candidate

client = TestClient(app)

def test_calculate_stock_subscores():
    metrics = {
        "roic": 0.20, "roe": 0.25, "operating_margin": 0.30, "fcf_margin": 0.25,
        "debt_to_equity": 0.5, "revenue_growth_yoy": 0.20, "eps_growth_yoy": 0.25,
        "fcf_growth_yoy": 0.18, "pe_ratio": 25.0, "forward_pe": 20.0, "ev_to_ebitda": 15.0,
        "fcf_yield": 0.05, "eps_surprise_pct": 0.08, "revenue_surprise_pct": 0.03
    }
    prices = {
        "close": 150.0, "sma_50": 140.0, "sma_200": 120.0, "rsi_14": 60.0,
        "relative_strength_sp500": 0.10, "relative_strength_sector": 0.05
    }

    scores = calculate_stock_subscores(metrics, prices)

    assert "quality_score" in scores
    assert "growth_score" in scores
    assert "valuation_score" in scores
    assert "overall_score" in scores
    assert scores["overall_score"] > 60.0

def test_evaluate_investment_candidate():
    stock_scores = {"overall_score": 85.0, "quality_score": 80.0, "growth_score": 90.0, "valuation_score": 75.0, "technical_score": 80.0}
    metrics = {"debt_to_equity": 0.5}

    cand = evaluate_investment_candidate(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        sector_name="Information Technology",
        stock_scores=stock_scores,
        sector_score=85.0,
        metrics=metrics
    )

    assert cand["candidate_score"] >= 80.0
    assert cand["category"] == "Strong Candidate"
    assert len(cand["explanations"]) >= 1

def test_companies_api_endpoints():
    res = client.get("/api/companies")
    assert res.status_code == 200
    companies = res.json()
    assert len(companies) > 0

    rankings_res = client.get("/api/companies/rankings")
    assert rankings_res.status_code == 200

    candidates_res = client.get("/api/candidates")
    assert candidates_res.status_code == 200
