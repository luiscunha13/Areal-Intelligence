"""
Alembic migration: 0002_etf_holdings
Adds etf_holdings table for storing ETF constituent data.
Run: alembic upgrade head
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS etf_holdings (
            etf_ticker   TEXT NOT NULL,
            holding_date DATE NOT NULL,
            rank         INTEGER,
            symbol       TEXT NOT NULL,
            name         TEXT,
            weight_pct   NUMERIC(8, 4),
            PRIMARY KEY (etf_ticker, holding_date, symbol)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_etf_holdings_ticker
        ON etf_holdings (etf_ticker, holding_date DESC)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS etf_holdings CASCADE")
