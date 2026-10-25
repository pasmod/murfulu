"""The sāzāyi check: take a word apart, and prove it by rebuilding.

Everything here runs against the fixture lexicon. The behaviour that matters
most is the refusal — a decomposer that explains everything is inventing.
"""

from pathlib import Path

import pytest

from murfulu import analysis
from murfulu.engine.decompose import propose
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import RulePack, loaded


@pytest.fixture(scope="module")
def pack() -> RulePack:
    return loaded()


def test_a_verb_form_is_traced_to_its_infinitive(
    lexicon_snapshot: Path, pack: RulePack
):
    """Raftār is raft + -ār, and raft is a stem, not a headword."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        found = analysis.explain(lexicon, pack, "Raftār")
    assert found.explained
    assert "raftan" in {account.base.latin for account in found.analyses}
    assert any(step.rule_id == "V-010" for one in found.analyses for step in one.steps)


def test_a_two_step_word_is_taken_apart_in_two(lexicon_snapshot: Path, pack: RulePack):
    """Ravandegi is ravande then -gi, and ravande is in no dictionary."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        found = analysis.explain(lexicon, pack, "Ravandegi")
    assert found.explained
    assert any(one.depth == 2 for one in found.analyses)


def test_the_shortest_account_comes_first(lexicon_snapshot: Path, pack: RulePack):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        found = analysis.explain(lexicon, pack, "Raftār")
    depths = [one.depth for one in found.analyses]
    assert depths == sorted(depths)


def test_a_word_that_only_looks_derived_is_refused(
    lexicon_snapshot: Path, pack: RulePack
):
    """The whole reason the account is rebuilt.

    Stripping *-nā* off a word can leave something a dictionary knows, and a
    decomposer that stopped there would announce a derivation that nobody
    built. Nothing in the fixture can produce these, so nothing claims them.
    """
    with Lexicon.open(lexicon_snapshot) as lexicon:
        for invented in ("Mowlānā", "Fanā", "Zzzqi"):
            found = analysis.explain(lexicon, pack, invented)
            assert not found.explained, invented


def test_capitalisation_belongs_to_the_result_not_the_base(pack: RulePack):
    """Raftār strips to *Raft*; the entry is *raft*. Both are proposed."""
    bases = {one.base for one in propose(pack, "Raftār")}
    assert "raft" in bases
    assert "Raft" in bases


def test_a_stem_written_one_way_and_behaving_another_is_reversed(pack: RulePack):
    """*rav* is how *row* behaves, so a remainder of *rav* proposes *row*."""
    bases = {one.base for one in propose(pack, "Raveš")}
    assert "row" in bases or "Row" in bases


def test_the_glide_is_taken_back_out(pack: RulePack):
    """*guyande* is *gu* + *-ande*; the *y* belongs to neither of them."""
    bases = {one.base for one in propose(pack, "guyande")}
    assert "gu" in bases


def test_a_word_built_over_a_glide_is_analysed(lexicon_snapshot: Path, pack: RulePack):
    """Built and then read back — the sāzāyi rule, on گفتن.

    The engine has always built *guyande* and *Guyeš* from گو. Until
    2026-08-20 it could not take either apart: the decomposer removed the
    affix as a string, which left *guy*, and no dictionary has that. All 13
    one-step forms with a glide in them from گفتن failed the same way, and all
    6 from آمدن.
    """
    with Lexicon.open(lexicon_snapshot) as lexicon:
        for word in ("guyande", "Guyeš"):
            found = analysis.explain(lexicon, pack, word)
            assert found.explained, word
            assert "goftan" in {one.base.latin for one in found.analyses}, word


def test_nothing_is_proposed_for_a_word_with_no_affix_shape(pack: RulePack):
    assert propose(pack, "x") == []


def test_the_affixes_tried_are_reported(lexicon_snapshot: Path, pack: RulePack):
    """Naming the attempts beats a bare "we could not take this apart"."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        found = analysis.explain(lexicon, pack, "Fanā")
    assert not found.explained
    assert found.unmatched_affixes


def test_a_search_that_ran_out_of_room_is_not_a_refusal(
    lexicon_snapshot: Path,
) -> None:
    """An empty answer means *no* only when the search finished.

    Found 2026-08-17 asking why درافکندگی does not rebuild — the case the
    coining experiment named as the engine's largest gap, and it turned out not
    to be a gap in the rules at all. The engine stops at 20,000 forms per base;
    building forward from افکندن reaches 20,050 at three steps, so the run
    stops before *Darafkandegi*. Every rule its chain needs exists and fires.

    The forward side has always reported this and the analysis threw it away,
    so a truncated search and an exhausted one gave a reader the same sentence.
    """
    from murfulu.analysis import Result

    unfinished = Result(form="X", searched_partially=["afkandan"])
    assert unfinished.explained is False
    assert unfinished.settled is False

    # مولانا is the case the whole check exists for: it strips to a real
    # dictionary word and nothing builds it back. That refusal must stay a
    # refusal — softening every empty answer would throw the check away.
    refused = Result(form="Mowlānā")
    assert refused.explained is False
    assert refused.settled is True

    # A found account settles the question whatever else ran short: the word
    # was rebuilt, and how much room the search had left does not change that.
    found = Result(form="X", searched_partially=["afkandan"])
    found.analyses.append(object())  # type: ignore[arg-type]
    assert found.settled is True
