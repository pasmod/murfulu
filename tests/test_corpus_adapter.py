"""The shared adapter contract, proved with a fixture adapter."""

from collections.abc import Iterator

import pytest

from murfulu.corpus.adapter import SourceAdapter
from murfulu.corpus.contract import AdapterContractError, check_adapter
from murfulu.corpus.documents import Document, InvalidDocumentError

POEMS = [
    ("fixture:poet_a:divan:1", "شنیدم که چون قوی زیبا بمیرد", "poet_a", 7),
    ("fixture:poet_a:divan:2", "توانا بود هر که دانا بود", "poet_a", 7),
    ("fixture:poet_b:prose:1", "روش رفتار گفتار", "poet_b", 12),
]


class FixtureCorpus(SourceAdapter):
    """A three-document corpus, standing in for a real source."""

    @property
    def source_id(self) -> str:
        return "fixture"

    @property
    def licence(self) -> str:
        return "CC0-1.0"

    def documents(self) -> Iterator[Document]:
        for document_id, text, author, century in POEMS:
            yield Document(
                source_id="fixture",
                document_id=document_id,
                text_fa=text,
                author=author,
                century=century,
            )


def test_the_fixture_adapter_passes_the_shared_test():
    assert check_adapter(FixtureCorpus()) == 3


def test_the_adapter_describes_itself_for_the_ingest_log():
    assert FixtureCorpus().describe() == "fixture (CC0-1.0)"


class Nameless(FixtureCorpus):
    @property
    def source_id(self) -> str:
        return "Fixture Corpus"


class Unlicensed(FixtureCorpus):
    @property
    def licence(self) -> str:
        return "  "


class Empty(FixtureCorpus):
    def documents(self) -> Iterator[Document]:
        return iter(())


class Repeating(FixtureCorpus):
    def documents(self) -> Iterator[Document]:
        for _ in range(2):
            yield Document(source_id="fixture", document_id="fixture:a:1", text_fa="x")


class Unstable(FixtureCorpus):
    def __init__(self) -> None:
        self.pass_number = 0

    def documents(self) -> Iterator[Document]:
        self.pass_number += 1
        order = POEMS if self.pass_number == 1 else list(reversed(POEMS))
        for document_id, text, author, century in order:
            yield Document(
                source_id="fixture",
                document_id=document_id,
                text_fa=text,
                author=author,
                century=century,
            )


@pytest.mark.parametrize(
    ("adapter", "complaint"),
    [
        (Nameless(), "lower-case"),
        (Unlicensed(), "licence"),
        (Empty(), "no documents"),
        (Repeating(), "twice"),
        (Unstable(), "not repeatable"),
    ],
)
def test_a_broken_adapter_is_rejected_with_a_reason(
    adapter: SourceAdapter, complaint: str
):
    with pytest.raises(AdapterContractError, match=complaint):
        check_adapter(adapter)


@pytest.mark.parametrize(
    ("kwargs", "complaint"),
    [
        ({"document_id": "nocolon"}, "source:path:to:item"),
        ({"document_id": "other:a:1"}, "does not start with"),
        ({"text_fa": "   "}, "no text"),
        ({"century": 99}, "out of range"),
    ],
)
def test_an_unindexable_document_is_rejected(kwargs: dict[str, object], complaint: str):
    fields: dict[str, object] = {
        "source_id": "fixture",
        "document_id": "fixture:a:1",
        "text_fa": "متن",
        **kwargs,
    }
    with pytest.raises(InvalidDocumentError, match=complaint):
        Document(**fields)  # type: ignore[arg-type]


def test_source_specific_fields_go_in_extra():
    """Adding a corpus must not widen the shared document class."""
    document = Document(
        source_id="fixture",
        document_id="fixture:a:1",
        text_fa="متن",
        extra={"metre": "hazaj"},
    )
    assert document.extra["metre"] == "hazaj"


def test_a_source_with_no_persian_licence_falls_back_to_the_english():
    """A missing sentence about copyright is worse than one in English.

    `licence_fa` is not abstract for exactly this reason: adding it must not
    make every existing adapter fail to construct, and a source that has not
    written its Persian yet still has something to show.
    """
    assert FixtureCorpus().licence_fa == "CC0-1.0"
