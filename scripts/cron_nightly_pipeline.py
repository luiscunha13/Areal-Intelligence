import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.ingest_stock_data import main as run_ingest
from scripts.sync_bulk_prices import batch_download_prices
from scripts.ingest_sector_prices import main as run_sector_ingest
from scripts.calculate_sector_features import main as run_sector_scoring
from scripts.run_cross_sectional_scoring import main as run_scoring
from scripts.refresh_materialized_snapshots import main as refresh_snapshots

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_nightly_pipeline():
    logger.info(f"=== STARTING NIGHTLY STOCK & SECTOR INTELLIGENCE PIPELINE ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")

    # Step 1: Ingest latest prices & SEC fundamentals for core universe
    try:
        logger.info("Step 1/4: Running daily stock price & sector ETF price ingestion...")
        batch_download_prices(batch_size=200, limit=2000)
        run_sector_ingest()
        sys.argv = ["ingest_stock_data.py", "--sp500-only"]
        run_ingest()
        logger.info("Step 1/4: Market price & fundamental ingestion complete.")
    except Exception as e:
        logger.error(f"Step 1/4 Warning: Market ingestion encountered non-fatal error: {e}")

    # Step 2: Compute Sector RRG Features & Relative Strength
    try:
        logger.info("Step 2/4: Computing Sector & Industry RRG features and macro sensitivities...")
        run_sector_scoring()
        logger.info("Step 2/4: Sector RRG calculation complete.")
    except Exception as e:
        logger.error(f"Step 2/4 Warning: Sector RRG scoring failed: {e}")

    # Step 3: Compute Methodology v2.0-PIT Cross-Sectional Z-Scores
    try:
        logger.info("Step 3/4: Executing Methodology v2.0-PIT Cross-Sectional Z-Score Scoring engine...")
        run_scoring()
        logger.info("Step 3/4: Cross-sectional Z-Score calculation complete.")
    except Exception as e:
        logger.error(f"Step 3/4 Error: Z-Score engine failed: {e}")
        raise e

    # Step 4: Refresh Materialized Screener Snapshots
    try:
        logger.info("Step 4/4: Refreshing Materialized Company Snapshots in Docker Postgres...")
        refresh_snapshots()
        logger.info("Step 4/4: Materialized snapshots refresh complete.")
    except Exception as e:
        logger.error(f"Step 4/4 Error: Materialized snapshot refresh failed: {e}")
        raise e

    logger.info("=== NIGHTLY STOCK INTELLIGENCE PIPELINE EXECUTED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_nightly_pipeline()
