from pydantic import BaseModel
from datetime import date
from typing import Optional, List


class DimensionScores(BaseModel):
    growth: float
    inflation: float
    rates: float
    liquidity: float
    credit: float
    risk: float


class DriverExplanation(BaseModel):
    positive: List[str] = []
    negative: List[str] = []


class MarketRegimeResponse(BaseModel):
    date: date
    regime: str
    overall_score: float
    confidence: float
    dimensions: DimensionScores
    methodology_version: str = "1.0"
    why: Optional[DriverExplanation] = None

    class Config:
        from_attributes = True


class MarketRegimeHistoryPoint(BaseModel):
    date: date
    regime: str
    overall_score: float
    confidence: float
