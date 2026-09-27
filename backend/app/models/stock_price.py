from sqlalchemy import Column, Integer, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=False)
    adjusted_close = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)

    # Subphase 3.6 Technical Indicators
    return_1m = Column(Float, nullable=True)
    return_3m = Column(Float, nullable=True)
    return_6m = Column(Float, nullable=True)
    return_12m = Column(Float, nullable=True)

    relative_strength_sp500 = Column(Float, nullable=True)
    relative_strength_sector = Column(Float, nullable=True)

    sma_50 = Column(Float, nullable=True)
    sma_200 = Column(Float, nullable=True)
    rsi_14 = Column(Float, nullable=True)
    volatility_20d = Column(Float, nullable=True)
    drawdown = Column(Float, nullable=True)

    company = relationship("Company", back_populates="stock_prices")

    __table_args__ = (
        UniqueConstraint("company_id", "date", name="uix_stock_price_date"),
    )
