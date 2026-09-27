# Areal Intelligence

Automated quantitative macroeconomic intelligence platform & Point-in-Time equity/sector regime identification engine.

---

## Architecture Overview

```text
Areal-Intelligence/
├── backend/            ← FastAPI application, SQLAlchemy models, schemas, and scoring engines
│   ├── app/
│   │   ├── api/routes/ ← REST endpoints (macro, sectors, companies, candidates, entry timing)
│   │   ├── models/     ← DB models (macro series, sector returns, company snapshots, stock scores)
│   │   └── services/   ← Analytical engines (macro regime, stock scoring, relative strength, entry timing)
│   └── tests/          ← Pytest test suite (31 unit & API integration tests)
├── scripts/            ← Data pipeline, ingestion, backtesting, and DB migration utilities
│   ├── cron_nightly_pipeline.py    ← Nightly automated ELT orchestrator
│   ├── run_cross_sectional_scoring.py ← Point-in-Time Z-Score normalization engine
│   ├── calculate_sector_features.py  ← Sector RRG (RS-Ratio / RS-Momentum) calculator
│   ├── refresh_materialized_snapshots.py ← Materialized company snapshot view refresher
│   └── migrate_v2_schema.py        ← DB schema migrations
├── transformation/     ← dbt transformation project (staging → intermediate → marts)
├── airflow/            ← Apache Airflow DAGs for automated workflow scheduling
├── docs/               ← Architecture specifications and methodology guides
├── frontend/           ← Next.js 14 web dashboard (Tailwind CSS, React 18, Recharts)
└── docker-compose.yml  ← Docker environment for PostgreSQL & backend execution
```

**Tech Stack**: PostgreSQL 15 · Apache Airflow 2.9 · dbt-postgres · FastAPI · Next.js 14 · Pandas · NumPy · Pytest · Docker

---

## Key Features & Analytics Engines

- **Automated Data Harvesting:** Extracts 18 core FRED macro series, daily stock/sector ETF time-series (yfinance), and corporate fundamentals (SEC EDGAR REST APIs).
- **Macro Regime Classification:** Rule-based 5-regime market classification (`Strong Risk-On`, `Moderate Risk-On`, `Neutral / Transition`, `Slowdown / Risk-Off`, `Recession / Strong Risk-Off`) with dynamic driver decomposition.
- **Cross-Sectional Z-Score Ranking Engine:** Methodology v2.0 Point-in-Time Z-Score normalization across Quality, Growth, Valuation, Earnings, Technicals, and Relative Strength.
- **Sector Rotation & RRG Features:** Relative Rotation Graph metrics (RS-Ratio and RS-Momentum) across GICS sectors and thematic ETFs.
- **Entry Timing & Opportunity Scanner:** Short-term momentum, moving average distance (20D/50D/200D SMA/EMA), and RSI signal triggers.
- **Materialized Screener Snapshots:** High-performance pre-computed PostgreSQL snapshot views serving downstream REST APIs.
- **Point-in-Time (PIT) Backtesting:** Historical simulator enforcing `vintage_date <= simulation_date` to prevent look-ahead bias.

---

## Quickstart Guide

### 1. Configure Environment Variables
```bash
cp .env.example .env
```
Edit `.env` to supply your FRED API Key:
```env
FRED_API_KEY=your_fred_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/macrodb
```

### 2. Start PostgreSQL via Docker
```bash
docker compose up -d db
```

### 3. Run Schema Migrations & Data Pipeline
```bash
# Apply v2 schema migrations
python scripts/migrate_v2_schema.py

# Execute full ingestion & scoring pipeline
python scripts/cron_nightly_pipeline.py
```

### 4. Run FastAPI Backend & Next.js Frontend

```bash
# FastAPI Backend REST Server
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/macrodb uvicorn backend.app.main:app --reload --port 8000

# Next.js Web Dashboard
cd frontend
npm install
npm run dev
```

* **Web Dashboard:** [http://localhost:3000](http://localhost:3000)
* **API Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing & Data Quality Verification

Execute the complete backend test suite using `pytest`:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/macrodb python3 -m pytest backend/tests
```

Run dbt data quality tests (if running inside Airflow/dbt environment):
```bash
dbt test --project-dir transformation
```

---

## License

MIT License