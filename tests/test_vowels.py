"""The short vowels put on a Persian word from its Behnevis reading.

The project lead's decision of 2026-11-21: marks on the Persian words, made
from the reading so the two scripts agree, for display only. The rule of
which marks is ours and unconfirmed (FOR_THE_LINGUIST L48).
"""

from __future__ import annotations

import time

import pytest

from murfulu.behnevis.vowels import strip, vocalise


@pytest.mark.parametrize(
    ("spelling", "reading", "marked"),
    [
        # A short vowel after a letter: zabar, zir, pish.
        ("رفتار", "Raftār", "رَفتار"),
        ("گفتار", "Goftār", "گُفتار"),
        ("دانش", "Dāneš", "دانِش"),
        ("رونده", "ravande", "رَوَنده"),
        # Carried by ا or ع themselves.
        ("اندیشه", "andiše", "اَندیشه"),
        ("امروز", "emruz", "اِمروز"),
        ("علی", "Ali", "عَلی"),
        # The vowel of a joined word's ا is the ا's, not the letter before.
        ("هم‌اندیشنده", "hamandišande", "هَم‌اَندیشَنده"),
        # The diphthongs: the mark of the vowel the reading writes — a pish
        # before *ow*, a zir before *ey*, a zabar before *ay* (2026-11-22;
        # a zabar stood before all of them until then).
        ("نو", "now", "نُو"),
        ("دولت", "dowlat", "دُولَت"),
        ("پیوند", "peyvand", "پِیوَند"),
        ("کی", "key", "کِی"),
        ("کی", "Kay", "کَی"),
        # A doubled letter Behnevis writes twice.
        ("معلم", "moˈallem", "مُعَلِّم"),
        ("شدت", "šeddat", "شِدَّت"),
    ],
)
def test_the_marks_follow_the_reading(spelling: str, reading: str, marked: str) -> None:
    assert vocalise(spelling, reading) == marked


@pytest.mark.parametrize(
    ("spelling", "reading"),
    [
        # Long vowels are written already; nothing to add.
        ("دانا", "dānā"),
        ("خواب", "xāb"),
        ("او", "u"),
        # The silent ه of -e, and the last letter, carry nothing.
        ("خانه", "xāne"),
    ],
)
def test_no_mark_where_the_letters_say_it(spelling: str, reading: str) -> None:
    assert vocalise(spelling, reading) == spelling


def test_never_a_sokun_and_never_on_the_last_letter() -> None:
    marked = vocalise("بشر", "bašar")
    assert marked == "بَشَر"
    assert "ْ" not in vocalise("دستور", "dastur")


def test_a_reading_that_does_not_line_up_leaves_the_word_as_written() -> None:
    assert vocalise("رفتار", "goftār") == "رفتار"


def test_old_marks_are_replaced_by_the_readings() -> None:
    """A spelling that carries signs of its own is marked from the reading."""
    assert vocalise("تُرک", "Tark") == "تَرک"


def test_the_joiner_and_letter_forms_are_kept() -> None:
    assert "‌" in vocalise("هم‌اندیشنده", "hamandišande")


def test_stripping_gives_back_the_plain_spelling() -> None:
    """What is matched is the plain form: the marks come off exactly."""
    for spelling, reading in [("رفتار", "Raftār"), ("معلم", "moˈallem")]:
        assert strip(vocalise(spelling, reading)) == spelling


class TestTheReviewOf20261121:
    """Cases the review of 2026-11-21 found in the first draft."""

    def test_a_reading_that_never_lines_up_is_quick(self) -> None:
        """The draft searched whole alignments: 1.2 s for twelve words."""
        started = time.perf_counter()
        assert vocalise("خانه " * 40 + "ب", "xāne" * 40 + "x") == "خانه " * 40 + "ب"
        assert time.perf_counter() - started < 0.5

    def test_every_alignment_is_counted_not_the_first_sixty_four(self) -> None:
        marked = vocalise("دره و تپه و دره و تپه", "DarreotappeoDarreotappe")
        assert marked.count("\u0650") == 0  # no disputed zir on a ر

    def test_an_agreed_tashdid_survives_a_disputed_vowel(self) -> None:
        assert vocalise("دره‌ام", "darream") == "دَرّه‌ام"

    def test_a_silent_ain_inside_a_word_takes_no_vowel(self) -> None:
        """*lal*: لَعل or لعَل? The letters cannot say, so neither."""
        assert vocalise("لعل", "lal") == "لعل"

    def test_a_consonant_vav_takes_the_mark_of_the_diphthongs_vowel(self) -> None:
        """*vey* and *vay* are two words in the bank, and must not look alike.

        Both were shown وَی until 2026-11-22: the project lead read a zabar
        over the reading *vey* on the reading screen and took it for a wrong
        pronunciation.
        """
        assert vocalise("وی", "vey") == "وِی"
        assert vocalise("وی", "vay") == "وَی"
        # Shown side by side, they disagree about the mark, so there is none.
        assert vocalise("وی", "vey", ("vay",)) == "وی"

    def test_the_tatweel_is_not_a_boundary(self) -> None:
        assert vocalise("کـتاب", "ketāb") == "کِـتاب"


def test_only_marks_every_shown_pronunciation_agrees_on() -> None:
    """The marks are the ones every shown pronunciation agrees on.

    برنا is *barnā* or *bornā*: the ب takes nothing, not a zabar that
    contradicts the second (the review of 2026-11-21).
    """
    assert vocalise("برنا", "barnā") == "بَرنا"
    assert vocalise("برنا", "barnā", ("bornā",)) == "برنا"


def test_a_search_hit_is_marked_with_its_variants_in_mind() -> None:
    from murfulu.api.search import _marked

    hit = _marked(
        {"spelling_fa": "برنا", "latin": "barnā", "latin_variants": ["bornā"]}
    )
    assert hit["spelling_fa_marked"] == "برنا"
    assert hit["spelling_fa"] == "برنا"
