from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Index
from datetime import datetime
from backend.app.core.database import Base

class CompanySnapshot(Base):
    """
    Materialized Snapshot table for sub-millisecond screener queries, multi-factor filtering,
    and cross-sectional benchmark comparisons.
    """
    __tablename__ = "company_snapshots"

    company_id = Column(Integer, ForeignKey("companies.id"), primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    company_name = Column(String, nullable=False)
    sector_id = Column(Integer, ForeignKey("sectors.id"), index=True)
    sector_name = Column(String)
    
    # Valuation & Market Size
    market_cap = Column(Float, nullable=True)
    close_price = Column(Float, nullable=True)
    
    # Stock Intelligence Scores & Ranks
    rank = Column(Integer, nullable=True, index=True)
    overall_score = Column(Float, nullable=True, index=True)
    quality_score = Column(Float, nullable=True)
    growth_score = Column(Float, nullable=True)
    valuation_score = Column(Float, nullable=True)
    earnings_score = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    relative_strength_score = Column(Float, nullable=True)
    
    # Core Fundamentals
    revenue = Column(Float, nullable=True)
    net_income = Column(Float, nullable=True)
    eps = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    revenue_growth_yoy = Column(Float, nullable=True)
    gross_margin = Column(Float, nullable=True)
    fcf_yield = Column(Float, nullable=True)
    roic = Column(Float, nullable=True)

    as_of_date = Column(Date, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_snapshot_sector_rank", "sector_id", "rank"),
        Index("idx_snapshot_score_rank", "overall_score", "rank"),
    )
