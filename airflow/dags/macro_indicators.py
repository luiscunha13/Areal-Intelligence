"""
airflow/dags/macro_indicators.py
──────────────────────────────────
DAG: Macro Indicators Ingestion
Schedule: Daily weekdays at 07:00 UTC
Purpose: Fetch all FRED macro series and compute derived indicators.
"""
import os
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/arealdb")

default_args = {
    "owner": "areal-intelligence",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "email_on_failure": False,
}


def run_macro_ingest(**context):
    """Ingest all active FRED macro series (incremental)."""
    import sys
    sys.path.insert(0, "/opt/airflow/src")

    from ingestion.loaders.macro_loader import MacroLoader

    loader = MacroLoader(database_url=DATABASE_URL)
    result = loader.run()

    logger.info(f"Macro ingest complete: {result}")

    if result["status"] == "failed":
        raise RuntimeError(f"Macro ingest failed: {result['error']}")

    # Push summary to XCom for downstream tasks
    context["ti"].xcom_push(key="macro_result", value=result)
    return result


def run_catalog_sync(**context):
    """Sync YAML catalogs to DB (idempotent — safe to run daily)."""
    import sys
    sys.path.insert(0, "/opt/airflow/src")
    import subprocess
    result = subprocess.run(
        ["python", "/opt/airflow/src/scripts/catalog_sync.py"],
        capture_output=True, text=True
    )
    logger.info(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)


def run_quality_check(**context):
    """
    Basic data freshness check — verifies key series have recent data.
    Fails the DAG if critical series are stale (> 40 days).
    """
    import sys
    sys.path.insert(0, "/opt/airflow/src")

    from sqlalchemy import create_engine, text
    from datetime import date

    engine = create_engine(DATABASE_URL)
    critical_series = ["CPIAUCSL", "UNRATE", "FEDFUNDS", "VIXCLS"]
    staleness_limit_days = 40

    with engine.connect() as conn:
        for sid in critical_series:
            row = conn.execute(text("""
                SELECT MAX(date) as latest FROM macro_observations WHERE series_id = :sid
            """), {"sid": sid}).fetchone()

            latest = row.latest if row else None
            if not latest:
                raise ValueError(f"Quality check FAILED: {sid} has NO data")

            age_days = (date.today() - latest).days
            if age_days > staleness_limit_days:
                raise ValueError(
                    f"Quality check FAILED: {sid} is {age_days} days stale "
                    f"(limit: {staleness_limit_days})"
                )
            logger.info(f"  ✅ {sid}: latest = {latest} ({age_days}d ago)")


with DAG(
    dag_id="macro_indicators",
    description="Daily FRED macro data ingestion + quality checks",
    schedule="0 7 * * 1-5",   # 07:00 UTC, Mon–Fri
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["macro", "fred", "ingestion"],
    default_args=default_args,
) as dag:

    t_catalog_sync = PythonOperator(
        task_id="catalog_sync",
        python_callable=run_catalog_sync,
        doc_md="Sync YAML catalog definitions to database.",
    )

    t_macro_ingest = PythonOperator(
        task_id="macro_ingest",
        python_callable=run_macro_ingest,
        doc_md="Fetch all active FRED series + compute derived indicators.",
    )

    t_quality_check = PythonOperator(
        task_id="quality_check",
        python_callable=run_quality_check,
        doc_md="Verify key series are fresh. Fails DAG if stale.",
    )

    # Dependency chain: sync catalog → ingest → quality check
    t_catalog_sync >> t_macro_ingest >> t_quality_check
