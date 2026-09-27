"""Genres take turns in the onboarding list."""

from app.services.onboarding import interleave


def test_turns_repeats_and_limit() -> None:
    drama, comedy, horror = [1, 2, 3], [4, 1, 5], [6]
    assert interleave([drama, comedy, horror], 100) == [1, 4, 6, 2, 3, 5]
    assert interleave([drama, comedy, horror], 3) == [1, 4, 6]
    assert interleave([], 5) == []
