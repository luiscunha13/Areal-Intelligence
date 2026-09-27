from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index
from sqlalchemy.orm import relationship

from backend.app.core.database import Base

class EntrySetup(Base):
    """
    Stores detected technical setup patterns (e.g., TREND_PULLBACK, BREAKOUT, BASE_BREAKOUT, DEEP_PULLBACK, MEAN_REVERSION).
    """
    __tablename__ = "entry_setups"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD

    setup_type = Column(String(50), nullable=False, index=True) # TREND_PULLBACK, BREAKOUT, BASE_BREAKOUT, DEEP_PULLBACK, MEAN_REVERSION
    signal_strength = Column(Float, nullable=False, default=70.0) # 0-100 score
    description = Column(String(255), nullable=True)

    company = relationship("Company", backref="entry_setups")

    __table_args__ = (
        Index("idx_entry_setups_company_date_setup", "company_id", "date", "setup_type", unique=True),
    )
