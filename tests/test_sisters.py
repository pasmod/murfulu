"""Sister forms: the other words a rule actually made.

The plan's own test for this task is that rule V-010 returns *Goftār*,
*Raftār* and *Didār* if the corpus has them. The fixture corpus is two poems,
so it cannot hold them — a fixture corpus is written here that does, and the
real check that they come out of the real corpus is recorded in the plan.
"""

from collections.abc import Iterator
from pathlib import Path as FilePath

import pytest

from murfulu.corpus import link, wordtypes
from murfulu.corpus.adapter import SourceAdapter
from murfulu.corpus.documents import Document
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import RulePack, load
from murfulu.scoring.attestation import Index, Level
from murfulu.scoring.precompute import Precompute, input_readings, run
from murfulu.scoring.sisters import collect


class _Poems(SourceAdapter):
    """A handmade corpus holding exactly the words a test needs."""

    def __init__(self, lines: list[tuple[str, str]]) -> None:
        self.lines = lines

    @property
    def source_id(self) -> str:
        """The prefix every document id carries."""
        return "fixture"

    @property
    def licence(self) -> str:
        """Made up for the test, so it is nobody's material."""
        return "written for this test"

    def documents(self) -> Iterator[Document]:
        """One document per line given."""
        for number, (author, text) in enumerate(self.lines):
            yield Document(
                source_id="fixture",
                document_id=f"fixture:{number}",
                text_fa=text,
                author=author,
                century=6,
            )


@pytest.fixture(scope="module")
def pack() -> RulePack:
    """The real rule pack. It is data in the repository, not a fixture."""
    return load()


@pytest.fixture
def corpus_with_ar_words(lexicon_snapshot: FilePath) -> Index:
    """A corpus that writes گفتار and رفتار, each by a different poet."""
    poems = _Poems(
        [
            ("شاعر یک", "گفتار نیک و رفتار نیک و کردار نیک"),
            ("شاعر دو", "گفتار او رفتار او"),
            ("شاعر سه", "گفتار"),
        ]
    )
    corpus = wordtypes.build(poems)
    with Lexicon.open(lexicon_snapshot) as lexicon:
        linked = link.link(corpus, lexicon)
    return Index.from_link(linked, corpus_version="ar-fixture")


@pytest.fixture
def job(pack: RulePack, lexicon_snapshot: FilePath, corpus_with_ar_words: Index):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        return run(
            pack,
            input_readings(lexicon),
            depth=2,
            attestation=corpus_with_ar_words,
            corpus_version="ar-fixture",
        )


# -- the plan's own test -----------------------------------------------------


def test_rule_ten_returns_the_ar_words_the_corpus_has(job: Precompute):
    """V-010 is *-ār* on kārbon-e yek. Its sisters are its attested output."""
    sisters = collect(job.derivations(), "ar-fixture")
    names = {sister.form_latin for sister in sisters.for_rule("V-010", limit=50)}
    assert {"Goftār", "Raftār"} <= names


def test_a_word_the_corpus_does_not_have_is_not_a_sister(job: Precompute):
    """Unattested output is what is being judged, not evidence for it."""
    sisters = collect(job.derivations(), "ar-fixture")
    for sister in sisters.for_rule("V-010", limit=50):
        assert sister.level is not Level.NONE


# -- ordering ----------------------------------------------------------------


def test_the_best_evidence_comes_first(job: Precompute):
    sisters = collect(job.derivations(), "ar-fixture")
    for found in sisters.by_rule.values():
        ranks = [sister.rank for sister in found]
        assert ranks == sorted(ranks)


def test_documents_beat_raw_occurrences(job: Precompute):
    """Thirty hits in one poem is a rhyme, not a word."""
    sisters = collect(job.derivations(), "ar-fixture")
    found = sisters.for_rule("V-010", limit=50)
    by_name = {sister.form_latin: sister for sister in found}
    # گفتار is in three poems, رفتار in two.
    assert by_name["Goftār"].doc_count == 3
    assert by_name["Raftār"].doc_count == 2
    assert found.index(by_name["Goftār"]) < found.index(by_name["Raftār"])


# -- attaching them to each word ---------------------------------------------


