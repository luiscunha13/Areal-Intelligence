import sys
import os
import logging
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models.company_snapshot import CompanySnapshot
from backend.app.models.sector import Sector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    today = datetime.now().date()
    now = datetime.now()

    try:
        logger.info("Building materialized company snapshots from Postgres database...")

        # SQL to combine latest company, sector, price, fundamental metric, and methodology 2.0 stock score
        sql = """
        WITH latest_fin AS (
            SELECT DISTINCT ON (company_id) *
            FROM financial_metrics
            ORDER BY company_id, period_end DESC
        ),
        latest_price AS (
            SELECT DISTINCT ON (company_id) *
            FROM stock_prices
            ORDER BY company_id, date DESC
        ),
        latest_score AS (
            SELECT DISTINCT ON (company_id) *
            FROM stock_scores
            ORDER BY company_id, date DESC
        )
        SELECT 
            c.id AS company_id,
            c.ticker,
            c.company_name,
            c.sector_id,
            s.name AS sector_name,
            COALESCE(c.market_cap, p.close * 10000000.0) AS market_cap,
            p.close AS close_price,
            sc.rank,
            COALESCE(sc.overall_score, 50.0) AS overall_score,
            sc.quality_score,
            sc.growth_score,
            sc.valuation_score,
            sc.earnings_score,
            sc.technical_score,
            sc.relative_strength_score,
            f.revenue,
            f.net_income,
            f.eps,
            f.pe_ratio,
            f.revenue_growth_yoy,
            f.gross_margin,
            f.price_to_fcf AS fcf_yield,
            f.roic
        FROM companies c
        LEFT JOIN sectors s ON c.sector_id = s.id
        LEFT JOIN latest_fin f ON c.id = f.company_id
        LEFT JOIN latest_price p ON c.id = p.company_id
        LEFT JOIN latest_score sc ON c.id = sc.company_id
        WHERE c.is_active = TRUE
        ORDER BY sc.overall_score DESC NULLS LAST, c.ticker ASC;
        """

        df = pd.read_sql(sql, db.bind)
        logger.info(f"Assembled {len(df)} company snapshot records. Updating table...")

        # Sanitize NaN values to None for clean database insertion
        df = df.where(pd.notnull(df), None)

        # Truncate existing snapshots and bulk insert new snapshot view
        db.execute(CompanySnapshot.__table__.delete())
        
        snapshots = []
        for rank_idx, row in df.iterrows():
            sec_id = int(row["sector_id"]) if pd.notnull(row["sector_id"]) else None
            rnk = rank_idx + 1

            sn = CompanySnapshot(
                company_id=int(row["company_id"]),
                ticker=str(row["ticker"]),
                company_name=str(row["company_name"]),
                sector_id=sec_id,
                sector_name=str(row["sector_name"]) if pd.notnull(row["sector_name"]) else None,
                market_cap=float(row["market_cap"]) if pd.notnull(row["market_cap"]) else None,
                close_price=float(row["close_price"]) if pd.notnull(row["close_price"]) else None,
                rank=rnk,
                overall_score=float(row["overall_score"]) if pd.notnull(row["overall_score"]) else 50.0,
                quality_score=float(row["quality_score"]) if pd.notnull(row["quality_score"]) else None,
                growth_score=float(row["growth_score"]) if pd.notnull(row["growth_score"]) else None,
                valuation_score=float(row["valuation_score"]) if pd.notnull(row["valuation_score"]) else None,
                earnings_score=float(row["earnings_score"]) if pd.notnull(row["earnings_score"]) else None,
                technical_score=float(row["technical_score"]) if pd.notnull(row["technical_score"]) else None,
                relative_strength_score=float(row["relative_strength_score"]) if pd.notnull(row["relative_strength_score"]) else None,
                revenue=float(row["revenue"]) if pd.notnull(row["revenue"]) else None,
                net_income=float(row["net_income"]) if pd.notnull(row["net_income"]) else None,
                eps=float(row["eps"]) if pd.notnull(row["eps"]) else None,
                pe_ratio=float(row["pe_ratio"]) if pd.notnull(row["pe_ratio"]) else None,
                revenue_growth_yoy=float(row["revenue_growth_yoy"]) if pd.notnull(row["revenue_growth_yoy"]) else None,
                gross_margin=float(row["gross_margin"]) if pd.notnull(row["gross_margin"]) else None,
                fcf_yield=float(row["fcf_yield"]) if pd.notnull(row["fcf_yield"]) else None,
                roic=float(row["roic"]) if pd.notnull(row["roic"]) else None,
                as_of_date=today,
                updated_at=now
            )
            snapshots.append(sn)

        db.bulk_save_objects(snapshots)
        db.commit()
        logger.info(f"Successfully refreshed {len(snapshots)} materialized company snapshots in Docker Postgres!")

    except Exception as e:
        logger.error(f"Error refreshing materialized snapshots: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
