from typing import Dict, List, Any, Tuple

def calculate_entry_subscores(
    price: float,
    sma20: float,
    sma50: float,
    sma200: float,
    rsi14: float,
    atr14: float,
    high_52w: float,
    low_52w: float,
    valuation_score: float = 50.0,
    days_to_earnings: int = 30
) -> Dict[str, float]:
    """
    Calculates sub-scores for Entry Timing across 6 core technical & contextual dimensions (0-100 scale).
    """
    if not price or price <= 0:
        return {
            "trend_score": 50.0,
            "momentum_score": 50.0,
            "extension_score": 50.0,
            "support_resistance_score": 50.0,
            "valuation_context_score": 50.0,
            "event_risk_score": 50.0,
        }

    # 1. Trend Score (Price > SMA50 > SMA200)
    if price > sma50 > sma200:
        trend_score = 90.0
    elif price > sma200:
        trend_score = 75.0
    elif price > sma50:
        trend_score = 60.0
    else:
        trend_score = 35.0

    # 2. Momentum Score (Optimal RSI pullback zone: 45-60)
    if 45.0 <= rsi14 <= 60.0:
        momentum_score = 90.0  # Healthy pullback momentum
    elif 60.0 < rsi14 <= 70.0:
        momentum_score = 75.0  # Strong upward momentum
    elif rsi14 > 70.0:
        momentum_score = 55.0  # Overbought extension risk
    elif 30.0 <= rsi14 < 45.0:
        momentum_score = 65.0  # Dip buying zone
    else:
        momentum_score = 40.0  # Oversold / breakdown

    # 3. Price Extension Score (Price vs SMA50 relative to ATR)
    extension_atr = (price - sma50) / atr14 if atr14 > 0 else 0.0
    if -0.5 <= extension_atr <= 1.5:
        extension_score = 95.0 # Ideal non-extended entry zone
    elif 1.5 < extension_atr <= 3.0:
        extension_score = 70.0 # Slightly stretched
    elif extension_atr > 3.0:
        extension_score = 35.0 # Overextended (high chase risk)
    else:
        extension_score = 55.0 # Deep pullback

    # 4. Support / Resistance Score (Proximity to key moving average support or 52W breakout)
    dist_to_sma50_pct = abs(price - sma50) / price
    dist_to_52w_high_pct = (high_52w - price) / high_52w if high_52w > 0 else 0.1

    if dist_to_sma50_pct <= 0.025:
        support_resistance_score = 92.0 # Bouncing off SMA50 support
    elif dist_to_52w_high_pct <= 0.02:
        support_resistance_score = 88.0 # 52-week High Breakout zone
    elif dist_to_sma50_pct <= 0.05:
        support_resistance_score = 80.0
    else:
        support_resistance_score = 60.0

    # 5. Valuation Context Score (Phase 3 valuation score integration)
    valuation_context_score = min(100.0, max(0.0, float(valuation_score)))

    # 6. Event Risk Score (Earnings proximity)
    if days_to_earnings > 21:
        event_risk_score = 95.0 # Low earnings risk
    elif 14 < days_to_earnings <= 21:
        event_risk_score = 80.0
    elif 7 < days_to_earnings <= 14:
        event_risk_score = 60.0 # Moderate risk
    else:
        event_risk_score = 35.0 # High earnings volatility risk

    return {
        "trend_score": round(trend_score, 1),
        "momentum_score": round(momentum_score, 1),
        "extension_score": round(extension_score, 1),
        "support_resistance_score": round(support_resistance_score, 1),
        "valuation_context_score": round(valuation_context_score, 1),
        "event_risk_score": round(event_risk_score, 1),
    }

