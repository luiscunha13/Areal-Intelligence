from sqlalchemy import Column, Integer, ForeignKey, Date, Float, DateTime, UniqueConstraint
from ..core.database import Base
import datetime


class MacroObservation(Base):
    __tablename__ = "macro_observations"
    __table_args__ = (
        UniqueConstraint("series_id", "observation_date", "vintage_date", name="uix_series_obs_vintage"),
    )

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("macro_series.id"), index=True)
    observation_date = Column(Date, index=True)
    vintage_date = Column(Date, index=True)
    value = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

