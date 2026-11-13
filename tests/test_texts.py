"""Reading a text: the words as written, their readings, and the marks.

Every line here is written for the test; no corpus text (NOTICE).
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from elasticsearch import NotFoundError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from murfulu.api import texts as route
from murfulu.api.app import app
from murfulu.corpus.wordtypes import tokenise
from murfulu.db.models import Base
from murfulu.search import texts

LINES = [
    "دلِ ما با رفتار تو آرام گرفت",
    "«سخن» کوتاه، بهتر از سخنِ دراز!",
    "خانهٔ ما می‌رود به سوي باغ",  # an Arabic ي, folded as the count folds it
    "این ‌ نیم‌فاصلهٔ تنها ‌ واژه نیست",
    "۱۲۳ عدد است و ABC هم",
]


@pytest.mark.parametrize("line", LINES)
def test_the_words_are_the_counted_words(line: str):
    """The screen's word is always the word whose count it shows."""
    assert [t.spelling for t in texts.tokens(line) if t.spelling] == tokenise(line)


def test_a_word_keeps_its_marks_and_its_punctuation():
    first, *_ = texts.tokens("دلِ ما")
    assert (first.fa, first.spelling) == ("دلِ", "دل")
    words = texts.tokens("«سخن» کوتاه، بهتر!")
    assert words[0] == texts.Token("«", None)
    assert (words[1].fa, words[1].after) == ("سخن", "»")
    assert (words[2].fa, words[2].after) == ("کوتاه", "،")
    assert words[-1].after == "!"


def test_the_hamza_of_the_ezafe_stays_on_the_word():
    [house, ours] = texts.tokens("خانهٔ ما")
    assert house.fa == "خانهٔ" and house.spelling == "خانه"
    assert ours.fa == "ما"


STORED: dict[str, Any] = {
    "document_id": "fixture:a:1",
    "author": "نویسنده",
    "work": "کتاب",
    "section": ["باب نخست"],
    "title": "عنوان",
    "corpus_version": "v17",
    "source_id": "fixture",
    "units": [
        {"kind": "note", "lines": [{"text": "یادداشت گردآورنده", "position": "note"}]},
        {
            "kind": "couplet",
            "lines": [
                {"text": "دلِ ما آرام", "position": "first"},
                {"text": "راه تازه", "position": "second"},
            ],
        },
        {"kind": "prose", "lines": [{"text": "نثر کوتاه. دل.", "position": "prose"}]},
    ],
}


def test_a_window_is_numbered_by_counted_units_and_a_note_is_not_split():
    units, spellings, total = texts.lay_out(STORED)
    assert total == 3
    assert [(u["index"], u["number"], u["kind"]) for u in units] == [
        (0, None, "note"),
        (1, 1, "couplet"),
        (2, 2, "prose"),
    ]
    assert units[0]["lines"] == [{"position": "note", "text": "یادداشت گردآورنده"}]
    assert "یادداشت" not in spellings
    assert {"دل", "ما", "آرام", "راه", "تازه", "نثر", "کوتاه"} == spellings


def test_a_window_keeps_the_numbers_of_the_whole_text():
    units, _, _ = texts.lay_out(STORED, start=2, limit=5)
    assert [(u["index"], u["number"]) for u in units] == [(2, 2)]


def test_a_text_stored_before_units_is_one_unit_per_line():
    units, _, total = texts.lay_out({"text_fa": "سطر یکم\nسطر دوم"})
    assert total == 2
    assert [u["kind"] for u in units] == ["line", "line"]


class _Client:
    """Stands in for Elasticsearch: answers ``get`` and ``search`` from lists."""

    def __init__(self, words: list[dict[str, Any]], document: dict[str, Any]) -> None:
        self.words = words
        self.document = document
        self.asked: list[dict[str, Any]] = []

    def get(self, index: str, id: str) -> dict[str, Any]:
        if id != self.document.get("document_id"):
            raise NotFoundError(404, "not found", {})  # type: ignore[arg-type]
        return {"_source": self.document}

    def search(self, **asked: Any) -> dict[str, Any]:
        self.asked.append(asked)
        if asked["index"] == "documents":
            return {
                "hits": {
                    "total": {"value": 1},
                    "hits": [{"_source": self.document}],
                }
            }
        wanted = set(asked["query"]["terms"]["spelling_fa"])
        hits = [{"_source": w} for w in self.words if w["spelling_fa"] in wanted]
        return {"hits": {"hits": hits}}


