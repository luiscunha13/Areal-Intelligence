import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

SECTOR_SCORE_WEIGHTS_MASTER_V2 = {
    "rs_ratio": 0.20,
    "rs_momentum": 0.15,
    "regime_fit": 0.20,
    "fundamental": 0.15,
    "surprise": 0.10,
    "trend": 0.10,
    "breadth": 0.05,
    "risk": 0.05,
}

def zscore_sigmoid_transform(series: pd.Series) -> Dict[str, float]:
    """
    Converts continuous raw values into a 0-100 score via Z-score -> Sigmoid transform.
    Preserves magnitude differences across the universe.
    Sigmoid(z) = 100.0 / (1.0 + exp(-z))
    """
    clean_s = series.dropna()
    if len(clean_s) <= 1 or clean_s.std() == 0:
        return {s: 50.0 for s in series.index}
    
    mean = clean_s.mean()
    std = clean_s.std()
    z = (series - mean) / (std + 1e-8)
    sigmoid_vals = 100.0 / (1.0 + np.exp(-z))
    return sigmoid_vals.to_dict()

def compute_cross_sector_scores(
    sector_features_today: Dict[str, pd.Series],
    regime_fit_scores: Optional[Dict[str, float]] = None,
    fundamental_scores: Optional[Dict[str, float]] = None,
    surprise_scores: Optional[Dict[str, float]] = None,
    features_df_map: Optional[Dict[str, pd.DataFrame]] = None,
    tail_periods: int = 10
) -> List[Dict[str, Any]]:
    """
    Computes Phase 3 master institutional RRG composite sector & industry rankings.
    
    Master Weights (Total 100%):
      - RS-Ratio Score: 20%
      - RS-Momentum Score: 15%
      - Regime Sensitivity Fit Score: 20%
      - Growth-Quality Fundamental Score: 15%
      - Earnings Surprise / Revision Score: 10%
      - Continuous Trend Score: 10%
      - Constituent Breadth Score: 5%
      - Risk Score: 5%
    """
    symbols = list(sector_features_today.keys())
    if not symbols:
        return []

    raw_rs_ratio = {}
    raw_rs_momentum = {}
    trend_scores = {}
    breadth_scores = {}
    risk_scores = {}

    for sym, feat in sector_features_today.items():
        # RRG Factors
        rs_ratio_val = feat.get("rs_ratio", 100.0)
        if pd.isnull(rs_ratio_val) or rs_ratio_val == 0:
            rs_ratio_val = 100.0
        raw_rs_ratio[sym] = float(rs_ratio_val)

        rs_mom_val = feat.get("rs_momentum", 100.0)
        if pd.isnull(rs_mom_val) or rs_mom_val == 0:
            rs_mom_val = 100.0
        raw_rs_momentum[sym] = float(rs_mom_val)

        # Continuous Trend Score
        tr_cont = feat.get("trend_score_continuous", None)
        if tr_cont is not None and not pd.isnull(tr_cont):
            trend_scores[sym] = float(tr_cont)
        else:
            close = feat.get("adjusted_close", 0.0) or feat.get("close", 0.0) or 0.0
            sma50 = feat.get("sma_50", 0.0) or 0.0
            sma200 = feat.get("sma_200", 0.0) or 0.0
            slope200 = feat.get("slope_200d", 0.0) or 0.0
            t_score = 0.0
            if close > sma200 and sma200 > 0: t_score += 25.0
            if close > sma50 and sma50 > 0: t_score += 25.0
            if sma50 > sma200 and sma200 > 0: t_score += 25.0
            if slope200 > 0: t_score += 25.0
            trend_scores[sym] = t_score

        # Breadth Score
        br_val = feat.get("breadth_sma", 50.0)
        breadth_scores[sym] = float(br_val) if not pd.isnull(br_val) else 50.0

        # Risk Score
        vol20 = float(feat.get("volatility_20d", 0.15) or 0.15)
        dd = abs(float(feat.get("drawdown", 0.0) or 0.0))
        corr_spy = float(feat.get("correlation_spy", 0.85) or 0.85)
        
        risk_penalty = (vol20 * 100.0) + (dd * 100.0) + (1.0 - corr_spy) * 20.0
        risk_scores[sym] = max(10.0, min(100.0, 100.0 - risk_penalty))

    # Cross-Sectional Z-Score -> Sigmoid Normalization for RRG axes
    ratio_score_dict = zscore_sigmoid_transform(pd.Series(raw_rs_ratio))
    momentum_score_dict = zscore_sigmoid_transform(pd.Series(raw_rs_momentum))

    results = []
    weights = SECTOR_SCORE_WEIGHTS_MASTER_V2

    for sym in symbols:
        feat = sector_features_today[sym]
        r_ratio_raw = raw_rs_ratio.get(sym, 100.0)
        r_mom_raw = raw_rs_momentum.get(sym, 100.0)

        ratio_s = round(float(ratio_score_dict.get(sym, 50.0)), 1)
        mom_s = round(float(momentum_score_dict.get(sym, 50.0)), 1)
        rf_s = round(float((regime_fit_scores or {}).get(sym, 50.0)), 1)
        fund_s = round(float((fundamental_scores or {}).get(sym, 50.0)), 1)
        surp_s = round(float((surprise_scores or {}).get(sym, 50.0)), 1)
        tr_s = round(float(trend_scores.get(sym, 50.0)), 1)
        br_s = round(float(breadth_scores.get(sym, 50.0)), 1)
        rk_s = round(float(risk_scores.get(sym, 50.0)), 1)

        # Master Composite Score
        overall = (
            weights["rs_ratio"] * ratio_s +
            weights["rs_momentum"] * mom_s +
            weights["regime_fit"] * rf_s +
            weights["fundamental"] * fund_s +
            weights["surprise"] * surp_s +
            weights["trend"] * tr_s +
            weights["breadth"] * br_s +
            weights["risk"] * rk_s
        )
        overall = round(float(overall), 1)

        # Classification based on RRG raw coordinates (baseline 100.0)
        if r_ratio_raw >= 100.0 and r_mom_raw >= 100.0:
            classification = "LEADING"
        elif r_ratio_raw < 100.0 and r_mom_raw >= 100.0:
            classification = "IMPROVING"
        elif r_ratio_raw >= 100.0 and r_mom_raw < 100.0:
            classification = "WEAKENING"
        else:
            classification = "LAGGING"

        # Trajectory / Tails (last N periods of coordinates)
        tails_list = []
        if features_df_map and sym in features_df_map and not features_df_map[sym].empty:
            df_hist = features_df_map[sym].tail(tail_periods)
            for _, r in df_hist.iterrows():
                r_ratio = float(r.get("rs_ratio", 100.0)) if pd.notnull(r.get("rs_ratio")) else 100.0
                r_mom = float(r.get("rs_momentum", 100.0)) if pd.notnull(r.get("rs_momentum")) else 100.0
                d_str = str(r["date"])
                tails_list.append({
                    "date": d_str,
                    "rs_ratio": round(r_ratio, 2),
                    "rs_momentum": round(r_mom, 2)
                })

        r_ratio_strat = float(feat["rs_ratio_strategic"]) if "rs_ratio_strategic" in feat and pd.notnull(feat["rs_ratio_strategic"]) else 100.0
        r_mom_strat = float(feat["rs_momentum_strategic"]) if "rs_momentum_strategic" in feat and pd.notnull(feat["rs_momentum_strategic"]) else 100.0

        results.append({
            "symbol": sym,
            "rs_ratio": round(r_ratio_raw, 2),
            "rs_momentum": round(r_mom_raw, 2),
            "rs_ratio_strategic": round(r_ratio_strat, 2),
            "rs_momentum_strategic": round(r_mom_strat, 2),
            "momentum_score": mom_s,
            "relative_strength_score": ratio_s,
            "regime_fit_score": rf_s,
            "fundamental_score": fund_s,
            "surprise_score": surp_s,
            "trend_score": tr_s,
            "breadth_score": br_s,
            "risk_score": rk_s,
            "overall_score": overall,
            "classification": classification,
            "tails": json.dumps(tails_list),
        })

    # Sort by overall_score descending to assign rank
    results.sort(key=lambda x: x["overall_score"], reverse=True)
    for idx, item in enumerate(results, start=1):
        item["rank"] = idx

    return results
