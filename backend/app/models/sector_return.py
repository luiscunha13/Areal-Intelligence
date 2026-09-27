from sqlalchemy import Column, Integer, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class SectorReturn(Base):
    __tablename__ = "sector_returns"

    id = Column(Integer, primary_key=True, index=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    return_1d = Column(Float, nullable=True)
    return_5d = Column(Float, nullable=True)
    return_1m = Column(Float, nullable=True)
    return_3m = Column(Float, nullable=True)
    return_6m = Column(Float, nullable=True)
    return_12m = Column(Float, nullable=True)

    sector = relationship("Sector", back_populates="returns")

    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uix_sector_return_date"),
    )
