"""Migration round-trip.

A migration that cannot be undone is a migration you cannot deploy safely.
This runs upgrade to head, then downgrade to base, against a throwaway
database. Skipped when TEST_DATABASE_URL is not set.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config

from tests.conftest import TEST_DATABASE_URL, requires_db

API_ROOT = Path(__file__).resolve().parents[1]


def _alembic_config(database_url: str = "") -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_migration_scripts_are_discoverable() -> None:
    """Runs without a database: catches a broken revision chain."""
    from alembic.script import ScriptDirectory

    scripts = ScriptDirectory.from_config(_alembic_config())
    revisions = list(scripts.walk_revisions())
    assert revisions, "no migration revisions found"
    assert scripts.get_current_head() is not None


@requires_db
def test_upgrade_then_downgrade() -> None:
    assert TEST_DATABASE_URL, "guarded by requires_db"
    config = _alembic_config(TEST_DATABASE_URL)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
