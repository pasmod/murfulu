"""Persian word in, derived words out — the whole system end to end.

Runs against the fixture lexicon, never the real 28 MB snapshot, so it works
in CI. The fixture carries رفتن with both its stems, which is exactly the case
the build plan names.
"""

from pathlib import Path

import pytest

from murfulu.generation import DEFAULT_DEPTH, WordNotFoundError, from_word
from murfulu.lexicon import Lexicon
from murfulu.rules.pack import load

PACK = load()

#: What PLAN task 3.3 requires رفتن to produce.
REQUIRED = ["Raftār", "Raveš", "ravande", "Ravandegi"]


def _forms(snapshot: Path, word: str) -> set[str]:
    with Lexicon.open(snapshot) as lexicon:
        results = from_word(lexicon, PACK, word)
    return {f.latin for result in results for f in result.forms}


@pytest.mark.parametrize("expected", REQUIRED)
def test_raftan_produces_what_the_plan_asks_for(lexicon_snapshot: Path, expected: str):
    assert expected in _forms(lexicon_snapshot, "رفتن")


def test_a_verb_is_entered_through_both_its_stems(lexicon_snapshot: Path):
    """Raftār comes from the past stem, Raveš from the present one."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (result,) = from_word(lexicon, PACK, "رفتن")
    assert [base.latin for base in result.bases] == ["raft", "row"]
    assert [base.word_class for base in result.bases] == ["karbon_yek", "karbon_do"]


def test_the_reading_it_was_built_from_travels_with_the_result(
    lexicon_snapshot: Path,
):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (result,) = from_word(lexicon, PACK, "رفتن")
    assert result.reading.latin == "raftan"
    assert result.reading.snapshot_id.startswith("lexicon-fixture:")


def test_a_spelling_with_two_readings_gives_two_results(lexicon_snapshot: Path):
    """مرد is mard and mord. Two words, never one merged pile."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        results = from_word(lexicon, PACK, "مرد")
    assert len(results) == 2
    assert {r.reading.latin for r in results} == {"mard", "mord"}


def test_a_reading_the_dictionary_doubts_does_not_open_the_screen(
    lexicon_snapshot: Path,
):
    """بلند is *Baland*, flagged, and *boland*, clean. The clean one is first.

    The readings arrived in the lexicon's row order, and the flagged one is
    written first, so the build screen opened on it and produced *Sarbalandi*
    where the same snapshot spells سربلند ``sarboland``. Both readings are
    still returned — this is an order, not a filter. See S13.
    """
    with Lexicon.open(lexicon_snapshot) as lexicon:
        results = from_word(lexicon, PACK, "بلند")
    assert [result.reading.latin for result in results] == ["boland", "Baland"]
    assert results[1].reading.needs_review


def test_no_word_is_built_by_hanging_a_clitic_on_the_base(lexicon_snapshot: Path):
    """The ezāfe and the indefinite -i are not word formation.

    Found by building from an ordinary adjective and reading the top of the
    list: four of the first five results were the base word with a کسره or a
    نکره on it — *Balandé*, *Balandéé*, *Balandéí*, *Balandíé* — and each
    carried the base's own corpus count, because the corpus writes no کسره.
    Measured over v4: 28,148 such forms, 2,252 of them counted as attested.

    Rows 90 and 99 of the nominal table stay in the pack with their ids; they
    are simply not run. See FOR_THE_LINGUIST L8.
    """
    with Lexicon.open(lexicon_snapshot) as lexicon:
        results = from_word(lexicon, PACK, "مرد")
    built = {f.latin for result in results for f in result.forms}
    hung = {form for form in built if "é" in form or "í" in form}
    assert hung == set(), f"a clitic was treated as a suffix: {sorted(hung)}"


def test_a_noun_is_built_from_itself_not_from_stems(lexicon_snapshot: Path):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        results = from_word(lexicon, PACK, "مرد")
    for result in results:
        assert [base.latin for base in result.bases] == [result.reading.latin]
        assert [base.word_class for base in result.bases] == ["nam"]


def test_a_word_whose_category_we_did_not_map_yields_nothing(
    lexicon_snapshot: Path,
):
    """The row with no category. Not a crash, and not a guess either."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (result,) = from_word(lexicon, PACK, "بی‌نام")
    assert result.bases == ()
    assert result.forms == []


def test_an_unknown_word_says_which_snapshot_it_looked_in(lexicon_snapshot: Path):
    with (
        Lexicon.open(lexicon_snapshot) as lexicon,
        pytest.raises(WordNotFoundError) as e,
    ):
        from_word(lexicon, PACK, "واژه‌ای‌که‌نیست")
    assert "lexicon-fixture" in str(e.value)


def test_a_word_can_be_looked_up_by_its_latin_form(lexicon_snapshot: Path):
    assert _forms(lexicon_snapshot, "raftan") == _forms(lexicon_snapshot, "رفتن")


def test_every_form_still_carries_its_derivation(lexicon_snapshot: Path):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (result,) = from_word(lexicon, PACK, "رفتن")
    assert result.forms
    for form in result.forms:
        assert form.paths, form.latin
        assert 1 <= form.depth <= DEFAULT_DEPTH


def test_forms_reached_two_ways_keep_both_paths(lexicon_snapshot: Path):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (result,) = from_word(lexicon, PACK, "رفتن")
    assert any(len(form.paths) > 1 for form in result.forms)


def test_meanings_are_attached_where_a_template_exists(lexicon_snapshot: Path):
    """Only the Jā tag has a template so far, so most forms have no meaning."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (result,) = from_word(lexicon, PACK, "رفتن")
    for latin, meaning in result.meanings.items():
        assert meaning.text_fa, latin
        assert result.meaning_of(latin) is meaning


def test_a_word_read_two_ways_is_built_from_both(lexicon_snapshot: Path):
    """آبرو is Ābrav or Ābrov. Building on one alone would be a guess."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (result,) = from_word(lexicon, PACK, "آبرو")
    assert [base.latin for base in result.bases] == ["Ābrav", "Ābrov"]
    produced = {f.latin for f in result.forms}
    assert any(f.startswith("Ābrav") for f in produced)
    assert any(f.startswith("Ābrov") for f in produced)


def test_a_prefixed_verb_is_built_from_its_own_stems(lexicon_snapshot: Path):
    """PLAN 9.10, from the lexicon side.

    *vā-* on گفتن gives *vāgoftan*, whose kārbon-e do is *vāgu*, and
    *vāguyande* is reachable only through it. Only this module knows the pair:
    a present stem is irregular and is read from the lexicon, so the engine
    handed one stem at a time could never work the other one out.
    """
    assert "vāguyande" in _forms(lexicon_snapshot, "گفتن")


def test_the_stems_are_handed_over_only_for_a_verb(lexicon_snapshot: Path):
    """A noun has one base and no stems.

    Nothing is passed for it, and nothing about it changes.
    """
    with Lexicon.open(lexicon_snapshot) as lexicon:
        results = from_word(lexicon, PACK, "مرد")
    assert all(len(result.bases) == 1 for result in results)
