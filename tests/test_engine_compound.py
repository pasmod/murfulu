"""Compound words, checked against the grammar's own examples."""

import pytest

from murfulu.engine import CannotApplyError, Verb, Word, fill
from murfulu.engine.compound import fill_slot
from murfulu.rules.pack import load

PACK = load()


def _verb(past: str, past_fa: str, present: str, present_fa: str) -> Verb:
    return Verb(
        past_stem=Word(past, past_fa, "karbon_yek"),
        present_stem=Word(present, present_fa, "karbon_do"),
    )


GOFTAN = _verb("goft", "گفت", "gu", "گو")
ZADAN = _verb("zad", "زد", "zan", "زن")
XORDAN = _verb("xord", "خورد", "xor", "خور")
KEŠIDAN = _verb("kešid", "کشید", "keš", "کش")
BUDAN = _verb("bud", "بود", "bāš", "باش")
XĀBIDAN = _verb("xābid", "خوابید", "xāb", "خواب")


@pytest.mark.parametrize(
    ("rule_id", "first", "second", "expected"),
    [
        # The two PLAN 2.3 names by hand.
        ("V-018", GOFTAN, None, "Goftogu"),
        ("V-017", ZADAN, XORDAN, "Zadoxord"),
        # The rest of the grammar's compounding examples.
        ("V-044", KEŠIDAN, None, "Kešākeš"),
        ("V-021", BUDAN, None, "Budonabud"),
        ("V-019", XORDAN, XĀBIDAN, "Xordoxāb"),
    ],
)
def test_the_compounds_the_grammar_demonstrates(
    rule_id: str, first: Verb, second: Verb | None, expected: str
):
    rule = PACK.by_id(rule_id)
    assert fill(rule, first, second).latin == expected
    assert expected in rule.examples, "the grammar's own example"


def test_persian_is_built_at_the_same_time():
    assert fill(PACK.by_id("V-017"), ZADAN, XORDAN).fa == "زدوخورد"
    assert fill(PACK.by_id("V-044"), KEŠIDAN).fa == "کشاکش"


def test_the_same_verb_gives_both_halves():
    """Goftogu is goft and gu — one verb's two stems."""
    result = fill(PACK.by_id("V-018"), GOFTAN)
    assert result.latin == "Goftogu"
    assert result.base_latin == "goft"


def test_a_rule_needing_two_verbs_refuses_one():
    with pytest.raises(CannotApplyError, match="second verb is required"):
        fill(PACK.by_id("V-017"), ZADAN)


def test_a_rule_needing_one_verb_refuses_two():
    with pytest.raises(CannotApplyError, match="one verb"):
        fill(PACK.by_id("V-018"), GOFTAN, XORDAN)


def test_a_negated_slot_puts_na_in_the_middle():
    result = fill(PACK.by_id("V-021"), BUDAN)
    assert result.latin == "Budonabud"
    # Was asserted as بودونبود until 2026-08-14, which is the Persian pattern's
    # own bug written into a test: `{a}ون{b}` dropped the ا of *na*. The rule's
    # example — Budonabud, بود و نابود — says which side was wrong.
    assert result.fa == "بودونابود"


def test_a_non_template_rule_is_refused():
    with pytest.raises(CannotApplyError, match="not a template"):
        fill(PACK.by_id("V-010"), GOFTAN)


def test_every_compound_carries_its_rule_and_class():
    result = fill(PACK.by_id("V-018"), GOFTAN)
    assert [step.rule_id for step in result.path] == ["V-018"]
    assert result.word_class == "karnam"
    assert result.latin[0].isupper(), "a kārnām is written with a capital"


@pytest.mark.parametrize(
    ("second", "expected"),
    [(Word("sar", "سر", "nam"), "Sarāsar"), (Word("pā", "پا", "nam"), "Sarāpā")],
)
def test_a_noun_compound_is_built_from_nouns_not_verbs(second: Word, expected: str):
    """N-104 joins two nouns: sar + ā + sar, and sar + ā + pā."""
    result = fill(PACK.by_id("N-104"), Word("sar", "سر", "nam"), second)
    assert result.latin == expected
    assert expected in PACK.by_id("N-104").examples


def test_a_slot_refuses_the_wrong_kind_of_word():
    with pytest.raises(CannotApplyError, match="was given"):
        fill(PACK.by_id("N-104"), Word("goft", "گفت", "karbon_yek"), GOFTAN)


def test_every_compounding_rule_in_the_pack_can_be_filled():
    """No template may sit in the pack unusable."""
    templates = [r for r in PACK.rules if r.kind == "template" and r.active]
    assert len(templates) == 10, "nine join verb stems, one joins nouns"
    sar = Word("sar", "سر", "nam")
    for rule in templates:
        needs_two = any(
            slot.get("constraint") in {"different_verb", "different_stem"}
            for slot in rule.slots
        )
        joins_nouns = all(slot["type"] == "nam" for slot in rule.slots)
        first = sar if joins_nouns else GOFTAN
        second = sar if joins_nouns else (XORDAN if needs_two else None)
        result = fill(rule, first, second)
        assert result.latin and result.fa, rule.id


# -- slot rules ---------------------------------------------------------------
#
# The six that pair a word with a *class* rather than with another pattern:
# V-078 is `Nām-` + kārboné do, "a noun in front of a present stem". They were
# unbuilt until 2026-08-14, so no compound of this shape had ever been made.


@pytest.mark.parametrize(
    ("rule_id", "front", "behind", "expected"),
    [
        (
            "V-078",
            Word("soxan", "سخن", "nam"),
            Word("guy", "گوی", "karbon_do"),
            "soxanguy",
        ),
        (
            "V-080",
            Word("tond", "تند", "barnam"),
            Word("row", "رو", "karbon_do"),
            "tondrow",
        ),
        (
            "V-016",
            Word("čašm", "چشم", "nam"),
            Word("dāšt", "داشت", "karbon_yek"),
            "Čašmdāšt",
        ),
    ],
)
def test_the_slot_compounds_the_grammar_demonstrates(
    rule_id: str, front: Word, behind: Word, expected: str
):
    rule = PACK.by_id(rule_id)
    assert fill_slot(rule, front, behind).latin == expected
    assert expected in rule.examples, "the grammar's own example"


def test_a_slot_writes_the_two_words_together_in_both_alphabets():
    """Nothing goes between them, which is what the source's dash means."""
    built = fill_slot(
        PACK.by_id("V-078"),
        Word("soxan", "سخن", "nam"),
        Word("guy", "گوی", "karbon_do"),
    )
    assert built.fa == "سخنگوی"
    assert built.word_class == "karandekarbahr"


def test_the_front_word_must_be_the_class_the_rule_names():
    """V-080 takes a manner word in front, not a noun: tondrow, not soxanrow."""
    with pytest.raises(CannotApplyError, match="in front"):
        fill_slot(
            PACK.by_id("V-080"),
            Word("soxan", "سخن", "nam"),
            Word("row", "رو", "karbon_do"),
        )


def test_a_template_is_not_a_slot_and_says_so():
    with pytest.raises(CannotApplyError, match="not a slot"):
        fill_slot(
            PACK.by_id("V-018"),
            Word("soxan", "سخن", "nam"),
            Word("gu", "گو", "karbon_do"),
        )
