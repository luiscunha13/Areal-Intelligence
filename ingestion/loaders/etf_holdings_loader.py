"""
ingestion/loaders/etf_holdings_loader.py
─────────────────────────────────────────
Fetches top ETF holdings (constituents + weights) from yfinance
and upserts them into the etf_holdings table.

Run:
    docker compose exec api python -c "
    from ingestion.loaders.etf_holdings_loader import EtfHoldingsLoader
    loader = EtfHoldingsLoader('postgresql://postgres:postgres@postgres:5432/arealdb')
    loader.run()
    "
"""
import logging
import time
from datetime import date, datetime
from typing import Optional

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

_DELAY = 0.5  # seconds between yfinance requests


def load_etf_tickers_from_db(database_url: str) -> list[str]:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT ticker FROM etfs WHERE is_active = true ORDER BY ticker")).all()
    return [r[0] for r in rows]


class EtfHoldingsLoader:
    """
    Fetches top ETF holdings via yfinance and upserts into etf_holdings.
    yfinance's .funds_data.top_holdings works for most major ETFs.
    Falls back to .info['holdings'] for others.
    """

    def __init__(
        self,
        database_url: str,
        tickers: Optional[list[str]] = None,
        holding_date: Optional[date] = None,
    ):
        self.database_url = database_url
        self.tickers = tickers  # None = load from DB
        self.holding_date = holding_date or date.today()

    def run(self) -> None:
        engine = create_engine(self.database_url)
        tickers = self.tickers or load_etf_tickers_from_db(self.database_url)
        logger.info(f"Fetching holdings for {len(tickers)} ETFs")

        total_rows = 0
        with engine.begin() as conn:
            for ticker in tickers:
                rows = self._fetch_holdings(ticker)
                if not rows:
                    logger.debug(f"  {ticker}: no holdings available")
                    continue

                for row in rows:
                    conn.execute(text("""
                        INSERT INTO etf_holdings (etf_ticker, holding_date, rank, symbol, name, weight_pct)
                        VALUES (:etf_ticker, :holding_date, :rank, :symbol, :name, :weight_pct)
                        ON CONFLICT (etf_ticker, holding_date, symbol) DO UPDATE SET
                            rank       = EXCLUDED.rank,
                            name       = EXCLUDED.name,
                            weight_pct = EXCLUDED.weight_pct
                    """), row)
                total_rows += len(rows)
                logger.info(f"  {ticker}: {len(rows)} holdings upserted")
                time.sleep(_DELAY)

        logger.info(f"Done — {total_rows} total holding rows upserted for date {self.holding_date}")

    def _fetch_holdings(self, ticker: str) -> list[dict]:
        """Try multiple yfinance APIs to get holdings."""
        try:
            yf_ticker = yf.Ticker(ticker)

            # Method 1: funds_data.top_holdings (newer yfinance, most ETFs)
            try:
                holdings_df = yf_ticker.funds_data.top_holdings
                if holdings_df is not None and not holdings_df.empty:
                    return self._parse_holdings_df(ticker, holdings_df)
            except Exception:
                pass

            # Method 2: info['holdings'] dict (older yfinance fallback)
            try:
                info = yf_ticker.info
                holdings = info.get("holdings", [])
                if holdings:
                    rows = []
                    for i, h in enumerate(holdings[:25], start=1):
                        symbol = h.get("symbol") or h.get("ticker", "")
                        if not symbol:
                            continue
                        rows.append({
                            "etf_ticker":   ticker,
                            "holding_date": self.holding_date,
                            "rank":         i,
                            "symbol":       symbol,
                            "name":         h.get("holdingName") or h.get("name"),
                            "weight_pct":   round(float(h.get("holdingPercent", 0)) * 100, 4),
                        })
                    return rows
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"  {ticker}: failed to fetch holdings — {e}")

        return []

    def _parse_holdings_df(self, ticker: str, df: pd.DataFrame) -> list[dict]:
        """Parse a funds_data.top_holdings DataFrame into row dicts."""
        rows = []
        name_col = next((c for c in df.columns if c.lower() in ["name", "holdingname", "holding name"]), None)
        weight_col = next((c for c in df.columns if any(w in c.lower() for w in ["percent", "weight", "assets"])), None)

        for i, (idx_symbol, row) in enumerate(df.iterrows(), start=1):
            symbol = str(row.get("Symbol")) if "Symbol" in df.columns else str(idx_symbol)
            if not symbol or symbol == "nan":
                continue

            name = str(row[name_col]) if name_col and pd.notna(row[name_col]) else None

            weight_pct = None
            if weight_col and pd.notna(row[weight_col]):
                try:
                    w = float(row[weight_col])
                    weight_pct = round(w * 100 if w <= 1.0 else w, 4)
                except (ValueError, TypeError):
                    weight_pct = None

            rows.append({
                "etf_ticker":   ticker,
                "holding_date": self.holding_date,
                "rank":         i,
                "symbol":       symbol,
                "name":         name,
                "weight_pct":   weight_pct,
            })
            if i >= 25:
                break

        return rows
