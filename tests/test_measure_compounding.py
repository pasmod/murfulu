"""The second productivity pass, and the merge that puts it in one file.

The compounding rules reported `types_built: 0` for as long as they existed,
with a reason that was wrong three times running — most recently "nothing
calls it yet", which stopped being true the morning `/compound` was written.
A zero beside a rule that builds 28 million forms is worse than no figure.

What matters in the merge is what it must **not** do: touch a row it did not
measure, or move a figure into a file belonging to another corpus version.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"


def _tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "measure_compounding", TOOLS / "measure_compounding.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _file(path: Path, version: str = "v8") -> Path:
    path.write_text(
        json.dumps(
            {
                "corpus_version": version,
                "rules": [
                    {"rule_id": "N-048", "types_built": 24153, "band": "middle"},
                    {"rule_id": "V-078", "types_built": 0, "band": None},
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_only_the_rules_it_measured_are_touched(tmp_path: Path) -> None:
    tool = _tool()
    target = _file(tmp_path / "productivity.json")

    changed = tool._merge(
        target,
        {"V-078": {"types_built": 28896536, "unmeasurable_reason": ""}},
        "v8",
    )

    rows = {
        row["rule_id"]: row
        for row in json.loads(target.read_text(encoding="utf-8"))["rules"]
    }
    assert changed == 1
    assert rows["V-078"]["types_built"] == 28896536
    assert rows["V-078"]["measured"] is True
    # The affix rule is left exactly as it was, band and all.
    assert rows["N-048"]["types_built"] == 24153
    assert rows["N-048"]["band"] == "middle"


def test_a_measured_compounding_rule_gets_no_band(tmp_path: Path) -> None:
    """The bands are cut from the affixation rates; a product is not on that scale."""
    tool = _tool()
    target = _file(tmp_path / "productivity.json")

    tool._merge(target, {"V-078": {"types_built": 10, "unmeasurable_reason": ""}}, "v8")

    rows = {
        row["rule_id"]: row
        for row in json.loads(target.read_text(encoding="utf-8"))["rules"]
    }
    assert rows["V-078"]["band"] is None
    assert rows["V-078"]["measured_by"] == "tools/measure_compounding.py"


def test_a_rule_with_no_pool_is_not_marked_measured(tmp_path: Path) -> None:
    """A refusal with a reason is not a measurement of zero."""
    tool = _tool()
    target = _file(tmp_path / "productivity.json")

    tool._merge(target, {"V-078": {"unmeasurable_reason": "no pool"}}, "v8")

    rows = {
        row["rule_id"]: row
        for row in json.loads(target.read_text(encoding="utf-8"))["rules"]
    }
    assert rows["V-078"]["measured"] is False
    assert rows["V-078"]["unmeasurable_reason"] == "no pool"


def test_a_figure_never_moves_into_another_versions_file(tmp_path: Path) -> None:
    """Every one of these numbers is about one corpus and only that one."""
    tool = _tool()
    target = _file(tmp_path / "productivity.json", version="v7")

    with pytest.raises(SystemExit):
        tool._merge(target, {"V-078": {"types_built": 1}}, "v8")
