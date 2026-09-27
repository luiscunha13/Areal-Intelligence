"""Ingestion script for all 18 macro series using FRED API.

Usage: python scripts/ingest_macro.py
"""
import os
import sys
import datetime
import logging

# Make backend importable when running the script directly
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.app.services.fred import FredClient
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.series_config import SERIES_CATALOG, get_analytical_metadata
from backend.app.models import MacroSeries, MacroObservation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def upsert_series(session, meta: dict):
    fred_id = meta["fred_series_id"]
    name = meta.get("name", fred_id)
    category = meta.get("category", "")
    description = meta.get("description", "")
    
    analytics = get_analytical_metadata(fred_id, name, category, description)

    series = session.query(MacroSeries).filter_by(fred_series_id=fred_id).one_or_none()
    if series:
        series.name = name
        series.category = category
        series.description = description
        series.frequency = meta.get("frequency", series.frequency)
        series.unit = meta.get("unit", series.unit)
        series.seasonally_adjusted = meta.get("seasonally_adjusted", series.seasonally_adjusted)
        series.analysis_overview = analytics["analysis_overview"]
        series.impact_rising = analytics["impact_rising"]
        series.impact_falling = analytics["impact_falling"]
        series.updated_at = datetime.datetime.utcnow()
        session.commit()
        return series

    series = MacroSeries(
        fred_series_id=fred_id,
        name=name,
        category=category,
        description=description,
        frequency=meta.get("frequency"),
        unit=meta.get("unit"),
        source="FRED",
        seasonally_adjusted=meta.get("seasonally_adjusted", False),
        analysis_overview=analytics["analysis_overview"],
        impact_rising=analytics["impact_rising"],
        impact_falling=analytics["impact_falling"],
    )
    session.add(series)
    session.commit()
    session.refresh(series)
    return series


def batch_upsert_observations(session, series_obj, observations: list):
    count = 0
    # Fetch existing (obs_date, vintage_date) tuples for fast deduplication
    existing = set(
        session.query(MacroObservation.observation_date, MacroObservation.vintage_date)
        .filter(MacroObservation.series_id == series_obj.id)
        .all()
    )

    new_objs = []
    for o in observations:
        date_str = o.get("date")
        try:
            obs_date = datetime.date.fromisoformat(date_str)
        except Exception:
            continue

        vintage_iso = o.get("vintage_date") or o.get("realtime_start")
        try:
            vintage_date = datetime.date.fromisoformat(vintage_iso) if vintage_iso else obs_date
        except Exception:
            vintage_date = obs_date

        value = o.get("value")

        if (obs_date, vintage_date) not in existing:
            new_objs.append(
                MacroObservation(
                    series_id=series_obj.id,
                    observation_date=obs_date,
                    vintage_date=vintage_date,
                    value=value,
                )
            )
            existing.add((obs_date, vintage_date))
            count += 1

    if new_objs:
        session.bulk_save_objects(new_objs)
        session.commit()
    return count


def compute_derived_series(session):
    logger.info("Computing derived series (FED_NET_LIQUIDITY, COPPER_GOLD)...")
    
    # 1. FED_NET_LIQUIDITY = WALCL (Assets, millions) - WTREGEN (TGA, millions) - RRPONTSYD (ON RRP, billions) * 1000
    # Net Liquidity in Billions = (WALCL - WTREGEN)/1000 - RRPONTSYD
    walcl_s = session.query(MacroSeries).filter_by(fred_series_id="WALCL").first()
    tga_s = session.query(MacroSeries).filter_by(fred_series_id="WTREGEN").first()
    rrp_s = session.query(MacroSeries).filter_by(fred_series_id="RRPONTSYD").first()
    net_liq_s = session.query(MacroSeries).filter_by(fred_series_id="FED_NET_LIQUIDITY").first()

    if walcl_s and tga_s and rrp_s and net_liq_s:
        walcl_obs = {o.observation_date: o.value for o in session.query(MacroObservation).filter_by(series_id=walcl_s.id).all() if o.value is not None}
        tga_obs = {o.observation_date: o.value for o in session.query(MacroObservation).filter_by(series_id=tga_s.id).all() if o.value is not None}
        rrp_obs = {o.observation_date: o.value for o in session.query(MacroObservation).filter_by(series_id=rrp_s.id).all() if o.value is not None}

        all_dates = sorted(set(walcl_obs.keys()) | set(tga_obs.keys()) | set(rrp_obs.keys()))
        last_walcl, last_tga, last_rrp = None, None, None
        net_liq_points = []
        for d in all_dates:
            if d in walcl_obs: last_walcl = walcl_obs[d]
            if d in tga_obs: last_tga = tga_obs[d]
            if d in rrp_obs: last_rrp = rrp_obs[d]

            if last_walcl is not None and last_tga is not None and last_rrp is not None:
                val = ((last_walcl - last_tga) / 1000.0) - last_rrp
                net_liq_points.append({"date": d.isoformat(), "value": round(val, 2)})

        added = batch_upsert_observations(session, net_liq_s, net_liq_points)
        logger.info("Computed %d points for FED_NET_LIQUIDITY (%d new)", len(net_liq_points), added)

    # 2. COPPER_GOLD = PCOPPUSDM (Global Copper) / IQ12260 (Gold Price Index)
    cop_s = session.query(MacroSeries).filter_by(fred_series_id="PCOPPUSDM").first()
    gold_s = session.query(MacroSeries).filter_by(fred_series_id="IQ12260").first()
    cop_gold_s = session.query(MacroSeries).filter_by(fred_series_id="COPPER_GOLD").first()

    if cop_s and gold_s and cop_gold_s:
        cop_obs = {o.observation_date: o.value for o in session.query(MacroObservation).filter_by(series_id=cop_s.id).all() if o.value is not None}
        gold_obs = {o.observation_date: o.value for o in session.query(MacroObservation).filter_by(series_id=gold_s.id).all() if o.value is not None}

        all_dates = sorted(set(cop_obs.keys()) | set(gold_obs.keys()))
        last_cop, last_gold = None, None
        cg_points = []
        for d in all_dates:
            if d in cop_obs: last_cop = cop_obs[d]
            if d in gold_obs: last_gold = gold_obs[d]

            if last_cop is not None and last_gold is not None and last_gold > 0:
                val = last_cop / last_gold
                cg_points.append({"date": d.isoformat(), "value": round(val, 4)})

        added = batch_upsert_observations(session, cop_gold_s, cg_points)
        logger.info("Computed %d points for COPPER_GOLD ratio (%d new)", len(cg_points), added)


def main():
    Base.metadata.create_all(bind=engine)
    client = FredClient()

    session = SessionLocal()
    total_added = 0
    logger.info("Starting ingestion of %d series...", len(SERIES_CATALOG))

    DERIVED_IDS = {"FED_NET_LIQUIDITY", "COPPER_GOLD"}

    for meta in SERIES_CATALOG:
        fred_id = meta["fred_series_id"]
        series_obj = upsert_series(session, meta)

        if fred_id in DERIVED_IDS:
            continue

        try:
            data = client.get_series_observations(fred_id)
            observations = data.get("observations", [])
            added = batch_upsert_observations(session, series_obj, observations)
            logger.info("Ingested %s (%s): %d new observations", fred_id, meta["name"], added)
            total_added += added
        except Exception as e:
            logger.error("Error ingesting series %s: %s", fred_id, e)

    # Compute synthetic derived series
    compute_derived_series(session)

    session.close()
    logger.info("Ingestion completed. Total new observations added: %d", total_added)


if __name__ == "__main__":
    main()
