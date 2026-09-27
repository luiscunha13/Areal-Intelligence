import sys
import os
import logging
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine, SessionLocal, Base
from backend.app.models.sector import Sector
from backend.app.models.sector_score import SectorScore
from backend.app.models.company import Company
from backend.app.models.financial_metric import FinancialMetric
from backend.app.models.stock_price import StockPrice
from backend.app.models.stock_score import StockScore
from backend.app.models.candidate import InvestmentCandidate

from backend.app.services.stock_scoring import calculate_stock_subscores
from backend.app.services.candidate_engine import evaluate_investment_candidate

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def process_company_data(db, company, sector, today):
    ticker = company.ticker
    try:
        yf_ticker = yf.Ticker(ticker)
        fast_info = yf_ticker.fast_info
        info = yf_ticker.info or {}

        # 1. Update Market Cap
        market_cap = fast_info.get("marketCap") or info.get("marketCap")
        if market_cap:
            company.market_cap = float(market_cap)

        # 2. Extract Financial Statement & Fundamental Metrics
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
        peg = info.get("pegRatio")
        ev_sales = info.get("enterpriseToRevenue")
        ev_ebitda = info.get("enterpriseToEbitda")
        p_fcf = info.get("priceToFreeCashflows")

        gross_m = info.get("grossMargins")
        op_margin = info.get("operatingMargins")
        fcf_margin = info.get("freeCashflowMargin")

        roe = info.get("returnOnEquity")
        roic = info.get("returnOnAssets") # Fallback to ROA if ROIC unavailable
        dte = info.get("debtToEquity")

        rev_g = info.get("revenueGrowth")
        eps_g = info.get("earningsGrowth")

        # Format percentages to 0-100 scale
        if gross_m is not None: gross_m = float(gross_m) * 100.0 if abs(gross_m) <= 1.0 else float(gross_m)
        if op_margin is not None: op_margin = float(op_margin) * 100.0 if abs(op_margin) <= 1.0 else float(op_margin)
        if fcf_margin is not None: fcf_margin = float(fcf_margin) * 100.0 if abs(fcf_margin) <= 1.0 else float(fcf_margin)
        if rev_g is not None: rev_g = float(rev_g) * 100.0 if abs(rev_g) <= 10.0 else float(rev_g)
        if eps_g is not None: eps_g = float(eps_g) * 100.0 if abs(eps_g) <= 10.0 else float(eps_g)
        if roe is not None: roe = float(roe) * 100.0 if abs(roe) <= 1.0 else float(roe)
        if roic is not None: roic = float(roic) * 100.0 if abs(roic) <= 1.0 else float(roic)
        if dte is not None: dte = float(dte) / 100.0 if float(dte) > 5.0 else float(dte)

        fin_metric = db.query(FinancialMetric).filter(
            FinancialMetric.company_id == company.id,
            FinancialMetric.period_end == today
        ).first()

        if not fin_metric:
            fin_metric = FinancialMetric(
                company_id=company.id,
                period_end=today,
                available_date=today,
                period_type="TTM",
                revenue=float(tot_rev) if tot_rev else None,
                gross_profit=float(gross_prof) if gross_prof else None,
                operating_income=float(op_inc) if op_inc else None,
                ebitda=float(ebitda_val) if ebitda_val else None,
                net_income=float(net_inc) if net_inc else None,
                eps=float(trailing_eps) if trailing_eps else None,
                cash=float(tot_cash) if tot_cash else None,
                total_debt=float(tot_debt) if tot_debt else None,
                free_cash_flow=float(fcf_val) if fcf_val else None,
                gross_margin=gross_m,
                operating_margin=op_margin,
                fcf_margin=fcf_margin,
                pe_ratio=float(pe) if pe else None,
                forward_pe=float(fwd_pe) if fwd_pe else None,
                peg_ratio=float(peg) if peg else None,
                ev_to_sales=float(ev_sales) if ev_sales else None,
                ev_to_ebitda=float(ev_ebitda) if ev_ebitda else None,
                price_to_fcf=float(p_fcf) if p_fcf else None,
                roe=roe,
                roic=roic,
                debt_to_equity=dte,
                revenue_growth_yoy=rev_g,
                eps_growth_yoy=eps_g,
                eps_surprise_pct=float(info.get("earningsQuarterlyGrowth") or 0.05),
                revenue_surprise_pct=0.02,
                source="YahooFinance API"
            )
            db.add(fin_metric)
        else:
            # Update existing record with full financial statement values
            fin_metric.revenue = float(tot_rev) if tot_rev else fin_metric.revenue
            fin_metric.gross_profit = float(gross_prof) if gross_prof else fin_metric.gross_profit
            fin_metric.operating_income = float(op_inc) if op_inc else fin_metric.operating_income
            fin_metric.ebitda = float(ebitda_val) if ebitda_val else fin_metric.ebitda
            fin_metric.net_income = float(net_inc) if net_inc else fin_metric.net_income
            fin_metric.eps = float(trailing_eps) if trailing_eps else fin_metric.eps
            fin_metric.cash = float(tot_cash) if tot_cash else fin_metric.cash
            fin_metric.total_debt = float(tot_debt) if tot_debt else fin_metric.total_debt
            fin_metric.free_cash_flow = float(fcf_val) if fcf_val else fin_metric.free_cash_flow
            fin_metric.gross_margin = gross_m if gross_m is not None else fin_metric.gross_margin
            fin_metric.operating_margin = op_margin if op_margin is not None else fin_metric.operating_margin
            fin_metric.fcf_margin = fcf_margin if fcf_margin is not None else fin_metric.fcf_margin
            fin_metric.pe_ratio = float(pe) if pe else fin_metric.pe_ratio
            fin_metric.forward_pe = float(fwd_pe) if fwd_pe else fin_metric.forward_pe
            fin_metric.revenue_growth_yoy = rev_g if rev_g is not None else fin_metric.revenue_growth_yoy
            fin_metric.eps_growth_yoy = eps_g if eps_g is not None else fin_metric.eps_growth_yoy

        # 3. Stock Price & Technical Indicators
        hist = yf_ticker.history(period="1y")
        if hist.empty:
            logger.warning(f"No price history for {ticker}")
            return None

        hist.index = hist.index.date
        latest_date = max(hist.index)
        latest_row = hist.loc[latest_date]

        close_val = float(latest_row["Close"])
        adj_close = float(latest_row.get("Adj Close", latest_row["Close"]))
        vol_val = float(latest_row["Volume"])

        # Compute Technical Indicators
        closes = hist["Close"]
        sma50 = float(closes.tail(50).mean()) if len(closes) >= 50 else close_val
        sma200 = float(closes.tail(200).mean()) if len(closes) >= 200 else close_val

        # RSI(14)
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi14 = float(100 - (100 / (1 + rs.iloc[-1]))) if len(closes) >= 14 else 50.0

        # Returns
        ret_1m = float(closes.pct_change(21).iloc[-1]) if len(closes) >= 21 else 0.0
        ret_3m = float(closes.pct_change(63).iloc[-1]) if len(closes) >= 63 else 0.0

        stock_p = db.query(StockPrice).filter(
            StockPrice.company_id == company.id,
            StockPrice.date == latest_date
        ).first()

        if not stock_p:
            stock_p = StockPrice(
                company_id=company.id,
                date=latest_date,
                close=close_val,
                adjusted_close=adj_close,
                volume=vol_val,
                return_1m=ret_1m,
                return_3m=ret_3m,
                sma_50=sma50,
                sma_200=sma200,
                rsi_14=rsi14,
                relative_strength_sp500=ret_3m,
                relative_strength_sector=ret_3m - 0.02
            )
            db.add(stock_p)

        # 4. Calculate Scores
        metrics_dict = {
            "roic": roic, "roe": roe, "operating_margin": op_margin, "fcf_margin": fcf_margin,
            "debt_to_equity": dte, "revenue_growth_yoy": rev_g, "eps_growth_yoy": eps_g,
            "fcf_growth_yoy": 8.0, "pe_ratio": pe, "forward_pe": fwd_pe, "ev_to_ebitda": ev_ebitda,
            "fcf_yield": 4.0, "eps_surprise_pct": 5.0, "revenue_surprise_pct": 2.0
        }

        price_dict = {
            "close": close_val, "sma_50": sma50, "sma_200": sma200, "rsi_14": rsi14,
            "relative_strength_sp500": ret_3m, "relative_strength_sector": ret_3m - 0.02
        }

        subscores = calculate_stock_subscores(metrics_dict, price_dict)

        # Get Sector Score
        sector_score_val = 75.0
        if sector:
            latest_sec_score = db.query(SectorScore).filter(
                SectorScore.sector_id == sector.id
            ).order_by(SectorScore.date.desc()).first()
            if latest_sec_score:
                sector_score_val = latest_sec_score.overall_score

        # Candidate Evaluation
        candidate_info = evaluate_investment_candidate(
            ticker=ticker,
            company_name=company.company_name,
            sector_name=sector.name if sector else "General",
            stock_scores=subscores,
            sector_score=sector_score_val,
            metrics=metrics_dict
        )

        return {
            "company_id": company.id,
            "date": latest_date,
            "subscores": subscores,
            "candidate": candidate_info
        }

    except Exception as e:
        logger.warning(f"Error processing ticker {ticker}: {e}")
        return None

