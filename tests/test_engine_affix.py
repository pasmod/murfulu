"""Affixation and vowel joining, checked against the grammar's own examples."""

import pytest

from murfulu.engine import (
    CannotApplyError,
    Word,
    ambiguous_pairs,
    apply,
    apply_all,
    join,
    undo,
    working_form,
)
from murfulu.rules.pack import Glide, Rule, load

PACK = load()


def _rule(rule_id: str) -> Rule | Glide:
    return PACK.by_id(rule_id)


# -- the joins the build plan names -----------------------------------------


#: The table's own worked examples. PLAN 2.2 names dānā + i; row + eš is not
#: here because it is no longer a join at all — the stem is rav once anything
#: follows it.
JOINS = [
    ("dānā", "i", "dānāyi"),
    ("pā", "e", "pāye"),
    ("ā", "am", "āyam"),
    ("gu", "eš", "guyeš"),
    ("gu", "ande", "guyande"),
    ("gu", "ā", "guyā"),
    ("niku", "i", "nikuyi"),
    ("morde", "ān", "mordegān"),
    ("zi", "ān", "ziyān"),
    ("zi", "ande", "ziyande"),
    ("ni", "i", "niyi"),
]


@pytest.mark.parametrize(("base", "affix", "expected"), JOINS)
def test_the_vowel_joins_the_grammar_demonstrates(base: str, affix: str, expected: str):
    assert join(PACK, base, affix).latin == expected


@pytest.mark.parametrize(("base", "affix", "expected"), JOINS)
def test_every_join_can_be_taken_back_apart(base: str, affix: str, expected: str):
    """The sāzāyi rule, on the one table that used to break it.

    Whatever the engine joins it must be able to unjoin, or a word it built
    itself comes back as a word that cannot be built. Removing the affix as a
    string is not enough: *guyande* minus *-ande* is *guy*, which is nothing.
    """
    assert base in {found for found, _ in undo(PACK, affix, expected)}


def test_a_join_records_which_glide_rule_fired():
    """Every result must be able to explain itself."""
    result = join(PACK, "dānā", "i")
    assert result.glide_id == "G-02"


def test_no_glide_where_the_vowels_never_meet():
    result = join(PACK, "goft", "ār")
    assert result.latin == "goftār"
    assert result.glide_id is None


def test_the_retired_glide_rule_is_never_applied():
    """G-01 is retired. G-03 says the same thing and does the work."""
    assert join(PACK, "pā", "e").glide_id == "G-03"


def test_the_one_ambiguous_vowel_pair_is_reported_not_hidden():
    """The vowel e meets i twice: taze + i = Tāzegi, but rafte + i = raftei."""
    pairs = ambiguous_pairs(PACK)
    assert ("e", "i") in pairs
    assert sorted(pairs[("e", "i")]) == ["G-09", "G-17"]
    assert join(PACK, "taze", "i").alternatives, "the caller must see the choice"


# -- affixation --------------------------------------------------------------


@pytest.mark.parametrize(
    ("rule_id", "base", "word_class", "expected"),
    [
        # Suffixes. The capital letter is not decoration: a kārnām is a word
        # used as a name, so Behnevis writes it with one.
        ("V-010", "goft", "karbon_yek", "Goftār"),
        ("V-011", "xārid", "karbon_yek", "xāridār"),
        ("V-022", "rav", "karbon_do", "ravande"),
        ("V-024", "dān", "karbon_do", "dānā"),
        ("V-033", "pazir", "karbon_do", "Pazireš"),
        # PLAN 2.2 names this one: row + eš.
        ("V-033", "row", "karbon_do", "Raveš"),
        ("V-025", "dānā", "karandekarbahr", "Dānāyi"),
        # Prefixes.
        ("V-053", "angixtan", "nabesudkarvaze", "barangixtan"),
        ("N-008", "kār", "nam", "bikār"),
    ],
)
def test_a_rule_builds_the_form_its_own_example_shows(
    rule_id: str, base: str, word_class: str, expected: str
):
    result = apply(PACK, _rule(rule_id), Word(latin=base, fa="", word_class=word_class))
    assert result.latin == expected


def test_the_same_stem_gives_a_capital_or_not_by_word_class():
    """Verb rows 5 and 6 differ only in this. porsidan vs Porsidan."""
    stem = Word(latin="porsid", fa="پرسید", word_class="karbon_yek")
    infinitive = apply(PACK, _rule("V-005"), stem)
    noun = apply(PACK, _rule("V-006"), stem)
    assert infinitive.latin == "porsidan", "to ask"
    assert noun.latin == "Porsidan", "the asking"
    assert infinitive.latin.lower() == noun.latin.lower()


