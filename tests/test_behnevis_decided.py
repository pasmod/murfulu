"""A reading decided once for every like place of a spelling (2026-11-21).

Every word here is written for the test; no corpus text (NOTICE).
"""

from __future__ import annotations

import importlib.util
import json
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from murfulu.api.app import app
from murfulu.behnevis import serve
from murfulu.behnevis.choice import Answered, ChoiceModel
from murfulu.behnevis.decided import (
    AFTER_WORD,
    BEFORE_WORD,
    EVERYWHERE,
    KIND,
    Decided,
    Decision,
    current,
    decisions_from,
    from_record,
)
from murfulu.behnevis.letters import LetterModel
from murfulu.behnevis.picks import picks_from
from murfulu.behnevis.transcribe import DECIDED, Transcriber, bank_from
from murfulu.db.models import Base


def _record(
    latin: str | None, scope: str, word: str | None = None, **more: Any
) -> dict[str, Any]:
    place = {k: more[k] for k in ("document_id", "unit", "line", "word") if k in more}
    return place | {
        "screen": "texts",
        "kind": KIND,
        "spelling_fa": more.get("spelling", "بود"),
        "latin": latin,
        "scope": scope,
        "scope_word": word,
        "withdrawn": more.get("withdrawn", False),
    }


def test_a_record_is_a_decision_only_with_a_scope_it_can_read():
    assert from_record(_record("bovad", EVERYWHERE, "ignored"), 1) == Decision(
        "بود", "bovad", EVERYWHERE, None, 1
    )
    one = from_record(_record("bud", AFTER_WORD, "می‌"), 2)
    assert one is not None and one.word == "می"  # keyed, joiner dropped
    assert from_record(_record("bud", AFTER_WORD), 3) is None  # no word
    assert from_record(_record("bud", "somewhere"), 4) is None
    assert (
        from_record({**_record("bud", EVERYWHERE), "kind": "reading_here"}, 5) is None
    )
    taken_back = from_record(_record(None, EVERYWHERE, withdrawn=True), 6)
    assert taken_back is not None and taken_back.latin is None


def test_the_newest_decision_for_a_spelling_and_scope_is_in_force():
    rows = [
        Decision("بود", "Bud", EVERYWHERE, None, 1),
        Decision("بود", "bovad", EVERYWHERE, None, 3),
        Decision("بود", "bud", AFTER_WORD, "که", 2),
        Decision("بود", "bud", BEFORE_WORD, "که", 4),
        Decision("بود", None, BEFORE_WORD, "که", 5),  # taken back
    ]
    assert [(d.scope, d.latin) for d in current(rows)] == [
        (EVERYWHERE, "bovad"),
        (AFTER_WORD, "bud"),
    ]


def test_the_narrower_scope_wins_and_between_two_the_newer():
    decided = Decided.of(
        [
            Decision("بود", "bovad", EVERYWHERE, None, 1),
            Decision("بود", "bud", AFTER_WORD, "که", 2),
            Decision("بود", "Bud", BEFORE_WORD, "از", 3),
        ]
    )
    assert decided.lookup("بود", "دل", "دست") == "bovad"
    assert decided.lookup("بود", "که", "دست") == "bud"
    assert decided.lookup("بود", "که", "از") == "Bud"  # the newer of the two
    assert decided.lookup("دل", "که", "از") is None
    assert Decided.from_dict(json.loads(json.dumps(decided.to_dict()))) == decided


def test_only_a_reading_the_bank_holds_is_learned_the_rest_waits_for_karbon():
    bank = {"بود": ("Bud",)}
    functions = {"که": ("ke", "keh")}
    rows = [
        {**_record("Bud", EVERYWHERE), "id": 1},
        {**_record("bovad", AFTER_WORD, "نه"), "id": 2},
        {**_record("keh", EVERYWHERE, spelling="که"), "id": 3},
        {"kind": "reading_here", "spelling_fa": "بود", "latin": "Bud", "id": 4},
    ]
    learned, waiting = decisions_from(rows, bank, functions)
    assert learned.lookup("بود", None, None) == "Bud"
    assert learned.lookup("که", None, None) == "keh"
    assert [(d.spelling, d.latin) for d in waiting] == [("بود", "bovad")]
    # A newer decision for a reading the bank lacks still replaces the older.
    rows.append({**_record("bovad", EVERYWHERE), "id": 5})
    learned, waiting = decisions_from(rows, bank, functions)
    assert learned.lookup("بود", None, None) is None
    assert len(waiting) == 2


