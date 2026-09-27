from typing import Dict, List, Any

def generate_sector_explanations(scores_dict: Dict[str, Any], features_dict: Dict[str, Any]) -> List[str]:
    """
    Generates human-readable deterministic explanations ("Why Drivers") for a sector's score.
    """
    explanations = []

    rs_score = scores_dict.get("relative_strength_score", 50)
    mom_score = scores_dict.get("momentum_score", 50)
    trend_score = scores_dict.get("trend_score", 50)
    regime_fit_score = scores_dict.get("regime_fit_score", 50)
    risk_score = scores_dict.get("risk_score", 50)

    if rs_score >= 70:
        explanations.append("Outperforming S&P 500 benchmark across multiple timeframes")
    elif rs_score <= 30:
        explanations.append("Underperforming S&P 500 benchmark relative strength")

    if mom_score >= 70:
        explanations.append("Strong multi-month positive price momentum")
    elif mom_score <= 30:
        explanations.append("Weak short and medium term price momentum")

    if trend_score >= 75:
        explanations.append("Price trading cleanly above 50D and 200D Moving Averages")
    elif trend_score <= 25:
        explanations.append("Price trading below 200D Moving Average (downtrend)")

    if regime_fit_score >= 70:
        explanations.append("Historically strong return profile during active market regime")
    elif regime_fit_score <= 30:
        explanations.append("Historically weak performance in current macroeconomic regime")

    if risk_score <= 30:
        explanations.append("Elevated short-term price volatility or drawdown risk")

    return explanations if explanations else ["Balanced technical and macro factor profile"]
