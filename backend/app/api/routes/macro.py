import logging
import requests
import pandas as pd
import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import SessionLocal
from ...models import MacroSeries, MacroObservation, MacroFeature, MacroConsensus
from ...schemas.macro import (
    MacroSeriesResponse,
    MacroSeriesDetailResponse,
    MacroObservationPoint,
    MacroFeatureResponse,
    MacroConsensusPoint,
)
from ...services.fred import FredClient

logger = logging.getLogger(__name__)

router = APIRouter()
fred_client = FredClient()
release_cache = {}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def auto_ingest_fred_series(series_id: str, db: Session) -> Optional[MacroSeries]:
    """Dynamically fetches and seeds an unregistered FRED series (e.g., USREC)."""
    sid = series_id.upper()
    csv_url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"

    try:
        logger.info(f"Auto-ingesting FRED series '{sid}' from {csv_url}...")
        df = pd.read_csv(csv_url)
        if df.empty or len(df.columns) < 2:
            return None

        name_map = {
            "USREC": "NBER U.S. Recession Indicator",
            "RECPROUSM156N": "Smoothed U.S. Recession Probability",
        }
        series_name = name_map.get(sid, f"FRED Series {sid}")

        s = MacroSeries(
            fred_series_id=sid,
            name=series_name,
            category="Growth / Business Cycle" if "REC" in sid else "Macro Indicator",
            description=f"Auto-ingested FRED series {sid}",
            frequency="Monthly",
            unit="Binary / Index",
            source="FRED",
            seasonally_adjusted=True
        )
        db.add(s)
        db.flush()

        date_col = df.columns[0]
        val_col = df.columns[1]

        obs_objects = []
        for _, row in df.iterrows():
            d_str = str(row[date_col])
            val_raw = row[val_col]
            try:
                d_obj = datetime.date.fromisoformat(d_str)
                val_float = float(val_raw) if pd.notnull(val_raw) and val_raw != "." else None
                obs_objects.append(MacroObservation(
                    series_id=s.id,
                    observation_date=d_obj,
                    value=val_float
                ))
            except Exception:
                continue

        db.bulk_save_objects(obs_objects)
        db.commit()
        db.refresh(s)
        logger.info(f"Successfully auto-ingested {len(obs_objects)} observations for {sid}.")
        return s
    except Exception as e:
        logger.error(f"Failed auto-ingestion for FRED series '{sid}': {e}")
        db.rollback()
        return None


@router.get("/series", response_model=List[MacroSeriesResponse])
def list_series(db: Session = Depends(get_db)):
    """List all available macro series in the database."""
    series = db.query(MacroSeries).order_by(MacroSeries.category, MacroSeries.fred_series_id).all()
    return series


@router.get("/series/{series_id}", response_model=MacroSeriesDetailResponse)
def get_series_detail(
    series_id: str,
    limit: int = Query(default=50000, ge=1, le=100000),
    db: Session = Depends(get_db),
):
    """Get metadata and historical observations for a specific series, with dynamic fallback for unseeded FRED series."""
    sid = series_id.upper()
    s = db.query(MacroSeries).filter(MacroSeries.fred_series_id == sid).first()

    if not s:
        # Dynamic fallback: Auto-ingest series from FRED if requested by frontend
        s = auto_ingest_fred_series(sid, db=db)
        if not s:
            raise HTTPException(status_code=404, detail=f"Series '{series_id}' not found and could not be fetched from FRED.")

    observations = (
        db.query(MacroObservation)
        .filter(MacroObservation.series_id == s.id)
        .order_by(MacroObservation.observation_date.desc())
        .limit(limit)
        .all()
    )

    obs_points = [
        MacroObservationPoint(
            date=o.observation_date,
            value=o.value,
            vintage_date=o.vintage_date,
        )
        for o in reversed(observations)
    ]

    if sid not in release_cache:
        release_cache[sid] = fred_client.get_series_release_dates(sid)

    latest_c = (
        db.query(MacroConsensus)
        .filter(MacroConsensus.series_id == s.id)
        .order_by(MacroConsensus.release_date.desc())
        .first()
    )

    latest_consensus_point = (
        MacroConsensusPoint(
            release_date=latest_c.release_date,
            period=latest_c.period,
            consensus=latest_c.consensus_value,
            actual=latest_c.actual_value,
            previous=latest_c.previous_value,
            surprise_delta=latest_c.surprise_delta,
            unit=latest_c.unit,
        )
        if latest_c
        else None
    )

    return MacroSeriesDetailResponse(
        id=s.id,
        fred_series_id=s.fred_series_id,
        name=s.name,
        category=s.category,
        description=s.description,
        frequency=s.frequency,
        unit=s.unit,
        source=s.source,
        seasonally_adjusted=s.seasonally_adjusted,
        created_at=s.created_at,
        updated_at=s.updated_at,
        release_info=release_cache.get(sid),
        latest_consensus=latest_consensus_point,
        observations=obs_points,
    )


@router.get("/features", response_model=List[MacroFeatureResponse])
def list_features(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get calculated features and dimension scores history."""
    features = db.query(MacroFeature).order_by(MacroFeature.feature_date.desc()).limit(limit).all()
    return list(reversed(features))


@router.get("/scores")
def get_current_scores(db: Session = Depends(get_db)):
    """Get current dimension scores breakdown."""
    mf = db.query(MacroFeature).order_by(MacroFeature.feature_date.desc()).first()
    if not mf:
        return {"error": "No scores calculated yet. Run calculate_features script."}
    return {
        "date": mf.feature_date.isoformat(),
        "scores": {
            "growth": mf.growth_score,
            "inflation": mf.inflation_score,
            "rates": mf.rates_score,
            "liquidity": mf.liquidity_score,
            "credit": mf.credit_score,
            "risk": mf.risk_score,
            "overall": mf.overall_score,
        },
    }
