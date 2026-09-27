"""Backfill historical macro features and regime classifications at monthly intervals."""
import os
import sys
import datetime
import logging
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.services.pipeline import compute_scores_for_date

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def backfill_history():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        # Generate monthly dates from 2018-01-01 to current date
        start_date = datetime.date(2018, 1, 1)
        end_date = datetime.date(2026, 8, 1)
        
        # Monthly frequency
        date_range = pd.date_range(start=start_date, end=end_date, freq='MS')
        monthly_dates = [d.date() for d in date_range]
        
        logger.info("Starting macro history backfill for %d monthly dates...", len(monthly_dates))

        count = 0
        for dt in monthly_dates:
            try:
                res = compute_scores_for_date(session, asof=dt)
                count += 1
                if count % 10 == 0 or count == len(monthly_dates):
                    logger.info("Backfilled %d/%d dates (Latest: %s -> %s)", count, len(monthly_dates), dt, res["regime"]["regime"])
            except Exception as e:
                logger.warning("Error backfilling date %s: %s", dt, str(e))

        logger.info("Successfully completed macro historical backfill for %d dates!", count)

    finally:
        session.close()


if __name__ == "__main__":
    backfill_history()
