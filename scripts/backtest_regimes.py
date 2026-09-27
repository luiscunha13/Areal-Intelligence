"""Point-in-Time Backtesting Engine for Market Regimes.

Calculates historical market regimes without look-ahead bias by enforcing vintage_date <= simulation_date.
Usage: python scripts/backtest_regimes.py --start 2015-01-01 --end 2026-08-01
"""
import os
import sys
import argparse
import logging
from datetime import date, timedelta
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.services.pipeline import compute_scores_for_date

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_backtest(start_date: date, end_date: date, step_days: int = 30):
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    current = start_date
    simulation_results = []
    logger.info("Starting Point-in-Time Backtest from %s to %s (step: %d days)...", start_date, end_date, step_days)

    try:
        while current <= end_date:
            res = compute_scores_for_date(session, asof=current)
            regime_info = res["regime"]
            scores = res["scores"]

            simulation_results.append({
                "date": current.isoformat(),
                "regime": regime_info["regime"],
                "confidence": regime_info["confidence"],
                "overall_score": regime_info["overall_score"],
                "growth": scores["growth"],
                "inflation": scores["inflation"],
                "rates": scores["rates"],
                "liquidity": scores["liquidity"],
                "credit": scores["credit"],
                "risk": scores["risk"],
            })
            current += timedelta(days=step_days)

        df = pd.DataFrame(simulation_results)
        logger.info("Backtest complete. Simulated %d historical periods.", len(df))

        # Transition metrics
        if not df.empty:
            transitions = (df["regime"] != df["regime"].shift(1)).sum() - 1
            regime_counts = df["regime"].value_counts().to_dict()
            logger.info("--- BACKTEST SUMMARY METRICS ---")
            logger.info("Total Periods: %d", len(df))
            logger.info("Regime Transitions: %d", max(0, transitions))
            logger.info("Regime Breakdown: %s", regime_counts)

        return df
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Point-in-time macro regime backtest")
    parser.add_argument("--start", type=str, default="2020-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default=date.today().isoformat(), help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    s_date = date.fromisoformat(args.start)
    e_date = date.fromisoformat(args.end)
    run_backtest(s_date, e_date)
