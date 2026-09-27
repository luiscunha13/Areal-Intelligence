from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

class IndustryBase(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class CompanyBase(BaseModel):
    id: int
    ticker: str
    company_name: str
    legal_name: Optional[str] = None
    exchange: str
    country: str
    currency: str
    sector_id: Optional[int] = None
    industry_id: Optional[int] = None
    market_cap: Optional[float] = None
    is_active: bool
    first_seen: Optional[date] = None
    last_seen: Optional[date] = None
    model_config = ConfigDict(from_attributes=True)

class StockPriceResponse(BaseModel):
    id: int
    company_id: int
    date: date
    close: float
    adjusted_close: float
    volume: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi_14: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class StockScoreResponse(BaseModel):
    id: int
    company_id: int
    date: date
    quality_score: Optional[float] = None
    growth_score: Optional[float] = None
    valuation_score: Optional[float] = None
    earnings_score: Optional[float] = None
    technical_score: Optional[float] = None
    relative_strength_score: Optional[float] = None
    overall_score: float
    rank: Optional[int] = None
    rank_change: Optional[int] = None
    methodology_version: str
    model_config = ConfigDict(from_attributes=True)

class FinancialMetricResponse(BaseModel):
    id: int
    company_id: int
    period_end: date
    period_type: str
    revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    ebitda: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None
    cash: Optional[float] = None
    total_debt: Optional[float] = None
    total_assets: Optional[float] = None
    equity: Optional[float] = None
    free_cash_flow: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    fcf_margin: Optional[float] = None
    roic: Optional[float] = None
    roe: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    price_to_fcf: Optional[float] = None
    eps_surprise_pct: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class CompanyDetailResponse(CompanyBase):
    industry: Optional[IndustryBase] = None
    sector_name: Optional[str] = None
    sector_score: Optional[float] = None
    active_regime: Optional[str] = None
    macro_fit_score: Optional[float] = None
    composite_candidate_score: Optional[float] = None
    candidate_category: Optional[str] = None
    thesis_explanations: Optional[List[str]] = None
    latest_score: Optional[StockScoreResponse] = None
    latest_price: Optional[StockPriceResponse] = None
    latest_financials: Optional[FinancialMetricResponse] = None
    model_config = ConfigDict(from_attributes=True)
