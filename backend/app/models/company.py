from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.core.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    exchange = Column(String(50), default="NASDAQ/NYSE")
    country = Column(String(10), default="US")
    currency = Column(String(10), default="USD")

    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=True, index=True)
    industry_id = Column(Integer, ForeignKey("industries.id"), nullable=True, index=True)

    market_cap = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    first_seen = Column(Date, nullable=True)
    last_seen = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    industry = relationship("Industry", back_populates="companies")
    index_memberships = relationship("IndexMembership", back_populates="company", cascade="all, delete-orphan")
    financial_metrics = relationship("FinancialMetric", back_populates="company", cascade="all, delete-orphan")
    stock_prices = relationship("StockPrice", back_populates="company", cascade="all, delete-orphan")
    stock_scores = relationship("StockScore", back_populates="company", cascade="all, delete-orphan")
