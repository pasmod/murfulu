"""The committed transcription of the linguist's corrected rules of 2026-11-19.

These tests run against ``rules/affix_source_rows.json``, never against the
.docx, which is not in the repository.
"""

import json
from pathlib import Path

import pytest

DUMP = json.loads(
    (
        Path(__file__).resolve().parents[1] / "rules" / "affix_source_rows.json"
    ).read_text(encoding="utf-8")
)

#: The three tables and the linguist's running numbers in each.
EXPECTED = {"prefixes": (1, 64), "suffixes": (65, 211), "no_affix": (212, 229)}


@pytest.mark.parametrize(("table", "span"), EXPECTED.items())
def test_content_row_counts(table: str, span: tuple[int, int]):
    rows = [r for r in DUMP["tables"][table] if not r["blank"]]
    assert len(rows) == span[1] - span[0] + 1


def test_the_source_document_is_identified():
    assert DUMP["source_document"] == "Dasturhāyeé Vāžesāzi.docx"
    assert len(DUMP["source_sha256"]) == 64
    assert DUMP["received"] == "2026-11-19"


@pytest.mark.parametrize("table", EXPECTED)
def test_document_row_positions_are_complete_and_ordered(table: str):
    positions = [r["docx_row_position"] for r in DUMP["tables"][table]]
    assert positions == list(range(1, len(positions) + 1))


def test_the_running_number_is_kept_as_written():
    """1–229 across the three tables, with the one slip left in place.

    The prefix table's 48th row is numbered 46 a second time. The dump keeps
    the linguist's number; the row map tells the two 46s apart by position.
    """
    numbers = [
        r["row"] for table in EXPECTED for r in DUMP["tables"][table] if not r["blank"]
    ]
    assert numbers.count("46") == 2
    assert "48" not in numbers
    expected = [str(n) for n in range(1, 230)]
    expected[47] = "46"
    assert numbers == expected


@pytest.mark.parametrize(("table", "span"), EXPECTED.items())
def test_each_table_holds_its_own_number_range(table: str, span: tuple[int, int]):
    numbers = [int(r["row"]) for r in DUMP["tables"][table] if not r["blank"]]
    assert min(numbers) == span[0]
    assert max(numbers) == span[1]


def test_no_cell_was_interpreted():
    """The dump is a transcription: no rule ids, no parsed fields."""
    columns = {"examples", "produces", "attaches_to", "affix", "row"}
    for records in DUMP["tables"].values():
        for record in records:
            assert set(record) == columns | {"docx_row_position", "blank"}


def test_an_empty_cell_stays_empty():
    """Row 99 («-van (Mānandi)») names no base. Recorded as found."""
    row = next(r for r in DUMP["tables"]["suffixes"] if r["row"] == "99")
    assert row["attaches_to"] == ""
