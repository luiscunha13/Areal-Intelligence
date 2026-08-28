"""
airflow/dags/market_prices.py
───────────────────────────────
DAG: Market Prices Ingestion
Schedule: Daily weekdays at 22:00 UTC (post-market close)
Purpose: Fetch EOD OHLCV prices for all catalog ETFs via yfinance.
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
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,
}


def run_etf_price_ingest(**context):
    import sys
    sys.path.insert(0, "/opt/airflow/src")

    from ingestion.loaders.price_loader import PriceLoader

    loader = PriceLoader(database_url=DATABASE_URL)
    result = loader.run()
    logger.info(f"ETF price ingest: {result}")

    if result["status"] == "failed":
        raise RuntimeError(f"Price ingest failed: {result['error']}")

    context["ti"].xcom_push(key="price_result", value=result)
    return result


def run_scoring_trigger(**context):
    """
    Placeholder for triggering the scoring DAG downstream.
    In production, use TriggerDagRunOperator.
    """
    logger.info("Prices loaded — scoring pipeline can now be triggered.")


with DAG(
    dag_id="market_prices",
    description="Daily EOD price ingestion for all catalog ETFs",
    schedule="0 22 * * 1-5",   # 22:00 UTC, Mon–Fri
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["prices", "etf", "yfinance", "ingestion"],
    default_args=default_args,
) as dag:

    t_etf_prices = PythonOperator(
        task_id="etf_price_ingest",
        python_callable=run_etf_price_ingest,
        doc_md="Fetch EOD OHLCV for all active ETFs from catalog.",
    )

    t_scoring_trigger = PythonOperator(
        task_id="scoring_trigger",
        python_callable=run_scoring_trigger,
        doc_md="Signal that prices are ready for scoring.",
    )

    t_etf_prices >> t_scoring_trigger
