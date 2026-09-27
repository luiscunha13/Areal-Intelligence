from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.core.database import Base

class Sector(Base):
    __tablename__ = "sectors"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True) # e.g. XLK, XLV, SMH
    name = Column(String(100), nullable=False) # e.g. Information Technology
    gics_code = Column(String(50), nullable=True)
    description = Column(String(255), nullable=True)
    benchmark = Column(String(10), default="SPY")
    level = Column(Integer, default=1, index=True) # 1 = GICS Sector, 2 = Industry Group, 3 = Theme Basket
    category = Column(String(100), nullable=True) # e.g. Semiconductors, Biotech
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    prices = relationship("SectorPrice", back_populates="sector", cascade="all, delete-orphan")
    returns = relationship("SectorReturn", back_populates="sector", cascade="all, delete-orphan")
    features = relationship("SectorFeature", back_populates="sector", cascade="all, delete-orphan")
    scores = relationship("SectorScore", back_populates="sector", cascade="all, delete-orphan")
