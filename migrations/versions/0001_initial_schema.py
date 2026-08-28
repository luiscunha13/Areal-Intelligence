"""
Alembic migration: 0001_initial_schema
Creates the full production schema with TimescaleDB hypertables.
Run: alembic upgrade head
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ──────────────────────────────────────────────
    # ASSET CATALOG
    # ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS macro_series (
            series_id           TEXT PRIMARY KEY,
            name                TEXT NOT NULL,
            category            TEXT NOT NULL,
            source              TEXT NOT NULL DEFAULT 'fred',
            frequency           TEXT NOT NULL,
            unit                TEXT,
            is_derived          BOOLEAN DEFAULT FALSE,
            derive_formula      TEXT,
            is_active           BOOLEAN DEFAULT TRUE,
            display_color       TEXT,
            analysis_rising     TEXT,
            analysis_falling    TEXT,
            analysis_overview   TEXT,
            created_at          TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS etfs (
            id              SERIAL PRIMARY KEY,
            ticker          TEXT UNIQUE NOT NULL,
            name            TEXT NOT NULL,
            category        TEXT NOT NULL,
            sub_category    TEXT,
            benchmark       TEXT,
            gics_sector     TEXT,
            expense_ratio   NUMERIC(6,4),
            inception_date  DATE,
            is_active       BOOLEAN DEFAULT TRUE,
            created_at      TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id              SERIAL PRIMARY KEY,
            ticker          TEXT UNIQUE NOT NULL,
            name            TEXT NOT NULL,
            sector          TEXT,
            industry        TEXT,
            market_cap_tier TEXT,
            exchange        TEXT,
            country         TEXT DEFAULT 'US',
            is_active       BOOLEAN DEFAULT TRUE,
            created_at      TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS sectors (
            id              SERIAL PRIMARY KEY,
            code            TEXT UNIQUE NOT NULL,
            name            TEXT NOT NULL,
            etf_ticker      TEXT,
            description     TEXT,
            is_active       BOOLEAN DEFAULT TRUE
        )
    """)

    # ──────────────────────────────────────────────
    # RAW TIME-SERIES (staging)
    # ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS macro_observations_raw (
            series_id   TEXT NOT NULL REFERENCES macro_series(series_id),
            date        DATE NOT NULL,
            value       NUMERIC NOT NULL,
            source      TEXT NOT NULL,
            fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            run_id      TEXT,
            PRIMARY KEY (series_id, date)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS prices_raw (
            ticker      TEXT NOT NULL,
            date        DATE NOT NULL,
            open        NUMERIC,
            high        NUMERIC,
            low         NUMERIC,
            close       NUMERIC NOT NULL,
            adj_close   NUMERIC NOT NULL,
            volume      BIGINT,
            source      TEXT NOT NULL DEFAULT 'yfinance',
            fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            run_id      TEXT,
            PRIMARY KEY (ticker, date)
        )
    """)

    # ──────────────────────────────────────────────
    # PRODUCTION TIME-SERIES (hypertables)
    # ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS macro_observations (
            series_id   TEXT NOT NULL REFERENCES macro_series(series_id),
            date        DATE NOT NULL,
            value       NUMERIC NOT NULL,
            source      TEXT NOT NULL,
            fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            run_id      TEXT,
            PRIMARY KEY (series_id, date)
        )
    """)
    op.execute("SELECT create_hypertable('macro_observations', 'date', if_not_exists => TRUE)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            ticker      TEXT NOT NULL,
            date        DATE NOT NULL,
            open        NUMERIC,
            high        NUMERIC,
            low         NUMERIC,
            close       NUMERIC NOT NULL,
            adj_close   NUMERIC NOT NULL,
            volume      BIGINT,
            source      TEXT NOT NULL DEFAULT 'yfinance',
            fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            run_id      TEXT,
            PRIMARY KEY (ticker, date)
        )
    """)
    op.execute("SELECT create_hypertable('prices', 'date', if_not_exists => TRUE)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS financial_metrics (
            ticker          TEXT NOT NULL,
            period_end      DATE NOT NULL,
            period_type     TEXT NOT NULL DEFAULT 'annual',
            revenue         NUMERIC,
            net_income      NUMERIC,
            eps             NUMERIC,
            pe_ratio        NUMERIC,
            pb_ratio        NUMERIC,
            roe             NUMERIC,
            debt_to_equity  NUMERIC,
            free_cash_flow  NUMERIC,
            source          TEXT NOT NULL DEFAULT 'yfinance',
            fetched_at      TIMESTAMPTZ DEFAULT now(),
            run_id          TEXT,
            PRIMARY KEY (ticker, period_end, period_type)
        )
    """)

    # ──────────────────────────────────────────────
    # COMPUTED ANALYTICS (marts)
    # ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS macro_features (
            series_id           TEXT NOT NULL,
            date                DATE NOT NULL,
            value_mom_1m        NUMERIC,
            value_mom_3m        NUMERIC,
            value_yoy           NUMERIC,
            z_score_2y          NUMERIC,
            z_score_5y          NUMERIC,
            trend               TEXT,
            scoring_version     TEXT,
            computed_at         TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (series_id, date)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS market_regimes (
            date                DATE PRIMARY KEY,
            quadrant            TEXT NOT NULL,
            growth_momentum     NUMERIC,
            inflation_momentum  NUMERIC,
            fca_score           NUMERIC,
            policy_stance       TEXT,
            confidence          NUMERIC,
            scoring_version     TEXT,
            computed_at         TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS sector_scores (
            ticker              TEXT NOT NULL,
            date                DATE NOT NULL,
            horizon             TEXT NOT NULL DEFAULT 'tactical_50d',
            rs_ratio            NUMERIC,
            rs_momentum         NUMERIC,
            rrg_quadrant        TEXT,
            composite_score     NUMERIC,
            rank                INTEGER,
            scoring_version     TEXT,
            computed_at         TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (ticker, date, horizon)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS etf_scores (
            ticker              TEXT NOT NULL,
            date                DATE NOT NULL,
            momentum_1m         NUMERIC,
            momentum_3m         NUMERIC,
            momentum_6m         NUMERIC,
            momentum_12m        NUMERIC,
            sharpe_1y           NUMERIC,
            volatility_1y       NUMERIC,
            max_drawdown_1y     NUMERIC,
            composite_score     NUMERIC,
            rank_overall        INTEGER,
            rank_category       INTEGER,
            scoring_version     TEXT,
            computed_at         TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (ticker, date)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS stock_scores (
            ticker              TEXT NOT NULL,
            date                DATE NOT NULL,
            momentum_score      NUMERIC,
            trend_score         NUMERIC,
            quality_score       NUMERIC,
            value_score         NUMERIC,
            composite_score     NUMERIC,
            rank_overall        INTEGER,
            rank_sector         INTEGER,
            classification      TEXT,
            scoring_version     TEXT,
            computed_at         TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (ticker, date)
        )
    """)

    # ──────────────────────────────────────────────
    # PIPELINE OBSERVABILITY
    # ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id          TEXT PRIMARY KEY,
            dag_id          TEXT NOT NULL,
            task_id         TEXT,
            started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at    TIMESTAMPTZ,
            status          TEXT DEFAULT 'running',
            rows_ingested   INTEGER DEFAULT 0,
            rows_failed     INTEGER DEFAULT 0,
            error_message   TEXT
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS data_quality_checks (
            id              SERIAL PRIMARY KEY,
            run_id          TEXT REFERENCES pipeline_runs(run_id),
            check_name      TEXT NOT NULL,
            entity          TEXT,
            passed          BOOLEAN NOT NULL,
            metric          NUMERIC,
            threshold       NUMERIC,
            message         TEXT,
            checked_at      TIMESTAMPTZ DEFAULT now()
        )
    """)

    # Useful indexes
    op.execute("CREATE INDEX IF NOT EXISTS idx_prices_ticker ON prices(ticker)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_macro_obs_series ON macro_observations(series_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sector_scores_date ON sector_scores(date)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_etf_scores_date ON etf_scores(date)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_stock_scores_date ON stock_scores(date)")


def downgrade() -> None:
    tables = [
        "data_quality_checks", "pipeline_runs",
        "stock_scores", "etf_scores", "sector_scores",
        "market_regimes", "macro_features",
        "financial_metrics", "prices", "prices_raw",
        "macro_observations", "macro_observations_raw",
        "sectors", "stocks", "etfs", "macro_series",
    ]
    for t in tables:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