WORDS = [
    {"id": "دل:Del", "spelling_fa": "دل", "latin": "Del", "bank_groups": ["nam"]},
    {"id": "دل:dall", "spelling_fa": "دل", "latin": "dall", "bank_groups": []},
    {
        "id": "دل:Dal",
        "spelling_fa": "دل",
        "latin": "Dal",
        "total_count": 9,
        "doc_count": 4,
        "lexicon_snapshot_id": "lexicon-test",
    },
    # A spelling the bank does not read: counted, no reading.
    {"id": "راه:", "spelling_fa": "راه", "latin": None, "total_count": 3},
]


def test_every_reading_comes_back_in_alphabetical_order_and_none_is_proposed():
    found, snapshot = texts.look_up(
        _Client(WORDS, STORED),  # type: ignore[arg-type]
        ["دل", "راه", "تازه"],
        {"nam": "نام"},
    )
    assert [one["latin"] for one in found["دل"]["readings"]] == ["Dal", "dall", "Del"]
    assert "proposed" not in str(found)
    assert found["دل"]["readings"][2]["groups"] == ["نام"]
    assert (found["دل"]["total_count"], found["دل"]["doc_count"]) == (9, 4)
    assert snapshot == "lexicon-test"


def test_a_spelling_without_a_reading_comes_back_empty_never_guessed():
    found, _ = texts.look_up(
        _Client(WORDS, STORED),  # type: ignore[arg-type]
        ["راه", "تازه"],
        {},
    )
    assert found["راه"]["readings"] == [] and found["راه"]["total_count"] == 3
    assert found["تازه"] == {
        "readings": [],
        "total_count": None,
        "doc_count": None,
        "function_word": None,
    }


def test_a_heading_search_needs_every_word_and_keeps_the_source_order():
    client = _Client(WORDS, STORED)
    found = texts.find(client, "نویسنده، کتاب")  # type: ignore[arg-type]
    query = client.asked[0]
    assert query["query"]["match"]["heading"] == {
        "query": "نویسنده کتاب",
        "operator": "and",
    }
    assert query["sort"][1] == {"order": {"order": "asc", "missing": "_last"}}
    assert found["texts"][0]["section"] == ["باب نخست"]
    assert found["corpus_version"] == "v17"


# -- over HTTP -----------------------------------------------------------------


@pytest.fixture
def http(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    url = f"sqlite:///{tmp_path / 'authored.sqlite'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    monkeypatch.setenv("MURFULU_DATABASE_URL", url)
    monkeypatch.setattr(route, "connect", lambda: _Client(WORDS, STORED))
    yield TestClient(app)


def test_a_text_is_served_with_its_place_and_its_words(http: TestClient):
    answer = http.get("/texts/fixture:a:1")
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert (body["work"], body["section"], body["corpus_version"]) == (
        "کتاب",
        ["باب نخست"],
        "v17",
    )
    assert body["units"][1]["lines"][0]["words"][0] == {"fa": "دلِ", "s": "دل"}
    assert len(body["words"]["دل"]["readings"]) == 3


def test_an_unknown_text_is_a_404(http: TestClient):
    assert http.get("/texts/fixture:a:2").status_code == 404


def test_a_text_is_found_by_its_heading(http: TestClient):
    body = http.get("/texts", params={"q": "عنوان"}).json()
    assert body["total"] == 1 and body["texts"][0]["document_id"] == "fixture:a:1"


def test_a_reading_marked_wrong_is_listed_for_review(http: TestClient):
    """Through the feedback store, owned by karbon, read back here."""
    mark = {
        "category": "linguistic",
        "target_type": "lexicon_entry",
        "target_id": "دل:dall",
        "verdict": "wrong",
        "note": None,
        "context": {
            "screen": "texts",
            "spelling_fa": "دل",
            "latin": "dall",
            "written": "دلِ",
            "document_id": "fixture:a:1",
            "unit": 1,
            "heading": "نویسنده · کتاب · عنوان",
        },
        "corpus_version": "v17",
    }
    written = http.post("/feedback", json=mark)
    assert written.status_code == 201, written.text
    assert written.json()["owner"] == "karbon"
    # Feedback that is not a wrong reading stays off the list.
    http.post(
        "/feedback",
        json={**mark, "target_type": "derivation", "target_id": "Dalbar:nam"},
    )

    listed = http.get("/texts/marked").json()
    assert listed["returned"] == 1
    [row] = listed["marked"]
    assert (row["spelling_fa"], row["latin"], row["document_id"], row["unit"]) == (
        "دل",
        "dall",
        "fixture:a:1",
        1,
    )
