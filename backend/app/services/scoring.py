def percentile_score(value, series_history):
    # placeholder: compute percentile rank of value in series_history
    try:
        series = sorted(series_history)
        rank = sum(1 for v in series if v < value)
        return 100.0 * rank / max(1, len(series) - 1)
    except Exception:
        return 50.0


def percentile_to_score(percentile: float, invert: bool = False) -> float:
    """Convert a percentile (0-100) to a 0-100 score, optionally inverting direction.

    If invert=True, higher percentiles become lower scores.
    """
    try:
        p = float(percentile)
    except Exception:
        return 50.0
    if invert:
        return 100.0 - p
    return p


def weighted_average(scores: dict, weights: dict) -> float:
    """Combine dimension scores in `scores` using `weights` (both dicts of same keys).

    Missing weights default to equal weighting among provided keys.
    """
    keys = list(scores.keys())
    if not keys:
        return 50.0
    if not weights:
        return float(sum(scores.values()) / len(keys))
    total_w = sum(weights.get(k, 0) for k in keys)
    if total_w == 0:
        return float(sum(scores.values()) / len(keys))
    s = 0.0
    for k in keys:
        w = weights.get(k, 0)
        s += scores.get(k, 0) * (w / total_w)
    return float(s)

