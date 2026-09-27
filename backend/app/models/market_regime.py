from sqlalchemy import Column, Integer, Date, String, Float
from ..core.database import Base


class MarketRegime(Base):
    __tablename__ = "market_regimes"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    regime = Column(String)
    confidence = Column(Float)
    growth_score = Column(Float)
    inflation_score = Column(Float)
    liquidity_score = Column(Float)
    rates_score = Column(Float)
    credit_score = Column(Float)
    risk_score = Column(Float)
    overall_score = Column(Float)
    methodology_version = Column(String)
