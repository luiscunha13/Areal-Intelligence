from typing import Dict, List, Any

def evaluate_investment_candidate(
    ticker: str,
    company_name: str,
    sector_name: str,
    stock_scores: Dict[str, float],
    sector_score: float,
    metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates an equity as an Investment Candidate by combining Stock Score (60%) and Sector Score (40%).
    Generates deterministic thesis explanations, risk flags, and confidence levels.
    """
    stock_score = stock_scores["overall_score"]

    # Candidate Score Formula
    candidate_score = round(0.60 * stock_score + 0.40 * sector_score, 1)

    # Category Classification
    if candidate_score >= 80.0:
        category = "Strong Candidate"
    elif candidate_score >= 70.0:
        category = "Candidate"
    elif candidate_score >= 55.0:
        category = "Watchlist"
    else:
        category = "Weak Candidate"

    # Risk Flags Detections
    risk_flags = []
    if stock_scores.get("valuation_score", 50.0) < 40.0:
        risk_flags.append("HIGH_VALUATION")
    if (metrics.get("debt_to_equity") or 0) > 1.5:
        risk_flags.append("WEAK_BALANCE_SHEET")
    if stock_scores.get("relative_strength_score", 50.0) < 45.0:
        risk_flags.append("WEAK_RELATIVE_STRENGTH")

    # Deterministic Thesis Explanations
    explanations = []

    if sector_score >= 75.0:
        explanations.append(f"Sector '{sector_name}' is currently in a top-performing leadership regime ({sector_score:.1f}/100).")
    elif sector_score < 45.0:
        explanations.append(f"Sector '{sector_name}' faces headwinds in the current macro regime.")

    if stock_scores.get("quality_score", 50.0) >= 75.0:
        explanations.append(f"Strong quality metrics (Score: {stock_scores.get('quality_score', 50.0):.1f}) backed by high ROIC and profit margins.")

    if stock_scores.get("growth_score", 50.0) >= 75.0:
        explanations.append(f"Robust revenue and EPS growth momentum (Score: {stock_scores.get('growth_score', 50.0):.1f}).")

    if stock_scores.get("valuation_score", 50.0) >= 70.0:
        explanations.append(f"Attractive valuation relative to peers (Valuation Score: {stock_scores.get('valuation_score', 50.0):.1f}).")
    elif stock_scores.get("valuation_score", 50.0) < 45.0:
        explanations.append("Demanding valuation multiple requires sustained high growth rates.")

    if stock_scores.get("technical_score", 50.0) >= 70.0:
        explanations.append("Favorable price trend and momentum above key moving averages.")

    return {
        "candidate_score": candidate_score,
        "stock_score": stock_score,
        "sector_score": sector_score,
        "category": category,
        "confidence": "High",
        "risk_flags": risk_flags,
        "explanations": explanations,
    }
