"""
ingestion/sources/yfinance_client.py
─────────────────────────────────────
Yahoo Finance client — wraps yfinance for price data fetching.
Handles rate limiting, missing tickers, and returns clean DataFrames.
"""
import time
import logging
from datetime import date, timedelta
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

_BATCH_DELAY = 1.0   # seconds between batch requests


class YFinanceClient:
    def fetch_prices(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV + adjusted close for a single ticker.
        Returns DataFrame with columns [date, open, high, low, close, adj_close, volume].
        """
        try:
            import yfinance as yf
        except ImportError:
            raise ImportError("Install yfinance: pip install yfinance")

        start = (start_date or (date.today() - timedelta(days=365 * 5))).isoformat()
        end = (end_date or date.today()).isoformat()

        logger.debug(f"Fetching yfinance prices: {ticker} [{start} → {end}]")
        time.sleep(_BATCH_DELAY)

        df = yf.download(
            ticker,
            start=start,
            end=end,
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if df.empty:
            logger.warning(f"No price data for {ticker}")
            return pd.DataFrame()

        # Flatten multi-level columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0].lower().replace(" ", "_") for col in df.columns]
        else:
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]

        df = df.rename(columns={"adj_close": "adj_close"}).reset_index()
        df["date"] = pd.to_datetime(df["Date"]).dt.date
        df = df.rename(columns={
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Adj Close": "adj_close", "Volume": "volume"
        })

        # Normalize column names regardless of case
        df.columns = [c.lower() for c in df.columns]
        df = df[["date", "open", "high", "low", "close", "adj_close", "volume"]]
        df = df.dropna(subset=["close"])
        return df

    def fetch_prices_batch(
        self,
        tickers: list[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict[str, pd.DataFrame]:
        """Fetch prices for multiple tickers. Returns {ticker: DataFrame}."""
        results = {}
        for ticker in tickers:
            try:
                df = self.fetch_prices(ticker, start_date, end_date)
                if not df.empty:
                    results[ticker] = df
            except Exception as e:
                logger.error(f"Failed to fetch {ticker}: {e}")
        return results

    def fetch_info(self, ticker: str) -> dict:
        """Fetch company/ETF metadata (name, sector, expense ratio, etc.)."""
        try:
            import yfinance as yf
            info = yf.Ticker(ticker).info or {}
            return {
                "name": info.get("longName") or info.get("shortName", ""),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "exchange": info.get("exchange"),
                "country": info.get("country", "US"),
                "expense_ratio": info.get("annualReportExpenseRatio"),
            }
        except Exception as e:
            logger.warning(f"Could not fetch info for {ticker}: {e}")
            return {}
