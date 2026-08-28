"""
airflow/dags/fundamentals.py
──────────────────────────────
DAG: Fundamentals Ingestion
Schedule: Weekly on Monday 08:00 UTC
Purpose:
  1. Sync S&P 500 stock universe (adds new constituents, marks delisted inactive)
  2. Fetch annual + quarterly financials for all active stocks via yfinance
  3. Trigger scoring_engine DAG to recompute stock scores with fresh fundamentals
"""
import os
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/arealdb")

default_args = {
    "owner": "areal-intelligence",
    "retries": 2,
    "retry_delay": timedelta(minutes=15),
    "email_on_failure": False,
}


def sync_stock_universe(**context):
    import sys
    sys.path.insert(0, "/opt/airflow/src")
    from ingestion.loaders.stock_universe_loader import StockUniverseLoader

    loader = StockUniverseLoader(database_url=DATABASE_URL)
    result = loader.run()
    logger.info(f"Universe sync: {result}")
    if result["status"] == "failed":
        raise RuntimeError(result["error"])
    context["ti"].xcom_push(key="universe_result", value=result)


def fetch_fundamentals(**context):
    import sys
    sys.path.insert(0, "/opt/airflow/src")
    from ingestion.loaders.fundamentals_loader import FundamentalsLoader

    loader = FundamentalsLoader(database_url=DATABASE_URL)
    result = loader.run()
    logger.info(f"Fundamentals: {result}")
    if result["status"] == "failed":
        raise RuntimeError(result["error"])
    context["ti"].xcom_push(key="fundamentals_result", value=result)


with DAG(
    dag_id="fundamentals",
    description="Weekly stock universe sync + fundamentals ingestion",
    schedule="0 8 * * 1",   # 08:00 UTC every Monday
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["stocks", "fundamentals", "yfinance", "ingestion"],
    default_args=default_args,
) as dag:

    t_universe = PythonOperator(
        task_id="sync_stock_universe",
        python_callable=sync_stock_universe,
        doc_md="Sync S&P 500 constituents into the stocks table.",
    )

    t_fundamentals = PythonOperator(
        task_id="fetch_fundamentals",
        python_callable=fetch_fundamentals,
        doc_md="Fetch annual financials for all active stocks via yfinance.",
    )

    t_trigger_scoring = TriggerDagRunOperator(
        task_id="trigger_scoring_engine",
        trigger_dag_id="scoring_engine",
        wait_for_completion=False,
        doc_md="Trigger scoring engine to recompute stock scores with fresh data.",
    )

    t_universe >> t_fundamentals >> t_trigger_scoring
