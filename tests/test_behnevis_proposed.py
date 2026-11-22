"""The readings the bank lacks, gathered for karbon, and the linguist's confirmation.

The project lead's rule of 2026-11-22: what the linguist confirms on the
reading screen and the bank lacks — the spelling altogether, or only this
reading — is gathered with an example and sent to karbon as one issue.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from murfulu.api.app import app
from murfulu.behnevis import decided, proposed, serve
from murfulu.behnevis.choice import ChoiceModel
from murfulu.behnevis.letters import LetterModel
from murfulu.behnevis.transcribe import Transcriber, bank_from
from murfulu.db.models import Base

#: The bank holds بود as the noun and دل two ways; آرد, کنم and و not at all
#: as the readings below need them.
BANK = bank_from(
    [("بود", "Bud"), ("دل", "Del"), ("دل", "Dal"), ("آرد", "Ārd"), ("تا", "Tā")]
)
#: The function-word list: و is not in the bank at all, تا only as the noun.
FUNCTIONS = {"و": ("va", "o"), "تا": ("tā",)}

PLACE = {
    "document_id": "fixture:a:1",
    "unit": 2,
    "line": 0,
    "word": 1,
    "heading": "حافظ · غزل ۳",
    "written": "آرد",
    "before": "دست",
    "after": "دل",
    "line_text": "به دست آرد دل ما را",
}


def _here(spelling: str, latin: str, **more: Any) -> dict[str, Any]:
    return {
        "screen": "texts",
        "kind": proposed.HERE,
        "spelling_fa": spelling,
        "latin": latin,
        "in_bank": False,
        "model_latin": more.pop("model", None),
        **more,
    }


def _decided(
    spelling: str, latin: str | None, scope: str, word: str | None = None, **more: Any
) -> dict[str, Any]:
    return {
        "screen": "texts",
        "kind": decided.KIND,
        "spelling_fa": spelling,
        "latin": latin,
        "scope": scope,
        "scope_word": word,
        "withdrawn": more.pop("withdrawn", False),
        **more,
    }


def _confirm(spelling: str, latin: str, **more: Any) -> dict[str, Any]:
    return {
        "screen": "texts",
        "kind": proposed.CONFIRMED,
        "spelling_fa": spelling,
        "latin": latin,
        "withdrawn": more.pop("withdrawn", False),
        **more,
    }


def _rows(*contexts: dict[str, Any]) -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            id=at,
            context=context,
            target_id=f"{context['spelling_fa']}:{context.get('latin') or ''}",
            verdict="unsure" if context.get("withdrawn") else "good",
            created_at=None,
        )
        for at, context in enumerate(contexts, start=1)
    ]


def _by_reading(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(one["spelling"], one["latin"]): one for one in rows}


# -- the confirmations ------------------------------------------------------------


def test_the_newest_confirmation_counts_and_one_taken_back_clears_it():
    def said(*contexts: dict[str, Any]) -> dict[tuple[str, str], int]:
        return proposed.confirmed(
            one
            for one in (
                proposed.confirmation_from(context, at)
                for at, context in enumerate(contexts, start=1)
            )
            if one is not None
        )

    assert said(_confirm("آرد", "ārad")) == {("آرد", "ārad"): 1}
    # Taken back, naming the one it takes back.
    assert said(_confirm("آرد", "ārad"), _confirm("آرد", "ārad", withdrawn=True)) == {}
    # Confirmed again after: in force again, under the newer id.
    assert said(
        _confirm("آرد", "ārad"),
        _confirm("آرد", "ārad", withdrawn=True, replaces=1),
        _confirm("آرد", "ārad"),
    ) == {("آرد", "ārad"): 3}
    # A withdrawal that names an older confirmation leaves the newer one.
    assert said(
        _confirm("آرد", "ārad"),
        _confirm("آرد", "ārad"),
        _confirm("آرد", "ārad", withdrawn=True, replaces=1),
    ) == {("آرد", "ārad"): 2}
    # One reading's confirmation says nothing of another's, and a half-space
    # in the spelling is the same spelling.
    assert said(_confirm("می‌کنم", "mikonam"), _confirm("میکنم", "mikonom")) == {
        ("میکنم", "mikonam"): 1,
        ("میکنم", "mikonom"): 2,
    }
    # A record of another kind, or one that names no reading, is not one.
    assert proposed.confirmation_from(_here("آرد", "ārad"), 1) is None
    assert proposed.confirmation_from(_confirm("آرد", ""), 1) is None


# -- what waits for karbon --------------------------------------------------------


def test_a_reading_the_bank_lacks_is_one_row_with_its_kind_and_its_places():
    rows = _rows(
        _here("آرد", "ārad", model="Ārd", **PLACE),
        _here("آرد", "ārad", **{**PLACE, "unit": 5, "line_text": None}),
        _here("کنم", "konam", **{**PLACE, "written": "کنم"}),
        # The bank holds it: a pick in context, the model's.
        _here("دل", "Del", **PLACE),
        # The function-word list holds it: the model's too.
        _here("و", "o", **PLACE),
        # Another screen's record on a reading is none of this list's.
        {**_here("دل", "dil"), "screen": "bank"},
    )
    found = _by_reading(proposed.waiting(rows, BANK, FUNCTIONS))
    arad = found[("آرد", "ārad")]
    assert (arad["kind"], arad["bank"], arad["times"]) == (proposed.READING, ["Ārd"], 2)
    assert (arad["origin"], arad["model"]) == (proposed.READER, "Ārd")
    assert [place["unit"] for place in arad["places"]] == [2, 5]
    assert arad["places"][0]["text"] == "به دست آرد دل ما را"
    assert arad["places"][1]["text"] is None
    konam = found[("کنم", "konam")]
    assert (konam["kind"], konam["bank"]) == (proposed.MISSING, [])
    assert ("دل", "Del") not in found and ("دل", "dil") not in found
    # The most proposed first.
    assert proposed.waiting(rows, BANK, FUNCTIONS)[0]["latin"] == "ārad"


def test_the_function_word_lists_own_readings_are_rows_where_the_bank_lacks_them():
    found = _by_reading(proposed.waiting([], BANK, FUNCTIONS))
    assert set(found) == {("و", "va"), ("و", "o"), ("تا", "tā")}
    assert found[("و", "va")]["kind"] == proposed.MISSING
    ta = found[("تا", "tā")]
    assert (ta["kind"], ta["bank"], ta["origin"]) == (
        proposed.READING,
        ["Tā"],
        proposed.FUNCTION,
    )
    assert ta["times"] == 0 and ta["places"] == []
    # Once the bank holds one, it is no longer a gap.
    richer = {**BANK, "تا": ("Tā", "tā")}
    assert ("تا", "tā") not in _by_reading(proposed.waiting([], richer, FUNCTIONS))


def test_a_decision_in_force_says_what_it_was_decided_for():
    rows = _rows(
        _decided("بود", "bovad", decided.EVERYWHERE),
        _decided("بود", "bovad", decided.AFTER_WORD, "که"),
        _decided("بود", "bud", decided.BEFORE_WORD, "از"),
        # Taken back: the reading leaves the list with it.
        _decided("بود", None, decided.BEFORE_WORD, "از", withdrawn=True, replaces=3),
    )
    found = _by_reading(proposed.waiting(rows, BANK, {}))
    assert set(found) == {("بود", "bovad")}
    assert found[("بود", "bovad")]["decided"] == [
        {"scope": decided.EVERYWHERE, "word": None},
        {"scope": decided.AFTER_WORD, "word": "که"},
    ]
    assert found[("بود", "bovad")]["times"] == 2


def test_a_row_says_whether_the_linguist_confirmed_it():
    rows = _rows(
        _here("آرد", "ārad", **PLACE),
        _here("کنم", "konam", **PLACE),
        _confirm("آرد", "ārad"),
        _confirm("کنم", "konam"),
        _confirm("کنم", "konam", withdrawn=True, replaces=4),
        _confirm("و", "va"),
    )
    found = _by_reading(proposed.waiting(rows, BANK, FUNCTIONS))
    assert found[("آرد", "ārad")]["confirmed"] == {"id": 3, "created_at": None}
    assert found[("کنم", "konam")]["confirmed"] is None
    assert found[("و", "va")]["confirmed"]["id"] == 6
    assert found[("و", "o")]["confirmed"] is None


def test_a_confirmation_is_not_a_save_for_a_word_in_a_line():
    """It names no place, so it never replaces a pick, and is never one itself."""
    rows = _rows(_here("آرد", "ārad", **PLACE), {**_confirm("آرد", "ārad"), **PLACE})
    assert len(proposed.latest(rows)) == 2
    assert all(proposed.good(row) for row in rows)
    back = _rows(_confirm("آرد", "ārad", withdrawn=True))[0]
    assert back.verdict == "unsure" and proposed.good(back)


# -- the issue's text -------------------------------------------------------------


def _export_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "export_reading_proposals",
        Path(__file__).resolve().parents[1] / "tools" / "export_reading_proposals.py",
    )
    tool = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(tool)  # type: ignore[union-attr]
    return tool


def test_the_issue_holds_only_what_was_confirmed_in_two_parts_with_an_example():
    tool = _export_tool()
    rows = _rows(
        _here("آرد", "ārad", **PLACE),
        _here("کنم", "konam", **{**PLACE, "written": "کنم", "line_text": None}),
        _here("نور", "nur", **PLACE),
        _decided("بود", "bovad", decided.AFTER_WORD, "که"),
        _confirm("آرد", "ārad"),
        _confirm("کنم", "konam"),
        _confirm("بود", "bovad"),
        _confirm("تا", "tā"),
    )
    text = tool.confirmed_report(proposed.waiting(rows, BANK, FUNCTIONS))
    assert "## Spellings the bank does not hold (1)" in text
    assert "## Spellings the bank holds, without this reading (3)" in text
    # The line where it has one, else the words around it; and where.
    assert "| آرد | ārad | Ārd | 1 |  | به دست آرد دل ما را — حافظ · غزل ۳ |" in text
    assert "| کنم | konam | 1 |  | دست کنم دل — حافظ · غزل ۳ |" in text
    assert "| بود | bovad | Bud | 1 | after که |  |" in text
    assert "| تا | tā (function word) | Tā | 0 |" in text
    # Proposed and never confirmed: not in the issue.
    assert "nur" not in text and "| و |" not in text
    # Nothing confirmed: both parts say so.
    assert tool.confirmed_report([]).count("None.") == 2


# -- the reading screen is told which readings are the bank's ---------------------


def test_each_word_says_which_readings_the_bank_holds():
    pairs = [
        ("دل", "Del"),
        ("دل", "Dal"),
        ("کار", "Kār"),
        ("دست", "Dast"),
        ("آرام", "ārām"),
    ]
    model = Transcriber(
        bank=bank_from(pairs),
        letters=LetterModel.train(pairs),
        choice=ChoiceModel.train([]),
        functions={"و": ("va", "o")},
    )
    words = [{"fa": fa, "s": fa} for fa in ("دل", "و", "کارم")]
    units = [{"kind": "couplet", "lines": [{"words": words}]}]
    serve.annotate(units, model)
    del_, va, karam = (word["auto"] for word in words)
    assert del_["bank"] == ["Del", "Dal"] and del_["latin"] in del_["bank"]
    # The function word's reading is this project's, not the bank's.
    assert va["bank"] == [] and va["latin"] in va["known"]
    # A guess for a word the bank lacks.
    assert karam["bank"] == [] and karam["latin"]


# -- over HTTP --------------------------------------------------------------------


@pytest.fixture
def http(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    url = f"sqlite:///{tmp_path / 'authored.sqlite'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    monkeypatch.setenv("MURFULU_DATABASE_URL", url)
    monkeypatch.setattr(serve, "held", lambda: (BANK, FUNCTIONS))
    monkeypatch.setattr(serve, "unsure_list", lambda: None)
    yield TestClient(app)


def _leave(http: TestClient, context: dict[str, Any]) -> int:
    answer = http.post(
        "/feedback",
        json={
            "category": "linguistic",
            "target_type": "lexicon_entry",
            "target_id": f"{context['spelling_fa']}:{context.get('latin') or ''}",
            "verdict": "unsure" if context.get("withdrawn") else "good",
            "context": context,
        },
    )
    assert answer.status_code == 201
    return int(answer.json()["id"])


def test_the_list_is_a_503_without_a_word_bank(
    http: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(serve, "held", lambda: None)
    assert http.get("/texts/karbon").status_code == 503


def test_the_list_is_served_filtered_and_follows_the_confirmations(http: TestClient):
    _leave(http, _here("آرد", "ārad", **PLACE))
    _leave(http, _here("کنم", "konam", **{**PLACE, "written": "کنم"}))
    page = http.get("/texts/karbon").json()
    # Two from readers, three from the function-word list.
    assert (page["total"], page["confirmed"], page["missing"]) == (5, 0, 3)
    first = page["rows"][0]
    assert first["times"] == 1 and first["confirmed"] is None
    assert first["places"][0]["text"] == "به دست آرد دل ما را"
    assert "spelling_fa_marked" in first and first["examples"] == []

    confirmation = _leave(http, _confirm("آرد", "ārad"))
    said = http.get("/texts/karbon", params={"state": "confirmed"}).json()
    assert (said["confirmed"], said["matching"]) == (1, 1)
    [row] = said["rows"]
    assert (row["spelling"], row["latin"]) == ("آرد", "ārad")
    assert row["confirmed"]["id"] == confirmation and row["confirmed"]["created_at"]
    waiting = http.get("/texts/karbon", params={"state": "open", "size": 2}).json()
    assert (waiting["matching"], len(waiting["rows"])) == (4, 2)

    # Taken back, it waits again.
    _leave(http, _confirm("آرد", "ārad", withdrawn=True, replaces=confirmation))
    assert http.get("/texts/karbon").json()["confirmed"] == 0
    assert http.get("/texts/karbon", params={"state": "sent"}).status_code == 422


def test_a_confirmation_is_not_listed_as_a_reading_saved_for_a_word(http: TestClient):
    _leave(http, _here("آرد", "ārad", **PLACE))
    _leave(http, {**_confirm("آرد", "ārad"), "document_id": "fixture:a:1"})
    saved = http.get(
        "/texts/marked", params={"kind": "proposed", "document_id": "fixture:a:1"}
    ).json()
    assert saved["total"] == 1 and saved["marked"][0]["latin"] == "ārad"


def test_a_row_without_a_line_borrows_the_measured_lists_examples(
    http: TestClient, monkeypatch: pytest.MonkeyPatch
):
    example = {
        "document_id": "fixture:b:2",
        "unit": 1,
        "line": 0,
        "word": 0,
        "heading": "سعدی · گلستان",
        "text": "بود مردی",
    }
    listed = [{"spelling": "بود", "examples": [example] * 5}]
    monkeypatch.setattr(serve, "unsure_list", lambda: ({}, listed))
    _leave(http, _decided("بود", "bovad", decided.EVERYWHERE))
    _leave(http, _here("آرد", "ārad", **PLACE))
    rows = _by_reading(http.get("/texts/karbon").json()["rows"])
    assert rows[("بود", "bovad")]["examples"] == [example] * proposed.PLACES
    # A row with a line of its own keeps to it.
    assert rows[("آرد", "ārad")]["examples"] == []
