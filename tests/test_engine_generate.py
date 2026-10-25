"""Feeding results back in: chains, loops and limits."""

import importlib

import pytest

from murfulu.engine import MAX_DEPTH, DerivedForm, Word, generate
from murfulu.rules.pack import load

PACK = load()

#: The module, not the function of the same name that ``murfulu.engine``
#: exports over it.
GENERATE = importlib.import_module("murfulu.engine.generate")

ROW = Word("row", "رو", "karbon_do")


def _names(word: Word, depth: int) -> set[str]:
    return {f.latin for f in generate(PACK, word, max_depth=depth).forms}


def test_the_chain_the_build_plan_names():
    """The chain row → ravande → Ravandegi, in two steps."""
    result = generate(PACK, ROW, max_depth=2)
    names = {f.latin for f in result.forms}
    assert "ravande" in names
    assert "Ravandegi" in names

    ravandegi = next(f for f in result.forms if f.latin == "Ravandegi")
    assert [step.rule_id for step in ravandegi.path] == ["V-022", "V-023"]


def test_a_form_records_every_step_that_made_it():
    """No unexplained output. The whole chain travels with the word."""
    result = generate(PACK, ROW, max_depth=2)
    for form in result.forms:
        assert form.path
        assert len(form.path) <= 2
        assert all(step.rule_id for step in form.path)


def test_depth_one_is_the_same_as_a_single_step():
    from murfulu.engine import apply_all

    assert _names(ROW, 1) == {f.latin for f in apply_all(PACK, ROW)}


def test_going_deeper_only_adds():
    shallow, deeper = _names(ROW, 1), _names(ROW, 2)
    assert shallow < deeper


def test_a_rule_never_runs_twice_on_the_same_form():
    """Cycle detection is on (form, rule), as docs/ARCHITECTURE.md specifies."""
    result = generate(PACK, ROW, max_depth=MAX_DEPTH, max_forms=5000)
    for form in result.forms:
        pairs = [(step.base_latin, step.rule_id) for step in form.path]
        assert len(pairs) == len(set(pairs)), form.latin


def test_a_looping_rule_terminates():
    """A rule that returns the type it consumes must not run forever."""
    looping = PACK.by_id("N-021")
    assert looping.input_types == looping.output_types == ("barnam",)
    result = generate(PACK, Word("dorost", "درست", "barnam"), max_depth=MAX_DEPTH)
    assert result.forms, "it must still produce something"
    assert max(len(f.path) for f in result.forms) <= MAX_DEPTH


def test_a_prefix_is_never_stacked_on_itself():
    """*nānādorost* is not a word, and the corpus says so.

    (form, rule) cycle detection does not catch this on its own: *nā-* on
    *dorost* gives *nādorost*, a **different** form, so the pair never repeats.
    Settled by measurement rather than by a ruling — v9 builds 4,968 words
    whose path adds one prefix twice and **not one of them is attested** in
    25,497,189 tokens. See OPEN_QUESTIONS item L and FINDINGS.
    """
    result = generate(PACK, Word("dorost", "درست", "barnam"), max_depth=3)
    assert result.forms, "it must still build the single-prefix forms"
    assert any(f.latin.startswith("nādorost") for f in result.forms)
    assert not [f for f in result.forms if f.latin.startswith("nānā")]


def test_the_guard_is_on_the_affix_not_the_rule_id():
    """The guard keys on the affix, not the rule id.

    V-059 and V-060 are both *farāz-*, so a rule-id guard would let one follow
    the other and build the same wrong word under two ids.
    """
    farāz = [
        r for r in PACK.rules if r.kind == "prefix" and r.affix.strip("-") == "farāz"
    ]
    assert {r.id for r in farāz} == {"V-059", "V-060"}, "the pack still has both"

    verb = Word("andišidan", "اندیشیدن", "nabesudkarvaze")
    built = {f.latin for f in generate(PACK, verb, max_depth=3).forms}
    assert "farāzandišidan" in built, "one farāz- is still built"
    assert not [name for name in built if name.count("farāz") > 1]