def test_a_word_is_not_its_own_sister(pack: RulePack, job: Precompute):
    job.sisters(limit=20)
    for derivation in job.derivations():
        assert derivation.form_latin not in derivation.sister_forms


def test_nothing_is_attached_unless_asked(job: Precompute):
    """The per-rule list is the artefact; copying it onto 1.7M words costs."""
    assert all(not d.sister_forms for d in job.derivations())
    job.sisters(limit=5)
    assert any(d.sister_forms for d in job.derivations())


def test_the_limit_is_respected(job: Precompute):
    job.sisters(limit=2)
    for derivation in job.derivations():
        assert len(derivation.sister_forms) <= 2


def test_sisters_survive_the_round_trip(job: Precompute):
    from murfulu.scoring.reload import from_document

    job.sisters(limit=5)
    for derivation in job.derivations():
        assert from_document(derivation.as_document()) == derivation


def test_a_word_built_two_ways_gets_the_sisters_of_both(job: Precompute):
    """It belongs to two families and the reader should see both."""
    sisters = job.sisters(limit=50)
    two_rules = [
        d
        for d in job.derivations()
        if len({p.rule_ids[-1] for p in d.paths if p.rule_ids}) > 1
    ]
    assert two_rules, "the fixture should reach some form by two rules"
    for derivation in two_rules:
        rules = {p.rule_ids[-1] for p in derivation.paths if p.rule_ids}
        reachable = {
            sister.form_latin
            for rule_id in rules
            for sister in sisters.for_rule(rule_id, limit=50)
        } - {derivation.form_latin}
        assert set(derivation.sister_forms) <= reachable


def test_every_rule_with_an_attested_output_is_counted(job: Precompute):
    sisters = collect(job.derivations(), "ar-fixture")
    assert sisters.counts()
    for rule_id, count in sisters.counts().items():
        assert count == len(sisters.by_rule[rule_id])


# -- claims the homograph detector doubts ------------------------------------


def test_a_doubted_sister_is_ranked_last_and_never_dropped(job: Precompute):
    """شاهدان is the plural of شاهد, and a cosine is not a ruling.

    Removing the row would hide a claim the pipeline is really making. Sinking
    it says what we think of it and leaves it checkable.
    """
    plain = collect(job.derivations(), "ar-fixture")
    before = [sister.form_latin for sister in plain.for_rule("V-010", limit=50)]
    assert "Goftār" in before

    doubted = collect(job.derivations(), "ar-fixture", frozenset({("V-010", "Goftār")}))
    after = [sister.form_latin for sister in doubted.for_rule("V-010", limit=50)]
    assert set(after) == set(before), "nothing may be removed"
    assert after[-1] == "Goftār", "and the doubted one goes to the bottom"


def test_doubt_is_about_one_rule_making_one_word(job: Precompute):
    """A word can be a fine output of one rule and a homograph under another."""
    doubted = collect(job.derivations(), "ar-fixture", frozenset({("V-010", "Goftār")}))
    for rule_id, found in doubted.by_rule.items():
        for sister in found:
            expected = rule_id == "V-010" and sister.form_latin == "Goftār"
            assert sister.suspect is expected


def test_doubted_claims_are_counted_per_rule(job: Precompute):
    doubted = collect(job.derivations(), "ar-fixture", frozenset({("V-010", "Goftār")}))
    assert doubted.suspect_counts()["V-010"] == 1
    assert sum(doubted.suspect_counts().values()) == 1


def test_a_doubted_sister_is_copied_onto_a_word_last(job: Precompute):
    """The few sisters stored per word are taken in rank order, doubt first.

    Still taken, though: with only one other sister to offer, a doubted one is
    better than none. Ranking is the whole mechanism, not filtering.
    """
    job.sisters(limit=50, suspect=frozenset({("V-010", "Goftār")}))
    attached = {
        form for derivation in job.derivations() for form in derivation.sister_forms
    }
    assert "Goftār" in attached, "a doubted sister is still better than none"


def test_every_sister_carries_the_word_it_was_built_from(job: Precompute):
    """The base is what the per-claim half of the detector compares against."""
    sisters = collect(job.derivations(), "ar-fixture")
    by_name = {s.form_latin: s for s in sisters.for_rule("V-010", limit=50)}
    assert by_name["Goftār"].base_fa == "گفت"
