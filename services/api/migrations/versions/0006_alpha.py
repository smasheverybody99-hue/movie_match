"""The closed alpha (Phase 5): events, "this recommendation was wrong", the tester flag,
the data notice, and sensitive films.

events: what testers do, for the alpha's metrics (app/pipelines/metrics.py). `props`
holds only enumerated values, never text a user typed (app/services/events.py).

recommendation_feedback: one row per user and film, the latest press of "wrong" and its
optional reason.

users.alpha_tester: the metrics count only flagged users (user decision, 2026-11-17).
users.data_notice_accepted_at: when the user accepted the free-tier data notice (ADR 0004,
exception of 2026-11-17).

movies.sensitive: explicit or extreme films, kept out of every list (TZ backlog, NSFW).

Every change only adds: the code before it runs unchanged on the new schema, so this can
be applied before the code that uses it is deployed.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column(
            "movie_id",
            sa.BigInteger(),
            sa.ForeignKey("movies.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("source", sa.String(30), nullable=True),
        sa.Column(
            "props", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_events_user_occurred", "events", ["user_id", "occurred_at"])
    op.create_index("ix_events_type_occurred", "events", ["type", "occurred_at"])

    op.create_table(
        "recommendation_feedback",
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
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("reason", sa.String(20), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.add_column(
        "users",
        sa.Column("alpha_tester", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "users", sa.Column("data_notice_accepted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "movies",
        sa.Column("sensitive", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("movies", "sensitive")
    op.drop_column("users", "data_notice_accepted_at")
    op.drop_column("users", "alpha_tester")
    op.drop_table("recommendation_feedback")
    op.drop_index("ix_events_type_occurred", table_name="events")
    op.drop_index("ix_events_user_occurred", table_name="events")
    op.drop_table("events")
