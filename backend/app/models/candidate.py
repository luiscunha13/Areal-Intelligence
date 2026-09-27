from sqlalchemy import Column, Integer, Float, Date, String, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class InvestmentCandidate(Base):
    __tablename__ = "investment_candidates"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    candidate_score = Column(Float, nullable=False) # 60% Stock Score + 40% Sector Score
    stock_score = Column(Float, nullable=False)
    sector_score = Column(Float, nullable=False)

    category = Column(String(50), nullable=False) # Strong Candidate, Candidate, Watchlist, Weak Candidate
    confidence = Column(String(20), default="High") # High, Medium, Low
    risk_flags = Column(JSON, nullable=True) # e.g. ["HIGH_VALUATION", "WEAK_BALANCE_SHEET"]
    explanations = Column(JSON, nullable=True) # Deterministic thesis bullets

    company = relationship("Company")

    __table_args__ = (
        UniqueConstraint("company_id", "date", name="uix_candidate_date"),
    )
