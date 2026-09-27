from abc import ABC, abstractmethod
import pandas as pd
import requests
import io
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Sector Mapping (Wikipedia GICS Sector Name -> Phase 2 Sector Symbol & Code)
GICS_SECTOR_MAP = {
    "Information Technology": ("XLK", "technology"),
    "Health Care": ("XLV", "healthcare"),
    "Financials": ("XLF", "financials"),
    "Consumer Discretionary": ("XLY", "consumer_discretionary"),
    "Communication Services": ("XLC", "communication_services"),
    "Industrials": ("XLI", "industrials"),
    "Consumer Staples": ("XLP", "consumer_staples"),
    "Energy": ("XLE", "energy"),
    "Utilities": ("XLU", "utilities"),
    "Real Estate": ("XLRE", "real_estate"),
    "Materials": ("XLB", "materials"),
}

class CompanyDataProvider(ABC):
    @abstractmethod
    def fetch_sp500_constituents(self) -> List[Dict[str, Any]]:
        """Fetch list of S&P 500 constituent companies with tickers, sectors, and industries."""
        pass

class WikipediaSP500Provider(CompanyDataProvider):
    def fetch_sp500_constituents(self) -> List[Dict[str, Any]]:
        logger.info("Fetching S&P 500 constituents table from Wikipedia...")
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ArealIntelligence/1.0"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()

            tables = pd.read_html(io.StringIO(resp.text))
            df = tables[0]

            # Normalize column names
            df.columns = [str(c).lower().replace(" ", "_").replace("-", "_") for c in df.columns]
            logger.info(f"Scraped table columns: {list(df.columns)}")

            ticker_col = next((c for c in df.columns if "symbol" in c or "ticker" in c), "symbol")
            name_col = next((c for c in df.columns if "security" in c or "company" in c), "security")
            sector_col = next((c for c in df.columns if "sector" in c), "gics_sector")
            industry_col = next((c for c in df.columns if "sub" in c or "industry" in c), "gics_sub_industry")

            constituents = []
            for _, row in df.iterrows():
                ticker = str(row[ticker_col]).replace(".", "-").strip().upper()
                company_name = str(row[name_col]).strip()
                sector_name = str(row[sector_col]).strip()
                industry_name = str(row[industry_col]).strip()

                sector_info = GICS_SECTOR_MAP.get(sector_name, (None, None))

                constituents.append({
                    "ticker": ticker,
                    "company_name": company_name,
                    "sector_name": sector_name,
                    "sector_symbol": sector_info[0],
                    "industry_name": industry_name,
                    "exchange": "NASDAQ/NYSE",
                    "country": "US",
                    "currency": "USD",
                })

            logger.info(f"Successfully scraped {len(constituents)} S&P 500 constituents.")
            return constituents
        except Exception as e:
            logger.error(f"Error fetching S&P 500 constituents from Wikipedia: {e}")
            raise e

    def fetch_nasdaq100_constituents(self) -> List[Dict[str, Any]]:
        logger.info("Fetching Nasdaq-100 constituents table from Wikipedia...")
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ArealIntelligence/1.0"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()

            tables = pd.read_html(io.StringIO(resp.text))
            df = None
            for t in tables:
                cols = [str(c).lower() for c in t.columns]
                if any("ticker" in c or "symbol" in c for c in cols):
                    df = t
                    break

            if df is None:
                return []

            df.columns = [str(c).lower().replace(" ", "_").replace("-", "_") for c in df.columns]
            ticker_col = next((c for c in df.columns if "ticker" in c or "symbol" in c), df.columns[1])
            name_col = next((c for c in df.columns if "company" in c or "name" in c), df.columns[0])
            sector_col = next((c for c in df.columns if "sector" in c), None)

            constituents = []
            for _, row in df.iterrows():
                ticker = str(row[ticker_col]).replace(".", "-").strip().upper()
                if not ticker or len(ticker) > 6 or ticker == "TICKER":
                    continue
                company_name = str(row[name_col]).strip()
                sector_name = str(row[sector_col]).strip() if sector_col else "Information Technology"
                sector_info = GICS_SECTOR_MAP.get(sector_name, ("XLK", "technology"))

                constituents.append({
                    "ticker": ticker,
                    "company_name": company_name,
                    "sector_name": sector_name,
                    "sector_symbol": sector_info[0] or "XLK",
                    "industry_name": sector_name,
                    "exchange": "NASDAQ",
                    "country": "US",
                    "currency": "USD",
                })

            logger.info(f"Successfully scraped {len(constituents)} Nasdaq-100 constituents.")
            return constituents
        except Exception as e:
            logger.error(f"Error fetching Nasdaq-100 constituents: {e}")
            return []
