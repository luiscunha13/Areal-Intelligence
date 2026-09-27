import sys
import os
import logging
import yfinance as yf
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine, SessionLocal, Base
from backend.app.models.company import Company
from backend.app.models.financial_metric import FinancialMetric

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    db = SessionLocal()
    today = datetime.utcnow().date()

    try:
        # Get top companies first (or all active)
        companies = db.query(Company).filter(Company.is_active == True).all()
        logger.info(f"Updating full financial statement metrics for {len(companies)} companies...")

        updated_count = 0

        for idx, comp in enumerate(companies, start=1):
            try:
                info = yf.Ticker(comp.ticker).info or {}

                tot_rev = info.get("totalRevenue")
                gross_prof = info.get("grossProfits")
                op_inc = info.get("operatingIncome")
                ebitda_val = info.get("ebitda")
                net_inc = info.get("netIncomeToCommon")
                trailing_eps = info.get("trailingEps")
                tot_cash = info.get("totalCash")
                tot_debt = info.get("totalDebt")
                fcf_val = info.get("freeCashflow")

                pe = info.get("trailingPE") or info.get("peRatio")
                fwd_pe = info.get("forwardPE")
                gross_m = info.get("grossMargins")
                op_m = info.get("operatingMargins")
                fcf_m = info.get("freeCashflowMargin")
                rev_g = info.get("revenueGrowth")
                eps_g = info.get("earningsGrowth")
                roe = info.get("returnOnEquity")
                roic = info.get("returnOnAssets")

                if gross_m is not None: gross_m = float(gross_m) * 100.0 if abs(gross_m) <= 1.0 else float(gross_m)
                if op_m is not None: op_m = float(op_m) * 100.0 if abs(op_m) <= 1.0 else float(op_m)
                if fcf_m is not None: fcf_m = float(fcf_m) * 100.0 if abs(fcf_m) <= 1.0 else float(fcf_m)
                if rev_g is not None: rev_g = float(rev_g) * 100.0 if abs(rev_g) <= 10.0 else float(rev_g)
                if eps_g is not None: eps_g = float(eps_g) * 100.0 if abs(eps_g) <= 10.0 else float(eps_g)
                if roe is not None: roe = float(roe) * 100.0 if abs(roe) <= 1.0 else float(roe)
                if roic is not None: roic = float(roic) * 100.0 if abs(roic) <= 1.0 else float(roic)

                fin = db.query(FinancialMetric).filter(
                    FinancialMetric.company_id == comp.id
                ).order_by(FinancialMetric.period_end.desc()).first()

                if not fin:
                    fin = FinancialMetric(
                        company_id=comp.id,
                        period_end=today,
                        available_date=today,
                        period_type="TTM",
                        source="YahooFinance API"
                    )
                    db.add(fin)

                if tot_rev is not None: fin.revenue = float(tot_rev)
                if gross_prof is not None: fin.gross_profit = float(gross_prof)
                if op_inc is not None: fin.operating_income = float(op_inc)
                if ebitda_val is not None: fin.ebitda = float(ebitda_val)
                if net_inc is not None: fin.net_income = float(net_inc)
                if trailing_eps is not None: fin.eps = float(trailing_eps)
                if tot_cash is not None: fin.cash = float(tot_cash)
                if tot_debt is not None: fin.total_debt = float(tot_debt)
                if fcf_val is not None: fin.free_cash_flow = float(fcf_val)

                if gross_m is not None: fin.gross_margin = gross_m
                if op_m is not None: fin.operating_margin = op_m
                if fcf_m is not None: fin.fcf_margin = fcf_m
                if pe is not None: fin.pe_ratio = float(pe)
                if fwd_pe is not None: fin.forward_pe = float(fwd_pe)
                if rev_g is not None: fin.revenue_growth_yoy = rev_g
                if eps_g is not None: fin.eps_growth_yoy = eps_g
                if roe is not None: fin.roe = roe
                if roic is not None: fin.roic = roic

                updated_count += 1

                if idx % 50 == 0:
                    db.commit()
                    logger.info(f"Updated financial statements for {idx}/{len(companies)} companies...")

            except Exception as e:
                logger.warning(f"Skipping financial metrics update for {comp.ticker}: {e}")

        db.commit()
        logger.info(f"Successfully populated financial statements for {updated_count} companies.")

    except Exception as e:
        logger.error(f"Error updating financial statements: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
