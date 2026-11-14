"""The ``/evidence`` route: its shape, its filter, and its answer when it cannot.

The client is the stand-in of ``test_evidence.py``; no cluster is needed.
"""

from typing import Any

import pytest
from elasticsearch import ConnectionError as Unreachable
from fastapi.testclient import TestClient

from murfulu.api import search as route
from murfulu.api.app import app

from .test_evidence import TEXTS, _Elasticsearch

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture
def http(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(route, "_client", lambda: _Elasticsearch(TEXTS))
    return TestClient(app)


def test_the_whole_list_comes_with_its_authors_and_its_counts(http: TestClient):
    body = http.get("/evidence", params={"spelling": "دل", "size": 2}).json()
    assert body["total"] == body["matching"] == 5
    assert body["lines"] == 6
    assert body["corpus_version"] == "v-test"
    # The text with no author is sent as null, in its place by its count.
    assert body["authors"] == [
        {"author": "الف", "texts": 3},
        {"author": None, "texts": 1},
        {"author": "ب", "texts": 1},
    ]
    first = body["texts"][0]
    assert first["document_id"] == "t:a:10"
    assert first["lines"] == [
        {"unit": 0, "kind": "couplet", "parts": ["", "دلِ", " من و ", "دل", " تو"]}
    ]
    assert first["held"] == "counted"


def test_one_author_is_its_own_list(http: TestClient):
    body = http.get(
        "/evidence", params={"spelling": "دل", "author": "الف", "page": 1, "size": 2}
    ).json()
    assert body["total"] == 5
    assert body["matching"] == 3
    assert body["lines"] == 4
    assert [one["document_id"] for one in body["texts"]] == ["t:a:30"]


def test_the_texts_with_no_author_are_asked_for_by_name(http: TestClient):
    body = http.get("/evidence", params={"spelling": "دل", "unnamed": True}).json()
    assert body["matching"] == 1
    assert body["author"] is None and body["unnamed"] is True
    assert [one["document_id"] for one in body["texts"]] == ["t:-:1"]


def test_the_lines_are_counted_only_when_asked(http: TestClient):
    body = http.get("/evidence", params={"spelling": "دل", "count_lines": False}).json()
    assert body["lines"] is None
    assert len(body["texts"]) == 5


def test_size_nought_gives_the_counts_alone(http: TestClient):
    body = http.get("/evidence", params={"spelling": "دل", "size": 0}).json()
    assert body["texts"] == []
    assert body["total"] == 5


def test_a_page_past_the_end_is_empty_not_an_error(http: TestClient):
    response = http.get("/evidence", params={"spelling": "دل", "page": 40})
    assert response.status_code == 200
    assert response.json()["texts"] == []


def test_no_spelling_is_refused(http: TestClient):
    assert http.get("/evidence", params={"spelling": ""}).status_code == 422
    # An empty name is no author's name; texts with none are `unnamed`.
    assert (
        http.get("/evidence", params={"spelling": "دل", "author": ""}).status_code
        == 422
    )
    assert (
        http.get("/evidence", params={"spelling": "دل", "size": 500}).status_code == 422
    )


def test_an_unreachable_index_is_a_503(monkeypatch: pytest.MonkeyPatch):
    class _Down:
        def search(self, **_: Any) -> dict[str, Any]:
            raise Unreachable("down")

    monkeypatch.setattr(route, "_client", lambda: _Down())
    response = TestClient(app).get("/evidence", params={"spelling": "دل"})
    assert response.status_code == 503


def test_voices_give_one_text_an_author(http: TestClient):
    body = http.get(
        "/evidence",
        params={"spelling": "دل", "size": 3, "voices": True, "count_lines": False},
    ).json()
    assert [one["author"] for one in body["texts"]] == ["الف", None, "ب"]
    assert body["total"] == 5


def test_voices_are_of_the_whole_list_whatever_else_is_asked(http: TestClient):
    body = http.get(
        "/evidence",
        params={"spelling": "دل", "size": 2, "voices": True, "author": "ب", "page": 3},
    ).json()
    assert [one["author"] for one in body["texts"]] == ["الف", None]
    assert body["author"] is None and body["unnamed"] is False
    assert body["matching"] == body["total"] == 5
    assert body["lines"] == 6
    nothing = http.get(
        "/evidence", params={"spelling": "دل", "size": 0, "voices": True}
    ).json()
    assert nothing["texts"] == []