def test_persian_and_latin_are_built_together():
    """There is no converter. Both forms come out of the same step."""
    result = apply(
        PACK, _rule("V-010"), Word(latin="goft", fa="گفت", word_class="karbon_yek")
    )
    assert result.latin == "Goftār"
    assert result.fa == "گفتار"


def test_a_prefix_goes_in_front_on_both_sides():
    result = apply(
        PACK,
        _rule("N-008"),
        Word(latin="kār", fa="کار", word_class="nam"),
    )
    assert result.latin == "bikār"
    assert result.fa == "بیکار"


def test_a_prefix_does_not_leave_a_capital_inside_the_word():
    """سربلند is Sarbaland, never SarBaland — the spelling karbon uses.

    Settled by matching karbon, because the linguist is behind that library.
    Measured over the whole snapshot: **0 of 45,579 readings and 0 of 20,263
    compounds** carry a capital after the first letter — *Ābādbum*,
    *Ābādjāi*, *Ābāngān* — and 8,116 rows carry karbon's own
    ``[v7:rule12-cap]`` marker, so capitalising the front alone is a rule it
    applies and not an artefact of its phonemizer.

    The alternative was live for one session: 16.2% of a random 5,000 of the
    v4 index carried an inner capital. What the result *is* was already
    written on the first letter by ``cased``. See FOR_THE_LINGUIST L9.
    """
    result = apply(
        PACK,
        _rule("N-028"),
        Word(latin="Baland", fa="بلند", word_class="nam"),
    )
    assert result.latin == "Sarbaland"
    assert result.fa == "سربلند"


def test_every_result_carries_the_rule_that_made_it():
    result = apply(
        PACK, _rule("V-033"), Word(latin="row", fa="رو", word_class="karbon_do")
    )
    assert [step.rule_id for step in result.path] == ["V-033"]
    assert result.path[0].stem_form == "ow->av"
    assert result.base_latin == "row"


def test_a_zero_affix_rule_only_changes_the_class():
    """Parhiz is the stem itself, used as a noun."""
    result = apply(
        PACK, _rule("V-049"), Word(latin="parhiz", fa="پرهیز", word_class="karbon_do")
    )
    assert result.latin == "Parhiz"
    assert result.fa == "پرهیز"


def test_a_rule_that_does_not_fit_refuses_rather_than_guessing():
    with pytest.raises(CannotApplyError, match="takes"):
        apply(PACK, _rule("V-010"), Word(latin="ketāb", fa="کتاب", word_class="nam"))


def test_a_template_rule_is_not_applied_here():
    """Compounding needs a second word. That is PLAN task 2.3."""
    with pytest.raises(CannotApplyError, match="template"):
        apply(PACK, _rule("V-017"), Word(latin="zad", fa="زد", word_class="karbon_yek"))


def test_a_retired_rule_is_never_applied():
    with pytest.raises(CannotApplyError, match="retired"):
        apply(PACK, _rule("G-01"), Word(latin="pā", fa="پا", word_class="nam"))


# -- everything that applies, in one step ------------------------------------


def test_one_stem_yields_a_whole_family():
    forms = apply_all(PACK, Word(latin="row", fa="رو", word_class="karbon_do"))
    produced = {f.latin for f in forms}
    assert "Raveš" in produced, "row + eš"
    assert "ravande" in produced, "row + ande"
    assert len(forms) > 5


def test_every_form_from_apply_all_knows_its_rule():
    forms = apply_all(PACK, Word(latin="goft", fa="گفت", word_class="karbon_yek"))
    assert forms
    for form in forms:
        assert form.path
        assert form.word_class


# -- a stem written one way, behaving another -------------------------------


@pytest.mark.parametrize(
    ("written", "expected"),
    [("row", "rav"), ("šow", "šav"), ("dow", "dav"), ("šenow", "šenav")],
)
def test_a_stem_takes_its_working_form_once_something_follows(
    written: str, expected: str
):
    """Measured against the lexicon: not one of 45,579 words contains ow."""
    assert working_form(PACK, written)[0] == expected


def test_a_stem_with_no_working_form_is_left_alone():
    assert working_form(PACK, "goft") == ("goft", None)


@pytest.mark.parametrize(
    ("rule_id", "expected"),
    [
        # The grammar's own examples for these rules, all previously wrong.
        ("V-029", "ravān"),
        ("V-033", "Raveš"),
        ("V-022", "ravande"),
        ("V-024", "ravā"),
        # A consonant follows here, and it is still av: cf. šenavgar.
        ("V-028", "ravgār"),
    ],
)
def test_the_working_form_fixes_the_words_the_grammar_expects(
    rule_id: str, expected: str
):
    result = apply(
        PACK, _rule(rule_id), Word(latin="row", fa="رو", word_class="karbon_do")
    )
    assert result.latin == expected


def test_the_change_of_form_is_recorded_not_silent():
    result = apply(
        PACK, _rule("V-029"), Word(latin="row", fa="رو", word_class="karbon_do")
    )
    assert result.path[0].stem_form == "ow->av"