def calculate_composite_entry_score(subscores: Dict[str, float]) -> Tuple[float, str]:
    """
    Computes overall Entry Score (0-100 scale) using weighted multi-factor formula.
    Weights: Trend 20%, Momentum 20%, Extension 20%, S/R 15%, Valuation Context 15%, Event Risk 10%.
    """
    weights = {
        "trend_score": 0.20,
        "momentum_score": 0.20,
        "extension_score": 0.20,
        "support_resistance_score": 0.15,
        "valuation_context_score": 0.15,
        "event_risk_score": 0.10,
    }

    composite = sum(subscores[k] * weights[k] for k in weights)
    entry_score = round(composite, 1)

    if entry_score >= 80.0:
        status = "EXCELLENT"
    elif entry_score >= 70.0:
        status = "GOOD"
    elif entry_score >= 60.0:
        status = "ACCEPTABLE"
    elif entry_score >= 45.0:
        status = "WEAK"
    else:
        status = "POOR"

    return entry_score, status

def detect_entry_setups(
    price: float,
    sma20: float,
    sma50: float,
    sma200: float,
    rsi14: float,
    atr14: float,
    high_52w: float
) -> List[Dict[str, Any]]:
    """
    Detects deterministic entry setup patterns (TREND_PULLBACK, BREAKOUT, BASE_BREAKOUT, DEEP_PULLBACK, MEAN_REVERSION).
    """
    setups = []

    # Setup A: Trend Pullback (Uptrend with price pulling back to SMA20/SMA50)
    if price > sma200 and sma50 > sma200 and (abs(price - sma50) / price <= 0.03 or abs(price - sma20) / price <= 0.02) and 45.0 <= rsi14 <= 62.0:
        setups.append({
            "setup_type": "TREND_PULLBACK",
            "signal_strength": 88.0,
            "description": "Price pulling back towards moving average support within an active uptrend."
        })

    # Setup B: 52-Week Breakout (Price breaking to new 52-week highs)
    if high_52w > 0 and (high_52w - price) / high_52w <= 0.015 and rsi14 >= 58.0:
        setups.append({
            "setup_type": "BREAKOUT",
            "signal_strength": 85.0,
            "description": "Price breaking out near or above 52-week high resistance."
        })

    # Setup C: Base Breakout (Consolidation near SMA20/SMA50 followed by upward expansion)
    if abs(sma20 - sma50) / price <= 0.015 and price > sma20 and rsi14 >= 55.0:
        setups.append({
            "setup_type": "BASE_BREAKOUT",
            "signal_strength": 82.0,
            "description": "Tight moving average consolidation with upward momentum breakout."
        })

    # Setup D: Deep Value Pullback (Price below SMA50 but cleanly above long-term SMA200)
    if price > sma200 and price < sma50 and rsi14 <= 45.0:
        setups.append({
            "setup_type": "DEEP_PULLBACK",
            "signal_strength": 75.0,
            "description": "Deep price retracement to major long-term structural support."
        })

    # Default fallback setup if no special pattern triggers
    if not setups:
        setups.append({
            "setup_type": "TREND_FOLLOWING",
            "signal_strength": 70.0,
            "description": "Standard trend alignment and momentum tracking."
        })

    return setups

def calculate_entry_zone(price: float, atr14: float, sma50: float) -> Dict[str, float]:
    """
    Computes transparent preferred entry range, invalidation level, target reference, and Risk/Reward ratio.
    """
    atr = atr14 if atr14 > 0 else price * 0.02

    # Preferred Entry Zone: [price - 0.5*ATR, price + 0.2*ATR]
    entry_low = round(price - 0.5 * atr, 2)
    entry_high = round(price + 0.2 * atr, 2)

    # Invalidation Price (Stop reference): price - 2.0*ATR
    invalidation = round(price - 2.0 * atr, 2)

    # Target Price (Reward reference): price + 4.5*ATR
    target = round(price + 4.5 * atr, 2)

    # Risk/Reward Ratio: (Target - Entry) / (Entry - Invalidation)
    risk = max(0.01, price - invalidation)
    reward = max(0.01, target - price)
    rr_ratio = round(reward / risk, 2)

    return {
        "current_price": round(price, 2),
        "entry_zone_low": entry_low,
        "entry_zone_high": entry_high,
        "invalidation_price": invalidation,
        "reference_target_price": target,
        "risk_reward_ratio": rr_ratio,
    }
