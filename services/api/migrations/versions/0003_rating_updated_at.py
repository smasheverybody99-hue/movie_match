"""ratings.updated_at: when the score was last set.

The taste vector weighs recent ratings higher, and a re-rating is a fresh opinion, so
recency is read from here rather than from created_at. Existing rows take created_at.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ratings",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.execute("UPDATE ratings SET updated_at = created_at")


def downgrade() -> None:
    op.drop_column("ratings", "updated_at")