def test_a_prefix_leaves_the_stem_ending_alone():
    """Nothing follows the stem, so it keeps the form it is written in."""
    assert working_form(PACK, "row")[0] == "rav"
    result = apply(
        PACK, _rule("V-053"), Word(latin="row", fa="رو", word_class="nabesudkarvaze")
    )
    assert result.latin == "barrow"


def test_the_two_ow_glide_rules_were_retired_by_this():
    """G-15 and G-16 said "ow + a" and "ow + e" give av. One fact, not two."""
    for glide_id in ("G-15", "G-16"):
        glide = PACK.by_id(glide_id)
        assert glide.active is False
        assert "superseded" in glide.retired_reason.lower()
    assert not [g for g in PACK.glides if g.active and g.left == "ow"]


def test_a_result_can_be_fed_back_in():
    """From ravande to Ravandegi. PLAN 2.4 needs this to chain."""
    ravande = apply(
        PACK, _rule("V-022"), Word(latin="rav", fa="رو", word_class="karbon_do")
    )
    assert ravande.latin == "ravande"
    again = apply(PACK, _rule("V-023"), ravande.as_word())
    assert again.latin == "Ravandegi"


# -- the Persian must not drift away from the Latin --------------------------


@pytest.mark.parametrize(
    ("rule_id", "base", "base_fa", "word_class", "latin", "fa"),
    [
        ("V-033", "gu", "گو", "karbon_do", "Guyeš", "گویش"),
        ("V-033", "row", "رو", "karbon_do", "Raveš", "روش"),
        ("V-025", "dānā", "دانا", "karandekarbahr", "Dānāyi", "دانایی"),
    ],
)
def test_the_persian_gets_the_glide_letter_too(
    rule_id: str, base: str, base_fa: str, word_class: str, latin: str, fa: str
):
    """Without this the two scripts drift: گوش ("ear") instead of گویش."""
    result = apply(PACK, _rule(rule_id), Word(base, base_fa, word_class))
    assert (result.latin, result.fa) == (latin, fa)


def test_the_he_ending_case_is_fixed():
    """A glide whose result adds *g*, not *y*, drops the ه first.

    This test used to assert the wrong answer — تازهی — and said the day it
    was fixed it would say so. That day is 2026-08-13: *taze* + *i* is
    *Tāzegi* and **تازگی**.
    """
    result = apply(PACK, _rule("N-093"), Word("taze", "تازه", "nam"))
    assert result.fa == "تازگی"


# -- the Persian side of a join --------------------------------------------


class TestTheSilentHeBeforeGaf:
    """زندگی, not زندهگی.

    Measured before it was written: 38,932 forms spelled this join wrong, and
    because attestation looks a form up by its Persian spelling, at least 658
    real corpus words — زندگی 4,571 times, مژگان 3,977 — were reported as
    never written.
    """

    def test_a_glide_that_inserts_a_g_replaces_the_he(self):
        """G-09, and the source grammar's own example: taze + i = Tāzegi."""
        from murfulu.engine.glides import join_fa

        assert join_fa("تازه", "taze", "گ", "ی") == "تازگی"

    def test_the_other_g_glide_too(self):
        """G-10: morde + ān = Mordegān."""
        from murfulu.engine.glides import join_fa

        assert join_fa("مرده", "morde", "گ", "ان") == "مردگان"

    @pytest.mark.parametrize(
        ("base_fa", "base_latin", "affix_fa", "expected"),
        [
            ("بنده", "bande", "گی", "بندگی"),
            ("دره", "dare", "گاه", "درگاه"),
            ("مژه", "může", "گان", "مژگان"),
            ("داده", "dāde", "گر", "دادگر"),
        ],
    )
    def test_an_affix_beginning_with_gaf_takes_the_he_too(
        self, base_fa: str, base_latin: str, affix_fa: str, expected: str
    ):
        from murfulu.engine.glides import join_fa

        assert join_fa(base_fa, base_latin, "", affix_fa) == expected

    def test_a_pronounced_he_is_kept(self):
        """شاه ends in ه and its ه is a consonant — the Latin says so.

        Reading *silent* off the Persian letter alone would turn شاهگان into
        شاگان, which is a different word and not one.
        """
        from murfulu.engine.glides import join_fa

        assert join_fa("شاه", "šāh", "", "گان") == "شاهگان"
        assert join_fa("ماه", "māh", "", "گی") == "ماهگی"

    def test_a_pronounced_he_is_kept_even_when_the_lexicon_says_otherwise(self):
        """The Latin decides — except where the Latin is wrong, and it is.

        karbon transliterates a *pronounced* final ه as **e**: شاه is held as
        `Šāe`, گاه as `Gāe` — 777 of the 803 readings ending in ـاه. Read off
        those, this rule deleted a consonant, and it reached real output:
        building from شاه gave شاگان, شاگین, شاگیدن, and 28% of one-step forms
        over a 40-reading sample lost the ه. Found 2026-08-20; the data fault
        is UPSTREAM A9 and is carried, not worked around.

        A final ه after ا is always pronounced — the silent one writes a short
        *e*, which cannot follow a long ā — so that one ending overrules the
        Latin.
        """
        from murfulu.engine.glides import join_fa

        assert join_fa("شاه", "Šāe", "", "گان") == "شاهگان"
        assert join_fa("گاه", "Gāe", "", "گان") == "گاهگان"
        assert join_fa("راه", "Rae", "", "گی") == "راهگی"

    def test_the_override_is_only_that_one_ending(self):
        """Narrow on purpose: کوه is *kuh* and میوه is *mive*, both وه.

        No rule over the Persian alone tells those apart, so nothing outside
        ـاه is guessed at — a word whose ه really is silent must still lose it.
        """
        from murfulu.engine.glides import join_fa

        assert join_fa("بنده", "bande", "", "گی") == "بندگی"
        assert join_fa("میوه", "mive", "", "گی") == "میوگی"

    def test_nothing_else_changes(self):
        """Only گ takes the ه. Every other join is still concatenation."""
        from murfulu.engine.glides import join_fa

        assert join_fa("دانا", "dānā", "ی", "ی") == "دانایی"
        assert join_fa("خانه", "xāne", "", "ها") == "خانهها"
        assert join_fa("گفت", "goft", "", "ار") == "گفتار"

    def test_the_engine_builds_it_end_to_end(self):
        """Through the real rules, not only through the helper."""
        built = apply_all(PACK, Word(latin="zende", fa="زنده", word_class="barnam"))
        spellings = {form.fa for form in built}
        assert "زندگی" in spellings, sorted(spellings)
        assert not any("هگ" in one for one in spellings)


