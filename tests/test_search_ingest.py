"""Putting the corpus into Elasticsearch.

The document shapes are checked without a cluster; the writes need one and
skip without it. The mappings are ``dynamic: strict``, so the live half is the
only real proof that what we build and what the index accepts agree.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from murfulu.corpus import link, wordtypes
from murfulu.corpus.adapter import SourceAdapter
from murfulu.corpus.documents import Document
from murfulu.corpus.ganjoor import GanjoorCorpus
from murfulu.corpus.link import LinkResult
from murfulu.lexicon.store import Lexicon
from murfulu.search import ingest
from murfulu.search.indices import IndexAdmin, connect
from murfulu.search.mappings import DOCUMENTS, WORD_TYPES

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

VERSION = "test-ingest"


class _Poems(SourceAdapter):
    """A handmade corpus that shares words with the fixture lexicon.

    The Ganjoor fixture is two real lines of Hafez and Khayyam, and it has no
    word in common with the handmade lexicon — so nothing links and the linked
    half of this module would go untested.
    """

    @property
    def source_id(self) -> str:
        """The prefix every document id carries."""
        return "fixture"

    @property
    def licence(self) -> str:
        """Written for the test, so it is nobody's material."""
        return "written for this test"

    def documents(self) -> Iterator[Document]:
        """Two poems using words the fixture lexicon knows."""
        for number, text in enumerate(["مرد و پی و رفتن", "مرد آبرو گفتن"]):
            yield Document(
                source_id="fixture",
                document_id=f"fixture:{number}",
                text_fa=text,
                author="شاعر",
                century=6,
            )


@pytest.fixture
def adapter(ganjoor_snapshot: Path) -> GanjoorCorpus:
    return GanjoorCorpus(ganjoor_snapshot, centuries={"hafez": 8})


@pytest.fixture
def linked(lexicon_snapshot: Path) -> LinkResult:
    corpus = wordtypes.build(_Poems())
    with Lexicon.open(lexicon_snapshot) as lexicon:
        return link.link(corpus, lexicon)


# -- the shapes, no cluster needed -------------------------------------------


def test_a_document_only_uses_declared_fields(adapter: GanjoorCorpus):
    declared = set(DOCUMENTS["properties"])
    for document in adapter.documents():
        source = ingest.document_source(document, VERSION, adapter.licence)
        assert set(source) <= declared


def test_a_word_type_only_uses_declared_fields(linked: LinkResult):
    declared = set(WORD_TYPES["properties"])
    for item in linked.linked:
        source = ingest.word_type_source(item, VERSION, linked.lexicon_snapshot_id)
        assert set(source) <= declared


def test_an_unlinked_spelling_still_gets_a_document(linked: LinkResult):
    """That pile is the coverage gap. Dropping it hides what is worth measuring."""
    assert linked.unlinked
    for item in linked.unlinked:
        source = ingest.word_type_source(item, VERSION, "")
        assert source["latin"] is None
        assert source["population"] == ["corpus"]


def test_a_linked_spelling_carries_its_reading(linked: LinkResult):
    by_id = {
        item.id: ingest.word_type_source(item, VERSION, linked.lexicon_snapshot_id)
        for item in linked.linked
        if item.reading
    }
    assert by_id
    for source in by_id.values():
        assert source["latin"]
        assert "lexicon" in source["population"]
        assert source["lexicon_snapshot_id"]


def test_the_reversed_field_is_the_reversed_latin(linked: LinkResult):
    """*Ends with nā* is a prefix query on this field. It is the whole point."""
    for item in linked.linked:
        source = ingest.word_type_source(item, VERSION, "")
        if source["latin"]:
            assert source["latin_reversed"] == source["latin"][::-1]
        else:
            assert source["latin_reversed"] is None


def test_the_derivation_fields_are_declared_but_empty(linked: LinkResult):
    """Written by a later pass. Empty here, never absent — see PLAN 6.4."""
    for item in linked.linked:
        source = ingest.word_type_source(item, VERSION, "")
        assert source["affixes"] == []
        assert source["rule_ids"] == []


def test_an_unmappable_category_yields_no_word_class(linked: LinkResult):
    """وام‌واژه and friends are deliberately unmapped, and must not crash."""
    assert ingest._word_classes("وام‌واژه") == []
    assert ingest._word_classes(None) == []
    assert ingest._word_classes("مصدر") == ["nabesudkarvaze"]


# -- the writes, live cluster --------------------------------------------------


@pytest.fixture
def admin() -> Iterator[IndexAdmin]:
    url = os.environ.get("MURFULU_ELASTICSEARCH_URL", "http://localhost:9200")
    client = connect(url)
    try:
        reachable = client.ping()
    except Exception:  # noqa: BLE001 - any failure means "not reachable"
        reachable = False
    if not reachable:
        pytest.skip(f"no Elasticsearch at {url}")

    def clean() -> None:
        for alias in (ingest.DOCUMENTS, ingest.WORD_TYPES):
            found = client.indices.get(
                index=f"{alias}-{VERSION}", ignore_unavailable=True
            )
            for name in found.body:
                client.indices.delete(index=name)

    clean()
    admin = IndexAdmin(client)
    admin.create(ingest.DOCUMENTS, VERSION)
    admin.create(ingest.WORD_TYPES, VERSION)
    yield admin
    clean()


def test_every_poem_is_written(admin: IndexAdmin, adapter: GanjoorCorpus):
    result = ingest.write_documents(admin.client, VERSION, adapter)
    assert result.complete, result.failures
    admin.client.indices.refresh(index=f"{ingest.DOCUMENTS}-{VERSION}")
    counted = admin.client.count(index=f"{ingest.DOCUMENTS}-{VERSION}")["count"]
    assert counted == result.written == len(list(adapter.documents()))


def test_every_word_type_is_written(admin: IndexAdmin, linked: LinkResult):
    result = ingest.write_word_types(admin.client, VERSION, linked)
    assert result.complete, result.failures
    admin.client.indices.refresh(index=f"{ingest.WORD_TYPES}-{VERSION}")
    counted = admin.client.count(index=f"{ingest.WORD_TYPES}-{VERSION}")["count"]
    assert counted == result.written == len(linked.linked)


def test_a_stored_poem_keeps_its_provenance(admin: IndexAdmin, adapter: GanjoorCorpus):
    ingest.write_documents(admin.client, VERSION, adapter)
    admin.client.indices.refresh(index=f"{ingest.DOCUMENTS}-{VERSION}")
    first = next(iter(adapter.documents()))
    stored = admin.client.get(
        index=f"{ingest.DOCUMENTS}-{VERSION}", id=first.document_id
    )["_source"]
    assert stored["author"] == first.author
    assert stored["licence"] == adapter.licence
    assert stored["corpus_version"] == VERSION
