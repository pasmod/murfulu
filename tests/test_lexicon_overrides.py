"""Values this project holds instead of the lexicon's.

The working rule these implement: build what we believe is right now, record
it for karbon, settle it with the linguist afterwards. What is tested here is
mostly the machinery that stops an override quietly becoming a fork:

- an override whose recorded old value no longer matches is **refused**, not
  applied — karbon changed the value and nobody looked
- an addition is a second reading, never a replacement
- everything unconfirmed says so
"""

from __future__ import annotations

from pathlib import Path

import pytest

from murfulu.lexicon import overrides
from murfulu.lexicon.entries import Reading
from murfulu.lexicon.store import Lexicon

RULES = Path(__file__).resolve().parents[1] / "rules"


@pytest.fixture
def held() -> overrides.Overrides:
    return overrides.load(RULES)


def _reading(**fields: object) -> Reading:
    base = {
        "spelling_fa": "آزردن",
        "spelling_normalized": "آزردن",
        "latin": "āzordan",
        "lexicon_categories": ("مصدر",),
        "past_stem_fa": "آزرد",
        "present_stem_fa": "آزُر",
        "snapshot_id": "test",
    }
    return Reading(**{**base, **fields})


# -- the authored file --------------------------------------------------------


def test_every_override_says_why_and_what_it_replaced(held: overrides.Overrides):
    """An override nobody can review or undo is a fork, not a holding."""
    for one in held.corrections:
        assert one.why.strip()
        assert one.was.strip()
        assert one.source.strip()
    for one in held.additions:
        assert one.why.strip()
        assert one.source.strip()


def test_everything_is_marked_unconfirmed_until_the_linguist_rules(
    held: overrides.Overrides,
):
    """Nothing claims to be settled.

    karbon was built from the linguist's rules and hand-checked, so a
    difference may be his later correction.
    """
    assert held.unconfirmed == len(held)


def test_a_correction_outside_the_stem_fields_is_refused():
    with pytest.raises(overrides.OverrideError):
        overrides._correction(
            {
                "headword_fa": "x",
                "field": "latin",
                "value": "y",
                "was": "z",
                "source": "s",
                "why": "w",
            }
        )


def test_a_correction_with_no_reason_is_refused():
    with pytest.raises(overrides.OverrideError):
        overrides._correction(
            {"headword_fa": "x", "field": "present_stem_fa", "value": "y", "was": "z"}
        )


# -- applying ----------------------------------------------------------------


def test_a_matching_override_is_applied(held: overrides.Overrides):
    changed = overrides.apply_to(_reading(), held)
    assert changed.present_stem_fa == "آزار"
    # And nothing else moved.
    assert changed.past_stem_fa == "آزرد"
    assert changed.latin == "āzordan"


def test_an_override_on_a_moved_value_is_refused_not_applied(
    held: overrides.Overrides,
):
    """The one way this file could do damage.

    If the snapshot no longer says what the override recorded, karbon changed
    it — possibly the very correction we were waiting for — and silently
    overwriting that would fork the two for good.
    """
    moved = _reading(present_stem_fa="آزار")  # upstream already fixed it
    with pytest.raises(overrides.OverrideError) as refused:
        overrides.apply_to(moved, held)
    assert "upstream" in str(refused.value)


def test_a_reading_with_no_override_passes_through_untouched(
    held: overrides.Overrides,
):
    same = _reading(spelling_fa="گفتن", present_stem_fa="گو")
    assert overrides.apply_to(same, held) == same


# -- through the store, against the real snapshot -----------------------------


def _real() -> bool:
    import os

    return bool(os.environ.get("MURFULU_LEXICON_PATH"))


@pytest.mark.skipif(not _real(), reason="no lexicon snapshot configured")
def test_the_two_corrections_come_out_of_the_real_lexicon():
    with Lexicon.open() as lexicon:
        azordan = lexicon.by_spelling("آزردن")[0]
        assert azordan.present_stem_fa == "آزار"
        gosixtan = lexicon.by_spelling("گسیختن")[0]
        assert gosixtan.present_stem_fa == "گسل"


@pytest.mark.skipif(not _real(), reason="no lexicon snapshot configured")
def test_roftan_is_a_second_reading_and_raftan_is_untouched():
    """The document's رُفتن (to sweep) beside the lexicon's رفتن (to go).

    One spelling, two readings — the same shape as مرد. The lexicon's own
    reading must come back exactly as before, and the added one must be
    flagged, because nobody has ruled on it.
    """
    with Lexicon.open() as lexicon:
        found = lexicon.by_spelling("رفتن")
    by_latin = {reading.latin: reading for reading in found}
    assert "raftan" in by_latin and "roftan" in by_latin
    assert by_latin["raftan"].present_stem_fa == "رو"
    assert by_latin["raftan"].needs_review is False
    assert by_latin["roftan"].present_stem_fa == "روب"
    assert by_latin["roftan"].needs_review is True


@pytest.mark.skipif(not _real(), reason="no lexicon snapshot configured")
def test_an_addition_is_not_returned_for_other_spellings():
    with Lexicon.open() as lexicon:
        assert all(reading.latin != "roftan" for reading in lexicon.by_spelling("گفتن"))
