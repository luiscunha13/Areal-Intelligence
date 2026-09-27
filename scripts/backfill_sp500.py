"""Backfill S&P 500 (SP500) historical daily data pre-2016 using Yahoo Finance (^GSPC)."""
import os
import sys
import datetime
import logging
import yfinance as yf

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.app.core.database import SessionLocal
from backend.app.models import MacroSeries, MacroObservation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def backfill_sp500():
    session = SessionLocal()
    sp500_series = session.query(MacroSeries).filter_by(fred_series_id="SP500").first()
    
    if not sp500_series:
        logger.error("SP500 series not found in database catalog!")
        return

    logger.info("Downloading historical S&P 500 (^GSPC) data from 1927 to 2016...")
    df = yf.download("^GSPC", start="1927-01-01", end="2016-08-15", progress=False)

    if df.empty:
        logger.error("No historical S&P 500 data fetched.")
        return

    # Get existing observation dates
    existing_dates = set(
        row[0] for row in session.query(MacroObservation.observation_date)
        .filter(MacroObservation.series_id == sp500_series.id)
        .all()
    )

    new_objs = []
    # yfinance MultiIndex check
    closes = df["Close"]
    if hasattr(closes, "^GSPC"):
        closes = closes["^GSPC"]

    for idx, row in df.iterrows():
        obs_date = idx.date()
        if obs_date in existing_dates:
            continue

        val = row["Close"]
        if hasattr(val, "item"):
            val = val.item()
        
        if val is None or str(val) == "nan":
            continue

        new_objs.append(
            MacroObservation(
                series_id=sp500_series.id,
                observation_date=obs_date,
                vintage_date=obs_date,
                value=round(float(val), 2),
            )
        )
        existing_dates.add(obs_date)

    if new_objs:
        session.bulk_save_objects(new_objs)
        session.commit()
        logger.info("Successfully backfilled %d historical observations for SP500 (1927-2016)!", len(new_objs))
    else:
        logger.info("SP500 is already fully backfilled.")


if __name__ == "__main__":
    backfill_sp500()
