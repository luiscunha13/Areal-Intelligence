import sys
import os
import logging
from datetime import datetime

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine, SessionLocal, Base
from backend.app.models.sector import Sector
from backend.app.models.industry import Industry
from backend.app.models.company import Company
from backend.app.models.index_membership import IndexMembership
from backend.app.providers.company_data import WikipediaSP500Provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    provider = WikipediaSP500Provider()

    try:
        constituents = provider.fetch_sp500_constituents()
        if not constituents:
            logger.error("No constituents fetched.")
            return

        # Build Sector map
        sectors = db.query(Sector).all()
        sector_symbol_map = {s.symbol: s.id for s in sectors}

        logger.info("Processing S&P 500 industries and companies...")
        today = datetime.utcnow().date()

        for item in constituents:
            ticker = item["ticker"]
            sector_sym = item["sector_symbol"]
            sector_id = sector_symbol_map.get(sector_sym)

            # Industry sync
            ind_name = item["industry_name"]
            industry = db.query(Industry).filter(Industry.name == ind_name).first()
            if not industry and sector_id:
                industry = Industry(
                    sector_id=sector_id,
                    name=ind_name,
                    description=f"{ind_name} Sub-Industry"
                )
                db.add(industry)
                db.flush()

            industry_id = industry.id if industry else None

            # Company sync
            company = db.query(Company).filter(Company.ticker == ticker).first()
            if not company:
                company = Company(
                    ticker=ticker,
                    company_name=item["company_name"],
                    exchange=item["exchange"],
                    country=item["country"],
                    currency=item["currency"],
                    sector_id=sector_id,
                    industry_id=industry_id,
                    is_active=True,
                    first_seen=today,
                    last_seen=today
                )
                db.add(company)
                db.flush()

                # Add S&P 500 membership record
                membership = IndexMembership(
                    company_id=company.id,
                    index_name="S&P 500",
                    valid_from=today,
                    valid_to=None,
                    source="Wikipedia S&P 500"
                )
                db.add(membership)
            else:
                # Update company details
                company.sector_id = sector_id
                company.industry_id = industry_id
                company.is_active = True
                company.last_seen = today

        db.commit()
        logger.info(f"Successfully synced S&P 500 universe with {len(constituents)} companies!")

    except Exception as e:
        logger.error(f"Error syncing S&P 500 universe: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
