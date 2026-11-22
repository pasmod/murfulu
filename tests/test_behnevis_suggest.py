"""The automatic suggestions beside the list of unsure spellings (2026-11-22).

Read, matched against the readings the list offers, served with each listed
spelling, and made from the offline readings by the import tool. Every word
and line here is written for the test; no corpus text (NOTICE).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from murfulu.api.app import app
from murfulu.behnevis import serve, suggest, unsure
from murfulu.db.models import Base

BANDS = [
    {"from": 0, "to": 50, "words": 10, "right": 6, "share": 0.6, "at_least": 0.3},
    {"from": 50, "to": 85, "words": 20, "right": 15, "share": 0.75, "at_least": 0.5},
    {"from": 85, "to": 100, "words": 40, "right": 36, "share": 0.9, "at_least": 0.76},
]

META = {"made": "2026-11-22", "corpus_version": "v0", "calibration": {"words": 70}}


def _listed(spelling: str, kind: str, known: list[str], **more: Any) -> dict[str, Any]:
    return {
        "rank": more.get("rank", 1),
        "spelling": spelling,
        "written": spelling,
        "places": 20,
        "unsure": 10,
        "kind": kind,
        "known": known,
        "sources": {},
        "read_as": more.get("read_as", []),
        "offered": more.get("offered", []),
        "before": [],
        "after": [],
        "examples": more.get("examples", []),
    }


def _row(latin: str, certainty: float, **more: Any) -> dict[str, Any]:
    return {
        "latin": latin,
        "as_read": more.get("as_read", latin),
        "certainty": certainty,
    }


# -- matching a suggestion to the readings the list offers ----------------------


def test_a_reading_is_compared_without_ezafe_case_accents_or_the_ain_mark():
    assert suggest.without_ezafe("sar-e") == "sar"
    assert suggest.without_ezafe("xāne-ye") == "xāne"
    # In any case, the accent composed or not (the review of 2026-11-22).
    assert suggest.without_ezafe("Del-E") == "Del"
    assert suggest.without_ezafe("del-é") == "del"
    assert suggest.without_ezafe("del-e\u0301") == "del"
    assert suggest.same("del-é", "Del") and suggest.same("Del-YE", "del")
    # Only a final ezafe: a hyphen inside is the reading's own.
    assert suggest.without_ezafe("ab-e-x") == "ab-e-x"
    assert suggest.same("bud", "Bud")
    assert suggest.same("bahre", "bahré")
    # Within one spelling the letters are the same: the mark for ع tells
    # nothing apart, and karbon mostly writes ع with a vowel letter.
    assert suggest.same("ˈelm", "Elm")
    assert not suggest.same("bud", "bovad")
    assert not suggest.same("", "")


def test_every_offered_reading_that_is_the_suggestion_matches_in_the_panels_order():
    one = _listed(
        "خود",
        "choice",
        ["Xod", "xod"],
        read_as=[["Xod", 5]],
        offered=[["xvad", 3], ["xod", 2]],
    )
    assert suggest.offered(one) == ["Xod", "xod", "xvad"]
    assert suggest.matching("xod", suggest.offered(one)) == ["Xod", "xod"]
    assert suggest.matching("xvod", suggest.offered(one)) == []


# -- the calibration --------------------------------------------------------------


def test_a_certainty_falls_in_one_band_and_100_in_the_last():
    bands = suggest.bands_from(BANDS)
    assert suggest.band_of(0, bands) == bands[0]
    assert suggest.band_of(50, bands) == bands[1]
    assert suggest.band_of(84.9, bands) == bands[1]
    assert suggest.band_of(85, bands) == bands[2]
    assert suggest.band_of(100, bands) == bands[2]
    assert suggest.band_of(101, bands) is None
    assert suggest.band_of(-1, bands) is None


@pytest.mark.parametrize(
    ("change", "says"),
    [
        ({1: {"from": 55}}, "gap or overlap"),
        ({0: {"from": 5}}, "cover 0 to 100"),
        ({2: {"to": 99}}, "cover 0 to 100"),
        ({1: {"share": 0.8}}, "share is not right/words"),
        ({1: {"at_least": 0.9}}, "lower bound above share"),
        ({0: {"right": 11}}, "impossible counts"),
        # Running backwards, or of no width: one certainty in two bands.
        ({0: {"to": 85}, 1: {"from": 85, "to": 50}, 2: {"from": 50}}, "not in order"),
        ({0: {"to": 0}, 1: {"from": 0}}, "not in order"),
        ({0: {"to": float("nan")}}, "gap or overlap|not in order"),
    ],
)
def test_a_calibration_that_does_not_add_up_is_refused(
    change: dict[int, dict[str, Any]], says: str
):
    bands = [dict(band) | change.get(i, {}) for i, band in enumerate(BANDS)]
    with pytest.raises(ValueError, match=says):
        suggest.bands_from(bands)


# -- what is served with a listed spelling ----------------------------------------


def _found(rows: dict[str, dict[str, Any]]) -> suggest.Suggestions:
    return suggest.Suggestions(META, rows, suggest.bands_from(BANDS))


def test_a_suggestion_the_bank_holds_is_served_as_the_banks_reading():
    found = _found({"بود": _row("bud", 95) | {"context": "x [بود] y"}})
    served = found.of(_listed("بود", "one", ["Bud"]))
    assert served is not None
    assert served["matches"] == ["Bud"] and served["in_bank"]
    assert (served["right_share"], served["right_at_least"]) == (0.9, 0.76)
    assert served["band"] == [85, 100]
    assert served["context"] == "x [بود] y"
    # A spelling the offline run did not read has none.
    assert found.of(_listed("دل", "choice", ["Del", "Dal"])) is None


def test_a_suggestion_no_offered_reading_matches_is_left_to_type():
    found = _found({"بود": _row("bovad", 60), "گفتم": _row("goftam", 40)})
    one = found.of(_listed("بود", "one", ["Bud"]))
    assert one is not None and one["matches"] == [] and not one["in_bank"]
    assert one["right_share"] == 0.75
    # Offered by the model, not held by the bank: matched, not in the bank.
    missing = found.of(_listed("گفتم", "missing", [], offered=[["goftam", 4]]))
    assert missing is not None
    assert missing["matches"] == ["goftam"] and not missing["in_bank"]


def test_the_file_lives_beside_its_model_and_reads_back(tmp_path: Path):
    model = tmp_path / "behnevis-v0.json"
    assert suggest.path_beside(model).name == "behnevis-suggest-v0.json"
    assert suggest.path_beside(tmp_path / "model.json").name == "model.suggest.json"
    meta = META | {"calibration": {"words": 70, "bands": BANDS}}
    suggest.write(suggest.path_beside(model), meta, {"بود": _row("bud", 95)})
    back = suggest.read(suggest.path_beside(model))
    assert back.rows == {"بود": _row("bud", 95)}
    assert back.about()["spellings"] == 1 and back.about()["tested_words"] == 70


def test_a_file_without_readings_or_of_another_format_is_refused(tmp_path: Path):
    path = tmp_path / "behnevis-suggest-v0.json"
    meta = META | {"calibration": {"words": 70, "bands": BANDS}}
    with pytest.raises(ValueError, match="lack a reading"):
        suggest.write(path, meta, {"بود": _row("", 95)})
    with pytest.raises(ValueError, match="lack a reading"):
        suggest.write(path, meta, {"بود": _row("bud", 120)})
    path.write_text(json.dumps({"format": 99, "meta": meta, "suggestions": {}}))
    with pytest.raises(ValueError, match="format"):
        suggest.read(path)
    # Fields the screens read, of the wrong kind (the review of 2026-11-22).
    for bad in (
        {"context": 42},
        {"context": "no brackets"},
        {"place": {"document_id": "x", "unit": "0", "line": 0, "word": 0}},
        {"marked": {"checked": 3, "fit": 5}},
        {"certainty": True},
    ):
        with pytest.raises(ValueError, match="lack a reading"):
            suggest.write(path, meta, {"بود": _row("bud", 95) | bad})


# -- served beside the model --------------------------------------------------------


@pytest.fixture
def model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "behnevis-v0.json"
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv(serve.PATH_VARIABLE, str(path))
    monkeypatch.delenv(serve.SUGGEST_VARIABLE, raising=False)
    unsure.write(
        unsure.path_beside(path),
        {"corpus_version": "v0", "words": 100, "unsure_words": 40},
        [_listed("بود", "one", ["Bud"]), _listed("دل", "choice", ["Del", "Dal"])],
    )
    return path


def _write_beside(model: Path, corpus_version: str = "v0") -> None:
    meta = META | {
        "corpus_version": corpus_version,
        "calibration": {"words": 70, "bands": BANDS},
    }
    suggest.write(suggest.path_beside(model), meta, {"بود": _row("bud", 95)})


def test_the_suggestions_are_read_beside_the_model_and_can_be_switched_off(
    model: Path, monkeypatch: pytest.MonkeyPatch
):
    assert serve.suggestions() is None
    _write_beside(model)
    found = serve.suggestions()
    assert found is not None and set(found.rows) == {"بود"}
    monkeypatch.setenv(serve.SUGGEST_VARIABLE, "off")
    assert serve.suggestions() is None


def test_suggestions_for_another_corpus_version_or_unreadable_are_not_shown(
    model: Path, caplog: pytest.LogCaptureFixture
):
    _write_beside(model, corpus_version="v9")
    with caplog.at_level(logging.WARNING):
        assert serve.suggestions() is None
    assert "suggestions are for v9" in caplog.text
    suggest.path_beside(model).write_text("{not json", encoding="utf-8")
    with caplog.at_level(logging.WARNING):
        assert serve.suggestions() is None
    assert "unreadable" in caplog.text


@pytest.fixture
def http(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    url = f"sqlite:///{tmp_path / 'authored.sqlite'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    monkeypatch.setenv("MURFULU_DATABASE_URL", url)
    yield TestClient(app)


def test_the_list_and_one_spelling_carry_the_suggestion(model: Path, http: TestClient):
    page = http.get("/texts/unsure").json()
    assert page["suggestions"] is None
    assert all(one["suggestion"] is None for one in page["spellings"])

    _write_beside(model)
    page = http.get("/texts/unsure").json()
    assert page["suggestions"]["spellings"] == 1
    assert page["suggestions"]["bands"][2]["share"] == 0.9
    bud, dil = page["spellings"]
    assert bud["suggestion"]["latin"] == "bud"
    assert bud["suggestion"]["matches"] == ["Bud"]
    assert bud["suggestion"]["right_share"] == 0.9
    assert dil["suggestion"] is None
    # Nothing is decided by it.
    assert bud["decided"] == []

    one = http.get("/texts/unsure/بود").json()
    assert one["listed"]["suggestion"]["in_bank"] is True
    assert one["decided"] == []
    assert http.get("/texts/unsure/دلم").json()["listed"] is None
