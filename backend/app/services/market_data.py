from abc import ABC, abstractmethod
import pandas as pd
import yfinance as yf
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

UNIVERSE_CATALOG = [
    # Benchmark
    {"symbol": "SPY", "name": "S&P 500 Benchmark", "gics_code": "benchmark", "level": 0, "category": "Benchmark"},
    
    # Level 1 — GICS Sectors (11)
    {"symbol": "XLK", "name": "Information Technology", "gics_code": "technology", "level": 1, "category": "Technology"},
    {"symbol": "XLV", "name": "Health Care", "gics_code": "healthcare", "level": 1, "category": "Health Care"},
    {"symbol": "XLF", "name": "Financials", "gics_code": "financials", "level": 1, "category": "Financials"},
    {"symbol": "XLY", "name": "Consumer Discretionary", "gics_code": "consumer_discretionary", "level": 1, "category": "Consumer Discretionary"},
    {"symbol": "XLC", "name": "Communication Services", "gics_code": "communication_services", "level": 1, "category": "Communication Services"},
    {"symbol": "XLI", "name": "Industrials", "gics_code": "industrials", "level": 1, "category": "Industrials"},
    {"symbol": "XLP", "name": "Consumer Staples", "gics_code": "consumer_staples", "level": 1, "category": "Consumer Staples"},
    {"symbol": "XLE", "name": "Energy", "gics_code": "energy", "level": 1, "category": "Energy"},
    {"symbol": "XLU", "name": "Utilities", "gics_code": "utilities", "level": 1, "category": "Utilities"},
    {"symbol": "XLRE", "name": "Real Estate", "gics_code": "real_estate", "level": 1, "category": "Real Estate"},
    {"symbol": "XLB", "name": "Materials", "gics_code": "materials", "level": 1, "category": "Materials"},

    # Level 2 — Industry Groups (16)
    {"symbol": "SMH", "name": "Semiconductors", "gics_code": "semiconductors", "level": 2, "category": "Technology"},
    {"symbol": "IGV", "name": "Software & Services", "gics_code": "software", "level": 2, "category": "Technology"},
    {"symbol": "XBI", "name": "Biotechnology", "gics_code": "biotech", "level": 2, "category": "Health Care"},
    {"symbol": "PPH", "name": "Pharmaceuticals", "gics_code": "pharma", "level": 2, "category": "Health Care"},
    {"symbol": "IHI", "name": "Health Care Equipment", "gics_code": "healthcare_equip", "level": 2, "category": "Health Care"},
    {"symbol": "KBE", "name": "Banks", "gics_code": "banks", "level": 2, "category": "Financials"},
    {"symbol": "KRE", "name": "Regional Banks", "gics_code": "regional_banks", "level": 2, "category": "Financials"},
    {"symbol": "KIE", "name": "Insurance", "gics_code": "insurance", "level": 2, "category": "Financials"},
    {"symbol": "KCE", "name": "Capital Markets", "gics_code": "capital_markets", "level": 2, "category": "Financials"},
    {"symbol": "XHB", "name": "Homebuilders", "gics_code": "homebuilders", "level": 2, "category": "Consumer Discretionary"},
    {"symbol": "ITA", "name": "Aerospace & Defense", "gics_code": "aerospace_defense", "level": 2, "category": "Industrials"},
    {"symbol": "IYT", "name": "Transportation", "gics_code": "transportation", "level": 2, "category": "Industrials"},
    {"symbol": "XRT", "name": "Retail", "gics_code": "retail", "level": 2, "category": "Consumer Discretionary"},
    {"symbol": "XOP", "name": "Oil & Gas E&P", "gics_code": "oil_gas_ep", "level": 2, "category": "Energy"},
    {"symbol": "OIH", "name": "Oilfield Services", "gics_code": "oil_services", "level": 2, "category": "Energy"},
    {"symbol": "XME", "name": "Metals & Mining", "gics_code": "metals_mining", "level": 2, "category": "Materials"},
]

SECTOR_ETFS: Dict[str, str] = {item["gics_code"]: item["symbol"] for item in UNIVERSE_CATALOG}
SECTOR_NAMES: Dict[str, str] = {item["symbol"]: item["name"] for item in UNIVERSE_CATALOG}

class MarketDataProvider(ABC):
    @abstractmethod
    def fetch_historical_prices(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """Fetch daily OHLCV prices for a ticker symbol."""
        pass

class YahooFinanceProvider(MarketDataProvider):
    def fetch_historical_prices(self, symbol: str, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        logger.info(f"Fetching market data for {symbol} from {start_date} to {end_date or 'today'} via yfinance...")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            if df.empty:
                logger.warning(f"No data returned for symbol {symbol}")
                return pd.DataFrame()

            df = df.reset_index()
            # Normalize column names
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]

            # Map columns
            df["date"] = pd.to_datetime(df["date"]).dt.date
            if "adj_close" in df.columns:
                df["adjusted_close"] = df["adj_close"]
            elif "close" in df.columns:
                df["adjusted_close"] = df["close"]

            return df[["date", "open", "high", "low", "close", "adjusted_close", "volume"]]
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} via YahooFinanceProvider: {e}")
            raise e
