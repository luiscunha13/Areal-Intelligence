from fastapi.testclient import TestClient
from backend.app.main import app


def test_api_series_list():
    client = TestClient(app)
    response = client.get("/api/macro/series")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_api_regime_current():
    client = TestClient(app)
    response = client.get("/api/regime/current")
    assert response.status_code == 200
    data = response.json()
    assert "regime" in data
    assert "overall_score" in data
    assert "why" in data
    assert "positive" in data["why"]
    assert "negative" in data["why"]


def test_api_regime_history():
    client = TestClient(app)
    response = client.get("/api/regime/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_macro_scores():
    client = TestClient(app)
    response = client.get("/api/macro/scores")
    assert response.status_code == 200
    data = response.json()
    assert "scores" in data
