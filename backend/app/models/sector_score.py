from sqlalchemy import Column, Integer, Float, Date, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class SectorScore(Base):
    __tablename__ = "sector_scores"

    id = Column(Integer, primary_key=True, index=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    momentum_score = Column(Float, nullable=True)
    relative_strength_score = Column(Float, nullable=True)
    trend_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    regime_fit_score = Column(Float, nullable=True)
    breadth_score = Column(Float, nullable=True)
    fundamental_score = Column(Float, nullable=True)
    surprise_score = Column(Float, nullable=True)

    rs_ratio = Column(Float, nullable=True) # Raw RRG RS-Ratio (Tactical 50d)
    rs_momentum = Column(Float, nullable=True) # Raw RRG RS-Momentum (Tactical 14d)
    rs_ratio_strategic = Column(Float, nullable=True) # Raw RRG RS-Ratio (Strategic 260d)
    rs_momentum_strategic = Column(Float, nullable=True) # Raw RRG RS-Momentum (Strategic 65d)
    tails = Column(String(2000), nullable=True) # JSON serialized list of last N period (rs_ratio, rs_momentum, date)

    overall_score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=True)
    rank_change = Column(Integer, nullable=True)
    classification = Column(String(50), nullable=True) # LEADING, IMPROVING, WEAKENING, LAGGING
    methodology_version = Column(String(20), default="2.0")

    sector = relationship("Sector", back_populates="scores")

    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uix_sector_score_date"),
    )
