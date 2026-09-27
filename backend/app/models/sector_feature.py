from sqlalchemy import Column, Integer, Float, Date, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class SectorFeature(Base):
    __tablename__ = "sector_features"

    id = Column(Integer, primary_key=True, index=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    momentum_1m = Column(Float, nullable=True)
    momentum_3m = Column(Float, nullable=True)
    momentum_6m = Column(Float, nullable=True)
    momentum_12m = Column(Float, nullable=True)

    relative_strength_1m = Column(Float, nullable=True)
    relative_strength_3m = Column(Float, nullable=True)
    relative_strength_6m = Column(Float, nullable=True)
    relative_strength_12m = Column(Float, nullable=True)

    rs_ratio = Column(Float, nullable=True) # RRG RS-Ratio Tactical (50d)
    rs_momentum = Column(Float, nullable=True) # RRG RS-Momentum Tactical (14d)
    rs_ratio_strategic = Column(Float, nullable=True) # RRG RS-Ratio Strategic (260d)
    rs_momentum_strategic = Column(Float, nullable=True) # RRG RS-Momentum Strategic (65d)

    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    sma_100 = Column(Float, nullable=True)
    sma_200 = Column(Float, nullable=True)
    slope_200d = Column(Float, nullable=True)

    volatility_20d = Column(Float, nullable=True)
    volatility_60d = Column(Float, nullable=True)
    drawdown = Column(Float, nullable=True)
    distance_from_high = Column(Float, nullable=True)
    volume_ratio = Column(Float, nullable=True)
    breadth_sma = Column(Float, nullable=True) # % constituents above SMA50/200
    correlation_spy = Column(Float, nullable=True) # 60-day correlation to SPY

    # Phase 2 Fundamentals Metrics (SEC EDGAR XBRL)
    eps_growth_yoy = Column(Float, nullable=True)
    revenue_growth_yoy = Column(Float, nullable=True)
    margin_trend = Column(Float, nullable=True)
    quality_flag = Column(String(50), nullable=True) # Clean growth, Diluted growth, Neutral / Contraction
    capex_growth_yoy = Column(Float, nullable=True)
    pe_ratio_ttm = Column(Float, nullable=True)
    pe_percentile_5y = Column(Float, nullable=True)

    # Phase 3 Earnings Surprise & Macro Betas
    eps_surprise_pct = Column(Float, nullable=True)
    beta_growth = Column(Float, nullable=True)
    beta_inflation = Column(Float, nullable=True)
    beta_fca = Column(Float, nullable=True)

    sector = relationship("Sector", back_populates="features")

    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uix_sector_feature_date"),
    )