def test_an_infix_rule_builds_nothing_rather_than_building_it_wrongly():
    """N-023's affix goes *between* two words: دل + نا + چسب = delnāčasb.

    ``infix`` was in the engine's SUPPORTED set with no branch for it, so both
    infix rules fell through to the suffix case and put the affix on the end —
    *časbnā*, چسبنا. 27,361 types each, 115,682 forms in the live index, all
    reported at middle-band productivity as though they had been measured.

    An infix needs a second word exactly as a slot does, so it belongs with
    compounding and PLAN 2.3. Until then it builds nothing, because a rule
    that builds nothing is better than one that builds the wrong thing.
    """
    rule = PACK.by_id("N-023")
    assert rule.kind == "infix"
    assert rule.active, "the rule is not retired; the engine simply cannot run it"
    with pytest.raises(CannotApplyError, match="infix"):
        apply(PACK, rule, Word(latin="časb", fa="چسب", word_class="barnam"))


class TestAPrefixThatMakesAnInfinitive:
    """V-070 to V-076 take a past stem and say they produce an infinitive.

    The prefix alone left *vāgoft* — a past stem carrying the label of an
    infinitive. All seventeen examples those seven rules list end in -an, and
    stem rule S-01 states the converse: taking -an off any infinitive leaves
    kārbon-e yek. Fixed 2026-08-15 with PLAN 9.3; it moved seven of the pack's
    own examples from *not rebuilt at all* to *explained by its own rule*.
    """

    def test_the_infinitive_ending_is_added(self):
        built = apply(PACK, PACK.by_id("V-071"), Word("goft", "گفت", "karbon_yek"))
        assert built.latin == "vāgoftan"
        assert built.fa == "واگفتن"
        assert built.word_class == "nabesudkarvaze"

    def test_it_applies_to_every_rule_of_that_shape(self):
        shape = [
            rule
            for rule in PACK.rules
            if rule.kind == "prefix"
            and rule.active
            and "karbon_yek" in rule.input_types
            and rule.output_types
            and rule.output_types[0] == "nabesudkarvaze"
        ]
        assert {rule.id for rule in shape} == {
            "V-070",
            "V-071",
            "V-072",
            "V-073",
            "V-074",
            "V-075",
            "V-076",
        }
        for rule in shape:
            built = apply(PACK, rule, Word("goft", "گفت", "karbon_yek"))
            assert built.latin.endswith("an"), rule.id
            assert built.fa.endswith("ن"), rule.id

    def test_a_prefix_on_an_infinitive_is_left_alone(self):
        """V-059 takes an infinitive already, so nothing is added to the end."""
        built = apply(
            PACK, PACK.by_id("V-059"), Word("āmadan", "آمدن", "nabesudkarvaze")
        )
        assert built.latin == "farāzāmadan"
        assert not built.latin.endswith("anan")
