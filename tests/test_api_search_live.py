"""The search routes against a live Elasticsearch.

Skips when no cluster is reachable, so the suite still runs on a bare machine.
What it proves is the half the offline tests cannot: that a real query returns
real hits, that the affix split is real, and that an index nobody has built
answers 503 rather than looking like an empty result.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from murfulu.api.app import app
from murfulu.search.indices import IndexAdmin, connect

from .conftest import aliases_restored

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

VERSION = "test-api"
ALIAS = "word_types"

# Two words that end in *-nā*, one of them actually formed with it. Keeping
# them apart is the whole reason the suffix search exists.
WORDS = [
    {
        "id": "تنکنا:Tonoknā",
        "spelling_fa": "تنکنا",
        "latin": "Tonoknā",
        "latin_reversed": "ānkonoT",
        "latin_wild": "Tonoknā",
        "word_class": "nam",
        "affixes": ["-nā"],
        "rule_ids": ["N-050"],
        "total_count": 3,
        "doc_count": 3,
        "author_count": 2,
        "first_century": 5,
        "last_century": 7,
        "population": ["corpus"],
        "corpus_version": VERSION,
    },
    {
        "id": "سنا:Sanā",
        "spelling_fa": "سنا",
        "latin": "Sanā",
        "latin_reversed": "ānaS",
        "latin_wild": "Sanā",
        "word_class": "nam",
        "affixes": [],
        "rule_ids": [],
        "total_count": 1,
        "doc_count": 1,
        "author_count": 1,
        "first_century": 6,
        "last_century": 6,
        "population": ["corpus"],
        "corpus_version": VERSION,
    },
]


@pytest.fixture
def live() -> Iterator[IndexAdmin]:
    """A filled, released ``word_types`` index, or skip."""
    url = os.environ.get("MURFULU_ELASTICSEARCH_URL", "http://localhost:9200")
    client = connect(url)
    try:
        reachable = client.ping()
    except Exception:  # noqa: BLE001 - any failure means "not reachable"
        reachable = False
    if not reachable:
        pytest.skip(f"no Elasticsearch at {url}")

    def clean() -> None:
        found = client.indices.get(index=f"{ALIAS}-{VERSION}", ignore_unavailable=True)
        for name in found.body:
            client.indices.delete(index=name)

    # This fixture moves the alias the app serves from, on purpose — that is
    # what makes it a test of the real route. Putting it back is not optional:
    # see tests/conftest.py.
    with aliases_restored(client, [ALIAS]):
        clean()
        admin = IndexAdmin(client)
        admin.create(ALIAS, VERSION)
        for word in WORDS:
            client.index(index=f"{ALIAS}-{VERSION}", id=word["id"], document=word)
        client.indices.refresh(index=f"{ALIAS}-{VERSION}")
        admin.release(ALIAS, VERSION)
        yield admin
        clean()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_a_suffix_search_finds_both_kinds_of_match(
    live: IndexAdmin, client: TestClient
):
    body = client.get("/search", params={"q": "*nā"}).json()
    assert body["total"] == 2


def test_the_two_groups_are_kept_apart(live: IndexAdmin, client: TestClient):
    """*Sanā* merely ends in the letters; *Tonoknā* was formed with them."""
    body = client.get("/search", params={"q": "*nā", "affix": "-nā"}).json()
    assert [hit["latin"] for hit in body["formed_with_affix"]] == ["Tonoknā"]
    assert [hit["latin"] for hit in body["string_match_only"]] == ["Sanā"]


def test_persian_input_searches_the_spelling(live: IndexAdmin, client: TestClient):
    body = client.get("/search", params={"q": "تنکنا"}).json()
    assert body["total"] == 1


def test_a_hapax_search_means_exactly_once(live: IndexAdmin, client: TestClient):
    body = client.get("/search", params={"q": "count:1"}).json()
    assert [hit["latin"] for hit in body["string_match_only"]] == ["Sanā"]


def test_a_century_range_matches_any_overlap(live: IndexAdmin, client: TestClient):
    body = client.get("/search", params={"q": "century:7-9"}).json()
    assert body["total"] == 1


def test_one_word_can_be_fetched_by_id(live: IndexAdmin, client: TestClient):
    body = client.get("/word/سنا:Sanā", params={"index": "word_types"}).json()
    assert body["word"]["latin"] == "Sanā"


def test_a_missing_word_is_a_404(live: IndexAdmin, client: TestClient):
    response = client.get("/word/nothing", params={"index": "word_types"})
    assert response.status_code == 404


def test_the_corpus_route_names_what_is_being_served(
    live: IndexAdmin, client: TestClient
):
    """Every count is true for one corpus version, so it has to be askable."""
    body = client.get("/corpus").json()
    assert body["serving"]["word_types"] == VERSION
    assert f"{ALIAS}-{VERSION}" in body["built"]["word_types"]


def test_the_corpus_route_serves_what_the_ingest_measured(
    live: IndexAdmin,
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """The sizes and the coverage are read, never counted here.

    Counting them from the index is wrong twice over and both ways look
    right — see murfulu/corpus/report.py.
    """
    from murfulu.corpus import report

    stored = report.CorpusReport(
        corpus_version=VERSION,
        source_id="fixture",
        licence="CC0-1.0",
        spellings=10,
        spellings_linked=4,
        tokens=100,
        tokens_linked=70,
    )
    written = report.write(stored, tmp_path / "corpus_report.json")
    monkeypatch.setenv(report.PATH_VARIABLE, str(written))
    report.loaded.cache_clear()
    try:
        body = client.get("/corpus").json()
    finally:
        report.loaded.cache_clear()

    assert body["report"]["licence"] == "CC0-1.0"
    assert body["report"]["type_share"] == 0.4
    assert body["report"]["token_share"] == 0.7
    assert body["describes_the_served_version"] is True


def test_a_report_for_another_version_is_not_passed_off_as_current(
    live: IndexAdmin,
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """A count is true for one corpus version and no other."""
    from murfulu.corpus import report

    written = report.write(
        report.CorpusReport(corpus_version="something-else", spellings=1),
        tmp_path / "corpus_report.json",
    )
    monkeypatch.setenv(report.PATH_VARIABLE, str(written))
    report.loaded.cache_clear()
    try:
        body = client.get("/corpus").json()
    finally:
        report.loaded.cache_clear()

    assert body["report"]["corpus_version"] == "something-else"
    assert body["describes_the_served_version"] is False


def test_no_report_leaves_the_route_working(
    live: IndexAdmin, client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    """A machine that never ran an ingest still has versions to name."""
    from murfulu.corpus import report

    monkeypatch.delenv(report.PATH_VARIABLE, raising=False)
    report.loaded.cache_clear()
    try:
        body = client.get("/corpus").json()
    finally:
        report.loaded.cache_clear()

    assert body["report"] is None
    assert body["describes_the_served_version"] is False
    assert body["serving"]["word_types"] == VERSION


def test_an_index_nobody_built_is_a_503(live: IndexAdmin, client: TestClient):
    """Not an empty result. The difference is whether to trust the answer."""
    live.client.indices.delete(index=f"{ALIAS}-{VERSION}")
    assert client.get("/search", params={"q": "*nā"}).status_code == 503
