"""SQLAlchemy models.

User identity comes from Supabase Auth; `users.id` is the Supabase user UUID.
Trait vectors are stored twice on purpose: as JSONB for readability and debugging,
and as a pgvector column for fast similarity search.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.traits import TRAIT_COUNT

EMBEDDING_DIM = 1536


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # TMDB id
    title: Mapped[str] = mapped_column(String(500), index=True)
    original_title: Mapped[str | None] = mapped_column(String(500))
    overview: Mapped[str | None] = mapped_column(Text)
    release_date: Mapped[date | None] = mapped_column(Date)
    runtime_minutes: Mapped[int | None] = mapped_column(Integer)
    original_language: Mapped[str | None] = mapped_column(String(10))
    poster_path: Mapped[str | None] = mapped_column(String(255))
    backdrop_path: Mapped[str | None] = mapped_column(String(255))
    tmdb_vote_average: Mapped[float | None] = mapped_column(Float)
    tmdb_vote_count: Mapped[int | None] = mapped_column(Integer)
    popularity: Mapped[float | None] = mapped_column(Float)
    adult: Mapped[bool] = mapped_column(Boolean, default=False)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    traits: Mapped[MovieTraits | None] = relationship(back_populates="movie", uselist=False)
    credits: Mapped[list[Credit]] = relationship(back_populates="movie")

    __table_args__ = (Index("ix_movies_popularity", "popularity"),)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class MovieGenre(Base):
    __tablename__ = "movie_genres"

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True
    )


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # TMDB id
    name: Mapped[str] = mapped_column(String(200))


class MovieKeyword(Base):
    __tablename__ = "movie_keywords"

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    keyword_id: Mapped[int] = mapped_column(
        ForeignKey("keywords.id", ondelete="CASCADE"), primary_key=True
    )


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # TMDB id
    name: Mapped[str] = mapped_column(String(300), index=True)
    profile_path: Mapped[str | None] = mapped_column(String(255))


class Credit(Base):
    """Cast and crew. `character_name` is the seed for Character Match."""

    __tablename__ = "credits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), index=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), index=True)
    department: Mapped[str] = mapped_column(String(50))  # "cast" | "directing" | ...
    job: Mapped[str | None] = mapped_column(String(100))
    character_name: Mapped[str | None] = mapped_column(String(300))
    billing_order: Mapped[int | None] = mapped_column(SmallInteger)

    movie: Mapped[Movie] = relationship(back_populates="credits")


class MovieTraits(Base):
    """The Movie DNA vector, produced by the trait pipeline."""

    __tablename__ = "movie_traits"

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    scores: Mapped[dict] = mapped_column(JSONB)  # {trait_key: 0..100}
    vector: Mapped[list[float]] = mapped_column(Vector(TRAIT_COUNT))
    summary: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(100))
    spec_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    movie: Mapped[Movie] = relationship(back_populates="traits")


class MovieEmbedding(Base):
    __tablename__ = "movie_embeddings"

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    model: Mapped[str] = mapped_column(String(100))


class SyncRun(Base):
    """One ingestion run. `planned_ids` + `cursor` make a dead run resumable.

    The plan is stored rather than recomputed because TMDB popularity changes daily:
    re-running the selection after a crash would pick a different catalogue.
    """

    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(50))  # "catalogue"
    status: Mapped[str] = mapped_column(String(20))  # running | finished | failed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    planned_ids: Mapped[list] = mapped_column(JSONB)
    cursor: Mapped[int] = mapped_column(Integer, default=0)  # index into planned_ids
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)  # e.g. 404 from TMDB
    last_processed_id: Mapped[int | None] = mapped_column(BigInteger)
    error: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_sync_runs_kind_status", "kind", "status"),)


class TraitBatch(Base):
    """An Anthropic message batch submitted by the trait pipeline."""

    __tablename__ = "trait_batches"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # Anthropic batch id
    movie_ids: Mapped[list] = mapped_column(JSONB)
    model: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))  # submitted | collected
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TraitFailure(Base):
    """A film whose trait extraction failed. Retried once; at 2 attempts it is failed.

    A failed film gets no MovieTraits row at all - never one filled with defaults.
    """

    __tablename__ = "trait_failures"

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    attempts: Mapped[int] = mapped_column(SmallInteger, default=1)
    last_error: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base):
    """Mirror of the Supabase auth user, plus product state."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(120))
    onboarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    taste_vector: Mapped[list[float] | None] = mapped_column(Vector(TRAIT_COUNT))
    taste_weights: Mapped[dict | None] = mapped_column(JSONB)
    taste_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), index=True)
    score: Mapped[float] = mapped_column(Float)  # 0.5 .. 10.0
    liked_aspects: Mapped[list | None] = mapped_column(JSONB)  # trait keys the user picked
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "movie_id", name="uq_rating_user_movie"),)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"))
    watched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "movie_id", name="uq_watchlist_user_movie"),)


class Explanation(Base):
    """Cached 'why you'll like this' text. Never generate one that already exists."""

    __tablename__ = "explanations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    text: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
