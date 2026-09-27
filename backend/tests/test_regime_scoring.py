from backend.app.services.scoring import percentile_to_score, weighted_average
from backend.app.services.regime import classify_regime


def test_percentile_to_score():
    assert percentile_to_score(80) == 80
    assert percentile_to_score(20, invert=True) == 80


def test_weighted_average():
    scores = {"a": 80, "b": 60}
    weights = {"a": 2, "b": 1}
    wa = weighted_average(scores, weights)
    assert round(wa, 6) == round((80 * 2 + 60 * 1) / 3, 6)


def test_classify_regime():
    scores = {"growth": 75, "credit": 78, "risk": 72, "liquidity": 65, "overall": 75}
    r = classify_regime(scores)
    assert "Goldilocks" in r["regime"] or "Growth" in r["regime"] or "Overheat" in r["regime"]