def test_the_two_farāz_rules_give_one_word_carrying_both():
    """V-059 and V-060 are the same prefix under two senses, not a duplicate.

    The coining run recorded this as *identical strings come back twice under
    two rule ids*. Checked 2026-08-15: they do not. Deduplication keys on
    (Latin, word class) and keeps every path, which is what it is for — two
    derivations of one form usually means the word carries two senses, and
    *farāz- (boland)* and *farāz- (bepiš)* are exactly that. So the reader gets
    one word naming both rules, which is the honest answer while the pack
    cannot tell the senses apart. See OPEN_QUESTIONS L10.
    """
    from murfulu.engine import deduplicate

    verb = Word("andišidan", "اندیشیدن", "nabesudkarvaze")
    grouped = deduplicate(generate(PACK, verb, max_depth=1).forms)

    farāz = [g for g in grouped if g.latin == "farāzandišidan"]
    assert len(farāz) == 1, "one word, not two rows"

    named = {step.rule_id for path in farāz[0].paths for step in path}
    assert {"V-059", "V-060"} <= named, "and it names both rules that build it"


def test_a_suffix_is_never_stacked_on_itself():
    """*Golstānstān* is not a word either, and the corpus says so too.

    The same fault as the prefix one and it was outside the same guard until
    2026-08-20, on the reasoning that *andišidegi* + *-i* is a real pattern —
    which is two **different** suffixes. What the engine built was
    *Golstānstān*, *Golzārzār*, *Golkadekade*, *Golāā*, *goftee*: 35 of the
    2,335 forms one reading of گل makes at two steps.

    Settled the way the prefix half was, by measurement: over 120 random
    readings, 2,725 of 161,774 forms at depth 2 add one suffix twice — 1,830
    distinct spellings, **none of them in the corpus** against 25,497,189
    tokens. See OPEN_QUESTIONS item L.
    """
    result = generate(PACK, Word("Gol", "گل", "nam"), max_depth=2)
    built = {f.latin for f in result.forms}
    assert "Golstān" in built, "it must still build the single-suffix forms"
    for wrong in ("Golstānstān", "Golzārzār", "Golkadekade", "Golāā"):
        assert wrong not in built


def test_the_suffix_guard_is_on_the_affix_not_the_rule_id():
    """N-093 and N-095 are both *-i*, so a rule-id guard would miss *Goliyi*."""
    same = [r.id for r in PACK.rules if r.active and (r.affix or "").strip("-") == "i"]
    assert len(same) > 1, "the pack still has more than one -i rule"

    built = {
        f.latin for f in generate(PACK, Word("Gol", "گل", "nam"), max_depth=2).forms
    }
    assert "Goli" in built, "one -i is still built"
    assert "Goliyi" not in built and "goliyi" not in built


def test_different_suffixes_still_stack():
    """The guard is per suffix, not a ban on suffixing a suffixed word.

    *Ravandegi* is *row* + *-ande* + *-gi*, and it must survive untouched.
    """
    built = {f.latin for f in generate(PACK, ROW, max_depth=2).forms}
    assert "Ravandegi" in built


def test_a_prefix_and_a_suffix_spelled_alike_are_not_the_same_affix():
    """A prefix and a suffix spelled alike are not one affix.

    N-022 prefixes *nā-*; N-072 suffixes *-nā*. Neither blocks the other, and
    whether ناگلنا is a word is a different question from this guard, which is
    about one affix added twice.
    """
    built = {
        f.latin for f in generate(PACK, Word("Gol", "گل", "nam"), max_depth=2).forms
    }
    assert "Nāgolnā" in built


def test_different_prefixes_still_stack():
    """The guard is per prefix, not a ban on prefixing a prefixed word."""
    verb = Word("andišidan", "اندیشیدن", "nabesudkarvaze")
    result = generate(PACK, verb, max_depth=2)
    two = [
        f
        for f in result.forms
        if len([s for s in f.path if s.affix.endswith("-")]) == 2
    ]
    assert two, "two different prefixes on one word is still reachable"


@pytest.mark.parametrize("depth", [1, 2, 3])
def test_no_form_is_deeper_than_asked_for(depth: int):
    result = generate(PACK, ROW, max_depth=depth)
    assert max(len(f.path) for f in result.forms) <= depth


