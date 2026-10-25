"""What one ingest measured, written down and read back.

The done test for PLAN 7.8 is that the corpus screen shows coverage. These
check the half the screen cannot invent: that the figures the ingest already
counts survive the round trip, that the two coverage shares stay apart, and
that a machine with no report says so instead of showing zeros.
"""

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from murfulu.corpus import report
from murfulu.corpus.adapter import SourceAdapter
from murfulu.corpus.documents import Document
from murfulu.corpus.link import link
from murfulu.corpus.wordtypes import build
from murfulu.lexicon import Lexicon

WHEN = datetime(2026, 8, 12, 9, 0, tzinfo=UTC)


class TinyCorpus(SourceAdapter):
    """Two poems: words the fixture lexicon knows, and one it does not."""

    @property
    def source_id(self) -> str:
        return "fixture"

    @property
    def licence(self) -> str:
        return "CC0-1.0"

    def poets_without_a_century(self) -> list[str]:
        return ["poet_b"]

    def centuries_without_a_poet(self) -> list[str]:
        return ["poet_who_is_not_here"]

    def documents(self) -> Iterator[Document]:
        # مرد has two readings, رفتن one, واژه none — and واژه occurs four
        # times, so it is the biggest gap.
        yield Document(
            source_id="fixture",
            document_id="fixture:a:1",
            text_fa="مرد رفتن واژه واژه واژه",
            author="poet_a",
            century=11,
        )
        yield Document(
            source_id="fixture",
            document_id="fixture:b:1",
            text_fa="واژه",
        )


def _report(snapshot: Path) -> report.CorpusReport:
    corpus_source = TinyCorpus()
    corpus = build(corpus_source)
    with Lexicon.open(snapshot) as lexicon:
        linked = link(corpus, lexicon)
    return report.build(corpus_source, corpus, linked, "v-test", now=WHEN)


def test_it_carries_the_source_its_licence_and_when_it_ran(lexicon_snapshot: Path):
    """A corpus whose licence nobody wrote down cannot be shipped."""
    measured = _report(lexicon_snapshot)
    assert measured.source_id == "fixture"
    assert measured.licence == "CC0-1.0"
    assert measured.built_at.startswith("2026-08-12")
    assert measured.corpus_version == "v-test"
    assert measured.lexicon_snapshot_id


def test_the_sizes_are_the_counts_the_ingest_made(lexicon_snapshot: Path):
    measured = _report(lexicon_snapshot)
    assert measured.documents == 2
    assert measured.tokens == 6, "مرد رفتن واژه×3, then واژه again"
    assert measured.spellings == 3
    # One document per *reading*: مرد is two, so four rather than three.
    assert measured.word_types == 4


def test_type_coverage_and_token_coverage_are_different_questions(
    lexicon_snapshot: Path,
):
    """The vocabulary we can read, and the text we can read, are not the same.

    On the real corpus this is 4.1% against 45.7%, and reading the first as a
    quality figure is the mistake the two numbers exist to prevent.
    """
    measured = _report(lexicon_snapshot)
    assert measured.spellings_linked == 2
    assert measured.type_share == pytest.approx(2 / 3)
    # واژه is four of the six words, so token coverage is the lower one here.
    assert measured.tokens_linked == 2
    assert measured.token_share == pytest.approx(1 / 3)
    assert measured.type_share != measured.token_share


def test_the_unmatched_pile_is_named_biggest_first(lexicon_snapshot: Path):
    """It is a deliverable, not a residue: the words the dictionary misses."""
    measured = _report(lexicon_snapshot)
    assert [gap.spelling_fa for gap in measured.biggest_gaps] == ["واژه"]
    gap = measured.biggest_gaps[0]
    assert gap.total_count == 4
    assert gap.doc_count == 2
    assert gap.author_count == 1, "one of the two poems has no author"


def test_the_gaps_in_the_evidence_are_reported_not_hidden(lexicon_snapshot: Path):
    """A document with no author or no date weakens every word it carries."""
    measured = _report(lexicon_snapshot)
    assert measured.documents_without_author == 1
    assert measured.documents_without_century == 1
    assert measured.poets_without_a_century == ["poet_b"]
    # A century-table entry naming a poet the corpus does not have dates
    # nothing and looks exactly like one that works.
    assert measured.centuries_without_a_poet == ["poet_who_is_not_here"]


