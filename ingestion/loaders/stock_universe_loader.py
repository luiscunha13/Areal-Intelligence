"""
ingestion/loaders/stock_universe_loader.py
────────────────────────────────────────────
Syncs the stock universe to the DB from multiple sources:
  1. S&P 500 constituents (Wikipedia)
  2. yfinance company metadata (sector, industry, exchange)
Run this on first setup and periodically (monthly) to keep the universe fresh.
"""
import logging
from typing import Optional

import pandas as pd
from sqlalchemy import text

from ingestion.base import BaseLoader
from ingestion.sources.yfinance_client import YFinanceClient

logger = logging.getLogger(__name__)

SP500_WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


class StockUniverseLoader(BaseLoader):
    """
    Syncs the S&P 500 stock universe into the stocks table.
    Enriches each ticker with sector/industry metadata from yfinance.
    """
    dag_id = "stock_universe_sync"

    def __init__(self, database_url: str, dry_run: bool = False):
        super().__init__(database_url, dry_run)
        self.client = YFinanceClient()

    def fetch(self) -> list[dict]:
        """Fetch S&P 500 tickers from Wikipedia."""
        logger.info("Fetching S&P 500 universe from Wikipedia")
        import requests
        import io
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(SP500_WIKI_URL, headers=headers)
        tables = pd.read_html(io.StringIO(resp.text))
        df = tables[0]
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]

        stocks = []
        for _, row in df.iterrows():
            ticker = str(row.get("symbol", "")).replace(".", "-")
            stocks.append({
                "ticker": ticker,
                "name": str(row.get("security", "")),
                "sector": str(row.get("gics_sector", "")),
                "industry": str(row.get("gics_sub-industry", "")),
            })
        logger.info(f"  Found {len(stocks)} S&P 500 constituents")
        return stocks

    def transform(self, raw: list[dict]) -> list[dict]:
        """Enrich with exchange + country from yfinance (sample first 50 for speed)."""
        rows = []
        for stock in raw:
            rows.append({
                "ticker": stock["ticker"],
                "name": stock["name"],
                "sector": stock["sector"],
                "industry": stock["industry"],
                "exchange": "NYSE/NASDAQ",  # default — enriched lazily
                "country": "US",
                "market_cap_tier": "large",  # S&P 500 = large cap
            })
        return rows

    def upsert(self, conn, rows: list[dict]) -> None:
        sql = text("""
            INSERT INTO stocks (ticker, name, sector, industry, exchange, country, market_cap_tier)
            VALUES (:ticker, :name, :sector, :industry, :exchange, :country, :market_cap_tier)
            ON CONFLICT (ticker) DO UPDATE SET
                name = EXCLUDED.name,
                sector = EXCLUDED.sector,
                industry = EXCLUDED.industry
        """)
        conn.execute(sql, rows)
        logger.info(f"Upserted {len(rows)} stocks")