def test_the_size_limit_is_reported_not_hidden():
    """A truncated result must never look like a complete one."""
    result = generate(PACK, ROW, max_depth=MAX_DEPTH, max_forms=100)
    assert result.truncated
    assert len(result.forms) == 100


def test_an_untruncated_result_says_so():
    assert not generate(PACK, ROW, max_depth=2).truncated


def test_generation_stops_when_no_rule_applies():
    """A word nothing matches yields nothing, and does not loop."""
    result = generate(PACK, Word("xyz", "؟", "nedayi"), max_depth=MAX_DEPTH)
    assert result.forms == []


def test_forms_can_be_grouped_by_how_many_steps_they_took():
    result = generate(PACK, ROW, max_depth=2)
    assert result.at_depth(1)
    assert result.at_depth(2)
    assert all(len(f.path) == 1 for f in result.at_depth(1))


# A prefixed verb and its stems — PLAN 9.10.
#
# *ham-* on *andišidan* builds *hamandišidan*, and nothing could be built from
# it, because a verb is entered through its stems and a verb the engine builds
# has none. Given the pair, the prefix goes on both and the family opens up.

ANDIŠID = Word("andišid", "اندیشید", "karbon_yek")
ANDIŠ = Word("andiš", "اندیش", "karbon_do")
ANDIŠIDAN = (ANDIŠID, ANDIŠ)

#: Enough headroom that these tests measure the rules and not the backstop.
ROOM = 5_000_000


def _verb(stems: tuple[Word, Word], depth: int) -> list[DerivedForm]:
    forms: list[DerivedForm] = []
    for base in stems:
        forms += generate(
            PACK, base, max_depth=depth, max_forms=ROOM, stems=stems
        ).forms
    return forms


def _verb_names(stems: tuple[Word, Word], depth: int) -> set[str]:
    return {f.latin for f in _verb(stems, depth)}


def test_a_prefixed_verb_is_reachable_through_its_own_stems():
    """hamandišande, which no route could reach before."""
    assert "hamandišande" in _verb_names(ANDIŠIDAN, 3)


def test_without_the_stems_it_is_still_unreachable():
    """The pair is what does it, so a caller that has none loses only this."""
    names = set()
    for base in ANDIŠIDAN:
        names |= {
            f.latin for f in generate(PACK, base, max_depth=3, max_forms=ROOM).forms
        }
    assert "hamandišidan" in names
    assert "hamandišande" not in names


def test_the_new_word_explains_itself_all_the_way_down():
    """The whole chain, and the last step names the stem it ran on.

    andišid → andišidan → hamandišidan → hamandišande. The final step says
    *hamandiš*, not *hamandišidan*, which is the difference this makes.
    """
    form = next(f for f in _verb(ANDIŠIDAN, 3) if f.latin == "hamandišande")
    assert [step.rule_id for step in form.path] == ["V-005", "V-062", "V-022"]
    assert form.path[-1].base_latin == "hamandiš"
    assert form.fa == "هماندیشنده"


def test_a_real_word_comes_back_that_did_not_before():
    """بازگوینده — one who retells.

    A word anybody would recognise, unreachable by any route until now. This is
    what says the change is a fix rather than a flourish.
    """
    goftan = (Word("goft", "گفت", "karbon_yek"), Word("gu", "گو", "karbon_do"))
    assert "bāzguyande" in _verb_names(goftan, 3)


def test_writing_a_verb_out_in_full_does_not_re_enter_it():
    """A verb written out in full is the verb we already have.

    V-005 turns *andišid* into *andišidan*, which is not a new verb, so its
    stems are unchanged and it must not generate the whole family a second
    time.
    """
    forms = _verb(ANDIŠIDAN, 2)
    chains = {(f.latin, tuple(step.rule_id for step in f.path)) for f in forms}
    assert len(forms) == len(chains)


