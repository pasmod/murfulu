"""The automatic suggestions, made from the offline readings (2026-11-22).

``murfulu.behnevis.offline`` checks the rows against the list and the
editions' marks; ``tools/import_reading_suggestions.py`` writes the file and
the report. Every word and line here is written for the test; no corpus text
(NOTICE).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from murfulu.behnevis import offline, suggest, unsure
from tests.test_behnevis_suggest import BANDS, _listed

# -- made from the offline readings -------------------------------------------------


def _example(text: str, word: int = 1) -> dict[str, Any]:
    return {
        "document_id": "fixture:a:1",
        "unit": 3,
        "line": 0,
        "word": word,
        "heading": "نویسنده · کتاب",
        "text": text,
    }


LISTED = [
    _listed("بود", "one", ["Bud"], rank=1, examples=[_example("ما بود او")]),
    _listed("دل", "choice", ["Del", "Dal"], rank=2, examples=[_example("یک دل دو")]),
]


def _offline(
    spelling: str, rank: int, kind: str, line: str, **more: Any
) -> dict[str, Any]:
    return {
        "rank": rank,
        "spelling": spelling,
        "kind": kind,
        "context": f"x [{spelling}] y",
        "example_line": line,
        "document_id": "fixture:a:1",
        "reader_reading": more.get("reading", "bud"),
        "reader_certainty": more.get("certainty", 95.0),
        "measured_right_share": more.get("share", 0.9),
        "matches_a_bank_reading": True,
    }


GOOD = [
    _offline("بود", 1, "one", "ما بود او"),
    _offline(
        "دل", 2, "choice", "یک دل دو", reading="del-e", certainty=60.0, share=0.75
    ),
]


def test_the_reading_and_certainty_fields_are_found_by_their_endings():
    assert offline.column(GOOD, "_reading", str, None) == "reader_reading"
    assert offline.column(GOOD, "_certainty", (int, float), None) == "reader_certainty"
    with pytest.raises(ValueError, match="no field"):
        offline.column(GOOD, "_reading", str, "other_reading")


def test_offline_rows_take_the_lists_place_and_lose_the_ezafe():
    bands = suggest.bands_from(BANDS)
    rows, problems = offline.convert(
        GOOD, LISTED, "reader_reading", "reader_certainty", bands
    )
    assert problems == []
    assert rows["دل"]["latin"] == "del" and rows["دل"]["as_read"] == "del-e"
    assert rows["دل"]["certainty"] == 60 and isinstance(rows["دل"]["certainty"], int)
    assert rows["بود"]["place"] == {
        "document_id": "fixture:a:1",
        "unit": 3,
        "line": 0,
        "word": 1,
    }


@pytest.mark.parametrize(
    ("bad", "says"),
    [
        ({"spelling": "گفتم"}, "not in the list"),
        ({"rank": 7}, "rank or kind"),
        ({"example_line": "ما بود"}, "example line"),
        ({"reader_certainty": 140}, "certainty"),
        ({"reader_reading": "-e"}, "no reading"),
        ({"measured_right_share": 0.6}, "not its band's"),
        ({"context": 42}, "context does not hold"),
        ({"context": "x [دل] y"}, "context does not hold"),
    ],
)
def test_an_offline_row_that_does_not_match_the_list_is_refused(
    bad: dict[str, Any], says: str
):
    rows, problems = offline.convert(
        [GOOD[0] | bad, GOOD[1], GOOD[1]],
        LISTED,
        "reader_reading",
        "reader_certainty",
        suggest.bands_from(BANDS),
    )
    assert "بود" not in rows
    assert any(says in one for one in problems)
    assert "دل: twice" in problems


def test_a_reading_is_checked_only_on_the_marked_places_it_lines_up_with():
    marked = [
        {"spelling": "بود", "written": "بُوَد"},  # bovad, not Bud
        {"spelling": "بود", "written": "بِود"},  # neither
        {"spelling": "بود", "written": "بود"},  # no sign: says nothing
        {"spelling": "دل", "written": "دِل"},  # not asked for
    ]
    fits = offline.marked_fits({"بود": ["bovad", "Bud"]}, marked)
    marks = fits["بود"]
    assert (marks.checked["bovad"], marks.fit["bovad"]) == (2, 1)
    assert (marks.checked["Bud"], marks.fit["Bud"]) == (2, 0)
    assert marks.of("bovad") == "1 of 2" and marks.of("bad") == "—"
    assert marks.share("bovad") == 0.5 and marks.share("bad") == 0.0


def _tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "import_reading_suggestions",
        Path(__file__).resolve().parents[1] / "tools" / "import_reading_suggestions.py",
    )
    tool = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(tool)  # type: ignore[union-attr]
    return tool


def test_the_tool_writes_the_file_and_a_report_without_quoting_a_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    model = tmp_path / "behnevis-v0.json"
    unsure.write(unsure.path_beside(model), {"corpus_version": "v0"}, LISTED)
    (tmp_path / "behnevis-marked-v0.jsonl").write_text(
        "\n".join(
            json.dumps({"spelling": "بود", "written": w}, ensure_ascii=False)
            for w in ("بُود", "بُود", "بُود", "بُود", "بُوَد")
        ),
        encoding="utf-8",
    )
    readings = tmp_path / "readings.json"
    calibration = {
        "words": 70,
        "bands": [{**b, "lower_95": b["at_least"]} for b in BANDS],
    }
    readings.write_text(
        json.dumps(
            {
                "meta": {
                    "made": "2026-11-22",
                    "corpus_version": "v0",
                    "calibration": calibration,
                },
                "readings": GOOD,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert _tool().main(["v0", str(readings), "--data", str(tmp_path)]) == 0
    found = suggest.read(suggest.path_beside(model))
    assert found.rows["بود"]["marked"] == {"checked": 5, "fit": 4}
    assert "language model" in found.meta["method"]
    report = capsys.readouterr().out
    assert "| one | 1 | 1 | 0 | 0 | 0 |" in report
    assert "ما بود او" not in report and "یک دل دو" not in report

    # One listed spelling unread: nothing is written over the file.
    readings.write_text(
        json.dumps(
            {
                "meta": {"corpus_version": "v0", "calibration": calibration},
                "readings": GOOD[:1],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="nothing written"):
        _tool().main(["v0", str(readings), "--data", str(tmp_path)])
    assert suggest.read(suggest.path_beside(model)).rows["بود"]["marked"]