@pytest.fixture
def model() -> Transcriber:
    pairs = [("بود", "Bud"), ("بود", "bovad"), ("دل", "Del"), ("دل", "Dal")]
    return Transcriber(
        bank=bank_from(pairs),
        letters=LetterModel.train(pairs),
        choice=ChoiceModel.train([Answered("بود", "bovad")] * 5),
        functions={"که": ("ke",)},
        decided=Decided.of(
            [
                Decision("دل", "Del", EVERYWHERE, None, 1),
                Decision("بود", "Bud", AFTER_WORD, "که", 2),
            ]
        ),
    )


def test_a_decided_reading_is_read_wherever_it_applies(model: Transcriber):
    first, second = model.line("دل که")
    assert (first.latin, first.source) == ("Del", DECIDED)
    assert first.confidence == model.decided_confidence
    # The model's other readings follow it without a number, to pick from.
    assert dict(first.candidates) == {"Del": model.decided_confidence, "Dal": None}
    assert second.source != DECIDED
    _, bud = model.line("که بود")
    assert (bud.latin, bud.source) == ("Bud", DECIDED)
    _, bovad = model.line("دل بود")
    assert bovad.source != DECIDED and bovad.latin == "bovad"


def test_the_words_own_signs_overrule_a_decision(model: Transcriber):
    [marked] = model.line("دَل")
    assert marked.latin == "Dal" and marked.source != DECIDED
    # Measured with the signs hidden, the decision applies again.
    [hidden] = model.line("دَل", use_signs=False)
    assert hidden.source == DECIDED


def test_the_decisions_survive_the_model_file(model: Transcriber, tmp_path: Path):
    path = tmp_path / "behnevis-v0.json"
    model.save(path)
    again = Transcriber.load(path, model.bank)
    assert again.decided == model.decided
    del model.decided
    model.decided = None
    model.save(path)
    assert Transcriber.load(path, model.bank).decided is None


def test_the_metre_leaves_a_decided_reading_as_decided(model: Transcriber):
    def verse() -> list[dict[str, Any]]:
        words = [{"fa": w, "s": w} for w in ("که", "بود")]
        return [{"kind": "couplet", "lines": [{"words": words}]}]

    # Read in فعل (U-), the line holds *Bud*, not the model's *bovad*.
    model.decided = None
    free = verse()
    serve.annotate(free, model, "فعل")
    assert free[0]["lines"][0]["words"][1]["auto"]["latin"] == "Bud"
    # A person decided *bovad* after که: the decision stands.
    model.decided = Decided.of([Decision("بود", "bovad", AFTER_WORD, "که", 1)])
    held = verse()
    serve.annotate(held, model, "فعل")
    auto = held[0]["lines"][0]["words"][1]["auto"]
    assert (auto["latin"], auto["source"], auto["level"]) == ("bovad", DECIDED, "sure")


def test_a_decision_is_not_learned_as_a_pick_for_one_place(tmp_path: Path):
    path = tmp_path / "proposals.jsonl"
    path.write_text(
        "\n".join(
            json.dumps(row, ensure_ascii=False)
            for row in (
                {**_record("Bud", EVERYWHERE), "id": 1},
                {"spelling_fa": "بود", "latin": "Bud", "kind": "reading_here"},
            )
        ),
        encoding="utf-8",
    )
    picks = picks_from(path, {"بود": ("Bud",)}, {})
    assert len(picks) == 1 and picks[0].by_person


def _export_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "export_reading_proposals",
        Path(__file__).resolve().parents[1] / "tools" / "export_reading_proposals.py",
    )
    tool = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(tool)  # type: ignore[union-attr]
    return tool


