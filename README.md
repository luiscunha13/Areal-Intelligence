# Areal Intelligence

Automated financial intelligence platform — macroeconomic indicators, ETFs, sectors, and stocks.

## Architecture

```
catalog/          ← YAML-driven asset registry (add data = edit YAML)
ingestion/        ← Data loaders (FRED, yfinance, EDGAR)
transformation/   ← dbt models (staging → intermediate → marts)
scoring/          ← Pure Python analytics engines
airflow/dags/     ← Automated pipeline DAGs
api/              ← FastAPI serving layer
frontend/         ← Next.js dashboard
migrations/       ← Alembic DB schema versions
```

**Stack**: PostgreSQL 16 + TimescaleDB · Apache Airflow · dbt · FastAPI · Next.js

## Quick Start

### 1. Prerequisites
```bash
docker compose version   # >= 2.20
python --version         # >= 3.11
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and add your FRED_API_KEY (free at https://fred.stlouisfed.org/docs/api/api_key.html)
```

### 3. Start the stack
```bash
docker compose up -d
```

Services available:
- **Airflow UI**: http://localhost:8080 (admin / admin)
- **API docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

### 4. Run initial setup (first time only)
```bash
# Apply DB schema
docker compose exec api alembic upgrade head

# Sync catalogs to DB
docker compose exec api python /app/../scripts/catalog_sync.py

# Backfill 5 years of macro data
docker compose exec airflow-scheduler airflow dags trigger macro_indicators --conf '{"start_date": "2020-01-01"}'

# Backfill 5 years of ETF prices
docker compose exec airflow-scheduler airflow dags trigger market_prices --conf '{"start_date": "2020-01-01"}'
```

### 5. Adding a new economic indicator

Edit `catalog/macro_series.yaml`, add:
```yaml
- series_id: YOUR_FRED_ID
  name: Indicator Name
  category: growth  # growth | inflation | rates | liquidity | credit | risk | benchmark
  source: fred
  frequency: monthly
  unit: index
```

Then commit and push — the `catalog_sync` task in the Airflow DAG runs daily and picks it up automatically. Zero code changes required.

### 6. Adding a new ETF

Edit `catalog/etfs.yaml`, add:
```yaml
- ticker: YOURETF
  name: Fund Full Name
  category: thematic
  sub_category: your_theme
  benchmark: Index Name
  expense_ratio: 0.0065
```

## Data Pipeline

```
FRED API ──────────────► macro_observations (hypertable)
                                   │
yfinance ──────────────► prices (hypertable)
                                   │
SEC EDGAR ─────────────► financial_metrics
                                   │
                         dbt transforms
                                   │
                    ┌──────────────┼──────────────┐
               macro_features  sector_scores  etf_scores  stock_scores
                                   │
                              FastAPI → Next.js
```

## Airflow DAGs

| DAG | Schedule | Purpose |
|---|---|---|
| `macro_indicators` | Daily 07:00 UTC | FRED macro ingestion + derived series |
| `market_prices` | Daily 22:00 UTC | EOD prices for all catalog ETFs |
| `fundamentals` | Weekly Monday | Earnings + financials (EDGAR + yfinance) |
| `scoring_engine` | Daily 23:00 UTC | Recalculate all scores + regimes |
| `data_quality` | Weekly Monday | Freshness + completeness report |

## Data Lineage

Every row in production tables carries:
- `source` — where the data came from (`fred_api`, `yfinance`, `derived`)
- `fetched_at` — timestamp of ingestion
- `run_id` — links back to the `pipeline_runs` audit table
- `scoring_version` — version of the scoring model that computed the row

## Development

```bash
# Run tests
pytest tests/

# Lint
ruff check .

# Apply new migration
alembic revision --autogenerate -m "description"
alembic upgrade head

# Sync catalog manually
python scripts/catalog_sync.py --dry-run
python scripts/catalog_sync.py
```

## ETF Universe

~95 ETFs across 9 categories, all priced via yfinance (free):
- **Sector** (11) — GICS sector SPDR funds
- **Factor/Style** (15) — momentum, quality, value, growth, small-cap
- **Fixed Income** (13) — treasury, corporate, TIPS, EM bonds
- **International** (13) — developed, emerging, regional
- **Commodity** (11) — gold, oil, copper, agriculture, broad
- **Real Estate** (5) — broad REIT, mortgage REIT, international
- **Thematic** (14) — AI, robotics, clean energy, cybersecurity, EV
- **Volatility** (5) — long/short vol, managed futures, tail risk
- **Multi-Asset** (5) — balanced, risk parity, leveraged core

---

> Designed to be portable to Snowflake/BigQuery and deployable to AWS via Terraform if data volume outgrows PostgreSQL.