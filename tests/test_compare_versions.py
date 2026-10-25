"""The release check, tested on the failure it exists to catch.

v6 was built without the poet-century table, which does not fail: the tool
prints one line and builds a corpus where every poem is undated. Four of its
five release figures were identical to v4 and it went into service anyway.
The shape of that failure is what is asserted here — four numbers still, one
number jumped to the whole document count — because a check that cannot
reproduce its own motivating failure is not a check.

The fixtures are written here rather than read from `data/`, which is not
committed.
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
        "compare_versions", TOOLS / "compare_versions.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _report(path: Path, version: str, **figures: int) -> Path:
    base = {
        "corpus_version": version,
        "documents": 133148,
        "tokens": 25497189,
        "spellings": 409916,
        "spellings_linked": 16714,
        "documents_without_century": 98627,
        "lexicon_snapshot_id": "lexicon-20260808:45e05ff66c37",
    }
    base.update(figures)
    path.write_text(json.dumps(base), encoding="utf-8")
    return path


def _derivations(path: Path, records: list[dict[str, object]]) -> Path:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    return path


def test_the_undated_corpus_shows_up_as_one_moved_number(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tool = _tool()
    before = _report(tmp_path / "before.json", "v4")
    after = _report(tmp_path / "after.json", "v6", documents_without_century=133148)

    tool.compare_reports(before, after)
    printed = capsys.readouterr().out

    assert printed.count("same") == 4
    assert "+34,521" in printed


def test_an_unchanged_rebuild_moves_none_of_the_five(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tool = _tool()
    before = _report(tmp_path / "before.json", "v7")
    after = _report(tmp_path / "after.json", "v8")

    tool.compare_reports(before, after)

    assert capsys.readouterr().out.count("same") == len(tool.RELEASE_FIGURES)


def test_a_rule_is_counted_on_every_path_not_only_the_first(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`rule_chain` carries the first path alone, so it understates a rule.

    The form below is reached two ways and `rule_chain` names one of them.
    Counting from it would report N-023 as building nothing, which is exactly
    the mistake this comparison is used to check.
    """
    tool = _tool()
    reached_twice: dict[str, object] = {
        "form_latin": "Dandānāyi",
        "attestation": "none",
        "rule_chain": ["V-024", "V-025"],
        "paths": [
            {"rule_ids": ["V-024", "V-025"]},
            {"rule_ids": ["N-023", "N-095"]},
        ],
    }
    before = _derivations(tmp_path / "before.jsonl", [reached_twice])
    after = _derivations(
        tmp_path / "after.jsonl",
        [{**reached_twice, "paths": [{"rule_ids": ["V-024", "V-025"]}]}],
    )

    tool.compare_derivations(before, after)
    printed = capsys.readouterr().out

    assert "N-023" in printed
    assert "records" in printed
    # The form survives; only the path through the retired rule goes.
    assert "1 rules moved" not in printed  # N-023 and N-095 both lose it
    assert "2 rules moved" in printed


def test_a_difference_the_named_rules_cannot_account_for_is_not_hidden(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The four zero lines are the whole point, so make one of them non-zero.

    Here a second form disappears for no reason connected to N-023. Totals
    alone would show only that the count fell; the attribution says the fall
    is not accounted for.
    """
    tool = _tool()
    before = _derivations(
        tmp_path / "before.jsonl",
        [
            {"id": "a", "paths": [{"rule_ids": ["N-023", "N-095"]}]},
            {"id": "b", "paths": [{"rule_ids": ["N-072"]}]},
        ],
    )
    after = _derivations(tmp_path / "after.jsonl", [])

    tool.attribute(before, after, {"N-023"})
    lines = capsys.readouterr().out.splitlines()

    def count(fragment: str) -> str:
        line = next(row for row in lines if fragment in row)
        return line.removesuffix("must be 0").split()[-1]

    assert count("every path one of these") == "1"
    assert count("another reason") == "1"


def _record(
    rid: str,
    fa: str,
    *,
    count: int = 5,
    homograph: str = "",
    sisters: tuple[str, ...] = (),
    rule: str = "V-049",
    base: str = "keh",
) -> dict[str, object]:
    record: dict[str, object] = {
        "id": f"{rid}:karnam",
        "form_latin": rid,
        "form_fa": fa,
        "paths": [{"base_form": base, "rule_ids": [rule]}],
        "attestation": "spelling",
        "attested_count": count,
        "sister_forms": list(sisters),
        "base_attested": True,
        "generated_at": "now",
    }
    if homograph:
        record["attestation_function_word"] = homograph
    return record


def _jsonl(path: Path, records: list[dict[str, object]]) -> Path:
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8",
    )
    return path


def test_function_word_changes_are_attributed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """که losing its count is expected; گفتار moving would not be."""
    before = _jsonl(
        tmp_path / "a.jsonl",
        [
            _record("Keh", "که", count=609699),
            _record("Goftār", "گفتار", sisters=("Keh", "Raftār"), rule="V-049"),
            _record("Raftār", "رفتار", rule="V-010", base="raft"),
        ],
    )
    after = _jsonl(
        tmp_path / "b.jsonl",
        [
            _record("Keh", "که", count=0, homograph="conjunction"),
            _record("Goftār", "گفتار", sisters=("Raftār", "Keh"), rule="V-049"),
            _record("Raftār", "رفتار", count=6, rule="V-010", base="raft"),
        ],
    )
    counts = _tool().function_words(before, after)
    assert counts["evidence_listed"] == 1
    assert counts["sisters_follow"] == 1
    # رفتار moved for no reason the list explains: reported, never hidden.
    assert counts["evidence_other"] == 1
    assert counts["other_field"] == 0
    assert "must be 0" in capsys.readouterr().out
