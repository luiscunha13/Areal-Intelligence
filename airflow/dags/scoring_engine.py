"""
airflow/dags/scoring_engine.py
────────────────────────────────
DAG: Scoring Engine
Schedule: Daily 23:00 UTC (after market_prices completes)
Purpose: Run dbt transformations to populate all analytics marts.

Pipeline:
  1. dbt run --select staging     → clean + cast raw data
  2. dbt run --select intermediate → compute features + returns
  3. dbt run --select marts        → compute scores + regimes + rankings
  4. dbt test                      → validate mart outputs
  5. Sync marts → production tables (for API consumption)
"""
import os
import subprocess
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

DBT_DIR = "/opt/airflow/src/transformation"
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/arealdb")

default_args = {
    "owner": "areal-intelligence",
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,
}


def run_dbt(select: str, **context):
    """Run a dbt command and raise on failure."""
    cmd = [
        "dbt", "run",
        "--select", select,
        "--profiles-dir", DBT_DIR,
        "--project-dir", DBT_DIR,
    ]
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=DBT_DIR)
    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise RuntimeError(f"dbt run failed for '{select}':\n{result.stderr}")
    return result.stdout


def run_dbt_test(**context):
    cmd = [
        "dbt", "test",
        "--profiles-dir", DBT_DIR,
        "--project-dir", DBT_DIR,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=DBT_DIR)
    logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise RuntimeError(f"dbt test failed:\n{result.stderr}")


def sync_marts_to_production(**context):
    """
    Copies dbt mart outputs into the main production tables
    (sector_scores, etf_scores, market_regimes) which the API reads.
    dbt writes to schema-prefixed tables; this sync step merges into
    the canonical production tables tracked by Alembic.
    """
    from sqlalchemy import create_engine, text

    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:

        # Market regimes
        conn.execute(text("""
            INSERT INTO market_regimes
                (date, quadrant, growth_momentum, inflation_momentum,
                 fca_score, policy_stance, confidence, scoring_version, computed_at)
            SELECT
                obs_date, quadrant, growth_momentum, inflation_momentum,
                fca_score, policy_stance, confidence, scoring_version, computed_at
            FROM marts.mart_market_regimes
            ON CONFLICT (date) DO UPDATE SET
                quadrant = EXCLUDED.quadrant,
                growth_momentum = EXCLUDED.growth_momentum,
                inflation_momentum = EXCLUDED.inflation_momentum,
                fca_score = EXCLUDED.fca_score,
                policy_stance = EXCLUDED.policy_stance,
                confidence = EXCLUDED.confidence,
                scoring_version = EXCLUDED.scoring_version,
                computed_at = EXCLUDED.computed_at
        """))
        logger.info("✅ market_regimes synced")

        # ETF scores
        conn.execute(text("""
            INSERT INTO etf_scores
                (ticker, date, momentum_1m, momentum_3m, momentum_6m, momentum_12m,
                 sharpe_1y, volatility_1y, composite_score, rank_overall, rank_category,
                 scoring_version, computed_at)
            SELECT
                ticker, price_date, ret_1m, ret_3m, ret_6m, ret_12m,
                sharpe_approx_1y, volatility_ann_pct, composite_score,
                rank_overall, rank_category, scoring_version, computed_at
            FROM marts.mart_etf_scores
            ON CONFLICT (ticker, date) DO UPDATE SET
                momentum_1m = EXCLUDED.momentum_1m,
                momentum_3m = EXCLUDED.momentum_3m,
                momentum_6m = EXCLUDED.momentum_6m,
                momentum_12m = EXCLUDED.momentum_12m,
                sharpe_1y = EXCLUDED.sharpe_1y,
                volatility_1y = EXCLUDED.volatility_1y,
                composite_score = EXCLUDED.composite_score,
                rank_overall = EXCLUDED.rank_overall,
                rank_category = EXCLUDED.rank_category,
                scoring_version = EXCLUDED.scoring_version,
                computed_at = EXCLUDED.computed_at
        """))
        logger.info("✅ etf_scores synced")

        # Sector scores
        conn.execute(text("""
            INSERT INTO sector_scores
                (ticker, date, horizon, rs_ratio, rs_momentum, rrg_quadrant,
                 composite_score, rank, scoring_version, computed_at)
            SELECT
                ticker, price_date, horizon, rs_ratio, rs_momentum, rrg_quadrant,
                composite_score, rank, scoring_version, computed_at
            FROM marts.mart_sector_scores
            ON CONFLICT (ticker, date, horizon) DO UPDATE SET
                rs_ratio = EXCLUDED.rs_ratio,
                rs_momentum = EXCLUDED.rs_momentum,
                rrg_quadrant = EXCLUDED.rrg_quadrant,
                composite_score = EXCLUDED.composite_score,
                rank = EXCLUDED.rank,
                scoring_version = EXCLUDED.scoring_version,
                computed_at = EXCLUDED.computed_at
        """))
        logger.info("✅ sector_scores synced")

        # Stock scores
        conn.execute(text("""
            INSERT INTO stock_scores
                (ticker, date, momentum_score, trend_score, quality_score,
                 value_score, composite_score, rank_overall, rank_sector,
                 classification, scoring_version, computed_at)
            SELECT
                ticker, price_date, momentum_score, trend_score, quality_score,
                value_score, composite_score, rank_overall, rank_sector,
                classification, scoring_version, computed_at
            FROM marts.mart_stock_scores
            ON CONFLICT (ticker, date) DO UPDATE SET
                momentum_score = EXCLUDED.momentum_score,
                trend_score = EXCLUDED.trend_score,
                quality_score = EXCLUDED.quality_score,
                value_score = EXCLUDED.value_score,
                composite_score = EXCLUDED.composite_score,
                rank_overall = EXCLUDED.rank_overall,
                rank_sector = EXCLUDED.rank_sector,
                classification = EXCLUDED.classification,
                scoring_version = EXCLUDED.scoring_version,
                computed_at = EXCLUDED.computed_at
        """))
        logger.info("✅ stock_scores synced")


with DAG(
    dag_id="scoring_engine",
    description="dbt transform pipeline — staging → intermediate → marts → production sync",
    schedule="0 23 * * 1-5",   # 23:00 UTC, Mon–Fri (after market_prices at 22:00)
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["scoring", "dbt", "transforms"],
    default_args=default_args,
) as dag:

    t_staging = PythonOperator(
        task_id="dbt_staging",
        python_callable=run_dbt,
        op_kwargs={"select": "staging"},
        doc_md="Clean + deduplicate raw ingested data.",
    )

    t_intermediate = PythonOperator(
        task_id="dbt_intermediate",
        python_callable=run_dbt,
        op_kwargs={"select": "intermediate"},
        doc_md="Compute macro features and price returns.",
    )

    t_marts = PythonOperator(
        task_id="dbt_marts",
        python_callable=run_dbt,
        op_kwargs={"select": "marts"},
        doc_md="Compute regime, ETF scores, and sector RRG.",
    )

    t_test = PythonOperator(
        task_id="dbt_test",
        python_callable=run_dbt_test,
        doc_md="Run all dbt data quality tests on mart outputs.",
    )

    t_sync = PythonOperator(
        task_id="sync_to_production",
        python_callable=sync_marts_to_production,
        doc_md="Merge dbt mart tables into canonical production tables for API.",
    )

    t_staging >> t_intermediate >> t_marts >> t_test >> t_sync
