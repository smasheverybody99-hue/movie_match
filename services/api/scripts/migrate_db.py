"""Upgrade one database to Alembic head, and prove the upgrade was saved.

Usage, from services/api:

    python -m scripts.migrate_db test    # TEST_DATABASE_URL (Frankfurt)
    python -m scripts.migrate_db main    # DATABASE_URL (Singapore, the real catalogue)

An ops tool, run by hand; the application never imports it. It uses the migration
scripts in migrations/ unchanged and adds guards around them.

Why the guards exist. On 2026-09-29 the first attempt to upgrade the main database
(0002 -> 0004) printed its migration steps and exited 0, but nothing was saved:

* lock_timeout, passed as an asyncpg connection setting, never reached the session:
  the Supavisor pooler drops it, and SHOW lock_timeout returned 0.
* the SHOW itself auto-began a transaction; Alembic took it for the caller's and did
  not COMMIT; closing the connection rolled everything back.

A silent success is worse than a loud failure, so this script:

1. sets lock_timeout with SET on the session and stops unless SHOW returns 5s, both
   before and inside the migration transaction (exit 2);
2. ends the auto-begun transaction, so Alembic begins and commits its own, and stops if
   a transaction is still open afterwards (exit 7);
3. after COMMIT, reads alembic_version on a brand-new connection and fails unless it is
   head (exit 3);
4. checks the schema objects of 0003-0004 (exit 4);
5. main only: refuses to run unless ratings, explanations and users are empty and no
   other session holds locks on movies or sits idle in a transaction (exit 5), and
   compares count(movies) before and after (exit 6).

Tested by hand on 2026-09-29, not yet by automated tests (backlog, docs/TZ.md §2):
the Frankfurt test DB from 0002 to head (exit 0); then a copy with the COMMIT removed
and check 7 disabled, to reproduce the bug: it printed the migration steps, the new
connection saw 0002, and it exited 3; then the main DB from 0002 to head (exit 0,
movies 5000 -> 5000).

Exit codes: 0 ok · 2 lock_timeout not in effect · 3 head not visible from a new
connection after commit · 4 schema check failed · 5 main-DB precondition failed ·
6 movies count changed · 7 transaction still open after Alembic.
"""

import asyncio
import logging
import sys
from typing import NoReturn

import asyncpg
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

import app.models  # noqa: F401  (registers tables on Base.metadata)
from app.config import Settings
from app.db import Base

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

TARGET = sys.argv[1]
settings = Settings()
if TARGET == "test":
    URL = settings.test_database_url
    assert "eu-central-1" in URL and "bixarelbydwinmfhmaka" in URL, "not the Frankfurt test DB"
elif TARGET == "main":
    URL = settings.database_url
    assert "ap-southeast-1" in URL and "pzuwzispquuxemqdjcjr" in URL, "not the Singapore main DB"
else:
    sys.exit("target must be test or main")
DSN = URL.replace("postgresql+asyncpg://", "postgresql://", 1)

cfg = Config("alembic.ini")
script = ScriptDirectory.from_config(cfg)
HEAD = script.get_current_head()


def fail(code: int, message: str) -> NoReturn:
    print(f"FAIL ({code}): {message}")
    sys.exit(code)


async def read_only(query: str):
    conn = await asyncpg.connect(DSN)
    try:
        async with conn.transaction(readonly=True):
            return await conn.fetchval(query)
    finally:
        await conn.close()


async def preconditions() -> int:
    """Main DB only: nothing to lose and nobody writing movies. Returns count(movies)."""
    conn = await asyncpg.connect(DSN)
    try:
        async with conn.transaction(readonly=True):
            for table in ("ratings", "explanations", "users"):
                n = await conn.fetchval(f"SELECT count(*) FROM {table}")
                print(f"precheck count({table}) = {n}")
                if n != 0:
                    fail(5, f"{table} is not empty")
            locks = await conn.fetchval(
                "SELECT count(*) FROM pg_locks WHERE relation = 'public.movies'::regclass"
                " AND pid <> pg_backend_pid()"
            )
            idle_tx = await conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                " AND state LIKE 'idle in transaction%'"
            )
            print(f"precheck locks on movies by others = {locks}, idle in transaction = {idle_tx}")
            if locks or idle_tx:
                fail(5, "another session holds locks on movies or is idle in a transaction")
            return await conn.fetchval("SELECT count(*) FROM movies")
    finally:
        await conn.close()


def migrate(sync_conn) -> None:
    sync_conn.exec_driver_sql("SET lock_timeout = '5s'")
    shown = sync_conn.execute(text("SHOW lock_timeout")).scalar()
    print(f"SHOW lock_timeout (session) = {shown}")
    if shown != "5s":
        fail(2, f"lock_timeout is {shown!r}, not '5s'")
    # End the transaction that SET/SHOW autobegan, so Alembic begins and commits its own.
    sync_conn.commit()

    def upgrade(rev, context):
        return script._upgrade_revs("head", rev)

    with EnvironmentContext(cfg, script, fn=upgrade, destination_rev="head") as env:
        env.configure(connection=sync_conn, target_metadata=Base.metadata)
        with env.begin_transaction():
            shown = sync_conn.execute(text("SHOW lock_timeout")).scalar()
            print(f"SHOW lock_timeout (inside the migration transaction) = {shown}")
            if shown != "5s":
                fail(2, f"lock_timeout is {shown!r} inside the transaction")
            env.run_migrations()
    if sync_conn.in_transaction():
        fail(7, "a transaction is still open after Alembic: nothing would be committed")


async def main() -> None:
    print(f"target = {TARGET}, head = {HEAD}")
    print("alembic_version before =", await read_only("SELECT version_num FROM alembic_version"))
    movies_before = await preconditions() if TARGET == "main" else None
    if movies_before is not None:
        print(f"count(movies) before = {movies_before}")

    engine = create_async_engine(URL, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            await conn.run_sync(migrate)
    finally:
        await engine.dispose()

    # The check that catches "exit 0 but nothing saved": a brand-new connection.
    after = await read_only("SELECT version_num FROM alembic_version")
    print(f"alembic_version after (new connection) = {after}")
    if after != HEAD:
        fail(3, f"alembic_version is {after!r}, expected {HEAD!r}")

    checks = {
        "ratings.updated_at exists": "SELECT count(*) = 1 FROM information_schema.columns"
        " WHERE table_schema='public' AND table_name='ratings' AND column_name='updated_at'",
        "ratings.updated_at has no NULL": "SELECT count(*) = 0 FROM ratings"
        " WHERE updated_at IS NULL",
        "explanations.lang exists": "SELECT count(*) = 1 FROM information_schema.columns"
        " WHERE table_schema='public' AND table_name='explanations' AND column_name='lang'",
        "explanations PK is (user_id, movie_id, lang)": "SELECT pg_get_constraintdef(oid) ="
        " 'PRIMARY KEY (user_id, movie_id, lang)' FROM pg_constraint"
        " WHERE conrelid='public.explanations'::regclass AND contype='p'",
        "dismissals exists": "SELECT to_regclass('public.dismissals') IS NOT NULL",
    }
    for name, query in checks.items():
        ok = await read_only(query)
        print(f"check {name}: {ok}")
        if ok is not True:
            fail(4, name)

    if movies_before is not None:
        movies_after = await read_only("SELECT count(*) FROM movies")
        print(f"count(movies) after = {movies_after} (before {movies_before})")
        if movies_after != movies_before:
            fail(6, "movies count changed")
    print("OK")


asyncio.run(main())
