"""Reading karbon 1.3.2's word bank (``lexicon-20261111``).

karbon 1.3.0 turned the lexicon into the linguist's word bank, and 1.3.2 is
its final form. Three additions, each read here only when present, so every
earlier snapshot still opens unchanged:

- ``bank_group`` and ``bank_labels``: the linguist's twelve groups, several
  per word;
- ``merge_map``: one entry per word now, and every id that was merged away
  points at the entry it went into;
- ``definition_truncated``: the preview was cut at 200 characters.
"""

from __future__ import annotations

import importlib.util
import sqlite3
import zipfile
from pathlib import Path
from types import ModuleType

import pytest

from murfulu.lexicon.overrides import Overrides
from murfulu.lexicon.store import Lexicon

from .conftest import FIELDS, SCHEMA

#: Rows as 1.3.2 ships them. آرش is two dictionary entries with one reading,
#: one filed نام and one کارنام — the collapsed reading must carry both. Row
#: 40 was merged into row 10, so a caller holding 40 must still find آب.
ROWS = [
    (10, "آب", "آب", "آب", "Āb", None, None, None, None, 1.0, 0, None, None,
     "اسم ذات", None, None),
    (20, "آرش", "آرش", "آرش", "Āreš", None, None, None, None, 1.0, 0, None, None,
     "اسم ذات", None, None),
    (30, "آرش", "آرش", "آرش", "Āreš", None, None, None, None, 1.0, 0, None, None,
     "اسم معنی", None, None),
    (50, "رفتن", "رفتن", "رفتن", "raftan", "رفت", "raft", "رو", "row", 1.0, 0, None,
     "intransitive", "مصدر", 1, None),
    (60, "آبجو", "آبجو", "آبجو", "ābjow", None, None, None, None, 1.0, 0, None, None,
     "وام‌واژه", None, None),
]  # fmt: skip

GROUPS = [
    (10, "نام"),
    (20, "نام"),
    (30, "کارنام"),
    (50, "نابسودکارواژه"),
    (60, "وام‌واژه"),
    (60, "کارنام"),
]

#: karbon's own order: the two stem names first, then the groups.
LABELS = [
    ("past_stem", "پیشین‌کاربن"),
    ("present_stem", "کنون‌کاربن"),
    ("نابسودکارواژه", "نابسودکارواژه"),
    ("نام", "نام"),
    ("کارنام", "کارنام"),
    ("وام‌واژه", "وام‌واژه"),
]

DEFINITIONS = {20: ("معنی. مقابل لفظ", 0), 30: ("اسم مصدر آردن", 1)}


def _bank(path: Path) -> Path:
    connection = sqlite3.connect(path)
    connection.execute(SCHEMA)
    connection.execute(
        "ALTER TABLE infinitives ADD COLUMN definition_truncated INTEGER"
    )
    connection.executemany(
        f"INSERT INTO infinitives ({FIELDS}) VALUES ({', '.join('?' * len(ROWS[0]))})",
        ROWS,
    )
    for row_id, (text, cut) in DEFINITIONS.items():
        connection.execute(
            "UPDATE infinitives SET definition_preview = ?, definition_truncated = ? "
            "WHERE id = ?",
            (text, cut, row_id),
        )
    connection.execute(
        "CREATE TABLE bank_group (word_id INTEGER, bank_group TEXT, "
        "PRIMARY KEY (word_id, bank_group))"
    )
    connection.executemany("INSERT INTO bank_group VALUES (?, ?)", GROUPS)
    connection.execute("CREATE TABLE bank_labels (key TEXT PRIMARY KEY, label_fa TEXT)")
    connection.executemany("INSERT INTO bank_labels VALUES (?, ?)", LABELS)
    connection.execute("CREATE TABLE merge_map (old_id, new_id, merged_at)")
    connection.execute("INSERT INTO merge_map VALUES (40, 10, '2026-11-11')")
    connection.commit()
    connection.close()
    return path


@pytest.fixture
def bank(tmp_path: Path) -> Path:
    return _bank(tmp_path / "lexicon-20261111.sqlite")


def test_a_reading_carries_every_group_of_every_collapsed_row(bank: Path) -> None:
    with Lexicon.open(bank, overrides=Overrides()) as lexicon:
        (aresh,) = lexicon.by_spelling("آرش")
    assert aresh.source_entry_ids == (20, 30)
    assert aresh.bank_groups == ("نام", "کارنام")


