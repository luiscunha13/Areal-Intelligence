"""
ingestion/loaders/macro_loader.py
──────────────────────────────────
Loads macro observations from FRED into the production DB.
Handles both real series and derived series (e.g. FED_NET_LIQUIDITY).
"""
import logging
import os
from datetime import date, timedelta
from typing import Optional

import yaml
import pandas as pd
from sqlalchemy import text

from ingestion.base import BaseLoader
from ingestion.sources.fred import FredClient

logger = logging.getLogger(__name__)

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "../../catalog/macro_series.yaml")


def load_catalog() -> list[dict]:
    with open(CATALOG_PATH) as f:
        return yaml.safe_load(f).get("series", [])


class MacroLoader(BaseLoader):
    """
    Ingests all active macro series from FRED into macro_observations.
    Derived series (e.g. FED_NET_LIQUIDITY) are computed after all base series land.
    """
    dag_id = "macro_indicators"

    def __init__(
        self,
        database_url: str,
        series_ids: Optional[list[str]] = None,
        start_date: Optional[date] = None,
        dry_run: bool = False,
    ):
        super().__init__(database_url, dry_run)
        self.fred = FredClient()
        self.catalog = load_catalog()
        self.series_ids = series_ids  # None = all active series
        # Default: fetch last 30 days (incremental) or override for backfill
        self.start_date = start_date or (date.today() - timedelta(days=35))

    def _active_series(self) -> list[dict]:
        series = [s for s in self.catalog if not s.get("is_derived", False)]
        if self.series_ids:
            series = [s for s in series if s["series_id"] in self.series_ids]
        return series

    def _derived_series(self) -> list[dict]:
        return [s for s in self.catalog if s.get("is_derived", False)]

    # ── fetch ─────────────────────────────────────────────────────
    def fetch(self) -> dict[str, pd.DataFrame]:
        """Fetch all base (non-derived) series from FRED."""
        results = {}
        for s in self._active_series():
            sid = s["series_id"]
            try:
                df = self.fred.fetch_series(sid, start_date=self.start_date)
                results[sid] = df
                logger.info(f"  FRED {sid}: {len(df)} observations")
            except Exception as e:
                logger.error(f"  FRED {sid} FAILED: {e}")
                self.rows_failed += 1
        return results

    # ── transform ─────────────────────────────────────────────────
    def transform(self, raw: dict[str, pd.DataFrame]) -> list[dict]:
        rows = []
        for sid, df in raw.items():
            for _, row in df.iterrows():
                rows.append({
                    "series_id": sid,
                    "date": row["date"],
                    "value": float(row["value"]),
                    "source": "fred_api",
                    "run_id": self.run_id,
                })
        return rows

    # ── upsert ────────────────────────────────────────────────────
    def upsert(self, conn, rows: list[dict]) -> None:
        if not rows:
            return
        sql = text("""
            INSERT INTO macro_observations (series_id, date, value, source, run_id)
            VALUES (:series_id, :date, :value, :source, :run_id)
            ON CONFLICT (series_id, date) DO UPDATE SET
                value = EXCLUDED.value,
                source = EXCLUDED.source,
                fetched_at = now(),
                run_id = EXCLUDED.run_id
        """)
        conn.execute(sql, rows)
        logger.info(f"Upserted {len(rows)} macro observations")

    # ── compute derived series ────────────────────────────────────
    def compute_derived(self, conn) -> None:
        """
        Compute derived series after base data is loaded.
        Currently supports: FED_NET_LIQUIDITY = WALCL - WTREGEN - RRPONTSYD
        """
        for s in self._derived_series():
            sid = s["series_id"]
            formula = s.get("derive_formula", "")
            logger.info(f"Computing derived series: {sid} = {formula}")

            if sid == "FED_NET_LIQUIDITY":
                conn.execute(text("""
                    INSERT INTO macro_observations (series_id, date, value, source, run_id)
                    SELECT
                        'FED_NET_LIQUIDITY',
                        w.date,
                        -- Convert all to billions: WALCL is in millions, WTREGEN in millions, RRPONTSYD in billions
                        (w.value / 1000.0) - (tga.value / 1000.0) - rrp.value,
                        'derived',
                        :run_id
                    FROM macro_observations w
                    JOIN macro_observations tga
                        ON tga.series_id = 'WTREGEN' AND tga.date = w.date
                    JOIN macro_observations rrp
                        ON rrp.series_id = 'RRPONTSYD' AND rrp.date = w.date
                    WHERE w.series_id = 'WALCL'
                    ON CONFLICT (series_id, date) DO UPDATE SET
                        value = EXCLUDED.value,
                        fetched_at = now(),
                        run_id = EXCLUDED.run_id
                """), {"run_id": self.run_id})
                logger.info(f"  {sid}: computed and upserted")

    def run(self) -> dict:
        """Override run to also compute derived series."""
        result = super().run()
        if result["status"] == "success" and not self.dry_run:
            logger.info("Computing derived series...")
            with self.engine.begin() as conn:
                self.compute_derived(conn)
        return result
