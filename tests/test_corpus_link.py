"""Joining corpus spellings to lexicon readings, and the coverage figures."""

from collections.abc import Iterator
from pathlib import Path

from murfulu.corpus.adapter import SourceAdapter
from murfulu.corpus.documents import Document
from murfulu.corpus.link import LinkResult, link
from murfulu.corpus.wordtypes import build
from murfulu.lexicon import Lexicon


class TinyCorpus(SourceAdapter):
    """Words the fixture lexicon knows, plus one it does not."""

    @property
    def source_id(self) -> str:
        return "fixture"

    @property
    def licence(self) -> str:
        return "CC0-1.0"

    def documents(self) -> Iterator[Document]:
        # مرد is two readings; رفتن is one; واژه is in no lexicon entry.
        yield Document(
            source_id="fixture",
            document_id="fixture:a:1",
            text_fa="مرد رفتن واژه واژه واژه",
            author="poet_a",
            century=11,
        )


def _link(snapshot: Path) -> LinkResult:
    with Lexicon.open(snapshot) as lexicon:
        return link(build(TinyCorpus()), lexicon)


def test_a_known_spelling_gets_its_reading(lexicon_snapshot: Path):
    result = _link(lexicon_snapshot)
    raftan = next(i for i in result.linked if i.spelling_fa == "رفتن")
    assert raftan.latin == "raftan"
    assert raftan.reading.past_stem_latin == "raft"


def test_a_spelling_with_two_readings_gives_two_records(lexicon_snapshot: Path):
    """The corpus cannot tell mard from mord, so both are kept."""
    result = _link(lexicon_snapshot)
    mard = [i for i in result.linked if i.spelling_fa == "مرد"]
    assert sorted(i.latin for i in mard) == ["mard", "mord"]
    assert {i.word.total_count for i in mard} == {1}, "both carry the same evidence"
    assert result.coverage.ambiguous_types == 1


def test_an_unknown_spelling_is_kept_with_no_reading(lexicon_snapshot: Path):
    """That pile is the coverage gap and the review list, not an error."""
    result = _link(lexicon_snapshot)
    vaje = next(i for i in result.linked if i.spelling_fa == "واژه")
    assert vaje.latin is None
    assert vaje.reading is None
    assert vaje in result.unlinked


def test_the_identity_is_spelling_plus_latin(lexicon_snapshot: Path):
    result = _link(lexicon_snapshot)
    raftan = next(i for i in result.linked if i.spelling_fa == "رفتن")
    assert raftan.id == "رفتن:raftan"


def test_coverage_is_reported_both_ways(lexicon_snapshot: Path):
    """Types say how much vocabulary; tokens say how much running text."""
    coverage = _link(lexicon_snapshot).coverage
    assert coverage.types_total == 3
    assert coverage.types_linked == 2
    assert coverage.tokens_total == 5, "واژه occurs three times"
    assert coverage.tokens_linked == 2
    assert coverage.type_share == 2 / 3
    assert coverage.token_share == 2 / 5


def test_the_summary_line_states_both_numbers(lexicon_snapshot: Path):
    summary = _link(lexicon_snapshot).coverage.summary()
    assert "spellings linked" in summary
    assert "words of text" in summary


def test_the_biggest_gaps_come_first(lexicon_snapshot: Path):
    """Fix the most common unlinked word first, not the rarest."""
    gaps = _link(lexicon_snapshot).biggest_gaps()
    assert gaps[0].spelling_fa == "واژه"
    assert gaps[0].word.total_count == 3


def test_the_snapshot_it_was_linked_against_is_recorded(lexicon_snapshot: Path):
    assert _link(lexicon_snapshot).lexicon_snapshot_id.startswith("lexicon-fixture:")


def test_an_empty_corpus_does_not_divide_by_zero(lexicon_snapshot: Path):
    from murfulu.corpus.wordtypes import Corpus

    with Lexicon.open(lexicon_snapshot) as lexicon:
        result = link(Corpus(), lexicon)
    assert result.coverage.type_share == 0.0
    assert result.coverage.token_share == 0.0
