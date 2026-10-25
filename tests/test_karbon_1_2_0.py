"""Reading karbon 1.2.0's lexicon (``lexicon-20261012``).

Three things moved between karbon's 1.1.0 state and its 1.2.0 release, and
each of them could change what murfulu builds without saying so:

- ``rules/lexicon_overrides.yaml`` applied to one named snapshot, so the
  آزردن / گسیختن / رُفتن overrides would have **dropped silently** on the move;
- ``notes`` and ``file_path`` are no longer shipped;
- ``phonemic_variants`` now repeats the main reading for adjectives,
  ``[main] + alternatives``.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path

import pytest

from murfulu.lexicon import overrides
from murfulu.lexicon.store import (
    NOT_SHIPPED_SINCE_1_2_0,
    REQUIRED_COLUMNS,
    Lexicon,
    SnapshotSchemaError,
)

from .conftest import FIELDS, ROWS, SCHEMA

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules"


def _without(schema: str, *columns: str) -> str:
    """The fixture schema with some columns taken out."""
    for column in columns:
        schema = re.sub(rf"\s*\b{column}\b [A-Z]+( DEFAULT '[^']*')?,", "", schema)
    return schema


def _write(path: Path, schema: str, rows: list[tuple[object, ...]]) -> Path:
    connection = sqlite3.connect(path)
    connection.execute(schema)
    placeholders = ", ".join("?" * len(rows[0]))
    connection.executemany(
        f"INSERT INTO infinitives ({FIELDS}) VALUES ({placeholders})", rows
    )
    connection.commit()
    connection.close()
    return path


#: An adjective as 1.2.0 ships it: the main reading listed first, then the
#: alternative.
ADJECTIVE = (
    90,
    "برنا",
    "برنا",
    "برنا",
    "barnā",
    None,
    None,
    None,
    None,
    1.0,
    0,
    None,
    None,
    "صفت",
    None,
    '["barnā", "bornā"]',
)


@pytest.fixture
def release_1_2_0(tmp_path: Path) -> Path:
    """A snapshot with 1.2.0's columns: no ``notes``, no ``file_path``."""
    schema = _without(SCHEMA, *NOT_SHIPPED_SINCE_1_2_0)
    assert "notes" not in schema and "file_path" not in schema
    return _write(tmp_path / "lexicon-20261012.sqlite", schema, [*ROWS, ADJECTIVE])


# -- notes and file_path -------------------------------------------------------


def test_nothing_murfulu_reads_was_dropped_in_1_2_0():
    """`notes` and `file_path` are gone, and neither is read here."""
    assert not set(NOT_SHIPPED_SINCE_1_2_0) & REQUIRED_COLUMNS


def test_a_1_2_0_snapshot_opens_and_reads(release_1_2_0: Path):
    with Lexicon.open(release_1_2_0, overrides.Overrides()) as lexicon:
        (verb,) = lexicon.by_spelling("رفتن")
    assert verb.present_stem_latin == "row"


def test_a_snapshot_without_a_column_we_read_is_refused_by_name(tmp_path: Path):
    """Better at open, naming the column, than a 500 on the first query."""
    schema = _without(SCHEMA, "definition_preview")
    path = _write(tmp_path / "lexicon-broken.sqlite", schema, ROWS)
    with pytest.raises(SnapshotSchemaError, match="definition_preview"):
        Lexicon.open(path, overrides.Overrides())


# -- phonemic_variants as [main] + alternatives --------------------------------


def test_the_main_reading_repeated_in_the_variants_is_not_a_variant(
    release_1_2_0: Path,
):
    with Lexicon.open(release_1_2_0, overrides.Overrides()) as lexicon:
        (adjective,) = lexicon.by_spelling("برنا")
    assert adjective.latin_variants == ("bornā",)
    assert adjective.all_latin == ("barnā", "bornā")


def test_the_main_reading_is_found_once_not_twice(release_1_2_0: Path):
    """The variant column now matches the main reading too; one hit, not two."""
    with Lexicon.open(release_1_2_0, overrides.Overrides()) as lexicon:
        assert len(lexicon.by_latin("barnā")) == 1
        assert len(lexicon.by_latin("bornā")) == 1


# -- the overrides follow the snapshot, or say they did not --------------------


def test_the_authored_table_was_checked_on_both_snapshots():
    held = overrides.load(RULES)
    assert held.applies_to("lexicon-20260808:45e05ff66c37")
    assert held.applies_to("lexicon-20261012:0123456789ab")


def test_a_name_is_matched_whole_never_by_prefix():
    held = overrides.Overrides(lexicon_snapshots=("lexicon-2026101",))
    assert not held.applies_to("lexicon-20261012:0123456789ab")


def test_the_first_versions_single_snapshot_is_still_read(tmp_path: Path):
    (tmp_path / overrides.OVERRIDES_FILE).write_text(
        "lexicon_snapshot: lexicon-20260808\n", encoding="utf-8"
    )
    assert overrides.load(tmp_path).lexicon_snapshots == ("lexicon-20260808",)


def test_a_table_that_names_no_snapshot_is_refused(tmp_path: Path):
    (tmp_path / overrides.OVERRIDES_FILE).write_text(
        "corrections: []\n", encoding="utf-8"
    )
    with pytest.raises(overrides.OverrideError):
        overrides.load(tmp_path)


def test_overrides_not_checked_on_this_snapshot_are_reported(
    release_1_2_0: Path, caplog: pytest.LogCaptureFixture
):
    """The failure this file exists for: a move that drops them in silence."""
    stale = overrides.Overrides(
        lexicon_snapshots=("lexicon-19990101",),
        corrections=overrides.load(RULES).corrections,
    )
    with (
        caplog.at_level(logging.WARNING, logger="murfulu.lexicon.store"),
        Lexicon.open(release_1_2_0, stale) as lexicon,
    ):
        assert lexicon.overrides_dropped == len(stale)
        assert lexicon.overrides_applied == 0
        assert lexicon.describe_overrides().startswith("NOT APPLIED")
    assert "NOT applied" in caplog.text


def test_overrides_checked_on_this_snapshot_are_applied(release_1_2_0: Path):
    held = overrides.Overrides(
        lexicon_snapshots=("lexicon-20261012",),
        additions=overrides.load(RULES).additions,
    )
    with Lexicon.open(release_1_2_0, held) as lexicon:
        assert lexicon.overrides_dropped == 0
        latin = {one.latin for one in lexicon.by_spelling("رفتن")}
    assert latin == {"raftan", "roftan"}


@pytest.mark.parametrize(
    "configuration", [ROOT / "deploy" / "server.env.example", ROOT / ".env.example"]
)
def test_the_configured_snapshot_is_one_the_overrides_were_checked_on(
    configuration: Path,
):
    """Moving the configured lexicon without re-checking the table fails here.

    Production reads the lexicon named in `deploy/server.env.example`
    (`deploy/server.sh data` copies exactly that file), so pointing it at a
    new snapshot before the overrides were re-read on it is caught in CI and
    not on the live site.
    """
    text = configuration.read_text(encoding="utf-8")
    found = re.search(r"^MURFULU_LEXICON_PATH=.*/([^/\s]+)\.sqlite$", text, re.M)
    assert found, f"no MURFULU_LEXICON_PATH in {configuration.name}"
    assert overrides.load(RULES).applies_to(found.group(1))
