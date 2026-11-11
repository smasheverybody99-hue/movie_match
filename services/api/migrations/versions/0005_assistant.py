"""assistant_turns and assistant_usage (Phase 4, FR-8).

assistant_turns: the last few exchanges per user, the assistant's context. Pruned to the
newest five on every write (services/assistant.py).

assistant_usage: messages per user per UTC day, for `assistant_daily_calls_per_user`.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assistant_turns",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column(
            "movie_ids", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_assistant_turns_user_id", "assistant_turns", ["user_id"])
    op.create_table(
        "assistant_usage",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("calls", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_table("assistant_usage")
    op.drop_index("ix_assistant_turns_user_id", table_name="assistant_turns")
    op.drop_table("assistant_turns")
