from sqlalchemy import Column, Integer, Date, Float
from ..core.database import Base


class MacroFeature(Base):
    __tablename__ = "macro_features"

    id = Column(Integer, primary_key=True, index=True)
    feature_date = Column(Date, index=True)
    growth_score = Column(Float)
    inflation_score = Column(Float)
    rates_score = Column(Float)
    liquidity_score = Column(Float)
    credit_score = Column(Float)
    risk_score = Column(Float)
    overall_score = Column(Float)
