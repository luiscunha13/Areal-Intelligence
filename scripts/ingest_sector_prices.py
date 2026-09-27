import sys
import os
import logging
from datetime import datetime, date
import pandas as pd
import requests

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine, SessionLocal, Base
from backend.app.models.sector import Sector
from backend.app.models.sector_price import SectorPrice
from backend.app.services.market_data import UNIVERSE_CATALOG

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_chart_data(symbol: str) -> pd.DataFrame:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5y&interval=1d"
    res = requests.get(url, headers=HEADERS, timeout=10)
    if res.status_code != 200:
        logger.error(f"Failed to fetch chart for {symbol}: HTTP {res.status_code}")
        return pd.DataFrame()

    data = res.json()
    result = data.get("chart", {}).get("result", [])
    if not result:
        return pd.DataFrame()

    timestamps = result[0].get("timestamp", [])
    quote = result[0].get("indicators", {}).get("quote", [{}])[0]

    if not timestamps or not quote:
        return pd.DataFrame()

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": quote.get("open", []),
        "high": quote.get("high", []),
        "low": quote.get("low", []),
        "close": quote.get("close", []),
        "volume": quote.get("volume", []),
    })

    df["date"] = pd.to_datetime(df["timestamp"], unit="s").dt.date
    df = df.dropna(subset=["close"])
    df["adjusted_close"] = df["close"]
    return df

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        logger.info("Initializing Level 1 & Level 2 Sector catalog...")
        sector_map = {}
        for item in UNIVERSE_CATALOG:
            symbol = item["symbol"]
            name = item["name"]
            gics_code = item["gics_code"]
            level = item["level"]
            category = item["category"]

            sector_obj = db.query(Sector).filter(Sector.symbol == symbol).first()
            if not sector_obj:
                sector_obj = Sector(
                    symbol=symbol,
                    name=name,
                    gics_code=gics_code,
                    level=level,
                    category=category,
                    description=f"{name} ETF proxy ({symbol})",
                    benchmark="SPY" if symbol != "SPY" else "SPY"
                )
                db.add(sector_obj)
                db.flush()
            else:
                sector_obj.level = level
                sector_obj.category = category
                sector_obj.name = name

            sector_map[symbol] = sector_obj.id

        db.commit()
        logger.info(f"Sector catalog initialized with {len(sector_map)} symbols across Level 1 & Level 2.")

        total_records = 0
        for symbol, sector_id in sector_map.items():
            logger.info(f"Ingesting 5-year daily price series for {symbol}...")
            df = fetch_chart_data(symbol)
            if df.empty:
                continue

            records = []
            for _, row in df.iterrows():
                existing = db.query(SectorPrice).filter(
                    SectorPrice.sector_id == sector_id,
                    SectorPrice.date == row["date"]
                ).first()

                if not existing:
                    records.append(
                        SectorPrice(
                            sector_id=sector_id,
                            date=row["date"],
                            open=float(row["open"]) if pd.notnull(row["open"]) else float(row["close"]),
                            high=float(row["high"]) if pd.notnull(row["high"]) else float(row["close"]),
                            low=float(row["low"]) if pd.notnull(row["low"]) else float(row["close"]),
                            close=float(row["close"]),
                            adjusted_close=float(row["adjusted_close"]),
                            volume=float(row["volume"]) if pd.notnull(row["volume"]) else 0.0,
                        )
                    )

            if records:
                db.bulk_save_objects(records)
                db.commit()
                logger.info(f"Saved {len(records)} new price records for {symbol}.")
                total_records += len(records)
            else:
                logger.info(f"{symbol} prices already up to date.")

        logger.info(f"Sector price ingestion complete! Total new records: {total_records}")

    except Exception as e:
        logger.error(f"Error during sector ingestion: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