def test_a_verb_coined_by_a_suffix_gets_no_stems():
    """A causative is built, and nothing is built from its stems.

    V-001 builds the causative *andišāndan* from the present stem. Its own
    present stem is written nowhere — the linguist's L16 ruling names *-āndan*
    and does not state it — and guessing one would be inventing a stem. The
    infinitive is still an ordinary form and rules that take an infinitive
    still run on it; what must not appear is a word that could only have come
    from a stem nobody wrote down.
    """
    names = _verb_names(ANDIŠIDAN, 3)
    assert "andišāndan" in names
    assert "andišānande" not in names
    assert "andišānd" not in names


# A verb coined with -idan — FOR_THE_LINGUIST L16, ruled 2026-05-16.
#
# The linguist: the past stem of such a verb is the infinitive less -an, and
# its present stem is the past stem less -id. سرشتیدن is his own example.

SEREŠT = Word("Serešt", "سرشت", "nam")


def test_the_linguists_own_example_gets_both_stems():
    """سرشتیدن → sereštid and serešt, exactly as he wrote it."""
    from murfulu.engine import apply

    rule = PACK.by_id("V-003")
    built = apply(PACK, rule, SEREŠT)
    assert (built.latin, built.fa) == ("sereštidan", "سرشتیدن")
    past, present = GENERATE._verb_built(rule, SEREŠT, None, built)
    assert (past.latin, past.fa, past.word_class) == (
        "sereštid",
        "سرشتید",
        "karbon_yek",
    )
    assert (present.latin, present.fa, present.word_class) == (
        "serešt",
        "سرشت",
        "karbon_do",
    )


def test_a_verb_coined_with_idan_is_entered_through_its_stems():
    """سرشتنده, built on the present stem the ruling gives.

    Before L16 the coined verb was a dead end and nothing could be built on
    *serešt* as a present stem. The last step must name that stem, so the word
    explains itself.
    """
    forms = generate(PACK, SEREŠT, max_depth=2, max_forms=ROOM).forms
    form = next(f for f in forms if f.latin == "sereštande")
    assert form.fa == "سرشتنده"
    assert [step.rule_id for step in form.path] == ["V-003", "V-022"]
    assert form.path[-1].base_latin == "serešt"


def test_only_idan_is_ruled_on():
    """-āndan and -ānidan are named in the ruling, and their stems are not."""
    assert set(GENERATE.COINED_VERB_ENDINGS) == {"idan"}
    tars = Word("Tars", "ترس", "nam")
    names = {f.latin for f in generate(PACK, tars, max_depth=3, max_forms=ROOM).forms}
    assert "tarsānidan" in names, "V-004 still builds the causative"


@pytest.mark.parametrize("rule_id", ["V-001", "V-002", "V-004"])
def test_nothing_is_built_on_a_causatives_stem(rule_id: str):
    """After a causative, the next step runs on the infinitive itself.

    *tarsānande* is still built, and rightly: *Tarsān* is a noun, and *Tarsān*
    + *-idan* is an ordinary L16 coinage. What must never happen is a step on a
    stem cut out of an *-āndan* or *-ānidan* infinitive.
    """
    forms = generate(PACK, Word("Tars", "ترس", "nam"), max_depth=3, max_forms=ROOM)
    forms_from_stems = _verb(ANDIŠIDAN, 3)
    for form in [*forms.forms, *forms_from_stems]:
        for before, after in zip(form.path, form.path[1:], strict=False):
            if before.rule_id == rule_id:
                assert after.base_latin.endswith("an"), (form.latin, form.path)


def test_a_prefix_still_cannot_stack_on_itself_through_a_stem():
    """The guard has to survive the new route, or ham-ham- comes back."""
    for form in _verb(ANDIŠIDAN, 4):
        assert "hamham" not in form.latin
        assert "vāvā" not in form.latin


def test_the_cost_is_measured_and_small():
    """Filed as multiplying generation by thirteen; measured at 1.4.

    The estimate was made for giving *every* built verb its stems. Restricted
    to prefixes — the only case where no stem has to be guessed — it costs far
    less, which is what turns 9.10 from a corpus-scale decision into a fix.
    """
    with_stems = len(_verb(ANDIŠIDAN, 3))
    without = sum(
        len(generate(PACK, b, max_depth=3, max_forms=ROOM).forms) for b in ANDIŠIDAN
    )
    assert 1.2 < with_stems / without < 1.8
