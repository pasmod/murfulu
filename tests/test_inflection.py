"""The instrument that tells an inflection from a word we built.

These check the *instrument*, never Persian. Where a spelling is genuinely
ambiguous the test asserts that both readings survive and that the ambiguity
is reported — not that one of them is right. See docs/OPEN_QUESTIONS.md S8.
"""

from murfulu.corpus.inflection import ZWNJ, Analyser, Held, patterns

#: رفتن and its two stems, plus a handful of ordinary words.
HELD = Held.of(
    headwords=["رفتن", "کتاب", "بلند", "بلندی", "مرد", "مردم", "گفتار"],
    past_stems=["رفت", "گفت"],
    present_stems=["رو", "گو"],
)


def _analyser(pack_suffixes: dict[str, tuple[str, ...]] | None = None) -> Analyser:
    return Analyser(held=HELD, pack_suffixes=pack_suffixes or {})


def test_the_founding_case_a_conjugated_verb_reads_as_one():
    """رفتی is "you went" — the base is the past stem, not the infinitive."""
    analysis = _analyser().best("رفتی")
    assert analysis is not None
    assert analysis.base == "رفت"
    assert analysis.pattern.base_kind == "past_stem"


def test_the_founding_contrast_a_word_we_built_reads_as_none():
    """گفتار is exactly the kind of word Murfulu builds, and is held."""
    assert _analyser().best("گفتار") is None


def test_a_negated_imperfective_is_read_through_both_its_parts():
    assert _analyser().best("نمی" + ZWNJ + "رفت").base == "رفت"
    assert _analyser().best("نمیرفت").base == "رفت"


def test_a_word_we_hold_is_never_called_an_inflection():
    """مردم is "people". That it also strips to مرد + م decides nothing.

    This is the guard that keeps the instrument from calling a real word an
    inflection just because its letters allow it.
    """
    assert _analyser().best("مردم") is None
    assert _analyser().best("بلندی") is None


def test_the_control_sees_the_ambiguity_the_measurement_hides():
    """The same spelling, asked without the held check, does strip.

    This is what the control run counts: بلندی is a word *and* reads as
    بلند + ی, and that overlap is the size of what no ranking can settle.
    """
    analysis = _analyser().control("بلندی")
    assert analysis is not None
    assert analysis.base == "بلند"


def test_a_pattern_a_derivational_rule_also_writes_is_marked_shared():
    """-ی is the indefinite and it is also N-099. The letters cannot decide."""
    plain = _analyser().best("کتابی")
    shared = _analyser({"ی": ("N-099",)}).best("کتابی")
    assert plain is not None and not plain.is_shared
    assert shared is not None and shared.shared_with == ("N-099",)


def test_an_unshared_pattern_is_preferred_over_a_shared_one():
    """Only an ordering convention, and it is stated as one."""
    analyser = _analyser({"ی": ("N-099",)})
    assert analyser.best("کتابها").pattern.id == "noun:ها"
    assert not analyser.best("کتابها").is_shared


def test_a_spelling_with_nothing_behind_it_reads_as_nothing():
    assert _analyser().best("قرمز") is None


def test_a_one_letter_base_is_never_looked_up():
    """Stripping ی off می would leave م, which is not a word in any lexicon."""
    for pattern in patterns():
        assert pattern.split("می") is None or len(pattern.split("می")) >= 2


def test_every_pattern_has_its_own_id():
    """The report counts by id, so a collision would merge two patterns."""
    ids = [pattern.id for pattern in patterns()]
    assert len(ids) == len(set(ids))


def test_a_verbal_pattern_never_takes_a_noun_as_its_base():
    """رفت is a stem and کتاب is not, so کتابی is not "you booked"."""
    analyses = _analyser().analyse("کتابی")
    assert all(one.pattern.base_kind == "headword" for one in analyses)
