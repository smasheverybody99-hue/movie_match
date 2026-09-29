"""dismissals, and a language on cached explanations.

dismissals: films a user has said "not for me" to. Recommendations exclude them (FR-5).

explanations.lang: the product ships in Uzbek and English (TZ section 5), so an
explanation is cached per (user, film, language). Without it, a user who switches
language would be served the cached text in the other one. Existing rows are Uzbek.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dismissals",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "movie_id",
            sa.BigInteger(),
            sa.ForeignKey("movies.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.add_column(
        "explanations",
        sa.Column("lang", sa.String(length=2), server_default="uz", nullable=False),
    )
    op.drop_constraint("explanations_pkey", "explanations", type_="primary")
    op.create_primary_key("explanations_pkey", "explanations", ["user_id", "movie_id", "lang"])


def downgrade() -> None:
    op.execute("DELETE FROM explanations WHERE lang <> 'uz'")
    op.drop_constraint("explanations_pkey", "explanations", type_="primary")
    op.create_primary_key("explanations_pkey", "explanations", ["user_id", "movie_id"])
    op.drop_column("explanations", "lang")
    op.drop_table("dismissals")
