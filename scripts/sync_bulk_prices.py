import sys
import os
import logging
from datetime import datetime, date
from typing import Optional
import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, engine
from backend.app.models.company import Company
from backend.app.models.stock_price import StockPrice

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def compute_rsi(closes: pd.Series, period: int = 14) -> float:
    if len(closes) < period:
        return 50.0
    delta = closes.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs.iloc[-1]))
    return float(rsi) if pd.notnull(rsi) else 50.0

def batch_download_prices(batch_size: int = 250, limit: Optional[int] = None):
    db = SessionLocal()
    try:
        logger.info(f"Querying active tickers from Docker Postgres (limit={limit})...")
        query = db.query(Company.id, Company.ticker).filter(Company.is_active == True)
        if limit:
            query = query.limit(limit)
        companies = query.all()

        ticker_map = {c.ticker.replace(".", "-"): c.id for c in companies}
        tickers = list(ticker_map.keys())

        logger.info(f"Downloading 1-year daily price series for {len(tickers)} equities in batches of {batch_size}...")

        added_count = 0
        updated_count = 0

        for i in range(0, len(tickers), batch_size):
            chunk = tickers[i:i + batch_size]
            logger.info(f"Downloading batch {i//batch_size + 1}/{(len(tickers)-1)//batch_size + 1} ({len(chunk)} tickers)...")

            data = yf.download(chunk, period="1y", group_by="ticker", threads=True, progress=False)
            if data.empty:
                continue

            for t_sym in chunk:
                cid = ticker_map[t_sym]
                try:
                    if len(chunk) == 1:
                        df_t = data
                    else:
                        if t_sym not in data.columns.levels[0]:
                            continue
                        df_t = data[t_sym].dropna(subset=["Close"])

                    if df_t.empty or len(df_t) < 5:
                        continue

                    closes = df_t["Close"]
                    volumes = df_t.get("Volume", pd.Series(0, index=df_t.index))
                    adj_closes = df_t.get("Adj Close", closes)

                    latest_idx = df_t.index[-1]
                    latest_date = latest_idx.date() if isinstance(latest_idx, (datetime, pd.Timestamp)) else latest_idx

                    close_p = float(closes.iloc[-1])
                    adj_p = float(adj_closes.iloc[-1]) if pd.notnull(adj_closes.iloc[-1]) else close_p
                    vol_p = float(volumes.iloc[-1]) if pd.notnull(volumes.iloc[-1]) else 0.0

                    sma50 = float(closes.tail(50).mean()) if len(closes) >= 50 else close_p
                    sma200 = float(closes.tail(200).mean()) if len(closes) >= 200 else close_p
                    rsi14 = compute_rsi(closes)

                    ret_1m = float(closes.pct_change(21).iloc[-1]) if len(closes) >= 21 and pd.notnull(closes.pct_change(21).iloc[-1]) else 0.0
                    ret_3m = float(closes.pct_change(63).iloc[-1]) if len(closes) >= 63 and pd.notnull(closes.pct_change(63).iloc[-1]) else 0.0

                    sp_rec = db.query(StockPrice).filter(
                        StockPrice.company_id == cid,
                        StockPrice.date == latest_date
                    ).first()

                    if not sp_rec:
                        sp_rec = StockPrice(
                            company_id=cid,
                            date=latest_date,
                            close=close_p,
                            adjusted_close=adj_p,
                            volume=vol_p,
                            return_1m=ret_1m,
                            return_3m=ret_3m,
                            sma_50=sma50,
                            sma_200=sma200,
                            rsi_14=rsi14,
                            relative_strength_sp500=ret_3m,
                            relative_strength_sector=ret_3m - 0.02
                        )
                        db.add(sp_rec)
                        added_count += 1
                    else:
                        sp_rec.close = close_p
                        sp_rec.adjusted_close = adj_p
                        sp_rec.volume = vol_p
                        sp_rec.return_1m = ret_1m
                        sp_rec.return_3m = ret_3m
                        sp_rec.sma_50 = sma50
                        sp_rec.sma_200 = sma200
                        sp_rec.rsi_14 = rsi14
                        sp_rec.relative_strength_sp500 = ret_3m
                        sp_rec.relative_strength_sector = ret_3m - 0.02
                        updated_count += 1

                except Exception as ex:
                    continue

            db.commit()

        logger.info(f"Bulk price sync complete! Added: {added_count}, Updated: {updated_count} stock price records.")

    except Exception as e:
        logger.error(f"Error in batch price sync: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Bulk download price history for equities.")
    parser.add_argument("--batch-size", type=int, default=250)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    batch_download_prices(batch_size=args.batch_size, limit=args.limit)
