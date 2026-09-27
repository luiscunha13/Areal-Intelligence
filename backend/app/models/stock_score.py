from sqlalchemy import Column, Integer, Float, Date, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class StockScore(Base):
    __tablename__ = "stock_scores"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    growth_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    valuation_score = Column(Float, nullable=True)
    earnings_score = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    relative_strength_score = Column(Float, nullable=True)

    overall_score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=True)
    rank_change = Column(Integer, nullable=True)
    methodology_version = Column(String(20), default="1.0")

    company = relationship("Company", back_populates="stock_scores")

    __table_args__ = (
        UniqueConstraint("company_id", "date", name="uix_stock_score_date"),
    )
