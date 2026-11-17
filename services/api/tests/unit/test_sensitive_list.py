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
