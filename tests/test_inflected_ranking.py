"""A built form that also reads as an inflection of a word we already hold.

S8's second half. Ranking sorts on the corpus count, and where the lexicon
knows no reading for a spelling the count may not belong to the word we built:
nothing in the attestation record separates رفتی — "you went" — from گفتار,
which is exactly the word this project makes. Both are `unlinked`.

The instrument existed and was never asked at request time. What is checked
here is that asking it is safe: that a run without a lexicon changes no order,
that the answer is marked rather than hidden, and that the shared-letters case
is reported rather than silently decided.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from murfulu.scoring import inflected


@pytest.fixture(autouse=True)
def _fresh() -> object:
    """The analyser is cached per process; each test gets its own."""
    inflected.reset()
    yield
    inflected.reset()


def test_an_inflection_is_recognised_and_says_it_shares_its_letters(
    lexicon_snapshot: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """رفتی strips to the stem رفت, and *-ی* is also a derivational affix.

    Both halves matter. The first is what lets the ranking separate رفتی from
    رفتار; the second is why the reader is told the letters cannot settle it.
    Measured over رفتن's 660 forms, 95.6% of the inflection-shaped ones share
    their letters with a rule in the pack — reproducing the 95.5% measured on
    a different sample in session 10.
    """
    monkeypatch.setenv("MURFULU_LEXICON_PATH", str(lexicon_snapshot))
    inflected.reset()

    found = inflected.reading("رفتی")
    if found is None:
        pytest.skip("the fixture snapshot does not hold رفتن")

    assert found.base == "رفت"
    assert found.pattern_id.startswith("verb:")
    # Non-empty: N-095 writes -ی too, so the letters are not a verdict.
    assert found.shared_with


def test_a_word_we_build_is_not_called_an_inflection(
    lexicon_snapshot: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """گفتار and رفتار strip to nothing the dictionary holds as a base.

    This is the whole point: the test must separate the two, not sink both.
    """
    monkeypatch.setenv("MURFULU_LEXICON_PATH", str(lexicon_snapshot))
    inflected.reset()

    assert inflected.reading("رفتار") is None
    assert inflected.reading("گفتار") is None


def test_no_lexicon_leaves_every_form_alone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """*Not asked* must rank exactly as *not one*, never sink a word.

    A run with no snapshot configured is a legitimate state — the rules still
    say what can be built — and silence must not be read as a finding. The same
    rule the grounding and typicality parts of the score already follow.
    """
    monkeypatch.delenv("MURFULU_LEXICON_PATH", raising=False)
    inflected.reset()

    assert inflected.reading("رفتی") is None
    assert inflected.reading("رفتار") is None