def test_groups_come_in_karbons_order_not_alphabetical(bank: Path) -> None:
    with Lexicon.open(bank, overrides=Overrides()) as lexicon:
        (beer,) = lexicon.by_spelling("آبجو")
    # By code point وام‌واژه (و) sorts before کارنام (ک); karbon lists
    # کارنام first, and karbon's order is the one shown.
    assert beer.bank_groups == ("کارنام", "وام‌واژه")
    with Lexicon.open(bank, overrides=Overrides()) as lexicon:
        assert list(lexicon.count_by_bank_group()) == [
            "نابسودکارواژه",
            "نام",
            "کارنام",
            "وام‌واژه",
        ]


def test_the_truncation_flag_is_the_shown_definitions(bank: Path) -> None:
    with Lexicon.open(bank, overrides=Overrides()) as lexicon:
        (aresh,) = lexicon.by_spelling("آرش")
        (water,) = lexicon.by_spelling("آب")
    # The reading shows row 20's definition, which was not cut; row 30's was.
    assert aresh.definition_fa == "معنی. مقابل لفظ"
    assert aresh.definition_truncated is False
    assert water.definition_truncated is None


def test_a_merged_id_still_finds_its_word(bank: Path) -> None:
    with Lexicon.open(bank, overrides=Overrides()) as lexicon:
        assert lexicon.current_id(10) == 10
        assert lexicon.current_id(40) == 10
        assert lexicon.current_id(99) is None
        assert [one.latin for one in lexicon.by_id(40)] == ["Āb"]
        assert lexicon.by_id(99) == []
        assert lexicon.merge_map() == {40: 10}


def test_the_labels_hold_the_stem_names(bank: Path) -> None:
    with Lexicon.open(bank, overrides=Overrides()) as lexicon:
        labels = lexicon.bank_labels()
    assert labels["past_stem"] == "پیشین‌کاربن"
    assert labels["present_stem"] == "کنون‌کاربن"


def test_a_snapshot_before_the_bank_opens_as_before(lexicon_snapshot: Path) -> None:
    with Lexicon.open(lexicon_snapshot, overrides=Overrides()) as lexicon:
        assert lexicon.has_bank is False
        assert lexicon.bank_labels() == {}
        assert lexicon.count_by_bank_group() == {}
        assert lexicon.merge_map() == {}
        assert lexicon.current_id(1) == 1
        assert lexicon.current_id(4040) is None
        (go,) = lexicon.by_spelling("رفتن")
    assert go.bank_groups == ()
    assert go.definition_truncated is None


def _fetch_tool() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "tools" / "fetch_lexicon.py"
    spec = importlib.util.spec_from_file_location("fetch_lexicon", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _wheel(tmp_path: Path, build_date: str) -> Path:
    source = tmp_path / f"in-{build_date}.sqlite"
    source.unlink(missing_ok=True)
    lexicon = _bank(source)
    connection = sqlite3.connect(lexicon)
    connection.execute("CREATE TABLE karbon_meta (key TEXT PRIMARY KEY, value TEXT)")
    connection.execute(
        "INSERT INTO karbon_meta VALUES ('build_date', ?)", (build_date,)
    )
    connection.commit()
    connection.close()
    wheel = tmp_path / f"karbon_nlp-{build_date}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.write(lexicon, "karbon/data/lexicon.sqlite")
    return wheel


def test_the_snapshot_is_named_after_karbons_build_date(tmp_path: Path) -> None:
    tool = _fetch_tool()
    target = tool.extract(_wheel(tmp_path, "2026-11-11"), tmp_path / "data")
    assert target.name == "lexicon-20261111.sqlite"
    # The same file again is accepted and left alone.
    assert tool.extract(_wheel(tmp_path, "2026-11-11"), tmp_path / "data") == target


def test_a_snapshot_name_is_never_reused_for_other_content(tmp_path: Path) -> None:
    tool = _fetch_tool()
    target = tool.extract(_wheel(tmp_path, "2026-11-11"), tmp_path / "data")
    target.write_bytes(target.read_bytes() + b"x")
    with pytest.raises(SystemExit, match="never reused"):
        tool.extract(_wheel(tmp_path, "2026-11-11"), tmp_path / "data")
