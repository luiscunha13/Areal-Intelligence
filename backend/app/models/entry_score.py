from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index
from sqlalchemy.orm import relationship

from backend.app.core.database import Base

class EntryScore(Base):
    """
    Stores calculated short-to-medium term Entry Timing scores for equities.
    Evaluates Trend, Momentum, Price Extension, Support/Resistance, Valuation Entry Context, and Event Risk.
    """
    __tablename__ = "entry_scores"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD

    # Sub-scores (0-100 scale)
    trend_score = Column(Float, nullable=False, default=50.0)
    momentum_score = Column(Float, nullable=False, default=50.0)
    extension_score = Column(Float, nullable=False, default=50.0)
    support_resistance_score = Column(Float, nullable=False, default=50.0)
    valuation_context_score = Column(Float, nullable=False, default=50.0)
    event_risk_score = Column(Float, nullable=False, default=50.0)

    # Composite Entry Score (0-100 scale)
    entry_score = Column(Float, nullable=False, index=True)

    # Entry Classification & Status
    status = Column(String(30), nullable=False, default="ACCEPTABLE")  # EXCELLENT, GOOD, ACCEPTABLE, WEAK, POOR
    confidence = Column(String(20), nullable=False, default="HIGH")    # HIGH, MEDIUM, LOW
    event_risk_level = Column(String(20), nullable=False, default="LOW") # LOW, MODERATE, HIGH

    methodology_version = Column(String(20), nullable=False, default="entry_v1.0")

    company = relationship("Company", backref="entry_scores")

    __table_args__ = (
        Index("idx_entry_scores_company_date", "company_id", "date", unique=True),
        Index("idx_entry_scores_date_score", "date", "entry_score"),
    )
