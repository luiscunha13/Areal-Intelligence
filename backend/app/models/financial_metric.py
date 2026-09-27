from sqlalchemy import Column, Integer, Float, Date, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    available_date = Column(Date, nullable=False, index=True)
    period_type = Column(String(10), default="TTM") # TTM, Annual, Quarterly

    # Core Financial Statements (USD)
    revenue = Column(Float, nullable=True)
    gross_profit = Column(Float, nullable=True)
    operating_income = Column(Float, nullable=True)
    ebitda = Column(Float, nullable=True)
    net_income = Column(Float, nullable=True)
    eps = Column(Float, nullable=True)
    cash = Column(Float, nullable=True)
    total_debt = Column(Float, nullable=True)
    total_assets = Column(Float, nullable=True)
    equity = Column(Float, nullable=True)
    operating_cash_flow = Column(Float, nullable=True)
    capex = Column(Float, nullable=True)
    free_cash_flow = Column(Float, nullable=True)

    # Subphase 3.3 Growth & Quality Metrics
    revenue_growth_yoy = Column(Float, nullable=True)
    eps_growth_yoy = Column(Float, nullable=True)
    fcf_growth_yoy = Column(Float, nullable=True)
    revenue_cagr_3y = Column(Float, nullable=True)
    roic = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    gross_margin = Column(Float, nullable=True)
    operating_margin = Column(Float, nullable=True)
    fcf_margin = Column(Float, nullable=True)
    debt_to_equity = Column(Float, nullable=True)

    # Subphase 3.4 Valuation Multiples
    pe_ratio = Column(Float, nullable=True)
    forward_pe = Column(Float, nullable=True)
    peg_ratio = Column(Float, nullable=True)
    ev_to_sales = Column(Float, nullable=True)
    ev_to_ebitda = Column(Float, nullable=True)
    price_to_fcf = Column(Float, nullable=True)
    fcf_yield = Column(Float, nullable=True)

    # Subphase 3.5 Earnings Surprises & Revisions
    eps_surprise_pct = Column(Float, nullable=True)
    revenue_surprise_pct = Column(Float, nullable=True)
    eps_revision_30d = Column(Float, nullable=True)

    source = Column(String(50), default="YahooFinance / SEC")

    company = relationship("Company", back_populates="financial_metrics")

    __table_args__ = (
        UniqueConstraint("company_id", "period_end", "period_type", name="uix_company_period"),
    )
