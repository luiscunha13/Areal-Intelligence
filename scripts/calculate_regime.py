"""Calculate market regime classification and dynamic explanation drivers for the latest date."""
import os
import sys
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.services.pipeline import compute_scores_for_date

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        res = compute_scores_for_date(session)
        asof = res["asof"]
        regime_info = res["regime"]
        logger.info("Market Regime calculated for date %s: %s (Confidence: %.1f%%)", asof, regime_info["regime"], regime_info["confidence"])
        logger.info("Overall Score: %.1f / 100", regime_info["overall_score"])
        logger.info("Positive Drivers: %s", regime_info["why"]["positive"])
        logger.info("Negative Drivers: %s", regime_info["why"]["negative"])
    finally:
        session.close()


if __name__ == "__main__":
    main()
