"""Has this word ever been used? Three answers, and what each one means."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from murfulu.corpus.adapter import SourceAdapter
from murfulu.corpus.documents import Document
from murfulu.corpus.link import link
from murfulu.corpus.wordtypes import build
from murfulu.lexicon import Lexicon
from murfulu.scoring.attestation import Index, Level


class TinyCorpus(SourceAdapter):
    """Words the fixture lexicon knows, and one it does not."""

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
            text_fa="مرد رفتن گفتار گفتار",
            author="poet_a",
            century=11,
        )
        yield Document(
            source_id="fixture",
            document_id="fixture:b:1",
            text_fa="گفتار",
            author="poet_b",
            century=14,
        )


@pytest.fixture
def index(lexicon_snapshot: Path) -> Index:
    with Lexicon.open(lexicon_snapshot) as lexicon:
        return Index.from_link(link(build(TinyCorpus()), lexicon), "fixture-v1")


def test_a_known_word_is_attested_at_reading_level(index: Index):
    """The corpus has the spelling and the lexicon reads it our way."""
    found = index.look_up("رفتن", "raftan")
    assert found.level is Level.READING
    assert found.found
    assert found.total_count == 1


def test_a_novel_word_is_not_found(index: Index):
    found = index.look_up("رواندنااا", "ravāndanāāā")
    assert found.level is Level.NONE
    assert not found.found
    assert found.total_count == 0


def test_not_found_never_claims_the_word_does_not_exist(index: Index):
    """It only ever says: not in this corpus, this version."""
    described = index.look_up("رواندنااا", "ravāndanāāā").describe()
    assert described == "not found in corpus fixture-v1"
    assert "not exist" not in described


def test_the_same_spelling_under_another_reading(index: Index):
    """مرد is written, but as mard or mord — not as whatever we built."""
    found = index.look_up("مرد", "Mordan")
    assert found.level is Level.SPELLING
    assert sorted(found.other_readings) == ["mard", "mord"]
    assert not found.spelling_unlinked
    assert "read as" in found.describe()


def test_a_written_word_the_lexicon_cannot_confirm(index: Index):
    """گفتار is written three times but has no lexicon entry.

    That is a gap in the dictionary, not a doubt about the word, and the two
    must not look the same to a reader.
    """
    found = index.look_up("گفتار", "Goftār")
    assert found.level is Level.SPELLING
    assert found.spelling_unlinked
    assert found.other_readings == ()
    assert found.total_count == 3
    assert "no reading for this spelling" in found.describe()


def test_the_evidence_travels_with_the_answer(index: Index):
    found = index.look_up("گفتار", "Goftār")
    assert found.doc_count == 2
    assert found.author_count == 2
    assert (found.first_century, found.last_century) == (11, 14)


def test_every_answer_names_the_corpus_it_came_from(index: Index):
    """A count is only true for one corpus version."""
    for pair in (("رفتن", "raftan"), ("مرد", "x"), ("نیست", "nist")):
        assert index.look_up(*pair).corpus_version == "fixture-v1"


def test_many_forms_are_asked_at_once(index: Index):
    """Generation makes hundreds of candidates; one at a time would be slow."""
    pairs = [("رفتن", "raftan"), ("گفتار", "Goftār"), ("نیست", "nist")]
    answers = index.look_up_many(pairs)
    assert set(answers) == set(pairs)
    assert [answers[p].level for p in pairs] == [
        Level.READING,
        Level.SPELLING,
        Level.NONE,
    ]


def test_spelling_variants_do_not_split_the_evidence(index: Index):
    """Arabic ي and Persian ی are one spelling, as in the counting pass."""
    assert index.look_up("گفتار", "Goftār").total_count == 3
