from sqlalchemy import Column, Integer, String, Boolean, DateTime
from ..core.database import Base
import datetime


class MacroSeries(Base):
    __tablename__ = "macro_series"

    id = Column(Integer, primary_key=True, index=True)
    fred_series_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    category = Column(String)
    description = Column(String, nullable=True)
    frequency = Column(String)
    unit = Column(String)
    source = Column(String)
    seasonally_adjusted = Column(Boolean, default=False)
    analysis_overview = Column(String, nullable=True)
    impact_rising = Column(String, nullable=True)
    impact_falling = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

