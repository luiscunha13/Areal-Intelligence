import sys
import os
import json
import urllib.request
import logging
from datetime import datetime
from typing import Dict, Optional

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

# Keyword-based Sector Classification Fallback Engine
KEYWORD_SECTOR_MAP = {
    "XLK": ["TECH", "SEMICONDUCTOR", "SOFTWARE", "COMPUTE", "CHIP", "DIGITAL", "MICRO", "CYBER", "CLOUD", "AI ", "NETWORKS", "DATA", "ROBOTICS"],
    "XLV": ["HEALTH", "PHARMA", "THERAPEUTIC", "BIO", "MEDICAL", "GENOMIC", "CLINICAL", "LAB", "MEDICINE", "SURGICAL", "DRUG"],
    "XLF": ["BANK", "FINANCIAL", "CAPITAL", "INSURANCE", "REINSURANCE", "CREDIT", "TRUST", "INVESTMENT", "ASSET", "BANCORP", "MORTGAGE", "PAYMENT"],
    "XLE": ["ENERGY", "OIL", "GAS", "PETROLEUM", "SOLAR", "CLEAN", "DRILLING", "PIPELINE", "RENEWABLE", "HYDROGEN", "URANIUM", "NUCLEAR", "FUEL", "POWER"],
    "XLB": ["MATERIALS", "MINING", "GOLD", "SILVER", "COPPER", "METALS", "CHEMICAL", "LITHIUM", "RARE EARTH", "STEEL", "ALUMINUM", "RESOURCES"],
    "XLI": ["INDUSTRIALS", "AEROSPACE", "DEFENSE", "ENGINEERING", "SYSTEMS", "AIRLINES", "CARGO", "FREIGHT", "TRANSPORT", "MACHINERY", "SPACE", "LOGISTICS"],
    "XLY": ["RETAIL", "MOTORS", "AUTOMOTIVE", "HOTELS", "ENTERTAINMENT", "APPARAL", "RESTAU", "BRANDS", "CASINO", "CONSUMER"],
    "XLP": ["STAPLES", "BEVERAGE", "FOOD", "PACKAG", "GROCERY", "SUPERMARKET", "DISTRIBUTOR", "TOBACCO", "COCA", "PEPSI"],
    "XLC": ["COMMUNICATION", "MEDIA", "TELECOM", "SATELLITE", "INTERNET", "BROADCAST", "ENTERTAINMENT", "PUBLISHING", "WIRELESS"],
    "XLU": ["UTILITIES", "ELECTRIC", "WATER", "GAS UTILITY", "INFRASTRUCTURE", "POWER & LIGHT", "EDISON"],
    "XLRE": ["REAL ESTATE", "REIT", "PROPERTIES", "REALTY", "HOMES", "EQUITY RESIDENTIAL"],
}

def classify_sector_by_title(title: str) -> str:
    t_upper = title.upper()
    for sector_symbol, keywords in KEYWORD_SECTOR_MAP.items():
        for kw in keywords:
            if kw in t_upper:
                return sector_symbol
    return "XLK"  # Default fallback sector

def fetch_sec_edgar_tickers() -> list:
    """Fetch the full SEC EDGAR official directory of 10,000+ active US public company tickers."""
    url = "https://www.sec.gov/files/company_tickers.json"
    req = urllib.request.Request(
        url, 
        headers={"User-Agent": "MacroAnalysisEngine/1.0 (admin@analysis.com)"}
    )
    try:
        logger.info("Fetching SEC EDGAR master directory (10,000+ active tickers)...")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            logger.info(f"Successfully retrieved {len(data)} companies from SEC EDGAR API.")
            return list(data.values())
    except Exception as e:
        logger.error(f"Failed to fetch SEC EDGAR tickers: {e}")
        return []

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    wiki_provider = WikipediaSP500Provider()

    try:
        logger.info("Initializing Autonomous Universe Ingestion Pipeline...")

        # 1. Fetch S&P 500 & Nasdaq-100 Verified Constituent Mappings
        sp500_items = wiki_provider.fetch_sp500_constituents() or []
        nasdaq100_items = wiki_provider.fetch_nasdaq100_constituents() or []

        verified_map: Dict[str, dict] = {}
        for item in sp500_items + nasdaq100_items:
            tk = item["ticker"].upper().replace('.', '-')
            verified_map[tk] = item

        # 2. Fetch full SEC EDGAR ticker directory (~10,000+ tickers)
        sec_tickers = fetch_sec_edgar_tickers()

        # Build Sector symbol to ID map
        sectors = db.query(Sector).all()
        sector_symbol_map = {s.symbol: s.id for s in sectors}

        today = datetime.utcnow().date()
        added_count = 0
        updated_count = 0

        # Process all SEC EDGAR Tickers
        logger.info("Processing & classifying all public tickers into GICS Sector Engine...")
        
        for sec_item in sec_tickers:
            raw_ticker = sec_item.get("ticker", "").upper()
            title = sec_item.get("title", "")
            if not raw_ticker:
                continue

            ticker = raw_ticker.replace('.', '-')

            # Determine Sector Symbol
            if ticker in verified_map:
                sec_sym = verified_map[ticker].get("sector_symbol", "XLK")
                ind_name = verified_map[ticker].get("industry_name", "General Equities")
                company_name = verified_map[ticker].get("company_name", title)
            else:
                sec_sym = classify_sector_by_title(title)
                ind_name = f"{title.split()[0]} Industry Group" if title else "General Equities"
                company_name = title.title()

            sector_id = sector_symbol_map.get(sec_sym, sector_symbol_map.get("XLK", 2))

            # Industry Lookup/Creation
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

            # Company Lookup/Creation
            company = db.query(Company).filter(Company.ticker == ticker).first()
            if not company:
                company = Company(
                    ticker=ticker,
                    company_name=company_name,
                    exchange="NASDAQ/NYSE",
                    country="US",
                    currency="USD",
                    sector_id=sector_id,
                    industry_id=industry_id,
                    is_active=True,
                    first_seen=today,
                    last_seen=today
                )
                db.add(company)
                db.flush()

                membership = IndexMembership(
                    company_id=company.id,
                    index_name="SEC Active Universe",
                    valid_from=today,
                    valid_to=None,
                    source="SEC EDGAR Official Feed"
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
        total_in_db = db.query(Company).filter(Company.is_active == True).count()
        logger.info(f"Autonomous Universe Sync Complete! Added {added_count} new tickers, updated {updated_count}. Total active equities in database: {total_in_db}")

    except Exception as e:
        logger.error(f"Error in Autonomous Universe Pipeline: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
