"""The attribution behind every lexicon-switch comparison (data/compare-*.md).

Its one promise is the check line: **every path two builds disagree on traces
to a lexicon reading that changed in a way the build can feel**. A tool that
can read zero while a path moved for another reason is worse than none, so
these are the ways it could be fooled.
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path
from types import ModuleType

import pytest

from .conftest import FIELDS, SCHEMA

ROOT = Path(__file__).resolve().parents[1]


def _tool() -> ModuleType:
    name = "attribute_lexicon_change"
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


tool = _tool()

NO_OVERRIDES = """version: 0.0.0
lexicon_snapshots: [lexicon-20990101, lexicon-20990102]
corrections: []
additions: []
"""


def _row(row_id: int, spelling: str, latin: str, pos: str, review: int = 0) -> tuple:
    return (row_id, spelling, spelling, spelling, latin, None, None, None, None,
            1.0, review, None, None, pos, None, None)  # fmt: skip


def _lexicon(
    path: Path,
    rows: list[tuple],
    merges: dict[int, int] | None = None,
    groups: dict[int, list[str]] | None = None,
) -> Path:
    connection = sqlite3.connect(path)
    connection.execute(SCHEMA)
    connection.executemany(
        f"INSERT INTO infinitives ({FIELDS}) VALUES ({', '.join('?' * 16)})", rows
    )
    if merges is not None:
        connection.execute("CREATE TABLE merge_map (old_id, new_id, merged_at)")
        connection.executemany(
            "INSERT INTO merge_map VALUES (?, ?, '2099')", list(merges.items())
        )
    if groups is not None:
        connection.execute("CREATE TABLE bank_group (word_id INTEGER, bank_group TEXT)")
        connection.executemany(
            "INSERT INTO bank_group VALUES (?, ?)",
            [(row, group) for row, names in groups.items() for group in names],
        )
        connection.execute(
            "CREATE TABLE bank_labels (key TEXT PRIMARY KEY, label_fa TEXT)"
        )
    connection.commit()
    connection.close()
    return path


def _derivations(path: Path, paths: dict[str, list[tuple[str, str, str]]]) -> Path:
    with path.open("w", encoding="utf-8") as handle:
        for record, sources in paths.items():
            handle.write(
                json.dumps(
                    {
                        "id": record,
                        "paths": [
                            {
                                "source_spelling_fa": spelling,
                                "source_latin": latin,
                                "base_form": latin,
                                "rule_ids": [rule],
                            }
                            for spelling, latin, rule in sources
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return path


@pytest.fixture
def rules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An overrides table that applies to both test snapshots and holds nothing."""
    directory = tmp_path / "rules"
    directory.mkdir()
    for name in ("bank_groups.yaml", "lexicon_categories.yaml"):
        (directory / name).write_text(
            (ROOT / "rules" / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    (directory / "lexicon_overrides.yaml").write_text(NO_OVERRIDES, encoding="utf-8")
    monkeypatch.setenv("MURFULU_RULES_PATH", str(directory))
    from murfulu.lexicon import overrides

    overrides.loaded.cache_clear()
    yield directory
    overrides.loaded.cache_clear()


def _run(tmp_path: Path, old: list[tuple], new: list[tuple], **extra: object) -> int:
    old_lexicon = _lexicon(tmp_path / "lexicon-20990101.sqlite", old)
    new_lexicon = _lexicon(
        tmp_path / "lexicon-20990102.sqlite",
        new,
        extra.get("merges"),  # type: ignore[arg-type]
        extra.get("groups"),  # type: ignore[arg-type]
    )
    before = _derivations(tmp_path / "before.jsonl", extra["before"])  # type: ignore[arg-type]
    after = _derivations(tmp_path / "after.jsonl", extra["after"])  # type: ignore[arg-type]
    argv = [str(old_lexicon), str(new_lexicon), str(before), str(after)]
    argv += list(extra.get("argv", ()))  # type: ignore[call-overload]
    return int(tool.main(argv))


def test_a_path_lost_where_only_the_review_flag_moved_fails_the_check(
    tmp_path: Path, rules: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    old = [_row(1, "کار", "Kār", "اسم معنی", review=1)]
    new = [_row(1, "کار", "Kār", "اسم معنی", review=0)]
    status = _run(
        tmp_path, old, new,
        before={"Kāri:barnam": [("کار", "Kār", "N-098")]}, after={},
    )  # fmt: skip
    assert status == 1
    assert "metadata only (needs_review changed)" in capsys.readouterr().out


def test_a_merged_row_is_named_as_merged_not_removed(
    tmp_path: Path, rules: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    old = [_row(1, "کار", "Kār", "اسم معنی"), _row(2, "کار", "Kar", "اسم معنی")]
    new = [_row(1, "کار", "Kār", "اسم معنی")]
    status = _run(
        tmp_path, old, new, merges={2: 1},
        before={"Kari:barnam": [("کار", "Kar", "N-098")]}, after={},
    )  # fmt: skip
    assert status == 0
    assert "merged into another row" in capsys.readouterr().out


def test_a_words_own_reading_wins_over_another_rows_variant(
    tmp_path: Path, rules: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """کشنی: *Košni* was a second reading of *Kešni*, and became a row of its own."""
    kesni = list(_row(1, "کشنی", "Kešni", "اسم ذات"))
    kesni[-1] = '["Kešni", "Košni"]'
    old = [tuple(kesni)]
    new = [tuple(kesni), _row(2, "کشنی", "Košni", "اسم معنی")]
    status = _run(
        tmp_path, old, new,
        before={}, after={"Košnii:barnam": [("کشنی", "Košni", "N-098")]},
    )  # fmt: skip
    assert status == 0
    # Matched to the new row's own reading, so what moved is named — not
    # "source unchanged", which matching it to *Kešni*'s variant would say.
    assert "entered the input pool" in capsys.readouterr().out


def test_leaving_the_input_pool_explains_a_lost_path(
    tmp_path: Path, rules: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """فری: صفت (in the pool) became صوت (out of it); the classes alone did not move."""
    old = [_row(1, "فری", "fari", "صفت")]
    new = [_row(1, "فری", "fari", "صوت")]
    status = _run(
        tmp_path, old, new, groups={1: ["برنام", "صوت"]},
        before={"nāfarie:barnam": [("فری", "fari", "N-087")]}, after={},
    )  # fmt: skip
    output = capsys.readouterr().out
    assert "left the input pool" in output
    assert "word classes changed" not in output, "barnam on both sides"
    assert status == 0


def test_a_missing_overrides_table_is_refused(tmp_path: Path, rules: Path) -> None:
    old = [_row(1, "کار", "Kār", "اسم معنی")]
    with pytest.raises(SystemExit, match="no such file"):
        _run(
            tmp_path, old, old, before={}, after={},
            argv=["--old-overrides", str(tmp_path / "missing.yaml")],
        )  # fmt: skip


def test_an_overrides_table_for_another_snapshot_is_refused(
    tmp_path: Path, rules: Path
) -> None:
    other = tmp_path / "other.yaml"
    other.write_text(NO_OVERRIDES.replace("20990101", "20000101"), encoding="utf-8")
    old = [_row(1, "کار", "Kār", "اسم معنی")]
    with pytest.raises(SystemExit, match="wrong table"):
        _run(
            tmp_path, old, old, before={}, after={},
            argv=["--old-overrides", str(other)],
        )  # fmt: skip