def test_the_export_passes_decisions_whole_and_lists_karbons_with_their_reach():
    tool = _export_tool()
    place = {"document_id": "fixture:a:1", "unit": 0, "line": 0, "word": 1}
    rows = [
        SimpleNamespace(
            id=1,
            context={**_record("bovad", EVERYWHERE), **place, "in_bank": False},
            target_id="بود:bovad",
        ),
        # The same place, another scope: not a correction of the first.
        SimpleNamespace(
            id=2,
            context={**_record("bud", AFTER_WORD, "نه"), **place, "in_bank": False},
            target_id="بود:bud",
        ),
        SimpleNamespace(
            id=3,
            context={**_record("Bud", BEFORE_WORD, "از"), **place, "in_bank": True},
            target_id="بود:Bud",
        ),
    ]
    kept = tool.latest(rows)
    assert len(kept) == 3
    exported = tool.picks(kept)
    assert [(p["kind"], p["scope"], p["id"]) for p in exported] == [
        (KIND, EVERYWHERE, 1),
        (KIND, AFTER_WORD, 2),
        (KIND, BEFORE_WORD, 3),
    ]
    listed = tool.report(tool.gather(kept))
    assert "| بود | bovad | 1 |" in listed and "| everywhere |" in listed
    assert "| بود | bud | 1 |" in listed and "| after نه |" in listed
    assert "| Bud |" not in listed  # the bank holds it: the model's
    # Taken back, a decision leaves karbon's list too.
    back = SimpleNamespace(
        id=4,
        context={**_record(None, EVERYWHERE, withdrawn=True), **place},
        target_id="بود:",
    )
    assert "bovad" not in tool.report(tool.gather([*kept, back]))


# -- over HTTP: the list and the decisions --------------------------------------


