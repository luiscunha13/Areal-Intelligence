from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.core.database import get_db
from backend.app.models.candidate import InvestmentCandidate
from backend.app.models.company import Company
from backend.app.schemas.candidate import InvestmentCandidateResponse

router = APIRouter(prefix="/api/candidates", tags=["Investment Candidates & Opportunity Engine"])

@router.get("", response_model=List[InvestmentCandidateResponse])
def get_investment_candidates(
    category: Optional[str] = Query(None),
    min_score: float = Query(default=0.0, ge=0.0, le=100.0),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List investment candidates combining Macro + Sector + Stock intelligence scores."""
    query = db.query(InvestmentCandidate).join(Company, InvestmentCandidate.company_id == Company.id)

    if category:
        query = query.filter(InvestmentCandidate.category == category)
    if min_score > 0:
        query = query.filter(InvestmentCandidate.candidate_score >= min_score)

    candidates = query.order_by(InvestmentCandidate.candidate_score.desc()).limit(limit).all()
    return candidates

@router.get("/top", response_model=List[InvestmentCandidateResponse])
def get_top_candidates(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    """Get the top-ranked investment candidates across the market."""
    return (
        db.query(InvestmentCandidate)
        .join(Company, InvestmentCandidate.company_id == Company.id)
        .order_by(InvestmentCandidate.candidate_score.desc())
        .limit(limit)
        .all()
    )