def test_two_readings_of_one_spelling_are_counted(lexicon_snapshot: Path):
    measured = _report(lexicon_snapshot)
    assert measured.ambiguous_spellings == 1


def test_it_survives_being_written_and_read_back(
    lexicon_snapshot: Path, tmp_path: Path
):
    measured = _report(lexicon_snapshot)
    written = report.write(measured, tmp_path / "corpus_report-v-test.json")
    again = report.from_document(json.loads(written.read_text(encoding="utf-8")))
    assert again == measured


def test_the_stored_shape_carries_the_shares_it_computes(
    lexicon_snapshot: Path, tmp_path: Path
):
    """The reader does the arithmetic once, not once per screen."""
    measured = _report(lexicon_snapshot)
    document = json.loads(
        report.write(measured, tmp_path / "r.json").read_text(encoding="utf-8")
    )
    assert document["type_share"] == pytest.approx(2 / 3)
    assert document["token_share"] == pytest.approx(1 / 3)
    assert document["spellings_unlinked"] == 1


def test_no_report_is_an_answer_not_an_error(monkeypatch: pytest.MonkeyPatch):
    """A machine that never ran an ingest has nothing to show, and says so."""
    monkeypatch.delenv(report.PATH_VARIABLE, raising=False)
    report.loaded.cache_clear()
    empty = report.loaded()
    assert not empty.measured
    assert empty.type_share == 0.0
    report.loaded.cache_clear()


def test_the_configured_file_is_read(
    lexicon_snapshot: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    written = report.write(_report(lexicon_snapshot), tmp_path / "r.json")
    monkeypatch.setenv(report.PATH_VARIABLE, str(written))
    report.loaded.cache_clear()
    assert report.loaded().corpus_version == "v-test"
    report.loaded.cache_clear()


def test_a_path_that_is_not_there_is_not_an_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv(report.PATH_VARIABLE, str(tmp_path / "nothing.json"))
    report.loaded.cache_clear()
    assert not report.loaded().measured
    report.loaded.cache_clear()


def test_a_report_written_before_the_field_still_shows_persian():
    """A licence is a fact about the source, not something an ingest measured.

    The live corpus report is v11 and was written before `licence_fa` existed,
    so the corpus screen fell back to the English — the exact thing the field
    was added to stop a reader seeing — and would have gone on doing so until
    the next ingest, which is hours of work for one sentence.
    """
    from murfulu.corpus.report import from_document

    stored = {"corpus_version": "v11", "source_id": "ganjoor", "licence": "in English"}
    read = from_document(stored)
    assert "گنجور" in read.licence_fa
    # The English is untouched: it is what the log and NOTICE carry.
    assert read.licence == "in English"


def test_a_source_we_have_no_persian_for_gets_none_rather_than_the_wrong_one():
    from murfulu.corpus.report import from_document

    read = from_document({"corpus_version": "v1", "source_id": "somewhere_else"})
    assert read.licence_fa == ""


def test_a_report_that_carries_its_own_persian_keeps_it():
    """Filling a gap, never overwriting what an ingest wrote."""
    from murfulu.corpus.report import from_document

    read = from_document(
        {"source_id": "ganjoor", "licence_fa": "چیز دیگری که خود درون‌ریزی نوشته"}
    )
    assert read.licence_fa == "چیز دیگری که خود درون‌ریزی نوشته"


def test_the_source_has_a_persian_name_to_read_beside_the_id_to_type():
    """The corpus screen headed a column سرچشمه and wrote «ganjoor» under it.

    The identifier is what `source:ganjoor` is written with and it does not
    move; what a Persian page shows a reader is the name. Same terms as the
    licence beside it — a name is a fact about the source, not a measurement,
    so a report written before the field existed can be filled in from here.
    """
    from murfulu.corpus.report import from_document

    read = from_document({"corpus_version": "v11", "source_id": "ganjoor"})
    assert read.source_name_fa == "گنجور"
    assert read.source_id == "ganjoor"


def test_a_source_we_have_no_persian_name_for_falls_back_to_its_id():
    """Named badly beats not named at all: the screen still shows something."""
    from murfulu.corpus.report import from_document

    read = from_document({"corpus_version": "v1", "source_id": "somewhere_else"})
    assert read.source_name_fa == ""