@pytest.fixture
def http(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    url = f"sqlite:///{tmp_path / 'authored.sqlite'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    monkeypatch.setenv("MURFULU_DATABASE_URL", url)
    yield TestClient(app)


def _listed(spelling: str, kind: str, n: int) -> dict[str, Any]:
    return {
        "rank": 0,
        "spelling": spelling,
        "written": spelling,
        "places": n * 2,
        "unsure": n,
        "kind": kind,
        "known": [],
        "sources": {},
        "read_as": [],
        "offered": [],
        "before": [["که", n, n]],
        "after": [],
        "examples": [],
    }


LISTED = (
    {"words": 100, "unsure_words": 40},
    [
        _listed("بود", "one", 9),
        _listed("دل", "choice", 7),
        _listed("گفتم", "missing", 5),
    ],
)


def _decide(http: TestClient, latin: str, scope: str, **more: Any) -> int:
    answer = http.post(
        "/feedback",
        json={
            "category": "linguistic",
            "target_type": "lexicon_entry",
            "target_id": f"{more.get('spelling', 'بود')}:{latin}",
            "verdict": "unsure" if more.get("withdrawn") else "good",
            "context": _record(
                latin,
                scope,
                more.get("word"),
                **{k: v for k, v in more.items() if k != "word"},
            )
            | {"in_bank": more.get("in_bank", True)},
        },
    )
    assert answer.status_code == 201
    return int(answer.json()["id"])


def test_the_list_is_a_503_until_it_is_measured(http: TestClient):
    assert http.get("/texts/unsure").status_code == 503
    # One spelling still answers: the panel works without the list.
    one = http.get("/texts/unsure/بود").json()
    assert one == {"spelling": "بود", "listed": None, "decided": []}


def test_the_list_is_paged_filtered_and_carries_the_decisions(
    http: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(serve, "unsure_list", lambda: LISTED)
    page = http.get("/texts/unsure", params={"size": 2}).json()
    assert page["total"] == 3 and page["meta"]["words"] == 100
    assert [one["spelling"] for one in page["spellings"]] == ["بود", "دل"]
    assert all(one["decided"] == [] for one in page["spellings"])
    missing = http.get("/texts/unsure", params={"kind": "missing"}).json()
    assert [one["spelling"] for one in missing["spellings"]] == ["گفتم"]
    assert http.get("/texts/unsure", params={"kind": "other"}).status_code == 422

    _decide(http, "Bud", EVERYWHERE)
    newer = _decide(http, "bovad", EVERYWHERE, in_bank=False)
    _decide(http, "bud", AFTER_WORD, word="که")
    (bud,) = http.get("/texts/unsure", params={"size": 1}).json()["spellings"]
    assert [(d["scope"], d["latin"]) for d in bud["decided"]] == [
        (AFTER_WORD, "bud"),
        (EVERYWHERE, "bovad"),
    ]
    assert bud["decided"][1]["id"] == newer
    assert bud["decided"][0]["scope_word"] == "که"

    # Taken back, a decision is no longer in force.
    _decide(http, "bud", AFTER_WORD, word="که", withdrawn=True)
    one = http.get("/texts/unsure/بود").json()
    assert one["listed"]["unsure"] == 9
    assert [(d["scope"], d["latin"]) for d in one["decided"]] == [(EVERYWHERE, "bovad")]
    # A spelling outside the list answers with its decisions alone.
    _decide(http, "Del", EVERYWHERE, spelling="دلم")
    other = http.get("/texts/unsure/دلم").json()
    assert other["listed"] is None and other["decided"][0]["latin"] == "Del"


def test_the_list_lives_beside_the_model_and_is_read_again_when_measured_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from murfulu.behnevis import unsure

    model = tmp_path / "behnevis-v0.json"
    model.write_text("{}", encoding="utf-8")
    monkeypatch.setenv(serve.PATH_VARIABLE, str(model))
    assert serve.unsure_list() is None
    unsure.write(unsure.path_beside(model), {"words": 1}, [])
    assert serve.unsure_list() == ({"words": 1}, [])


# -- from the review of 2026-11-21 ----------------------------------------------


def test_a_wider_decision_holds_where_the_signs_rule_out_the_narrower(
    model: Transcriber,
):
    model.decided = Decided.of(
        [
            Decision("دل", "Del", EVERYWHERE, None, 1),
            Decision("دل", "Dal", AFTER_WORD, "که", 2),
        ]
    )
    _, plain = model.line("که دل")
    assert plain.latin == "Dal"
    # The kasra rules out *Dal*; the decision for everywhere still stands.
    _, marked = model.line("که دِل")
    assert (marked.latin, marked.source) == ("Del", DECIDED)


def test_the_metre_offers_no_other_reading_for_a_decided_word():
    from murfulu.behnevis.metre import Metre
    from murfulu.behnevis.transcribe import Word

    # A decided word with a rival offered after it, as the screen sends it.
    decided = Word(
        "بود", "بود", "bovad", 0.95, DECIDED, (("bovad", 0.95), ("Bud", None))
    )
    free = Word("بود", "بود", "Bud", 0.55, "choice", (("Bud", 0.55), ("bovad", 0.45)))
    fixed, open_ = Metre().slots([decided, free])
    assert fixed.other == (1, 0) and not fixed.enclitic
    assert len(fixed.options) == 1  # the decided reading alone
    assert open_.other[0] <= open_.other[1]
    # Weighed directly, as the evaluation does, it comes back as decided,
    # even in a line that would rather hold the rival (فع: one long syllable).
    (alone,) = Metre().weigh([decided], ["-"])
    assert alone.word == decided


def test_a_decision_taken_back_reaches_the_export_and_two_reaches_stay_two():
    tool = _export_tool()
    first = SimpleNamespace(
        id=1,
        verdict="good",
        context={**_record("bovad", AFTER_WORD, "که"), "in_bank": False},
        target_id="بود:bovad",
    )
    second = SimpleNamespace(
        id=2,
        verdict="good",
        context={**_record("bovad", BEFORE_WORD, "از"), "in_bank": False},
        target_id="بود:bovad",
    )
    listed = tool.report(tool.gather([first, second]))
    assert "| after که; before از |" in listed
    back = SimpleNamespace(
        id=3,
        verdict="unsure",
        context=_record("bovad", AFTER_WORD, "که", withdrawn=True),
        target_id="بود:bovad",
    )
    # Taken back with `unsure`: still read, so the build drops the decision.
    assert tool._good(back)
    pick = SimpleNamespace(
        id=4, verdict="unsure", context={"kind": "reading_here"}, target_id="x:y"
    )
    assert not tool._good(pick)
    rows = tool.picks(tool.latest([first, second, back]))
    learned, waiting = decisions_from(rows, {"بود": ("bovad",)}, {})
    assert learned.lookup("بود", "که", None) is None
    assert learned.lookup("بود", None, "از") == "bovad"
    assert waiting == []


def test_a_decision_is_not_listed_as_a_pick_for_its_word(http: TestClient):
    place = {"document_id": "fixture:a:1", "unit": 0, "line": 0}
    _decide(http, "Bud", EVERYWHERE, **place)
    pick = {
        "category": "linguistic",
        "target_type": "lexicon_entry",
        "target_id": "بود:Bud",
        "verdict": "good",
        "context": {
            "screen": "texts",
            "kind": "reading_here",
            "spelling_fa": "بود",
            "latin": "Bud",
            **place,
        },
    }
    assert http.post("/feedback", json=pick).status_code == 201
    proposed = http.get(
        "/texts/marked", params={"kind": "proposed", "document_id": "fixture:a:1"}
    ).json()
    assert proposed["total"] == 1
