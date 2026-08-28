"""
catalog_sync.py
───────────────
Reads all YAML catalog files and upserts them into the database.
This is the single source of truth sync — run it after any catalog change.

Usage:
    python scripts/catalog_sync.py
    python scripts/catalog_sync.py --dry-run
"""
import argparse
import sys
from pathlib import Path

import yaml
from sqlalchemy import create_engine, text

# Resolve paths
ROOT = Path(__file__).parent.parent
CATALOG_DIR = ROOT / "catalog"

import os
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/arealdb")


def load_yaml(filename: str) -> dict:
    path = CATALOG_DIR / filename
    with open(path) as f:
        return yaml.safe_load(f)


def sync_macro_series(conn, dry_run: bool) -> int:
    data = load_yaml("macro_series.yaml")
    series_list = data.get("series", [])
    count = 0
    for s in series_list:
        analysis = s.get("analysis", {})
        sql = text("""
            INSERT INTO macro_series (
                series_id, name, category, source, frequency, unit,
                is_derived, derive_formula, display_color,
                analysis_rising, analysis_falling
            ) VALUES (
                :series_id, :name, :category, :source, :frequency, :unit,
                :is_derived, :derive_formula, :display_color,
                :analysis_rising, :analysis_falling
            )
            ON CONFLICT (series_id) DO UPDATE SET
                name = EXCLUDED.name,
                category = EXCLUDED.category,
                source = EXCLUDED.source,
                frequency = EXCLUDED.frequency,
                unit = EXCLUDED.unit,
                is_derived = EXCLUDED.is_derived,
                derive_formula = EXCLUDED.derive_formula,
                display_color = EXCLUDED.display_color,
                analysis_rising = EXCLUDED.analysis_rising,
                analysis_falling = EXCLUDED.analysis_falling
        """)
        params = {
            "series_id": s["series_id"],
            "name": s["name"],
            "category": s["category"],
            "source": s.get("source", "fred"),
            "frequency": s["frequency"],
            "unit": s.get("unit"),
            "is_derived": s.get("is_derived", False),
            "derive_formula": s.get("derive_formula"),
            "display_color": s.get("display_color"),
            "analysis_rising": analysis.get("rising"),
            "analysis_falling": analysis.get("falling"),
        }
        if not dry_run:
            conn.execute(sql, params)
        count += 1
    return count


def sync_etfs(conn, dry_run: bool) -> int:
    data = load_yaml("etfs.yaml")
    etf_list = data.get("etfs", [])
    count = 0
    for e in etf_list:
        sql = text("""
            INSERT INTO etfs (
                ticker, name, category, sub_category, benchmark,
                gics_sector, expense_ratio
            ) VALUES (
                :ticker, :name, :category, :sub_category, :benchmark,
                :gics_sector, :expense_ratio
            )
            ON CONFLICT (ticker) DO UPDATE SET
                name = EXCLUDED.name,
                category = EXCLUDED.category,
                sub_category = EXCLUDED.sub_category,
                benchmark = EXCLUDED.benchmark,
                gics_sector = EXCLUDED.gics_sector,
                expense_ratio = EXCLUDED.expense_ratio
        """)
        params = {
            "ticker": e["ticker"],
            "name": e["name"],
            "category": e["category"],
            "sub_category": e.get("sub_category"),
            "benchmark": e.get("benchmark"),
            "gics_sector": e.get("gics_sector"),
            "expense_ratio": e.get("expense_ratio"),
        }
        if not dry_run:
            conn.execute(sql, params)
        count += 1
    return count


def sync_sectors(conn, dry_run: bool) -> int:
    data = load_yaml("sectors.yaml")
    sector_list = data.get("sectors", [])
    count = 0
    for s in sector_list:
        sql = text("""
            INSERT INTO sectors (code, name, etf_ticker, description)
            VALUES (:code, :name, :etf_ticker, :description)
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                etf_ticker = EXCLUDED.etf_ticker,
                description = EXCLUDED.description
        """)
        params = {
            "code": s["code"],
            "name": s["name"],
            "etf_ticker": s.get("etf_ticker"),
            "description": s.get("description"),
        }
        if not dry_run:
            conn.execute(sql, params)
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Sync YAML catalogs to database")
    parser.add_argument("--dry-run", action="store_true", help="Print counts without writing to DB")
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL)
    dry = args.dry_run

    if dry:
        print("🔍 DRY RUN — no database writes\n")

    with engine.begin() as conn:
        n_macro = sync_macro_series(conn, dry)
        print(f"{'[DRY] ' if dry else ''}✅ macro_series: {n_macro} series synced")

        n_etfs = sync_etfs(conn, dry)
        print(f"{'[DRY] ' if dry else ''}✅ etfs: {n_etfs} ETFs synced")

        n_sectors = sync_sectors(conn, dry)
        print(f"{'[DRY] ' if dry else ''}✅ sectors: {n_sectors} sectors synced")

    total = n_macro + n_etfs + n_sectors
    print(f"\n{'🔍 Would sync' if dry else '🚀 Synced'} {total} catalog entries total")


if __name__ == "__main__":
    main()
