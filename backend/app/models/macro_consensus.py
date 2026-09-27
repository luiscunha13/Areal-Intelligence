from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from ..core.database import Base
import datetime


class MacroConsensus(Base):
    __tablename__ = "macro_consensus"

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("macro_series.id"), index=True, nullable=False)
    release_date = Column(Date, index=True, nullable=False)
    period = Column(String, nullable=True)  # e.g. "Jul 2026"
    consensus_value = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)
    previous_value = Column(Float, nullable=True)
    surprise_delta = Column(Float, nullable=True)  # actual - consensus
    unit = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