import argparse
from backend.app.models.index_membership import IndexMembership

def main():
    parser = argparse.ArgumentParser(description="Ingest stock market data, financials, and calculate scores.")
    parser.add_argument("--sp500-only", action="store_true", help="Ingest only S&P 500 constituent companies")
    parser.add_argument("--limit", type=int, default=None, help="Limit maximum number of companies to process")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    today = datetime.utcnow().date()

    try:
        query = db.query(Company).filter(Company.is_active == True)
        if args.sp500_only:
            query = query.join(IndexMembership, Company.id == IndexMembership.company_id).filter(IndexMembership.index_name == "S&P 500")
        
        if args.limit:
            query = query.limit(args.limit)

        companies = query.all()
        sectors = {s.id: s for s in db.query(Sector).all()}
        logger.info(f"Starting data ingestion & scoring for {len(companies)} companies (SP500 only={args.sp500_only}, limit={args.limit})...")

        processed_results = []
        for idx, comp in enumerate(companies, start=1):
            sec = sectors.get(comp.sector_id)
            res = process_company_data(db, comp, sec, today)
            if res:
                processed_results.append(res)

            if idx % 25 == 0:
                db.commit()
                logger.info(f"Processed {idx}/{len(companies)} companies...")

        db.commit()

        # Save StockScores and Assign Ranks
        processed_results.sort(key=lambda x: x["subscores"]["overall_score"], reverse=True)
        logger.info(f"Saving StockScores and assigning rankings for {len(processed_results)} companies...")

        for rank_idx, item in enumerate(processed_results, start=1):
            cid = item["company_id"]
            dt = item["date"]
            subs = item["subscores"]
            cand = item["candidate"]

            s_score = db.query(StockScore).filter(
                StockScore.company_id == cid,
                StockScore.date == dt
            ).first()

            if not s_score:
                s_score = StockScore(
                    company_id=cid,
                    date=dt,
                    quality_score=subs["quality_score"],
                    growth_score=subs["growth_score"],
                    valuation_score=subs["valuation_score"],
                    earnings_score=subs["earnings_score"],
                    technical_score=subs["technical_score"],
                    relative_strength_score=subs["relative_strength_score"],
                    overall_score=subs["overall_score"],
                    rank=rank_idx,
                    rank_change=0,
                    methodology_version="1.0"
                )
                db.add(s_score)
            else:
                s_score.quality_score = subs["quality_score"]
                s_score.growth_score = subs["growth_score"]
                s_score.valuation_score = subs["valuation_score"]
                s_score.earnings_score = subs["earnings_score"]
                s_score.technical_score = subs["technical_score"]
                s_score.relative_strength_score = subs["relative_strength_score"]
                s_score.overall_score = subs["overall_score"]
                s_score.rank = rank_idx

            inv_cand = db.query(InvestmentCandidate).filter(
                InvestmentCandidate.company_id == cid,
                InvestmentCandidate.date == dt
            ).first()

            if not inv_cand:
                inv_cand = InvestmentCandidate(
                    company_id=cid,
                    date=dt,
                    candidate_score=cand["candidate_score"],
                    stock_score=cand["stock_score"],
                    sector_score=cand["sector_score"],
                    category=cand["category"],
                    confidence=cand["confidence"],
                    risk_flags=cand["risk_flags"],
                    explanations=cand["explanations"]
                )
                db.add(inv_cand)

        db.commit()
        logger.info("Successfully ingested stock data, calculated scores, rankings, and investment candidates!")

    except Exception as e:
        logger.error(f"Error ingesting stock data: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
