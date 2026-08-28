"""
ingestion/base.py
─────────────────
BaseLoader: shared logic for all data loaders.
Provides retry, rate limiting, run_id tracking, and pipeline_runs audit logging.
"""
import uuid
import time
import logging
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_run_id(dag_id: str) -> str:
    ts = utcnow().strftime("%Y%m%dT%H%M%S")
    return f"{dag_id}__{ts}__{uuid.uuid4().hex[:8]}"


class BaseLoader(ABC):
    """
    Abstract base class for all ingestion loaders.

    Subclasses implement:
        fetch() -> raw data
        transform() -> list of dicts
        load() -> upsert to DB

    The run() method orchestrates all three and logs to pipeline_runs.
    """

    dag_id: str = "base"

    def __init__(self, database_url: str, dry_run: bool = False):
        self.engine: Engine = create_engine(database_url, pool_pre_ping=True)
        self.dry_run = dry_run
        self.run_id = new_run_id(self.dag_id)
        self.rows_ingested = 0
        self.rows_failed = 0

    # ── Subclass interface ────────────────────────────────────────
    @abstractmethod
    def fetch(self) -> Any:
        """Fetch raw data from the external source."""

    @abstractmethod
    def transform(self, raw: Any) -> list[dict]:
        """Transform raw data into a list of row dicts ready for upsert."""

    @abstractmethod
    def upsert(self, conn, rows: list[dict]) -> None:
        """Upsert rows into the target table."""

    # ── Pipeline run ──────────────────────────────────────────────
    def run(self) -> dict:
        """
        Full pipeline: start audit → fetch → transform → upsert → close audit.
        Returns a summary dict.
        """
        started_at = utcnow()
        logger.info(f"[{self.run_id}] Starting {self.dag_id}")

        if not self.dry_run:
            self._log_run_start(started_at)

        error_message = None
        try:
            raw = self.fetch()
            rows = self.transform(raw)

            if not self.dry_run:
                with self.engine.begin() as conn:
                    self.upsert(conn, rows)
            else:
                logger.info(f"[{self.run_id}] DRY RUN — {len(rows)} rows would be written")

            self.rows_ingested = len(rows)
            status = "success"
            logger.info(f"[{self.run_id}] Done — {self.rows_ingested} rows ingested")

        except Exception as e:
            status = "failed"
            error_message = str(e)
            logger.error(f"[{self.run_id}] Failed: {e}", exc_info=True)

        finally:
            if not self.dry_run:
                self._log_run_end(status, error_message)

        return {
            "run_id": self.run_id,
            "status": status,
            "rows_ingested": self.rows_ingested,
            "rows_failed": self.rows_failed,
            "error": error_message,
        }

    # ── Audit helpers ─────────────────────────────────────────────
    def _log_run_start(self, started_at: datetime) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO pipeline_runs (run_id, dag_id, started_at, status)
                VALUES (:run_id, :dag_id, :started_at, 'running')
                ON CONFLICT (run_id) DO NOTHING
            """), {"run_id": self.run_id, "dag_id": self.dag_id, "started_at": started_at})

    def _log_run_end(self, status: str, error_message: str | None) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("""
                UPDATE pipeline_runs SET
                    completed_at = :completed_at,
                    status = :status,
                    rows_ingested = :rows_ingested,
                    rows_failed = :rows_failed,
                    error_message = :error_message
                WHERE run_id = :run_id
            """), {
                "run_id": self.run_id,
                "completed_at": utcnow(),
                "status": status,
                "rows_ingested": self.rows_ingested,
                "rows_failed": self.rows_failed,
                "error_message": error_message,
            })

    # ── Retry helper ──────────────────────────────────────────────
    @staticmethod
    def retry(fn, retries: int = 3, backoff: float = 2.0):
        """Call fn with exponential backoff on failure."""
        last_exc = None
        for attempt in range(retries):
            try:
                return fn()
            except Exception as e:
                last_exc = e
                wait = backoff ** attempt
                logger.warning(f"Attempt {attempt + 1}/{retries} failed: {e}. Retrying in {wait}s")
                time.sleep(wait)
        raise last_exc
