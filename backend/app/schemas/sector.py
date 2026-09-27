from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import date

class SectorBase(BaseModel):
    symbol: str
    name: str
    gics_code: Optional[str] = None
    description: Optional[str] = None
    benchmark: str = "SPY"
    level: int = 1
    category: Optional[str] = None

class SectorResponse(SectorBase):
    id: int
    class Config:
        from_attributes = True

class SectorScoresSchema(BaseModel):
    momentum: float
    relative_strength: float
    trend: float
    regime_fit: float
    risk: float
    breadth: Optional[float] = 50.0
    fundamental: Optional[float] = 50.0
    surprise: Optional[float] = 50.0

class TailCoordinate(BaseModel):
    date: str
    rs_ratio: float
    rs_momentum: float

class SectorRankingItem(BaseModel):
    symbol: str
    name: str
    gics_code: Optional[str] = None
    level: int = 1
    category: Optional[str] = None
    rank: int
    rank_change: int = 0
    overall_score: float
    scores: SectorScoresSchema
    rs_ratio: Optional[float] = 100.0
    rs_momentum: Optional[float] = 100.0
    rs_ratio_strategic: Optional[float] = 100.0
    rs_momentum_strategic: Optional[float] = 100.0
    pe_ratio_ttm: Optional[float] = None
    pe_percentile_5y: Optional[float] = None
    quality_flag: Optional[str] = None
    eps_growth_yoy: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    eps_surprise_pct: Optional[float] = None
    beta_growth: Optional[float] = None
    beta_inflation: Optional[float] = None
    beta_fca: Optional[float] = None
    tails: Optional[List[TailCoordinate]] = None
    classification: str # LEADING, IMPROVING, WEAKENING, LAGGING
    why: List[str]

class SectorRankingResponse(BaseModel):
    date: date
    active_regime: str
    rankings: List[SectorRankingItem]

class SectorPerformanceItem(BaseModel):
    date: date
    return_1d: Optional[float] = None
    return_5d: Optional[float] = None
    return_1m: Optional[float] = None
    return_3m: Optional[float] = None
    return_6m: Optional[float] = None
    return_12m: Optional[float] = None

class SectorFeatureItem(BaseModel):
    date: date
    momentum_1m: Optional[float] = None
    momentum_3m: Optional[float] = None
    relative_strength_1m: Optional[float] = None
    relative_strength_3m: Optional[float] = None
    rs_ratio: Optional[float] = None
    rs_momentum: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    volatility_20d: Optional[float] = None
    drawdown: Optional[float] = None
    breadth_sma: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    pe_ratio_ttm: Optional[float] = None
    pe_percentile_5y: Optional[float] = None
    eps_surprise_pct: Optional[float] = None
    beta_growth: Optional[float] = None
    beta_inflation: Optional[float] = None
    beta_fca: Optional[float] = None
