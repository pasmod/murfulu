"""The word's own vowel signs against a Behnevis reading.

Every word here is written for the test; no corpus text (NOTICE).
"""

import pytest

from murfulu.search import harakat, texts


@pytest.mark.parametrize(
    ("written", "reading"),
    [
        ("تُرکِ", "tork"),  # the damma leaves tork; the last kasra is the ezafe
        ("دِل", "Del"),
        ("بَخشَم", "baxšam"),
        ("نَو", "now"),  # a fatha writes the diphthong too
        ("اَبر", "Abr"),  # a capital is grammar, not a sound
        ("مَسْت", "mast"),
        ("خواب", "Xāb"),  # no sign: nothing to say
        ("دلِ", "Dal"),  # only the last letter's sign: the ezafe
        ("زیادی", "Ziyādi"),
        ("سَرْآمد", "sarāmad"),  # a sukun, then a vowel the next letter writes
        ("مهرْافزا", "mehrāfzā"),
    ],
)
def test_a_reading_the_signs_allow_is_not_against(written: str, reading: str):
    assert not harakat.against(written, reading)


@pytest.mark.parametrize(
    ("written", "reading"),
    [
        ("تُرکِ", "Tarak"),
        ("تُرکِ", "Tark"),
        ("تُرکان", "Tarkān"),
        ("دِل", "Dal"),
        ("دِل", "dall"),
        ("بَخشَم", "boxšam"),
        ("سُخَن", "saxon"),
        ("مَسْت", "masat"),  # a sukun: no vowel after its letter
    ],
)
def test_a_reading_the_signs_rule_out_is_against(written: str, reading: str):
    assert harakat.against(written, reading)


def test_a_reading_with_a_variant_the_signs_allow_is_not_against():
    assert harakat.against("دِل", "Dal")
    assert not harakat.against("دِل", "Dal", ("Del",))


def test_a_reading_that_cannot_be_lined_up_is_never_said_to_be_against():
    # No letter of دل is spelled q: nothing can be said, so nothing is.
    assert not harakat.against("دِل", "qal")
    # An unknown letter, the same.
    assert not harakat.against("دِلχ", "Dal")


def test_only_a_vowel_sign_off_the_last_letter_counts():
    assert harakat.has_signs("دِل")
    assert not harakat.has_signs("دلِ")
    assert not harakat.has_signs("دلّ")  # a shadda allows a doubled letter, asks nothing


def test_the_reading_screen_carries_the_ids_the_signs_rule_out():
    source = {
        "units": [
            {"kind": "couplet", "lines": [{"text": "دِل و دلِ", "position": "first"}]}
        ]
    }
    units, _, _ = texts.lay_out(source)
    words = {
        "دل": {
            "readings": [
                {"id": "دل:Dal", "latin": "Dal", "latin_variants": []},
                {"id": "دل:dall", "latin": "dall", "latin_variants": []},
                {"id": "دل:Del", "latin": "Del", "latin_variants": []},
            ]
        },
        "و": {"readings": [{"id": "و:va", "latin": "va", "latin_variants": []}]},
    }
    texts.rule_out(units, words)
    first, and_, second = units[0]["lines"][0]["words"]
    assert first["against"] == ["دل:Dal", "دل:dall"]
    assert "against" not in and_ and "against" not in second


@pytest.mark.parametrize(
    ("written", "reading", "verdict"),
    [
        ("تُرکِ", "tork", True),
        ("تُرکِ", "Tark", False),
        ("دلِ", "Dal", None),  # only the ezafe: no sign that counts
        ("دِل", "qal", None),  # no spelling of the reading lines up
        ("طِبع", "tabˈ", False),  # the mark for ain is read, not skipped
        ("طَبع", "tabˈ", True),
    ],
)
def test_fits_tells_confirmed_from_ruled_out_from_undecided(
    written: str, reading: str, verdict: bool | None
):
    assert harakat.fits(written, reading) is verdict
