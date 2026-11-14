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
from murfulu.behnevis.transcribe import Transcriber
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


def test_a_number_or_a_latin_name_stands_on_its_own_with_its_spaces():
    """Not glued to the word before it: «سال ۱۲۳۴» stays two parts."""
    year = texts.tokens("سال ۱۲۳۴ خورشیدی")
    assert [(t.fa, t.spelling, t.after) for t in year] == [
        ("سال", "سال", ""),
        ("۱۲۳۴", None, ""),
        ("خورشیدی", "خورشیدی", ""),
    ]
    assert texts.tokens("ABC DEF و")[0] == texts.Token("ABC DEF", None)
    comma = texts.tokens("دل،  ۱۲ و")
    assert (comma[0].after, comma[1].fa) == ("،", "۱۲")


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
    assert query["sort"][1] == {
        "order": {"order": "asc", "missing": "_last", "unmapped_type": "integer"}
    }
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
    assert listed["returned"] == 1 and listed["total"] == 1
    [row] = listed["marked"]
    assert (row["spelling_fa"], row["latin"], row["document_id"], row["unit"]) == (
        "دل",
        "dall",
        "fixture:a:1",
        1,
    )


def test_the_marks_are_paged_and_can_be_asked_for_one_spelling(http: TestClient):
    """No mark falls off the list, and an old one still shows in its panel."""

    def mark(target: str) -> None:
        spelling, _, latin = target.partition(":")
        http.post(
            "/feedback",
            json={
                "category": "linguistic",
                "target_type": "lexicon_entry",
                "target_id": target,
                "verdict": "wrong",
                "context": {"spelling_fa": spelling, "latin": latin},
            },
        )

    for target in ["دل:Dol", "دلبر:Delbar", "د_ل:x", "ما:mā"]:
        mark(target)
    page = http.get("/texts/marked", params={"limit": 2, "offset": 2}).json()
    assert (page["total"], page["returned"]) == (4, 2)
    assert [row["latin"] for row in page["marked"]] == ["Delbar", "Dol"]
    # Only دل's own readings: not دلبر, and an underscore is a letter here.
    one = http.get("/texts/marked", params={"spelling": "دل"}).json()
    assert [row["target_id"] for row in one["marked"]] == ["دل:Dol"]
    odd = http.get("/texts/marked", params={"spelling": "د_ل"}).json()
    assert [row["target_id"] for row in odd["marked"]] == ["د_ل:x"]


# -- the automatic Behnevis on the screen (direction A, 2026-11-14) ------------


def _toy_transcriber() -> Transcriber:
    from murfulu.behnevis.choice import Answered, ChoiceModel
    from murfulu.behnevis.letters import LetterModel
    from murfulu.behnevis.transcribe import bank_from

    pairs = [
        ("دل", "Dal"),
        ("دل", "Del"),
        ("دست", "Dast"),
        ("کار", "Kār"),
        ("آرام", "ārām"),
    ]
    return Transcriber(
        bank=bank_from(pairs),
        letters=LetterModel.train(pairs),
        choice=ChoiceModel.train([Answered("دل", "Del")] * 30),
        functions={"ما": ("mā",)},
        covered={"دل": (30, 0)},  # marked often, and always one of its readings
    )


def test_each_word_gets_one_reading_and_a_level():
    from murfulu.behnevis import serve

    units, _, _ = texts.lay_out(STORED)
    serve.annotate(units, _toy_transcriber())
    first = units[1]["lines"][0]["words"]  # «دلِ ما آرام»
    del_, ma, aram = (w["auto"] for w in first)
    assert (del_["latin"], del_["level"]) == ("Del", "sure")
    assert ma["latin"] == "mā" and ma["level"] == "sure"
    assert [c[0] for c in del_["candidates"]] == ["Del", "Dal"]
    assert aram["source"] == "bank"
    assert serve.level(0.95) == "sure" and serve.level(0.8) == "mid"
    assert serve.level(0.2) == "unsure"
    assert "auto" not in str(units[0])  # the note: never split, never read


def test_a_text_carries_its_levels_when_the_model_is_on(
    http: TestClient, monkeypatch: pytest.MonkeyPatch
):
    from murfulu.behnevis import serve

    off = http.get("/texts/fixture:a:1").json()
    assert off["behnevis"] is None
    assert "auto" not in str(off["units"])

    monkeypatch.setattr(serve, "loaded", _toy_transcriber)
    on = http.get("/texts/fixture:a:1").json()
    assert on["behnevis"] == {"sure": serve.SURE, "mid": serve.MID}
    assert on["units"][1]["lines"][0]["words"][0]["auto"]["latin"] == "Del"


def test_a_proposed_reading_is_listed_apart_from_the_marks(http: TestClient):
    proposal = {
        "category": "linguistic",
        "target_type": "lexicon_entry",
        "target_id": "آرد:ārad",
        "verdict": "good",
        "note": None,
        "context": {
            "screen": "texts",
            "kind": "reading_here",
            "spelling_fa": "آرد",
            "latin": "ārad",
            "in_bank": False,
            "model_latin": "Ārd",
            "model_confidence": 0.06,
            "written": "آرد",
            "document_id": "fixture:a:1",
            "unit": 1,
            "heading": "نویسنده · کتاب · عنوان",
        },
        "corpus_version": "v17",
    }
    written = http.post("/feedback", json=proposal)
    assert written.status_code == 201, written.text
    assert written.json()["owner"] == "karbon"
    assert http.get("/texts/marked").json()["total"] == 0
    [row] = http.get("/texts/marked", params={"kind": "proposed"}).json()["marked"]
    assert (row["latin"], row["in_bank"], row["model_latin"]) == ("ārad", False, "Ārd")
    assert http.get("/texts/marked", params={"kind": "other"}).status_code == 422


def test_the_proposals_export_as_one_list_for_karbon():
    import importlib.util
    from types import SimpleNamespace

    spec = importlib.util.spec_from_file_location(
        "export_reading_proposals",
        Path(__file__).resolve().parents[1] / "tools" / "export_reading_proposals.py",
    )
    tool = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(tool)  # type: ignore[union-attr]
    context = {
        "screen": "texts",
        "kind": "reading_here",
        "spelling_fa": "آرد",
        "latin": "ārad",
        "in_bank": False,
        "model_latin": "Ārd",
        "heading": "حافظ · غزل ۳",
        "written": "آرد",
    }
    rows = [SimpleNamespace(context=context, target_id="آرد:ārad")] * 2 + [
        SimpleNamespace(context={**context, "kind": "other"}, target_id="x:y")
    ]
    text = tool.report(tool.gather(rows))
    assert "| آرد | ārad | 2 | no | Ārd |" in text
    assert "x:y" not in text and "| x |" not in text
