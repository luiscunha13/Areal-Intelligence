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

# Curated list of major growth & global tech/healthcare/consumer leaders beyond standard S&P 500
ADDITIONAL_POPULAR_EQUITIES = [
    # AI & Cloud Compute Infrastructure
    {"ticker": "PLTR", "company_name": "Palantir Technologies Inc.", "sector_symbol": "XLK", "industry_name": "Software - Infrastructure", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "NBIS", "company_name": "Nebius Group N.V.", "sector_symbol": "XLK", "industry_name": "Software - Infrastructure", "exchange": "NASDAQ", "country": "NL", "currency": "USD"},
    {"ticker": "APLD", "company_name": "Applied Digital Corporation", "sector_symbol": "XLK", "industry_name": "Software - Infrastructure", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "SMCI", "company_name": "Super Micro Computer Inc.", "sector_symbol": "XLK", "industry_name": "Computer Hardware", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "ARM", "company_name": "Arm Holdings plc", "sector_symbol": "XLK", "industry_name": "Semiconductors", "exchange": "NASDAQ", "country": "UK", "currency": "USD"},
    {"ticker": "TSM", "company_name": "Taiwan Semiconductor Manufacturing Co.", "sector_symbol": "XLK", "industry_name": "Semiconductors", "exchange": "NYSE", "country": "TW", "currency": "USD"},
    {"ticker": "ASML", "company_name": "ASML Holding N.V.", "sector_symbol": "XLK", "industry_name": "Semiconductors", "exchange": "NASDAQ", "country": "NL", "currency": "USD"},
    {"ticker": "CLS", "company_name": "Celestica Inc.", "sector_symbol": "XLK", "industry_name": "Computer Hardware", "exchange": "NYSE", "country": "CA", "currency": "USD"},
    {"ticker": "APP", "company_name": "AppLovin Corporation", "sector_symbol": "XLK", "industry_name": "Software - Application", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    
    # Clean Energy, Fuel Cells & Nuclear SMR Power
    {"ticker": "BE", "company_name": "Bloom Energy Corporation", "sector_symbol": "XLE", "industry_name": "Electrical Equipment & Clean Energy", "exchange": "NYSE", "country": "US", "currency": "USD"},
    {"ticker": "OKLO", "company_name": "Oklo Inc.", "sector_symbol": "XLE", "industry_name": "Independent Power & Nuclear", "exchange": "NYSE", "country": "US", "currency": "USD"},
    {"ticker": "SMR", "company_name": "NuScale Power Corporation", "sector_symbol": "XLE", "industry_name": "Independent Power & Nuclear", "exchange": "NYSE", "country": "US", "currency": "USD"},
    {"ticker": "CCJ", "company_name": "Cameco Corporation", "sector_symbol": "XLE", "industry_name": "Uranium & Nuclear Fuel", "exchange": "NYSE", "country": "CA", "currency": "USD"},
    {"ticker": "CEG", "company_name": "Constellation Energy Corp", "sector_symbol": "XLU", "industry_name": "Utilities - Renewable & Nuclear", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "VST", "company_name": "Vistra Corp.", "sector_symbol": "XLU", "industry_name": "Utilities - Independent Power", "exchange": "NYSE", "country": "US", "currency": "USD"},
    {"ticker": "GEV", "company_name": "GE Vernova Inc.", "sector_symbol": "XLI", "industry_name": "Electrical Equipment", "exchange": "NYSE", "country": "US", "currency": "USD"},
    {"ticker": "PLUG", "company_name": "Plug Power Inc.", "sector_symbol": "XLE", "industry_name": "Electrical Equipment & Hydrogen", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "ENPH", "company_name": "Enphase Energy Inc.", "sector_symbol": "XLE", "industry_name": "Solar & Storage", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "FSLR", "company_name": "First Solar Inc.", "sector_symbol": "XLE", "industry_name": "Solar & Storage", "exchange": "NASDAQ", "country": "US", "currency": "USD"},

    # Critical Minerals, Rare Earths & Metals
    {"ticker": "MP", "company_name": "MP Materials Corp.", "sector_symbol": "XLB", "industry_name": "Other Industrial Metals & Mining", "exchange": "NYSE", "country": "US", "currency": "USD"},
    {"ticker": "UUUU", "company_name": "Energy Fuels Inc.", "sector_symbol": "XLB", "industry_name": "Uranium & Critical Minerals", "exchange": "NYSE", "country": "US", "currency": "USD"},
    {"ticker": "USAR", "company_name": "USA Rare Earth Inc.", "sector_symbol": "XLB", "industry_name": "Critical Minerals & Metals", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "LAC", "company_name": "Lithium Americas Corp.", "sector_symbol": "XLB", "industry_name": "Lithium & Specialty Chemicals", "exchange": "NYSE", "country": "CA", "currency": "USD"},
    {"ticker": "ALB", "company_name": "Albemarle Corporation", "sector_symbol": "XLB", "industry_name": "Specialty Chemicals", "exchange": "NYSE", "country": "US", "currency": "USD"},

    # Space Tech, Robotics & Next-Gen Telecom
    {"ticker": "ASTS", "company_name": "AST SpaceMobile Inc.", "sector_symbol": "XLC", "industry_name": "Telecom Services & Satellites", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "RKLB", "company_name": "Rocket Lab USA Inc.", "sector_symbol": "XLI", "industry_name": "Aerospace & Defense", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "JOBY", "company_name": "Joby Aviation Inc.", "sector_symbol": "XLI", "industry_name": "Aerospace & Defense", "exchange": "NYSE", "country": "US", "currency": "USD"},
    {"ticker": "ACHR", "company_name": "Archer Aviation Inc.", "sector_symbol": "XLI", "industry_name": "Aerospace & Defense", "exchange": "NYSE", "country": "NYSE", "currency": "USD"},

    # Quantum & Next-Gen AI
    {"ticker": "IONQ", "company_name": "IonQ Inc.", "sector_symbol": "XLK", "industry_name": "Computer Hardware & Quantum", "exchange": "NYSE", "country": "US", "currency": "USD"},
    {"ticker": "SOUN", "company_name": "SoundHound AI Inc.", "sector_symbol": "XLK", "industry_name": "Software - Application", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "SERV", "company_name": "Serve Robotics Inc.", "sector_symbol": "XLK", "industry_name": "Robotics & Automation", "exchange": "NASDAQ", "country": "US", "currency": "USD"},

    # Digital Financials & Fintech
    {"ticker": "HOOD", "company_name": "Robinhood Markets Inc.", "sector_symbol": "XLF", "industry_name": "Financial Data & Stock Exchanges", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "MSTR", "company_name": "MicroStrategy Incorporated", "sector_symbol": "XLK", "industry_name": "Software - Application", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "COIN", "company_name": "Coinbase Global Inc.", "sector_symbol": "XLF", "industry_name": "Financial Data & Stock Exchanges", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "SQ", "company_name": "Block Inc.", "sector_symbol": "XLF", "industry_name": "Financial Data & Stock Exchanges", "exchange": "NYSE", "country": "US", "currency": "USD"},
    {"ticker": "NET", "company_name": "Cloudflare Inc.", "sector_symbol": "XLK", "industry_name": "Software - Infrastructure", "exchange": "NYSE", "country": "US", "currency": "USD"},
    {"ticker": "SNOW", "company_name": "Snowflake Inc.", "sector_symbol": "XLK", "industry_name": "Software - Application", "exchange": "NYSE", "country": "US", "currency": "USD"},
    {"ticker": "DDOG", "company_name": "Datadog Inc.", "sector_symbol": "XLK", "industry_name": "Software - Application", "exchange": "NASDAQ", "country": "US", "currency": "USD"},
    {"ticker": "NVO", "company_name": "Novo Nordisk A/S", "sector_symbol": "XLV", "industry_name": "Pharmaceuticals", "exchange": "NYSE", "country": "DK", "currency": "USD"},
    {"ticker": "SHOP", "company_name": "Shopify Inc.", "sector_symbol": "XLK", "industry_name": "Software - Application", "exchange": "NYSE", "country": "CA", "currency": "USD"},
    {"ticker": "SPOT", "company_name": "Spotify Technology S.A.", "sector_symbol": "XLC", "industry_name": "Internet Content & Information", "exchange": "NYSE", "country": "SE", "currency": "USD"},
    {"ticker": "RBLX", "company_name": "Roblox Corporation", "sector_symbol": "XLC", "industry_name": "Electronic Gaming & Multimedia", "exchange": "NYSE", "country": "US", "currency": "USD"},
]

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    provider = WikipediaSP500Provider()

    try:
        logger.info("Syncing expanded equities universe (S&P 500, Nasdaq 100 & Major Global Growth)...")
        sp500 = provider.fetch_sp500_constituents() or []
        nasdaq100 = provider.fetch_nasdaq100_constituents() or []

        # Merge all constituent lists removing duplicates
        all_constituents_map = {}
        for item in sp500 + nasdaq100 + ADDITIONAL_POPULAR_EQUITIES:
            tk = item["ticker"].upper()
            if tk not in all_constituents_map:
                all_constituents_map[tk] = item

        constituents = list(all_constituents_map.values())
        logger.info(f"Total unique expanded equities to sync: {len(constituents)}")

        # Build Sector map
        sectors = db.query(Sector).all()
        sector_symbol_map = {s.symbol: s.id for s in sectors}

        today = datetime.utcnow().date()
        added_count = 0
        updated_count = 0

        for item in constituents:
            ticker = item["ticker"]
            sector_sym = item.get("sector_symbol", "XLK")
            sector_id = sector_symbol_map.get(sector_sym, 1)

            # Industry sync
            ind_name = item.get("industry_name", "General Equities")
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
                    exchange=item.get("exchange", "NASDAQ/NYSE"),
                    country=item.get("country", "US"),
                    currency=item.get("currency", "USD"),
                    sector_id=sector_id,
                    industry_id=industry_id,
                    is_active=True,
                    first_seen=today,
                    last_seen=today
                )
                db.add(company)
                db.flush()

                # Add membership record
                membership = IndexMembership(
                    company_id=company.id,
                    index_name="Expanded Universe",
                    valid_from=today,
                    valid_to=None,
                    source="Expanded Equities Provider"
                )
                db.add(membership)
                added_count += 1
            else:
                company.sector_id = sector_id
                company.industry_id = industry_id
                company.is_active = True
                company.last_seen = today
                updated_count += 1

        db.commit()
        logger.info(f"Successfully synced expanded universe: {added_count} new companies added, {updated_count} updated. Total active: {len(constituents)} companies.")

    except Exception as e:
        logger.error(f"Error syncing expanded universe: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
