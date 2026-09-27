import sys
import os
import logging
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, engine
from backend.app.models.company import Company
from backend.app.models.financial_metric import FinancialMetric
from backend.app.models.stock_price import StockPrice
from backend.app.models.stock_score import StockScore
from backend.app.services.stock_scoring import calculate_cross_sectional_stock_scores

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    db = SessionLocal()
    today = datetime.now().date()

    try:
        logger.info("Loading latest financial metrics & price features for active equities...")
        
        # SQL query to pull latest metrics for each company
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
        )
        SELECT 
            c.id AS company_id,
            c.ticker,
            f.roic, f.roe, f.operating_margin, f.fcf_margin, f.debt_to_equity,
            f.revenue_growth_yoy, f.eps_growth_yoy, f.fcf_growth_yoy,
            f.pe_ratio, f.forward_pe, f.ev_to_ebitda, f.price_to_fcf AS fcf_yield,
            f.eps_surprise_pct, f.revenue_surprise_pct,
            p.close, p.sma_50, p.sma_200, p.rsi_14,
            p.relative_strength_sp500, p.relative_strength_sector
        FROM companies c
        LEFT JOIN latest_fin f ON c.id = f.company_id
        LEFT JOIN latest_price p ON c.id = p.company_id
        WHERE c.is_active = TRUE;
        """

        df = pd.read_sql(sql, db.bind)
        logger.info(f"Pulled {len(df)} active equities from Docker Postgres. Computing Z-Score scores...")

        scored = calculate_cross_sectional_stock_scores(df)

        # Sort by overall score to establish rank
        scored = scored.sort_values(by="overall_score", ascending=False).reset_index(drop=True)
        scored["rank"] = scored.index + 1

        logger.info(f"Saving cross-sectional scores and ranks for {len(scored)} companies...")

        # Update or bulk insert StockScore records
        for _, row in scored.iterrows():
            cid = int(row["company_id"])
            s_score = db.query(StockScore).filter(
                StockScore.company_id == cid,
                StockScore.date == today
            ).first()

            if not s_score:
                s_score = StockScore(
                    company_id=cid,
                    date=today,
                    quality_score=float(row["quality_score"]),
                    growth_score=float(row["growth_score"]),
                    valuation_score=float(row["valuation_score"]),
                    earnings_score=float(row["earnings_score"]),
                    technical_score=float(row["technical_score"]),
                    relative_strength_score=float(row["relative_strength_score"]),
                    overall_score=float(row["overall_score"]),
                    rank=int(row["rank"]),
                    rank_change=0,
                    methodology_version="2.0-pit"
                )
                db.add(s_score)
            else:
                s_score.quality_score = float(row["quality_score"])
                s_score.growth_score = float(row["growth_score"])
                s_score.valuation_score = float(row["valuation_score"])
                s_score.earnings_score = float(row["earnings_score"])
                s_score.technical_score = float(row["technical_score"])
                s_score.relative_strength_score = float(row["relative_strength_score"])
                s_score.overall_score = float(row["overall_score"])
                s_score.rank = int(row["rank"])
                s_score.methodology_version = "2.0-pit"

        db.commit()
        logger.info(f"Successfully computed & saved methodology v2.0-pit scores for {len(scored)} equities!")

    except Exception as e:
        logger.error(f"Error executing cross-sectional scoring: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
