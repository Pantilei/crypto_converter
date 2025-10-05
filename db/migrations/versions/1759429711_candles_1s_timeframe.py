"""
Candles 1s timeframe

Revision ID: baa5e36e9d93
Revises:
Create Date: 2025-10-02 21:28:31.591745

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "baa5e36e9d93"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "candles_1s",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("ticker", sa.String(100), nullable=False),
        sa.Column("t", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(38, 18), nullable=False),
        sa.Column("close", sa.Numeric(38, 18), nullable=False),
        sa.Column("high", sa.Numeric(38, 18), nullable=False),
        sa.Column("low", sa.Numeric(38, 18), nullable=False),
        sa.Column("volume", sa.Numeric(38, 18)),
    )
    op.create_index("idx__candles_1s__ticker__t", "candles_1s", ["ticker", "t"], unique=True)
    op.create_index("idx__candles_1s__t", "candles_1s",["t"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx__candles_1s__ticker__t", table_name="candles_1s")
    op.drop_index("idx__candles_1s__t", table_name="candles_1s")
    op.drop_table("candles_1s")
