import os
import sqlite3
import logging
from sqlalchemy import inspect

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend/macrodb.sqlite"))

def add_column_if_not_exists(cursor, table: str, column: str, col_type: str):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    if column not in cols:
        logger.info(f"Adding column '{column}' ({col_type}) to table '{table}'...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

def migrate():
    if not os.path.exists(DB_PATH):
        logger.info(f"No existing database file found at {DB_PATH}. Base.metadata.create_all will create schema.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Table: macro_series
        add_column_if_not_exists(cursor, "macro_series", "analysis_overview", "TEXT")
        add_column_if_not_exists(cursor, "macro_series", "impact_rising", "TEXT")
        add_column_if_not_exists(cursor, "macro_series", "impact_falling", "TEXT")

        # Table: sectors
        add_column_if_not_exists(cursor, "sectors", "level", "INTEGER DEFAULT 1")
        add_column_if_not_exists(cursor, "sectors", "category", "VARCHAR(100)")

        # Table: sector_features
        add_column_if_not_exists(cursor, "sector_features", "rs_ratio", "FLOAT")
        add_column_if_not_exists(cursor, "sector_features", "rs_momentum", "FLOAT")
        add_column_if_not_exists(cursor, "sector_features", "breadth_sma", "FLOAT")
        add_column_if_not_exists(cursor, "sector_features", "correlation_spy", "FLOAT")

        # Phase 2 Fundamentals
        add_column_if_not_exists(cursor, "sector_features", "eps_growth_yoy", "FLOAT")
        add_column_if_not_exists(cursor, "sector_features", "revenue_growth_yoy", "FLOAT")
        add_column_if_not_exists(cursor, "sector_features", "margin_trend", "FLOAT")
        add_column_if_not_exists(cursor, "sector_features", "quality_flag", "VARCHAR(50)")
        add_column_if_not_exists(cursor, "sector_features", "capex_growth_yoy", "FLOAT")
        add_column_if_not_exists(cursor, "sector_features", "pe_ratio_ttm", "FLOAT")
        add_column_if_not_exists(cursor, "sector_features", "pe_percentile_5y", "FLOAT")

        # Phase 3 Earnings Surprise & Macro Betas
        add_column_if_not_exists(cursor, "sector_features", "eps_surprise_pct", "FLOAT")
        add_column_if_not_exists(cursor, "sector_features", "beta_growth", "FLOAT")
        add_column_if_not_exists(cursor, "sector_features", "beta_inflation", "FLOAT")
        add_column_if_not_exists(cursor, "sector_features", "beta_fca", "FLOAT")

        # Table: sector_scores
        add_column_if_not_exists(cursor, "sector_scores", "breadth_score", "FLOAT")
        add_column_if_not_exists(cursor, "sector_scores", "fundamental_score", "FLOAT")
        add_column_if_not_exists(cursor, "sector_scores", "surprise_score", "FLOAT")
        add_column_if_not_exists(cursor, "sector_scores", "rs_ratio", "FLOAT")
        add_column_if_not_exists(cursor, "sector_scores", "rs_momentum", "FLOAT")
        add_column_if_not_exists(cursor, "sector_scores", "tails", "VARCHAR(2000)")

        conn.commit()
        logger.info("Schema migration completed successfully.")
    except Exception as e:
        logger.error(f"Error migrating schema: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
