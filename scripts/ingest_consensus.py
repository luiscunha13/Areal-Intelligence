"""Ingest market consensus vs actual release data into PostgreSQL macro_consensus table."""
import os
import sys
import datetime
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models import MacroSeries, MacroConsensus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CONSENSUS_SEED_DATA = [
    {
        "fred_series_id": "CPIAUCSL",
        "period": "Jul 2026",
        "release_date": datetime.date(2026, 8, 12),
        "consensus": 2.9,
        "actual": 3.1,
        "previous": 3.0,
        "unit": "%",
    },
    {
        "fred_series_id": "CPILFESL",
        "period": "Jul 2026",
        "release_date": datetime.date(2026, 8, 12),
        "consensus": 3.2,
        "actual": 3.2,
        "previous": 3.3,
        "unit": "%",
    },
    {
        "fred_series_id": "PAYEMS",
        "period": "Jul 2026",
        "release_date": datetime.date(2026, 8, 2),
        "consensus": 175.0,
        "actual": 114.0,
        "previous": 179.0,
        "unit": "k",
    },
    {
        "fred_series_id": "UNRATE",
        "period": "Jul 2026",
        "release_date": datetime.date(2026, 8, 2),
        "consensus": 4.1,
        "actual": 4.3,
        "previous": 4.1,
        "unit": "%",
    },
    {
        "fred_series_id": "RSAFS",
        "period": "Jun 2026",
        "release_date": datetime.date(2026, 7, 16),
        "consensus": 0.3,
        "actual": 0.4,
        "previous": -0.1,
        "unit": "%",
    },
    {
        "fred_series_id": "PCEPILFE",
        "period": "Jun 2026",
        "release_date": datetime.date(2026, 7, 26),
        "consensus": 2.5,
        "actual": 2.6,
        "previous": 2.6,
        "unit": "%",
    },
    {
        "fred_series_id": "GDPC1",
        "period": "Q2 2026",
        "release_date": datetime.date(2026, 7, 25),
        "consensus": 2.8,
        "actual": 3.0,
        "previous": 1.4,
        "unit": "%",
    },
]


def ingest_consensus():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    added = 0
    for item in CONSENSUS_SEED_DATA:
        s = session.query(MacroSeries).filter_by(fred_series_id=item["fred_series_id"]).first()
        if not s:
            continue

        existing = (
            session.query(MacroConsensus)
            .filter_by(series_id=s.id, release_date=item["release_date"])
            .first()
        )

        surprise_delta = round(item["actual"] - item["consensus"], 2)

        if existing:
            existing.period = item["period"]
            existing.consensus_value = item["consensus"]
            existing.actual_value = item["actual"]
            existing.previous_value = item["previous"]
            existing.surprise_delta = surprise_delta
            existing.unit = item["unit"]
        else:
            obj = MacroConsensus(
                series_id=s.id,
                release_date=item["release_date"],
                period=item["period"],
                consensus_value=item["consensus"],
                actual_value=item["actual"],
                previous_value=item["previous"],
                surprise_delta=surprise_delta,
                unit=item["unit"],
            )
            session.add(obj)
            added += 1

    session.commit()
    logger.info("Successfully ingested/updated %d consensus release items!", len(CONSENSUS_SEED_DATA))


if __name__ == "__main__":
    ingest_consensus()
