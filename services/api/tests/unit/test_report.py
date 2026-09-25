"""The quality report shows every trait for every film, in vector order."""

from app.pipelines.report import TITLE_WIDTH, format_report
from app.traits import TRAIT_KEYS

SCORES = {key: float(i * 7) for i, key in enumerate(TRAIT_KEYS)}


def test_one_row_per_film_with_every_score() -> None:
    lines = format_report([(550, "Fight Club", 1999, SCORES)]).splitlines()
    row = lines[1]
    assert row.split()[:4] == ["550", "Fight", "Club", "1999"]
    assert row.split()[-len(TRAIT_KEYS) :] == [str(i * 7) for i in range(len(TRAIT_KEYS))]


def test_header_columns_follow_trait_order() -> None:
    header = format_report([]).splitlines()[0].split()
    assert header[:3] == ["id", "title", "year"]
    assert header[3:] == [
        "psy_com",
        "plo_twi",
        "mys",
        "cha_dep",
        "emo_int",
        "pac",
        "hum",
        "rom",
        "act",
        "vio",
        "vis_sty",
        "rea",
        "dar",
        "end_amb",
    ]


def test_legend_spells_out_every_abbreviation() -> None:
    legend = format_report([]).splitlines()[-1]
    for key in TRAIT_KEYS:
        assert f"={key}" in legend


def test_film_without_traits_is_listed_not_dropped() -> None:
    assert "(no traits yet)" in format_report([(1, "Pending", None, None)])


def test_long_titles_are_truncated_to_keep_columns_aligned() -> None:
    long_title = "A" * (TITLE_WIDTH + 10)
    row = format_report([(1, long_title, 2001, SCORES)]).splitlines()[1]
    assert "…" in row
    assert long_title not in row
