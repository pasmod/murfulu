"""Suggestions while typing: `/suggest/words` and `/suggest/texts`.

The words come from a handmade snapshot with the bank's tables, the texts
from a stand-in for Elasticsearch that answers with the counts the index
would. What matters: what starts with the letters comes before what only holds
them, one spelling is one suggestion with all its readings, Latin is matched
without its marks and never against a stem, `builds` leaves out a word that
feeds no rule, a group of texts is offered only when its own name holds what
was typed, and every answer is capped.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from elasticsearch import NotFoundError
from fastapi.testclient import TestClient

from murfulu.api import bank as bank_api
from murfulu.api import suggest as route
from murfulu.api.app import app
from murfulu.search import suggest as texts_suggest

from .conftest import FIELDS, SCHEMA


def _row(row_id: int, spelling: str, latin: str, pos: str, **more: str) -> tuple:
    return (
        row_id, spelling, spelling, spelling, latin,
        more.get("past_fa"), more.get("past"),
        more.get("present_fa"), more.get("present"),
        1.0, 0, None, None, pos, None, more.get("variants"),
    )  # fmt: skip


ROWS = [
    _row(1, "دل", "Del", "اسم ذات"),
    _row(2, "دل", "dall", "اسم ذات"),
    _row(3, "دلبر", "Delbar", "اسم ذات"),
    _row(4, "دلدار", "deldār", "صفت"),
    _row(5, "بیدل", "bidel", "صفت"),
    _row(6, "رفتن", "raftan", "مصدر",
         past_fa="رفت", past="raft", present_fa="رو", present="row"),
    _row(7, "کار", "Kār", "اسم ذات", variants='["kor"]'),
    _row(8, "دلار", "dolār", "وام‌واژه"),
]  # fmt: skip

GROUPS = {1: ["نام"], 2: ["نام"], 3: ["نام"], 4: ["نام"], 5: ["نام"]}
GROUPS |= {6: ["نابسودکارواژه"], 7: ["نام"], 8: ["وام‌واژه"]}


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    path = tmp_path / "lexicon-20991230.sqlite"
    connection = sqlite3.connect(path)
    connection.execute(SCHEMA)
    connection.executemany(
        f"INSERT INTO infinitives ({FIELDS}) VALUES ({', '.join('?' * 16)})", ROWS
    )
    connection.execute("CREATE TABLE bank_group (word_id INTEGER, bank_group TEXT)")
    connection.executemany(
        "INSERT INTO bank_group VALUES (?, ?)",
        [(row, group) for row, names in GROUPS.items() for group in names],
    )
    connection.execute("CREATE TABLE bank_labels (key TEXT PRIMARY KEY, label_fa TEXT)")
    connection.commit()
    connection.close()
    monkeypatch.setenv("MURFULU_LEXICON_PATH", str(path))
    bank_api._shelf.cache_clear()
    route._index.cache_clear()
    yield TestClient(app)
    bank_api._shelf.cache_clear()
    route._index.cache_clear()


def _words(client: TestClient, q: str, **more: Any) -> list[dict[str, Any]]:
    answer = client.get("/suggest/words", params={"q": q, **more})
    assert answer.status_code == 200, answer.text
    return answer.json()["suggestions"]


def test_persian_letters_suggest_spellings_starting_with_them_first(
    client: TestClient,
) -> None:
    values = [one["value"] for one in _words(client, "دل")]
    # دل itself, then the words that start with it, then بیدل, which only holds it.
    assert values[:4] == ["دل", "دلار", "دلبر", "دلدار"]
    assert values[-1] == "بیدل"


def test_one_spelling_is_one_suggestion_with_every_reading(client: TestClient) -> None:
    first = _words(client, "دل")[0]
    assert first == {"value": "دل", "spellings": ["دل"], "latin": ["Del", "dall"]}


def test_latin_is_matched_without_its_marks_and_comes_back_as_written(
    client: TestClient,
) -> None:
    found = _words(client, "kar")
    assert found == [{"value": "Kār", "spellings": ["کار"], "latin": ["Kār"]}]
    assert client.get("/suggest/words", params={"q": "kar"}).json()["script"] == "latin"


def test_latin_starts_before_it_holds_and_a_stem_is_not_a_word(
    client: TestClient,
) -> None:
    assert [one["value"] for one in _words(client, "del")] == [
        "Del",
        "Delbar",
        "deldār",
        "bidel",
    ]
    # «row» is رفتن's present stem, which the bank search finds; it is not a
    # word, so it is not suggested as one.
    assert _words(client, "row") == []


def test_primary_keeps_to_a_words_first_reading(client: TestClient) -> None:
    # کار is Kār, or Kor as its second reading; the search matches the first only.
    assert [one["value"] for one in _words(client, "kor")] == ["Kor"]
    assert _words(client, "kor", primary=True) == []
    assert [one["value"] for one in _words(client, "kar", primary=True)] == ["Kār"]


def test_builds_leaves_out_a_word_that_feeds_no_rule(client: TestClient) -> None:
    assert "دلار" in [one["value"] for one in _words(client, "دل")]
    assert "دلار" not in [one["value"] for one in _words(client, "دل", builds=True)]
    assert [one["value"] for one in _words(client, "raf", builds=True)] == ["raftan"]


def test_the_answer_is_capped(client: TestClient) -> None:
    assert len(_words(client, "دل", limit=2)) == 2
    assert (
        client.get("/suggest/words", params={"q": "دل", "limit": 11}).status_code == 422
    )
    assert client.get("/suggest/words", params={"q": ""}).status_code == 422


def test_a_suggestion_finds_itself_in_the_bank(client: TestClient) -> None:
    for one in _words(client, "دل") + _words(client, "del"):
        page = client.get("/bank", params={"q": one["value"], "exact": True}).json()
        assert page["total"] >= 1, one


# -- texts -------------------------------------------------------------------


def _bucket(key: str, count: int, **inner: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "key": key,
        "doc_count": count,
        **{name: {"buckets": buckets} for name, buckets in inner.items()},
    }


AGGREGATIONS = {
    "authors": {
        "buckets": [
            _bucket(
                "حافظ",
                600,
                works=[
                    _bucket(
                        "غزلیات",
                        495,
                        sections=[],
                    ),
                    _bucket("رباعیات", 42, sections=[]),
                ],
            ),
            _bucket(
                "سید حامد احمدی",
                22,
                works=[_bucket("دیوان", 22, sections=[_bucket("غزل‌ها", 20)])],
            ),
            # Matched only through a title: its own name holds nothing typed.
            _bucket("سعدی", 9, works=[_bucket("گلستان", 9, sections=[])]),
        ]
    }
}

HITS = [
    {
        "document_id": "ganjoor:hafez:2051",
        "author": "حافظ",
        "work": "رباعیات",
        "section": [],
        "title": "رباعی شمارهٔ ۱",
    },
    {
        "document_id": "ganjoor:saadi:1",
        "author": "سعدی",
        "work": "گلستان",
        "section": ["باب اول"],
        "title": "حکایت حاتم",
    },
]


class _Client:
    """Stands in for Elasticsearch: one search, answered with fixed counts."""

    def __init__(self) -> None:
        self.asked: list[dict[str, Any]] = []

    def search(self, **asked: Any) -> dict[str, Any]:
        self.asked.append(asked)
        return {
            "hits": {"hits": [{"_source": one} for one in HITS]},
            "aggregations": AGGREGATIONS,
        }


def test_a_group_is_offered_only_when_its_own_name_holds_what_was_typed() -> None:
    client = _Client()
    found = texts_suggest.suggest(client, "حا")  # type: ignore[arg-type]
    groups = [(one["kind"], one["query"], one["texts"]) for one in found[:-2]]
    assert groups == [
        ("author", "حافظ", 600),
        ("author", "سید حامد احمدی", 22),
        ("work", "حافظ غزلیات", 495),
        ("work", "حافظ رباعیات", 42),
        ("work", "سید حامد احمدی دیوان", 22),
        ("section", "سید حامد احمدی دیوان غزل‌ها", 20),
    ]
    assert "سعدی" not in [one["query"] for one in found if one["kind"] != "text"]
    # The texts the list would show come last, each to be opened by its id.
    assert [one["document_id"] for one in found[-2:]] == [
        "ganjoor:hafez:2051",
        "ganjoor:saadi:1",
    ]
    assert client.asked[0]["query"] == {
        "match_bool_prefix": {"heading": {"query": "حا", "operator": "and"}}
    }


def test_every_word_typed_must_be_in_the_name_the_last_as_a_prefix() -> None:
    found = texts_suggest.suggest(_Client(), "حافظ غز")  # type: ignore[arg-type]
    assert [one["query"] for one in found if one["kind"] != "text"] == ["حافظ غزلیات"]


def test_after_a_space_the_name_typed_is_not_offered_again() -> None:
    client = _Client()
    found = texts_suggest.suggest(client, "حافظ ")  # type: ignore[arg-type]
    assert [one["query"] for one in found if one["kind"] != "text"] == [
        "حافظ غزلیات",
        "حافظ رباعیات",
    ]
    assert "match" in client.asked[0]["query"]


def test_texts_keep_room_in_a_full_list() -> None:
    found = texts_suggest.suggest(_Client(), "حا", limit=4)  # type: ignore[arg-type]
    assert [one["kind"] for one in found] == ["author", "author", "text", "text"]


def test_the_index_is_asked_in_the_letters_typed() -> None:
    # Folding ؤ into و is for comparing names; the index keeps ؤ.
    client = _Client()
    texts_suggest.suggest(client, "سؤال کرد")  # type: ignore[arg-type]
    assert client.asked[0]["query"] == {
        "match_bool_prefix": {"heading": {"query": "سؤال کرد", "operator": "and"}}
    }


def test_a_heading_is_compared_as_the_index_compares_it() -> None:
    # Persian digits are the analyser's ASCII ones, an Arabic yeh is a Persian
    # one, and the hamza of the ezafe is not a letter.
    assert texts_suggest.holds("غزل شمارهٔ ۳", ["غزل", "شماره"], "3")
    assert texts_suggest.holds("علي", [], "علی")
    assert not texts_suggest.holds("حافظ", ["سعدی"], None)


@pytest.fixture
def http(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr(route, "connect", _Client)
    yield TestClient(app)


def test_the_texts_route_answers_and_says_when_the_index_is_missing(
    http: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = http.get("/suggest/texts", params={"q": "حافظ غز"}).json()
    assert body["suggestions"][0]["query"] == "حافظ غزلیات"

    class _Missing:
        def search(self, **_asked: Any) -> dict[str, Any]:
            raise NotFoundError(404, "no such index", {})  # type: ignore[arg-type]

    monkeypatch.setattr(route, "connect", _Missing)
    assert http.get("/suggest/texts", params={"q": "حا"}).status_code == 503
