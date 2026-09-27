"""Maximal Marginal Relevance: pick a list that is relevant but not repetitive.

Each step takes the candidate with the highest

    lambda * relevance(c) - (1 - lambda) * max(similarity(c, s) for s already picked)

so a near-duplicate of a film already picked loses to a slightly less relevant film that
is different. Relevance and similarity are both expected on a 0..1 scale.

Generic on purpose: the recommendation service decides what relevance is (match / 100)
and what similarity is (embedding cosine similarity between two films).
"""

from collections.abc import Callable, Sequence

DEFAULT_LAMBDA = 0.7


def mmr[T](
    candidates: Sequence[T],
    relevance: Callable[[T], float],
    similarity: Callable[[T, T], float],
    k: int,
    lambda_: float = DEFAULT_LAMBDA,
    admissible: Callable[[T, Sequence[T]], bool] | None = None,
) -> list[T]:
    """Up to `k` candidates in pick order. Ties go to the earlier candidate.

    `admissible(candidate, picked)` can veto a candidate given what is already picked
    (the director cap uses it); a vetoed candidate is skipped at that step and may be
    admissible later only if the rule allows it.

    Each candidate's redundancy is updated only against the newest pick, so the cost is
    O(k · n) similarity calls rather than O(k² · n).
    """
    if not 0.0 <= lambda_ <= 1.0:
        raise ValueError(f"lambda must be in [0, 1], got {lambda_}")
    remaining = list(range(len(candidates)))
    scores = [relevance(c) for c in candidates]
    redundancy = [0.0] * len(candidates)
    picked: list[T] = []
    while remaining and len(picked) < k:
        best: int | None = None
        best_value = -float("inf")
        for index in remaining:
            if admissible is not None and not admissible(candidates[index], picked):
                continue
            value = lambda_ * scores[index] - (1.0 - lambda_) * redundancy[index]
            if value > best_value:
                best, best_value = index, value
        if best is None:
            break
        remaining.remove(best)
        chosen = candidates[best]
        picked.append(chosen)
        for index in remaining:
            redundancy[index] = max(redundancy[index], similarity(candidates[index], chosen))
    return picked
