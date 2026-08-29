"""
ingestion/loaders/price_loader.py
───────────────────────────────────
Loads EOD OHLCV prices for all catalog tickers (ETFs + stocks) into the prices table.
"""
import logging
import os
import yaml
from datetime import date, timedelta
from typing import Optional

import pandas as pd
from sqlalchemy import text

from ingestion.base import BaseLoader
from ingestion.sources.yfinance_client import YFinanceClient

logger = logging.getLogger(__name__)

CATALOG_DIR = os.path.join(os.path.dirname(__file__), "../../catalog")


def load_etf_tickers() -> list[str]:
    with open(os.path.join(CATALOG_DIR, "etfs.yaml")) as f:
        data = yaml.safe_load(f)
    return [e["ticker"] for e in data.get("etfs", []) if e.get("is_active", True) is not False]


class PriceLoader(BaseLoader):
    """
    Loads EOD prices for ETFs (and optionally stocks) via yfinance.
    Incremental by default — fetches the last 35 days.
    Pass start_date for full backfill.
    """
    dag_id = "market_prices"

    def __init__(
        self,
        database_url: str,
        tickers: Optional[list[str]] = None,
        start_date: Optional[date] = None,
        dry_run: bool = False,
    ):
        super().__init__(database_url, dry_run)
        self.client = YFinanceClient()
        # Load from catalog if no explicit tickers given
        self.tickers = tickers or load_etf_tickers()
        self.start_date = start_date or (date.today() - timedelta(days=35))

    def fetch(self) -> dict:
        logger.info(f"Fetching prices for {len(self.tickers)} tickers from {self.start_date}")
        return self.client.fetch_prices_batch(self.tickers, start_date=self.start_date)

    def transform(self, raw: dict) -> list[dict]:
        rows = []
        for ticker, df in raw.items():
            for _, row in df.iterrows():
                d = row["date"]
                if hasattr(d, "date") and not isinstance(d, date):
                    d = d.date()
                rows.append({
                    "ticker": ticker,
                    "date": d,
                    "open": float(row["open"]) if pd.notnull(row["open"]) else None,
                    "high": float(row["high"]) if pd.notnull(row["high"]) else None,
                    "low": float(row["low"]) if pd.notnull(row["low"]) else None,
                    "close": float(row["close"]),
                    "adj_close": float(row["adj_close"]) if pd.notnull(row.get("adj_close")) else float(row["close"]),
                    "volume": int(row["volume"]) if pd.notnull(row.get("volume")) else None,
                    "source": "yfinance",
                    "run_id": self.run_id,
                })
        return rows

    def upsert(self, conn, rows: list[dict]) -> None:
        if not rows:
            return
        sql = text("""
            INSERT INTO prices (ticker, date, open, high, low, close, adj_close, volume, source, run_id)
            VALUES (:ticker, :date, :open, :high, :low, :close, :adj_close, :volume, :source, :run_id)
            ON CONFLICT (ticker, date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                adj_close = EXCLUDED.adj_close,
                volume = EXCLUDED.volume,
                fetched_at = now(),
                run_id = EXCLUDED.run_id
        """)
        conn.execute(sql, rows)
        logger.info(f"Upserted {len(rows)} price rows")
