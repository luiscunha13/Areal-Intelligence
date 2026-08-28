"""
ingestion/sources/fred.py
──────────────────────────
FRED API client — thin wrapper around fredapi with rate limiting.
"""
import os
import time
import logging
from datetime import date
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

_RATE_LIMIT_DELAY = 0.5  # seconds between API calls (FRED allows ~120/min)


class FredClient:
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.environ.get("FRED_API_KEY")
        if not api_key:
            raise ValueError("FRED_API_KEY not set")
        try:
            from fredapi import Fred
            self._fred = Fred(api_key=api_key)
        except ImportError:
            raise ImportError("Install fredapi: pip install fredapi")

    def fetch_series(
        self,
        series_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """
        Fetch a FRED series. Returns a DataFrame with columns [date, value].
        Drops NaN values automatically.
        """
        logger.debug(f"Fetching FRED series: {series_id}")
        time.sleep(_RATE_LIMIT_DELAY)  # polite rate limiting

        kwargs = {}
        if start_date:
            kwargs["observation_start"] = start_date.isoformat()
        if end_date:
            kwargs["observation_end"] = end_date.isoformat()

        series = self._fred.get_series(series_id, **kwargs)
        df = series.dropna().reset_index()
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    def fetch_latest(self, series_id: str) -> Optional[tuple[date, float]]:
        """Fetch only the most recent observation."""
        df = self.fetch_series(series_id)
        if df.empty:
            return None
        row = df.iloc[-1]
        return row["date"], float(row["value"])
