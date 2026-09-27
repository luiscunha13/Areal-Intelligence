from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index
from sqlalchemy.orm import relationship

from backend.app.core.database import Base

class EntryZone(Base):
    """
    Stores transparent preferred entry price ranges, invalidation levels, targets, and Risk/Reward ratios.
    """
    __tablename__ = "entry_zones"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD

    current_price = Column(Float, nullable=False)
    entry_zone_low = Column(Float, nullable=False)
    entry_zone_high = Column(Float, nullable=False)
    invalidation_price = Column(Float, nullable=False)
    reference_target_price = Column(Float, nullable=False)
    risk_reward_ratio = Column(Float, nullable=False) # Potential Reward / Risk

    company = relationship("Company", backref="entry_zones")

    __table_args__ = (
        Index("idx_entry_zones_company_date", "company_id", "date", unique=True),
    )
