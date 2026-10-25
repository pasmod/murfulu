"""The committed transcription of the source grammar.

These tests run against ``rules/source_rows.json``, never against the .docx —
the document lives in the Drive archive and is not in the repository.
"""

import json
from pathlib import Path

import pytest

DUMP = json.loads(
    (Path(__file__).resolve().parents[1] / "rules" / "source_rows.json").read_text(
        encoding="utf-8"
    )
)

# What the build plan says the source grammar contains.
EXPECTED_CONTENT_ROWS = {"glides": 17, "verb_stems": 81, "nominals": 105}


@pytest.mark.parametrize(("table", "expected"), EXPECTED_CONTENT_ROWS.items())
def test_content_row_counts(table: str, expected: int):
    rows = [r for r in DUMP["tables"][table] if not r["blank"]]
    assert len(rows) == expected


def test_the_source_document_is_identified():
    assert DUMP["source_document"].endswith(".docx")
    assert len(DUMP["source_sha256"]) == 64


@pytest.mark.parametrize("table", EXPECTED_CONTENT_ROWS)
def test_document_row_positions_are_complete_and_ordered(table: str):
    positions = [r["docx_row_position"] for r in DUMP["tables"][table]]
    assert positions == list(range(1, len(positions) + 1))


@pytest.mark.parametrize("table", ["verb_stems", "nominals"])
def test_source_numbering_runs_without_gaps(table: str):
    """The document numbers its own rows. Nothing may be missing from the middle."""
    numbers = [int(r["row"]) for r in DUMP["tables"][table] if r["row"]]
    assert numbers == list(range(1, len(numbers) + 1))


def test_unnumbered_rows_are_recorded_as_such():
    """Both rule tables carry exactly one rule the document forgot to number."""
    for table in ("verb_stems", "nominals"):
        unnumbered = [
            r for r in DUMP["tables"][table] if r["row"] is None and not r["blank"]
        ]
        assert len(unnumbered) == 1, table


def test_no_cell_was_interpreted():
    """The dump is a transcription: no rule ids, no parsed fields."""
    for records in DUMP["tables"].values():
        for record in records:
            assert "id" not in record
