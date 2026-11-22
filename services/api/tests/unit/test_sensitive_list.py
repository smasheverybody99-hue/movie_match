"""Which films the NSFW command names (app/pipelines/sensitive.py), without a database."""

from app.pipelines.sensitive import HAND_LIST, refused


def test_only_googles_prohibited_content_refusal_counts() -> None:
    errors = [
        (1, "no candidates (prompt blocked: BlockedReason.PROHIBITED_CONTENT)"),
        (2, "finish_reason=SAFETY"),
        (3, "timeout"),
        (4, ""),
    ]
    assert refused(errors) == {1}


def test_the_hand_list_is_the_testers_three() -> None:
    # Tester, 2026-10-13; ids from TMDB's search on 2026-11-17.
    assert HAND_LIST == {
        3134: "Baise-moi (2000)",
        9453: "Caligula (1979)",
        979: "Irreversible (2002)",
    }


async def test_the_command_lists_and_skips_without_writing(monkeypatch, capsys) -> None:
    """Without --apply nothing is written; --skip leaves films out of what would be marked."""
    from contextlib import asynccontextmanager

    from app.pipelines import sensitive

    async def fake_candidates(_session):
        return [(670, "Oldboy", False), (979, "Irreversible", False), (3134, "Baise-moi", True)]

    @asynccontextmanager
    async def fake_session():
        yield object()

    async def no_mark(_session, _ids):
        raise AssertionError("wrote without --apply")

    monkeypatch.setattr(sensitive, "candidates", fake_candidates)
    monkeypatch.setattr(sensitive, "job_session", fake_session)
    monkeypatch.setattr(sensitive, "mark", no_mark)
    await sensitive.main(["--skip", "670"])
    out = capsys.readouterr().out
    assert "670  Oldboy  (skipped)" in out
    assert "3134  Baise-moi  (already marked)" in out
    assert "1 to mark; nothing written (add --apply)" in out
    assert "hand list, not in the catalogue: 9453" in out
