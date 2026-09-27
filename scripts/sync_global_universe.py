import sys
import os
import requests
import logging
from datetime import datetime

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine, SessionLocal, Base
from backend.app.models.sector import Sector
from backend.app.models.industry import Industry
from backend.app.models.company import Company
from backend.app.models.index_membership import IndexMembership

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def is_primary_equity(ticker: str) -> bool:
    """Filter out warrants, preferred stock, units, and debt instruments."""
    if not ticker or len(ticker) > 5:
        return False
    if any(ch in ticker for ch in ['-', '.', '+', '=', '^', '/', '$', '%']):
        return False
    return ticker.isalpha()

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    today = datetime.utcnow().date()

    try:
        logger.info("Fetching SEC official public company registry (US & Global ADRs)...")
        headers = {"User-Agent": "AnalysisApp admin@analysis.com"}
        resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers, timeout=20)
        resp.raise_for_status()

        raw_data = resp.json()
        logger.info(f"Retrieved {len(raw_data)} raw SEC registered entries.")

        # Default sector ID (1 = Technology / General)
        default_sector = db.query(Sector).first()
        default_sector_id = default_sector.id if default_sector else 1

        added_count = 0
        updated_count = 0
        skipped_count = 0

        # Batch insert for high performance
        existing_companies = {c.ticker: c for c in db.query(Company).all()}

        for idx_key, item in raw_data.items():
            raw_ticker = str(item.get("ticker", "")).strip().upper()
            title = str(item.get("title", "")).strip()

            if not is_primary_equity(raw_ticker):
                skipped_count += 1
                continue

            if raw_ticker in existing_companies:
                comp = existing_companies[raw_ticker]
                comp.is_active = True
                comp.last_seen = today
                if title and not comp.company_name:
                    comp.company_name = title
                updated_count += 1
            else:
                new_comp = Company(
                    ticker=raw_ticker,
                    company_name=title or raw_ticker,
                    exchange="NASDAQ/NYSE",
                    country="US/GLOBAL",
                    currency="USD",
                    sector_id=default_sector_id,
                    is_active=True,
                    first_seen=today,
                    last_seen=today
                )
                db.add(new_comp)
                existing_companies[raw_ticker] = new_comp
                added_count += 1

            if (added_count + updated_count) % 500 == 0:
                db.commit()

        db.commit()
        total_active = db.query(Company).filter(Company.is_active == True).count()
        logger.info(f"Successfully synced global universe: {added_count} new equities added, {updated_count} updated, {skipped_count} non-equity items skipped.")
        logger.info(f"Total active companies in PostgreSQL database: {total_active}")

    except Exception as e:
        logger.error(f"Error syncing global universe: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
