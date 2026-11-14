"""How sure a measured share of right answers is: an exact one-sided bound.

A test set where the model was right ``k`` times in ``n`` says the accuracy is
about k/n — but a small set can be lucky. The **lower confidence bound** at
level ``alpha`` is the smallest accuracy that would still produce ``k`` or
more right answers with probability at least ``alpha``: with ``alpha = 0.05``,
"we are 95 % sure the accuracy is at least this". It is the exact
Clopper–Pearson bound, computed from the binomial distribution itself rather
than a normal approximation, because near 100 % the approximation fails.

Read as a test: the hypothesis "accuracy ≤ target" is rejected at level
``alpha`` exactly when the bound lies above the target.

**Why 100 % can never be shown.** With every one of ``n`` answers right the
bound is ``alpha ** (1/n)``: 300 right out of 300 proves only 99.0 %, 3,000
out of 3,000 only 99.9 %.
"""

from __future__ import annotations

import math


def upper_tail(k: int, n: int, p: float) -> float:
    """P(X ≥ k) for X binomial with n trials and success probability p."""
    if k <= 0:
        return 1.0
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    log_p, log_q = math.log(p), math.log1p(-p)
    terms = [
        math.lgamma(n + 1)
        - math.lgamma(i + 1)
        - math.lgamma(n - i + 1)
        + i * log_p
        + (n - i) * log_q
        for i in range(k, n + 1)
    ]
    top = max(terms)
    return min(1.0, math.exp(top) * sum(math.exp(t - top) for t in terms))


def lower_bound(k: int, n: int, alpha: float = 0.05) -> float:
    """The exact one-sided lower confidence bound of an accuracy k/n."""
    if n <= 0 or k <= 0:
        return 0.0
    if k == n:
        return float(alpha ** (1 / n))
    low, high = 0.0, k / n
    for _ in range(100):
        middle = (low + high) / 2
        if upper_tail(k, n, middle) < alpha:
            low = middle
        else:
            high = middle
    return low


def needed_without_error(target: float, alpha: float = 0.05) -> int:
    """How many right answers in a row prove ``target`` at level ``alpha``."""
    return math.ceil(math.log(alpha) / math.log(target))


def cluster_lower_bound(
    groups: list[tuple[int, int]],
    alpha: float = 0.05,
    draws: int = 20_000,
    seed: int = 7,
) -> float:
    """A lower bound when right answers come in groups that hang together.

    Each group is (right, total) for one unit that was sampled as a whole —
    a poet, whose words share a style and an edition. The poets are drawn
    again with replacement ``draws`` times (a cluster bootstrap) and the
    accuracy's ``alpha`` quantile returned. Wider than :func:`lower_bound`
    when the poets differ, as it should be: treating 1,500 words of 33 poets as
    1,500 independent answers overstates the certainty (the review of
    2026-11-14). Approximate with few groups; the seed makes it repeatable.
    """
    import random

    if not groups:
        return 0.0
    rng = random.Random(seed)
    m = len(groups)
    shares = []
    for _ in range(draws):
        right = total = 0
        for _ in range(m):
            k, n = groups[rng.randrange(m)]
            right += k
            total += n
        shares.append(right / total if total else 0.0)
    shares.sort()
    drawn = shares[min(len(shares) - 1, int(alpha * draws))]
    # Never more certain than the same answers taken one by one: clustering
    # only widens a bound. This also stops a sample without a single error
    # from "proving" 100 % (the review of 2026-11-14).
    right = sum(k for k, _ in groups)
    total = sum(n for _, n in groups)
    return min(drawn, lower_bound(right, total, alpha))
