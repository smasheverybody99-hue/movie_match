"""Catalogue pipeline tables.

Keywords (the trait prompt and embedding text need them), resumable ingestion runs,
and trait-batch bookkeeping.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "keywords",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("name", sa.String(length=200), nullable=False),
    )
    op.create_table(
        "movie_keywords",
        sa.Column(
            "movie_id",
            sa.BigInteger(),
            sa.ForeignKey("movies.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "keyword_id",
            sa.BigInteger(),
            sa.ForeignKey("keywords.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "sync_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("planned_ids", postgresql.JSONB(), nullable=False),
        sa.Column("cursor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_processed_id", sa.BigInteger()),
        sa.Column("error", sa.Text()),
    )
    op.create_index("ix_sync_runs_kind_status", "sync_runs", ["kind", "status"])

    op.create_table(
        "trait_batches",
        sa.Column("id", sa.String(length=100), primary_key=True),
        sa.Column("movie_ids", postgresql.JSONB(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("collected_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "trait_failures",
        sa.Column(
            "movie_id",
            sa.BigInteger(),
            sa.ForeignKey("movies.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("attempts", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("last_error", sa.Text(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("trait_failures")
    op.drop_table("trait_batches")
    op.drop_index("ix_sync_runs_kind_status", table_name="sync_runs")
    op.drop_table("sync_runs")
    op.drop_table("movie_keywords")
    op.drop_table("keywords")
