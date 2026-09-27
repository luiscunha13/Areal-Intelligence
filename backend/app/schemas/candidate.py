from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import date
from backend.app.schemas.company import CompanyBase

class InvestmentCandidateResponse(BaseModel):
    id: int
    company_id: int
    date: date
    candidate_score: float
    stock_score: float
    sector_score: float
    category: str
    confidence: str
    risk_flags: Optional[List[str]] = None
    explanations: Optional[List[str]] = None
    company: CompanyBase

    model_config = ConfigDict(from_attributes=True)
