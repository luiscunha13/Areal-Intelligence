import sys
import os
import logging
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models.company import Company
from backend.app.models.financial_metric import FinancialMetric
from backend.app.providers.edgar import SECEdgarProvider

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Representative large-cap constituents per sector for fundamental aggregation
REPRESENTATIVE_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "AMD", # Technology (XLK, SMH, IGV)
    "UNH", "LLY", "JNJ", "ABBV", "MRK", "PFE", "TMO", # Healthcare (XLV, XBI, PPH, IHI)
    "JPM", "BAC", "WFC", "C", "GS", "MS", "PNC", "SCHW", # Financials (XLF, KBE, KRE, KIE, KCE)
    "AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "DHI", # Discretionary / Retail (XLY, XRT, XHB)
    "GOOGL", "META", "NFLX", "TMUS", "DIS", # Communication (XLC)
    "CAT", "GE", "HON", "UNP", "UPS", "LMT", "RTX", # Industrials (XLI, ITA, IYT)
    "PG", "KO", "PEP", "COST", "WMT", # Staples (XLP)
    "XOM", "CVX", "COP", "SLB", "EOG", "HAL", # Energy (XLE, XOP, OIH)
    "NEE", "DUK", "SO", # Utilities (XLU)
    "PLD", "AMT", "EQIX", # Real Estate (XLRE)
    "LIN", "APD", "NEM", "FCX", # Materials (XLB, XME)
]

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    edgar = SECEdgarProvider()

    try:
        logger.info("Fetching SEC EDGAR CIK mapping...")
        cik_map = edgar.get_ticker_cik_map()
        if not cik_map:
            logger.error("Could not retrieve CIK map from SEC EDGAR.")
            return

        logger.info(f"Ingesting fundamentals for {len(REPRESENTATIVE_TICKERS)} representative companies...")

        ingested_count = 0
        for ticker in REPRESENTATIVE_TICKERS:
            cik = cik_map.get(ticker)
            if not cik:
                logger.warning(f"Ticker {ticker} not found in SEC CIK map.")
                continue

            company = db.query(Company).filter(Company.ticker == ticker).first()
            if not company:
                company = Company(
                    ticker=ticker,
                    company_name=f"{ticker} Inc.",
                    is_active=True
                )
                db.add(company)
                db.flush()

            facts = edgar.fetch_company_facts(cik)
            if not facts:
                continue

            df = edgar.extract_financial_line_items(facts)
            if df.empty:
                continue

            # Deduplicate by end_date and form
            df = df.drop_duplicates(subset=["end_date", "form"], keep="last")

            # Store recent annual / quarterly line items
            records_saved = 0
            for _, row in df.tail(8).iterrows():
                p_end = row["end_date"].date() if isinstance(row["end_date"], pd.Timestamp) else row["end_date"]
                p_type = "Annual" if row.get("form") in ["10-K", "10-K/A"] else "Quarterly"

                existing = db.query(FinancialMetric).filter(
                    FinancialMetric.company_id == company.id,
                    FinancialMetric.period_end == p_end,
                    FinancialMetric.period_type == p_type
                ).first()

                rev = float(row["revenue"]) if "revenue" in row and pd.notnull(row["revenue"]) else None
                op_inc = float(row["operating_income"]) if "operating_income" in row and pd.notnull(row["operating_income"]) else None
                eps_dil = float(row["eps_diluted"]) if "eps_diluted" in row and pd.notnull(row["eps_diluted"]) else None
                capex_val = float(row["capex"]) if "capex" in row and pd.notnull(row["capex"]) else None

                op_margin = (op_inc / rev) if (rev and op_inc and rev > 0) else None

                if not existing:
                    fm = FinancialMetric(
                        company_id=company.id,
                        period_end=p_end,
                        available_date=p_end,
                        period_type=p_type,
                        revenue=rev,
                        operating_income=op_inc,
                        eps=eps_dil,
                        capex=capex_val,
                        operating_margin=op_margin,
                        source="SEC_EDGAR_XBRL"
                    )
                    db.add(fm)
                    records_saved += 1
                else:
                    existing.revenue = rev
                    existing.operating_income = op_inc
                    existing.eps = eps_dil
                    existing.capex = capex_val
                    existing.operating_margin = op_margin

            db.commit()
            ingested_count += 1
            logger.info(f"Saved {records_saved} financial records for {ticker} (CIK: {cik}).")

        logger.info(f"Finished SEC EDGAR ingestion for {ingested_count} companies.")

    except Exception as e:
        logger.error(f"Error during SEC EDGAR ingestion: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
