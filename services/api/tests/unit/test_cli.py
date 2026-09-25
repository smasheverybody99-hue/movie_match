"""Id lists for hand-picked runs, and console output that survives any title."""

import io
import sys
from pathlib import Path

import pytest

from app.pipelines.cli import read_ids, utf8_console

REVIEW_LIST = Path(__file__).resolve().parents[4] / "docs" / "review-films.md"


def test_ids_from_the_command_line() -> None:
    assert read_ids("550,680 13") == [550, 680, 13]


def test_repeats_are_dropped_order_kept() -> None:
    assert read_ids("13, 550, 13") == [13, 550]


def test_ids_from_a_markdown_table(tmp_path: Path) -> None:
    listing = tmp_path / "films.md"
    listing.write_text(
        "# Films\n\nSome prose with 1999 in it.\n\n"
        "| TMDB id | Title |\n|---:|---|\n| 550 | Fight Club |\n|  680 | Pulp Fiction |\n",
        encoding="utf-8",
    )
    assert read_ids(str(listing)) == [550, 680]


def test_garbage_is_rejected() -> None:
    with pytest.raises(ValueError, match="not a TMDB id"):
        read_ids("550, fight-club")


def test_empty_list_is_rejected(tmp_path: Path) -> None:
    listing = tmp_path / "empty.md"
    listing.write_text("# nothing here\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no TMDB ids"):
        read_ids(str(listing))


def test_the_committed_review_list_has_50_distinct_films() -> None:
    """Guards docs/review-films.md: an edit that breaks the table breaks stage 1."""
    assert len(read_ids(str(REVIEW_LIST))) == 50


def test_console_is_switched_to_utf8(monkeypatch: pytest.MonkeyPatch) -> None:
    """A cp1251 console cannot encode "Amélie"; the report used to crash on it."""
    fake = io.TextIOWrapper(io.BytesIO(), encoding="cp1251")
    monkeypatch.setattr(sys, "stdout", fake)
    monkeypatch.setattr(sys, "stderr", fake)
    utf8_console()
    print("Amélie, Léon, Pan's Labyrinth")
    sys.stdout.flush()
    assert fake.buffer.getvalue().decode("utf-8").startswith("Amélie")
