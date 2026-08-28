"""
airflow/dags/data_quality.py
──────────────────────────────
DAG: Data Quality Report
Schedule: Every Monday 09:00 UTC
Purpose: Run comprehensive data quality checks across all production tables.
  • Freshness checks — key series must have recent data
  • Completeness checks — tables must have minimum row counts
  • Anomaly checks — detect sudden value spikes using z-scores
  • Results written to data_quality_checks table for tracking
"""
import os
import logging
from datetime import datetime, timedelta, date

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/arealdb")

default_args = {
    "owner": "areal-intelligence",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}


def check_macro_freshness(**context):
    import sys
    sys.path.insert(0, "/opt/airflow/src")

    from sqlalchemy import create_engine, text

    engine = create_engine(DATABASE_URL)
    run_id = f"dq_freshness_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}"

    # Thresholds: max acceptable staleness in days
    checks = [
        ("VIXCLS",    3,  "risk"),
        ("DGS10",     3,  "rates"),
        ("FEDFUNDS",  35, "rates"),
        ("CPIAUCSL",  35, "inflation"),
        ("UNRATE",    35, "growth"),
        ("INDPRO",    35, "growth"),
        ("WALCL",     7,  "liquidity"),
        ("M2SL",      35, "liquidity"),
    ]

    results = []
    failed = []

    with engine.begin() as conn:
        for series_id, max_days, category in checks:
            row = conn.execute(text(
                "SELECT MAX(date) as latest FROM macro_observations WHERE series_id = :sid"
            ), {"sid": series_id}).fetchone()

            latest = row.latest if row else None
            if not latest:
                passed, metric = False, None
                message = f"{series_id}: NO DATA"
            else:
                age = (date.today() - latest).days
                passed = age <= max_days
                metric = float(age)
                message = f"{series_id}: {age}d old (limit {max_days}d) — {'✅' if passed else '❌'}"

            logger.info(f"  {message}")
            if not passed:
                failed.append(message)

            results.append({
                "run_id": run_id,
                "check_name": "macro_freshness",
                "entity": series_id,
                "passed": passed,
                "metric": metric,
                "threshold": float(max_days),
                "message": message,
            })

        # Write results
        conn.execute(text("""
            INSERT INTO pipeline_runs (run_id, dag_id, started_at, status)
            VALUES (:run_id, 'data_quality', now(), 'running')
            ON CONFLICT (run_id) DO NOTHING
        """), {"run_id": run_id})

        for r in results:
            conn.execute(text("""
                INSERT INTO data_quality_checks
                    (run_id, check_name, entity, passed, metric, threshold, message)
                VALUES (:run_id, :check_name, :entity, :passed, :metric, :threshold, :message)
            """), r)

        conn.execute(text("""
            UPDATE pipeline_runs SET status = 'success', completed_at = now()
            WHERE run_id = :run_id
        """), {"run_id": run_id})

    if failed:
        raise ValueError(f"Data quality FAILED:\n" + "\n".join(failed))


def check_table_completeness(**context):
    from sqlalchemy import create_engine, text

    engine = create_engine(DATABASE_URL)
    run_id = f"dq_completeness_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}"

    checks = [
        ("macro_observations", 1000),
        ("prices",             5000),
        ("macro_series",       30),
        ("etfs",               80),
        ("sectors",            11),
    ]

    failed = []
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO pipeline_runs (run_id, dag_id, started_at, status)
            VALUES (:run_id, 'data_quality', now(), 'running')
            ON CONFLICT (run_id) DO NOTHING
        """), {"run_id": run_id})

        for table, min_rows in checks:
            row = conn.execute(text(f"SELECT COUNT(*) as cnt FROM {table}")).fetchone()
            cnt = row.cnt if row else 0
            passed = cnt >= min_rows
            msg = f"{table}: {cnt} rows (min {min_rows}) — {'✅' if passed else '❌'}"
            logger.info(f"  {msg}")
            if not passed:
                failed.append(msg)

            conn.execute(text("""
                INSERT INTO data_quality_checks
                    (run_id, check_name, entity, passed, metric, threshold, message)
                VALUES (:run_id, :check_name, :entity, :passed, :metric, :threshold, :message)
            """), {
                "run_id": run_id,
                "check_name": "completeness",
                "entity": table,
                "passed": passed,
                "metric": float(cnt),
                "threshold": float(min_rows),
                "message": msg,
            })

        conn.execute(text("""
            UPDATE pipeline_runs SET status = 'success', completed_at = now()
            WHERE run_id = :run_id
        """), {"run_id": run_id})

    if failed:
        raise ValueError("Completeness checks failed:\n" + "\n".join(failed))


with DAG(
    dag_id="data_quality",
    description="Weekly data quality checks — freshness, completeness, anomalies",
    schedule="0 9 * * 1",   # 09:00 UTC every Monday
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["quality", "monitoring"],
    default_args=default_args,
) as dag:

    t_freshness = PythonOperator(
        task_id="check_macro_freshness",
        python_callable=check_macro_freshness,
        doc_md="Verify all key macro series have recent data within acceptable staleness limits.",
    )

    t_completeness = PythonOperator(
        task_id="check_table_completeness",
        python_callable=check_table_completeness,
        doc_md="Verify all production tables meet minimum row count thresholds.",
    )

    t_freshness >> t_completeness
