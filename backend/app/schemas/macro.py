from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


class MacroSeriesBase(BaseModel):
    fred_series_id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    unit: Optional[str] = None
    source: Optional[str] = "FRED"
    seasonally_adjusted: Optional[bool] = False
    analysis_overview: Optional[str] = None
    impact_rising: Optional[str] = None
    impact_falling: Optional[str] = None


class MacroSeriesResponse(MacroSeriesBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MacroObservationPoint(BaseModel):
    date: date
    value: Optional[float] = None
    vintage_date: Optional[date] = None


class ReleaseInfoSchema(BaseModel):
    last_release: Optional[str] = None
    next_release: Optional[str] = None
    days_until: Optional[int] = None
    release_name: Optional[str] = None


class MacroConsensusPoint(BaseModel):
    release_date: date
    period: Optional[str] = None
    consensus: Optional[float] = None
    actual: Optional[float] = None
    previous: Optional[float] = None
    surprise_delta: Optional[float] = None
    unit: Optional[str] = None


class MacroSeriesDetailResponse(MacroSeriesResponse):
    release_info: Optional[ReleaseInfoSchema] = None
    latest_consensus: Optional[MacroConsensusPoint] = None
    observations: List[MacroObservationPoint] = []


class MacroFeatureResponse(BaseModel):
    feature_date: date
    growth_score: float
    inflation_score: float
    rates_score: float
    liquidity_score: float
    credit_score: float
    risk_score: float
    overall_score: float

    class Config:
        from_attributes = True
