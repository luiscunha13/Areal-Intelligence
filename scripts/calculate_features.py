"""Compute macro features, scores, and historical trajectory for latest and historical dates."""
import os
import sys
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.services.pipeline import compute_scores_for_date
from backend.app.models import MarketRegime
from scripts.backfill_macro_history import backfill_history

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        regime_count = session.query(MarketRegime).count()
        if regime_count < 10:
            logger.info("Fewer than 10 regime history points found. Triggering monthly historical backfill...")
            backfill_history()

        res = compute_scores_for_date(session)
        logger.info("Features and scores computed for latest date: %s", res["asof"])
        logger.info("Scores: %s", res["scores"])
    finally:
        session.close()


if __name__ == "__main__":
    main()
