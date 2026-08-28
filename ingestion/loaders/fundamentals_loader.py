"""
ingestion/loaders/fundamentals_loader.py
──────────────────────────────────────────
Loads fundamental financial metrics for stocks from yfinance.
Runs quarterly (after earnings season) for all active stocks.
"""
import logging
import os
import yaml
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import text

from ingestion.base import BaseLoader
from ingestion.sources.yfinance_client import YFinanceClient

logger = logging.getLogger(__name__)

CATALOG_DIR = os.path.join(os.path.dirname(__file__), "../../catalog")


def load_active_stocks(db_url: str) -> list[str]:
    """Fetch active stock tickers from the DB (not YAML — stocks are DB-managed)."""
    from sqlalchemy import create_engine
    engine = create_engine(db_url)
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT ticker FROM stocks WHERE is_active = true ORDER BY ticker"
        )).fetchall()
    return [r[0] for r in rows]


class FundamentalsLoader(BaseLoader):
    """
    Fetches key financial metrics per stock per fiscal period via yfinance.
    Runs quarterly. Idempotent — upserts on (ticker, period_end, period_type).
    """
    dag_id = "fundamentals"

    def __init__(
        self,
        database_url: str,
        tickers: Optional[list[str]] = None,
        dry_run: bool = False,
    ):
        super().__init__(database_url, dry_run)
        self.client = YFinanceClient()
        # Use explicit tickers or pull all active stocks from DB
        self.tickers = tickers or load_active_stocks(database_url)

    def fetch(self) -> dict:
        """
        Fetch annual + quarterly financials for each ticker via yfinance.
        Returns {ticker: {"annual": df, "quarterly": df, "info": dict}}
        """
        import yfinance as yf
        import pandas as pd

        results = {}
        for ticker in self.tickers:
            try:
                t = yf.Ticker(ticker)
                info = t.info or {}

                # Income statement (annual)
                financials = t.financials  # columns = fiscal year dates
                bs = t.balance_sheet
                cf = t.cashflow

                results[ticker] = {
                    "info": info,
                    "financials": financials,
                    "balance_sheet": bs,
                    "cashflow": cf,
                }
                logger.debug(f"  {ticker}: financials fetched")
            except Exception as e:
                logger.warning(f"  {ticker}: fetch failed — {e}")
                self.rows_failed += 1
        return results

    def transform(self, raw: dict) -> list[dict]:
        import numpy as np

        rows = []
        for ticker, data in raw.items():
            info = data.get("info", {})
            fin = data.get("financials")
            bs = data.get("balance_sheet")
            cf = data.get("cashflow")

            if fin is None or fin.empty:
                continue

            for col in fin.columns:
                period_end = col.date() if hasattr(col, "date") else col

                def safe_get(df, key):
                    try:
                        val = df.loc[key, col] if df is not None and key in df.index else None
                        return None if val is None or (isinstance(val, float) and np.isnan(val)) else float(val)
                    except Exception:
                        return None

                revenue = safe_get(fin, "Total Revenue")
                net_income = safe_get(fin, "Net Income")
                total_assets = safe_get(bs, "Total Assets") if bs is not None else None
                total_equity = safe_get(bs, "Stockholders Equity") if bs is not None else None
                total_debt = safe_get(bs, "Total Debt") if bs is not None else None
                fcf = safe_get(cf, "Free Cash Flow") if cf is not None else None

                # Compute derived ratios from info (more reliable for latest period)
                pe = info.get("trailingPE") or info.get("forwardPE")
                pb = info.get("priceToBook")
                roe = (net_income / total_equity * 100) if net_income and total_equity and total_equity != 0 else None
                de = (total_debt / total_equity) if total_debt and total_equity and total_equity != 0 else None
                eps = info.get("trailingEps")

                rows.append({
                    "ticker": ticker,
                    "period_end": period_end,
                    "period_type": "annual",
                    "revenue": revenue,
                    "net_income": net_income,
                    "eps": eps,
                    "pe_ratio": float(pe) if pe else None,
                    "pb_ratio": float(pb) if pb else None,
                    "roe": roe,
                    "debt_to_equity": de,
                    "free_cash_flow": fcf,
                    "source": "yfinance",
                    "run_id": self.run_id,
                })
        return rows

    def upsert(self, conn, rows: list[dict]) -> None:
        if not rows:
            return
        sql = text("""
            INSERT INTO financial_metrics (
                ticker, period_end, period_type,
                revenue, net_income, eps, pe_ratio, pb_ratio,
                roe, debt_to_equity, free_cash_flow, source, run_id
            ) VALUES (
                :ticker, :period_end, :period_type,
                :revenue, :net_income, :eps, :pe_ratio, :pb_ratio,
                :roe, :debt_to_equity, :free_cash_flow, :source, :run_id
            )
            ON CONFLICT (ticker, period_end, period_type) DO UPDATE SET
                revenue = EXCLUDED.revenue,
                net_income = EXCLUDED.net_income,
                eps = EXCLUDED.eps,
                pe_ratio = EXCLUDED.pe_ratio,
                pb_ratio = EXCLUDED.pb_ratio,
                roe = EXCLUDED.roe,
                debt_to_equity = EXCLUDED.debt_to_equity,
                free_cash_flow = EXCLUDED.free_cash_flow,
                fetched_at = now(),
                run_id = EXCLUDED.run_id
        """)
        conn.execute(sql, rows)
        logger.info(f"Upserted {len(rows)} fundamental rows")
