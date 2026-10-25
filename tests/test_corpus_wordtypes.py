"""Counting spellings, and what each count means."""

from collections.abc import Iterator

import pytest

from murfulu.corpus.adapter import SourceAdapter
from murfulu.corpus.documents import Document
from murfulu.corpus.wordtypes import build, normalise, tokenise


class TinyCorpus(SourceAdapter):
    """Three poems by two poets, with known counts."""

    @property
    def source_id(self) -> str:
        return "fixture"

    @property
    def licence(self) -> str:
        return "CC0-1.0"

    def documents(self) -> Iterator[Document]:
        yield Document(
            source_id="fixture",
            document_id="fixture:a:1",
            text_fa="روش و روش نیک\nگفتار نیک",
            author="poet_a",
            century=11,
        )
        yield Document(
            source_id="fixture",
            document_id="fixture:a:2",
            text_fa="گفتار نیک",
            author="poet_a",
            century=11,
        )
        yield Document(
            source_id="fixture",
            document_id="fixture:b:1",
            text_fa="گفتار تازه",
            author="poet_b",
            century=14,
        )


CORPUS = build(TinyCorpus())


def test_the_corpus_is_counted_end_to_end():
    assert CORPUS.document_count == 3
    assert CORPUS.token_count == 10
    # روش، و، نیک، گفتار، تازه
    assert len(CORPUS) == 5


def test_occurrences_and_documents_are_different_numbers():
    """30 hits in one poem is a rhyme, not a word. That is why both exist."""
    ravesh = CORPUS.get("روش")
    assert ravesh.total_count == 2, "twice, but both in the same poem"
    assert ravesh.doc_count == 1


def test_a_word_across_poems_counts_each_one():
    goftar = CORPUS.get("گفتار")
    assert goftar.total_count == 3
    assert goftar.doc_count == 3


def test_authors_are_counted_distinctly():
    """One author means one poet's coinage, not a word of the language."""
    assert CORPUS.get("روش").author_count == 1
    assert CORPUS.get("گفتار").author_count == 2
    assert sorted(CORPUS.get("گفتار").top_authors) == ["poet_a", "poet_b"]


def test_centuries_show_whether_a_word_survived():
    goftar = CORPUS.get("گفتار")
    assert dict(goftar.counts_by_century) == {11: 2, 14: 1}
    assert (goftar.first_century, goftar.last_century) == (11, 14)

    tazé = CORPUS.get("تازه")
    assert (tazé.first_century, tazé.last_century) == (14, 14)


def test_a_word_the_corpus_does_not_have():
    assert CORPUS.get("واژه‌ای‌که‌نیست") is None


def test_the_source_travels_with_every_word():
    assert CORPUS.get("نیک").sources == {"fixture"}


# -- tokenising --------------------------------------------------------------


def test_the_zero_width_joiner_holds_a_word_together():
    """می‌رود is one word, not two."""
    assert tokenise("می‌رود") == ["می‌رود"]


@pytest.mark.parametrize(
    ("written", "expected"),
    [
        # Editions mix Arabic and Persian letters; both spell one word.
        ("كتاب", "کتاب"),
        ("يار", "یار"),
        # Harakat appear unevenly in classical texts.
        ("کِتاب", "کتاب"),
    ],
)
def test_spelling_variants_are_folded_into_one_word(written: str, expected: str):
    assert normalise(written) == expected
    assert tokenise(written) == [expected]


def test_punctuation_and_numbers_are_not_words():
    assert tokenise("گفتار، نیک! ۱۲۳") == ["گفتار", "نیک"]


def test_gaps_in_the_evidence_are_reported():
    """A document with no author or no date weakens every word in it."""

    class Anonymous(TinyCorpus):
        def documents(self) -> Iterator[Document]:
            yield Document(
                source_id="fixture", document_id="fixture:x:1", text_fa="گفتار"
            )

    corpus = build(Anonymous())
    assert corpus.documents_without_author == 1
    assert corpus.documents_without_century == 1
    assert corpus.get("گفتار").author_count == 0
    assert corpus.get("گفتار").first_century is None
