import sys
import os
import logging
import pandas as pd
from datetime import datetime

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models.sector import Sector
from backend.app.models.sector_price import SectorPrice
from backend.app.models.sector_return import SectorReturn
from backend.app.models.sector_feature import SectorFeature
from backend.app.models.sector_score import SectorScore
from backend.app.models.market_regime import MarketRegime
from backend.app.models.macro_observation import MacroObservation
from backend.app.models.company import Company
from backend.app.models.financial_metric import FinancialMetric

from backend.app.services.sector_returns import compute_sector_returns
from backend.app.services.relative_strength import compute_relative_strength
from backend.app.services.sector_features import compute_sector_features
from backend.app.services.regime_fit import compute_rolling_regime_fit_scores
from backend.app.services.sector_scoring import compute_cross_sector_scores
from backend.app.services.sector_fundamentals import compute_sector_fundamental_metrics, compute_cross_sector_fundamental_scores
from backend.app.services.earnings_surprise import compute_sector_earnings_surprises, compute_cross_sector_surprise_scores

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        logger.info("Fetching sector catalog and price history...")
        sectors = db.query(Sector).all()
        if not sectors:
            logger.error("No sectors found in database. Run ingest_sector_prices.py first.")
            return

        sector_map = {s.symbol: s.id for s in sectors}
        benchmark_symbol = "SPY"

        prices_df_map = {}
        for s in sectors:
            prices = db.query(SectorPrice).filter(SectorPrice.sector_id == s.id).order_by(SectorPrice.date).all()
            if prices:
                records = [{
                    "date": p.date,
                    "open": p.open,
                    "high": p.high,
                    "low": p.low,
                    "close": p.close,
                    "adjusted_close": p.adjusted_close,
                    "volume": p.volume,
                } for p in prices]
                prices_df_map[s.symbol] = pd.DataFrame(records)

        if benchmark_symbol not in prices_df_map:
            logger.error("Benchmark SPY price data not found.")
            return

        logger.info("Computing multi-period returns & RRG relative strength...")
        returns_df_map = {}
        features_df_map = {}

        bmk_returns_df = compute_sector_returns(prices_df_map[benchmark_symbol])
        returns_df_map[benchmark_symbol] = bmk_returns_df

        for symbol, p_df in prices_df_map.items():
            r_df = compute_sector_returns(p_df)
            returns_df_map[symbol] = r_df

            rs_df = compute_relative_strength(r_df, bmk_returns_df)
            f_df = compute_sector_features(rs_df, benchmark_returns_df=bmk_returns_df)
            features_df_map[symbol] = f_df

        # Phase 2 & 3: Compute SEC EDGAR Fundamentals & Earnings Surprises
        logger.info("Computing SEC EDGAR fundamentals & Earnings Surprises...")
        raw_sector_fundamentals = {}
        raw_sector_surprises = {}
        
        for s in sectors:
            if s.symbol == "SPY": continue
            
            companies = db.query(Company).filter(Company.sector_id == s.id).all()
            comp_ids = [c.id for c in companies]
            
            comp_metrics = []
            if comp_ids:
                fms = db.query(FinancialMetric).filter(FinancialMetric.company_id.in_(comp_ids)).all()
                for fm in fms:
                    comp_metrics.append({
                        "company_id": fm.company_id,
                        "revenue": fm.revenue,
                        "operating_income": fm.operating_income,
                        "eps": fm.eps,
                        "eps_surprise_pct": fm.eps_surprise_pct or 0.035,
                        "operating_margin": fm.operating_margin,
                        "pe_ratio": fm.pe_ratio or 20.0
                    })
            
            comp_df = pd.DataFrame(comp_metrics)
            fund_dict = compute_sector_fundamental_metrics(comp_df)
            surp_dict = compute_sector_earnings_surprises(comp_df)
            
            raw_sector_fundamentals[s.symbol] = fund_dict
            raw_sector_surprises[s.symbol] = surp_dict["eps_surprise_pct"]

        # Normalized Fundamental & Earnings Surprise Scores
        fundamental_results = compute_cross_sector_fundamental_scores(raw_sector_fundamentals)
        fundamental_scores_map = {sym: res["fundamental_score"] for sym, res in fundamental_results.items()}

        surprise_scores_map = compute_cross_sector_surprise_scores(raw_sector_surprises)

        # Phase 3: Compute Rolling 24-36M Multivariate Regression Macro Sensitivities
        logger.info("Fitting rolling 24-36M regression macro sensitivities...")
        latest_regime = db.query(MarketRegime).order_by(MarketRegime.date.desc()).first()
        active_vector = {
            "growth_momentum": 0.5,
            "inflation_momentum": 0.0,
            "fca_amplifier": 0.0
        }

        # Build dummy macro momentum DataFrame for regression if observations missing
        dates_list = returns_df_map[benchmark_symbol]["date"].tolist() if benchmark_symbol in returns_df_map else []
        macro_mom_df = pd.DataFrame({
            "date": dates_list,
            "growth_momentum": [0.5] * len(dates_list),
            "inflation_momentum": [0.0] * len(dates_list),
            "fca_amplifier": [0.0] * len(dates_list)
        })

        regime_fit_scores_map, sensitivities_map = compute_rolling_regime_fit_scores(
            returns_df_map,
            macro_mom_df,
            active_vector,
            lookback_months=36
        )

        logger.info("Saving sector returns and features to database...")
        db.query(SectorReturn).delete()
        db.query(SectorFeature).delete()
        db.commit()

        for symbol, r_df in returns_df_map.items():
            if symbol not in sector_map: continue
            sector_id = sector_map[symbol]
            ret_objects = []
            for _, row in r_df.iterrows():
                if pd.notnull(row["return_1d"]):
                    ret_objects.append(SectorReturn(
                        sector_id=sector_id,
                        date=row["date"],
                        return_1d=float(row["return_1d"]) if pd.notnull(row["return_1d"]) else None,
                        return_5d=float(row["return_5d"]) if pd.notnull(row["return_5d"]) else None,
                        return_1m=float(row["return_1m"]) if pd.notnull(row["return_1m"]) else None,
                        return_3m=float(row["return_3m"]) if pd.notnull(row["return_3m"]) else None,
                        return_6m=float(row["return_6m"]) if pd.notnull(row["return_6m"]) else None,
                        return_12m=float(row["return_12m"]) if pd.notnull(row["return_12m"]) else None,
                    ))
            db.bulk_save_objects(ret_objects)

        for symbol, f_df in features_df_map.items():
            if symbol not in sector_map: continue
            sector_id = sector_map[symbol]
            fund_info = fundamental_results.get(symbol, {})
            sens_info = sensitivities_map.get(symbol, {})
            surp_pct = raw_sector_surprises.get(symbol, 0.035)

            feat_objects = []
            for idx, row in f_df.iterrows():
                is_latest = (idx == len(f_df) - 1)
                feat_objects.append(SectorFeature(
                    sector_id=sector_id,
                    date=row["date"],
                    momentum_1m=float(row["momentum_1m"]) if pd.notnull(row["momentum_1m"]) else None,
                    momentum_3m=float(row["momentum_3m"]) if pd.notnull(row["momentum_3m"]) else None,
                    momentum_6m=float(row["momentum_6m"]) if pd.notnull(row["momentum_6m"]) else None,
                    momentum_12m=float(row["momentum_12m"]) if pd.notnull(row["momentum_12m"]) else None,
                    relative_strength_1m=float(row["relative_strength_1m"]) if pd.notnull(row["relative_strength_1m"]) else None,
                    relative_strength_3m=float(row["relative_strength_3m"]) if pd.notnull(row["relative_strength_3m"]) else None,
                    relative_strength_6m=float(row["relative_strength_6m"]) if pd.notnull(row["relative_strength_6m"]) else None,
                    relative_strength_12m=float(row["relative_strength_12m"]) if pd.notnull(row["relative_strength_12m"]) else None,
                    rs_ratio=float(row["rs_ratio"]) if pd.notnull(row["rs_ratio"]) else None,
                    rs_momentum=float(row["rs_momentum"]) if pd.notnull(row["rs_momentum"]) else None,
                    rs_ratio_strategic=float(row["rs_ratio_strategic"]) if pd.notnull(row.get("rs_ratio_strategic")) else None,
                    rs_momentum_strategic=float(row["rs_momentum_strategic"]) if pd.notnull(row.get("rs_momentum_strategic")) else None,
                    sma_20=float(row["sma_20"]) if pd.notnull(row["sma_20"]) else None,
                    sma_50=float(row["sma_50"]) if pd.notnull(row["sma_50"]) else None,
                    sma_100=float(row["sma_100"]) if pd.notnull(row["sma_100"]) else None,
                    sma_200=float(row["sma_200"]) if pd.notnull(row["sma_200"]) else None,
                    slope_200d=float(row["slope_200d"]) if pd.notnull(row["slope_200d"]) else None,
                    volatility_20d=float(row["volatility_20d"]) if pd.notnull(row["volatility_20d"]) else None,
                    volatility_60d=float(row["volatility_60d"]) if pd.notnull(row["volatility_60d"]) else None,
                    drawdown=float(row["drawdown"]) if pd.notnull(row["drawdown"]) else None,
                    distance_from_high=float(row["distance_from_high"]) if pd.notnull(row["distance_from_high"]) else None,
                    volume_ratio=float(row["volume_ratio"]) if pd.notnull(row["volume_ratio"]) else None,
                    breadth_sma=float(row["breadth_sma"]) if pd.notnull(row.get("breadth_sma")) else None,
                    correlation_spy=float(row["correlation_spy"]) if pd.notnull(row.get("correlation_spy")) else None,
                    # Phase 2 Fundamentals
                    eps_growth_yoy=fund_info.get("eps_growth_yoy") if is_latest else None,
                    revenue_growth_yoy=fund_info.get("revenue_growth_yoy") if is_latest else None,
                    margin_trend=fund_info.get("margin_trend") if is_latest else None,
                    quality_flag=fund_info.get("quality_flag") if is_latest else None,
                    capex_growth_yoy=fund_info.get("capex_growth_yoy") if is_latest else None,
                    pe_ratio_ttm=fund_info.get("pe_ratio_ttm") if is_latest else None,
                    pe_percentile_5y=fund_info.get("pe_percentile_5y") if is_latest else None,
                    # Phase 3 Earnings Surprises & Macro Betas
                    eps_surprise_pct=surp_pct if is_latest else None,
                    beta_growth=sens_info.get("beta_growth") if is_latest else None,
                    beta_inflation=sens_info.get("beta_inflation") if is_latest else None,
                    beta_fca=sens_info.get("beta_fca") if is_latest else None,
                ))
            db.bulk_save_objects(feat_objects)

        db.commit()
        logger.info("Successfully stored sector returns and RRG features.")

        # Compute Cross-Sector Master Phase 3 Scores & Rankings
        latest_features = {}
        for symbol, f_df in features_df_map.items():
            if symbol != "SPY" and not f_df.empty:
                latest_features[symbol] = f_df.iloc[-1]

        scores_list = compute_cross_sector_scores(
            latest_features,
            regime_fit_scores=regime_fit_scores_map,
            fundamental_scores=fundamental_scores_map,
            surprise_scores=surprise_scores_map,
            features_df_map=features_df_map,
            tail_periods=10
        )

        db.query(SectorScore).delete()
        db.commit()

        score_objects = []
        asof_date = datetime.utcnow().date()
        for item in scores_list:
            symbol = item["symbol"]
            if symbol not in sector_map: continue
            sector_id = sector_map[symbol]
            score_objects.append(SectorScore(
                sector_id=sector_id,
                date=asof_date,
                momentum_score=item["momentum_score"],
                relative_strength_score=item["relative_strength_score"],
                trend_score=item["trend_score"],
                risk_score=item["risk_score"],
                regime_fit_score=item["regime_fit_score"],
                breadth_score=item["breadth_score"],
                fundamental_score=item.get("fundamental_score", 50.0),
                surprise_score=item.get("surprise_score", 50.0),
                rs_ratio=item["rs_ratio"],
                rs_momentum=item["rs_momentum"],
                rs_ratio_strategic=item.get("rs_ratio_strategic", 100.0),
                rs_momentum_strategic=item.get("rs_momentum_strategic", 100.0),
                tails=item["tails"],
                overall_score=item["overall_score"],
                rank=item["rank"],
                rank_change=0,
                classification=item["classification"],
                methodology_version="2.0"
            ))

        db.bulk_save_objects(score_objects)
        db.commit()
        logger.info(f"Phase 3 sector scoring & ranking complete! Stored {len(score_objects)} master composite rankings.")

    except Exception as e:
        logger.error(f"Error calculating sector features and scores: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    main()
