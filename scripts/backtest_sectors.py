import sys
import os
import logging
import pandas as pd
import numpy as np

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.sector import Sector
from backend.app.models.sector_price import SectorPrice
from backend.app.services.sector_returns import compute_sector_returns
from backend.app.services.relative_strength import compute_relative_strength
from backend.app.services.sector_features import compute_sector_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_sector_backtest(start_date: str = "2019-01-01", end_date: str = "2026-08-01", top_n: int = 3):
    db = SessionLocal()
    try:
        sectors = db.query(Sector).all()
        if not sectors:
            logger.error("No sectors found in DB.")
            return

        sector_map = {s.symbol: s.id for s in sectors}

        prices_df_map = {}
        for s in sectors:
            prices = db.query(SectorPrice).filter(SectorPrice.sector_id == s.id).order_by(SectorPrice.date).all()
            if prices:
                prices_df_map[s.symbol] = pd.DataFrame([{
                    "date": p.date,
                    "close": p.close,
                    "adjusted_close": p.adjusted_close,
                    "volume": p.volume,
                } for p in prices])

        bmk_symbol = "SPY"
        if bmk_symbol not in prices_df_map:
            logger.error("SPY benchmark prices missing.")
            return

        # Precompute returns & features per sector
        features_df_map = {}
        bmk_returns = compute_sector_returns(prices_df_map[bmk_symbol])

        for symbol, p_df in prices_df_map.items():
            r_df = compute_sector_returns(p_df)
            rs_df = compute_relative_strength(r_df, bmk_returns)
            f_df = compute_sector_features(rs_df)
            features_df_map[symbol] = f_df.set_index("date")

        # Get monthly rebalancing dates
        bmk_df = prices_df_map[bmk_symbol].copy()
        bmk_df["date"] = pd.to_datetime(bmk_df["date"])
        bmk_df = bmk_df[(bmk_df["date"] >= pd.to_datetime(start_date)) & (bmk_df["date"] <= pd.to_datetime(end_date))]
        bmk_df["year_month"] = bmk_df["date"].dt.to_period("M")

        monthly_dates = bmk_df.groupby("year_month")["date"].max().tolist()
        monthly_dates = [d.date() for d in monthly_dates]

        logger.info(f"Running Sector Allocation Backtest from {start_date} to {end_date} across {len(monthly_dates)} monthly rebalancing periods...")

        strategy_returns = []
        benchmark_returns = []
        top_sector_history = []

        for i in range(len(monthly_dates) - 1):
            rebal_date = monthly_dates[i]
            next_rebal_date = monthly_dates[i + 1]

            # Rank sectors on rebal_date (point-in-time)
            sector_scores = {}
            for sym, f_df in features_df_map.items():
                if sym == "SPY": continue
                if rebal_date in f_df.index:
                    row = f_df.loc[rebal_date]
                    # Score = 0.5 * RS_3M + 0.5 * Momentum_3M
                    rs3 = row.get("relative_strength_3m", 0) or 0
                    m3 = row.get("momentum_3m", 0) or 0
                    sector_scores[sym] = 0.5 * rs3 + 0.5 * m3

            if not sector_scores:
                continue

            # Pick Top N sectors
            sorted_sectors = sorted(sector_scores.items(), key=lambda x: x[1], reverse=True)
            top_sectors = [s[0] for s in sorted_sectors[:top_n]]
            top_sector_history.append((rebal_date, top_sectors))

            # Measure next month return for Top N vs SPY
            strat_month_ret = 0.0
            for sym in top_sectors:
                p_df = features_df_map[sym]
                if rebal_date in p_df.index and next_rebal_date in p_df.index:
                    p_start = p_df.loc[rebal_date, "adjusted_close"]
                    p_end = p_df.loc[next_rebal_date, "adjusted_close"]
                    if p_start > 0:
                        strat_month_ret += (p_end / p_start - 1.0) / top_n

            bmk_p_df = features_df_map[bmk_symbol]
            bmk_month_ret = 0.0
            if rebal_date in bmk_p_df.index and next_rebal_date in bmk_p_df.index:
                b_start = bmk_p_df.loc[rebal_date, "adjusted_close"]
                b_end = bmk_p_df.loc[next_rebal_date, "adjusted_close"]
                if b_start > 0:
                    bmk_month_ret = (b_end / b_start - 1.0)

            strategy_returns.append(strat_month_ret)
            benchmark_returns.append(bmk_month_ret)

        strat_rets = np.array(strategy_returns)
        bmk_rets = np.array(benchmark_returns)

        cum_strat = np.prod(1.0 + strat_rets) - 1.0
        cum_bmk = np.prod(1.0 + bmk_rets) - 1.0

        n_years = len(strat_rets) / 12.0
        cagr_strat = (1.0 + cum_strat) ** (1.0 / n_years) - 1.0 if n_years > 0 else 0.0
        cagr_bmk = (1.0 + cum_bmk) ** (1.0 / n_years) - 1.0 if n_years > 0 else 0.0

        vol_strat = np.std(strat_rets) * np.sqrt(12)
        vol_bmk = np.std(bmk_rets) * np.sqrt(12)

        sharpe_strat = (cagr_strat - 0.02) / vol_strat if vol_strat > 0 else 0.0
        sharpe_bmk = (cagr_bmk - 0.02) / vol_bmk if vol_bmk > 0 else 0.0

        win_rate = float(np.sum(strat_rets > bmk_rets)) / len(strat_rets) * 100.0 if len(strat_rets) > 0 else 0.0

        print("\n" + "=" * 60)
        print("📊 PHASE 2 SECTOR ALLOCATION BACKTEST RESULTS")
        print("=" * 60)
        print(f"Backtest Period:      {start_date} to {end_date} ({len(strat_rets)} months)")
        print(f"Strategy Rules:       Equal-Weight Top {top_n} Sectors (Monthly Rebalance)")
        print("-" * 60)
        print(f"Cumulative Return:    Strategy: {cum_strat*100:.2f}% | SPY Benchmark: {cum_bmk*100:.2f}%")
        print(f"CAGR (Annual Return): Strategy: {cagr_strat*100:.2f}% | SPY Benchmark: {cagr_bmk*100:.2f}%")
        print(f"Annualized Vol:       Strategy: {vol_strat*100:.2f}% | SPY Benchmark: {vol_bmk*100:.2f}%")
        print(f"Sharpe Ratio (Rf=2%): Strategy: {sharpe_strat:.2f} | SPY Benchmark: {sharpe_bmk:.2f}")
        print(f"Outperformance Win %: {win_rate:.1f}%")
        print("=" * 60 + "\n")

    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Sector Backtest")
    parser.add_argument("--start", default="2019-01-01")
    parser.add_argument("--end", default="2026-08-01")
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args()
    run_sector_backtest(start_date=args.start, end_date=args.end, top_n=args.top)
