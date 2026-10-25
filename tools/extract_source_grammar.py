"""Transcribe the source grammar's tables into a raw JSON dump.

Run once, by hand, against the archived ``.docx``. It does no interpretation:
every cell is copied as written and the document's own row numbers are kept, so
any later rule can be traced back to the line that produced it.

    python tools/extract_source_grammar.py <path-to-docx> [-o rules/source_rows.json]

The document is not in the repository — it lives in the Google Drive archive
indexed in ``docs/SOURCES.md``. The dump it produces *is* committed, which is
what lets the rest of the build run without the archive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import docx

# Both rule tables and the glide table share one column order, right to left:
# row number, affix, what it attaches to, what it produces, examples.
RULE_COLUMNS = ["row", "affix", "attaches_to", "produces", "examples"]
GLIDE_COLUMNS = ["row", "left_vowel", "right_vowel", "result", "examples"]

# The document header cells, used to identify each table by content rather than
# by position, so a re-saved document does not silently shift the extraction.
HEADER_RULE = ("وند", "پیوند به", "برساخته", "نمونه")
HEADER_GLIDE = ("واکه", "پیوند به", "برساخته", "نمونه")

# What each table is expected to yield. A mismatch is an error, not a warning:
# a changed count means the document changed and the rule ids may no longer
# line up with their source rows.
EXPECTED_CONTENT_ROWS = {"glides": 17, "verb_stems": 81, "nominals": 105}


def _cells(row: Any) -> list[str]:
    return [c.text.strip() for c in row.cells]


def _is_blank(record: dict[str, str | None]) -> bool:
    return not any(v for k, v in record.items() if k != "row")


def _read_table(
    table: Any, columns: list[str], skip_header: bool
) -> list[dict[str, Any]]:
    """Copy one table verbatim, keeping the document's own row numbers."""
    records: list[dict[str, Any]] = []
    for position, row in enumerate(table.rows):
        if skip_header and position == 0:
            continue
        values = _cells(row)
        if len(values) != len(columns):
            raise ValueError(
                f"row {position} has {len(values)} cells, expected {len(columns)}"
            )
        record: dict[str, Any] = dict(zip(columns, values, strict=True))
        # An empty number cell is meaningful: the document leaves some rules
        # unnumbered. Recorded as null rather than invented.
        record["row"] = record["row"] or None
        record["docx_row_position"] = position
        record["blank"] = _is_blank({k: v for k, v in record.items() if k in columns})
        records.append(record)
    return records


def _find_table(document: Any, header: tuple[str, ...], row_count: int) -> Any:
    """Locate a table by its header cells and size, never by position alone."""
    matches = [
        t
        for t in document.tables
        if len(t.rows) == row_count and tuple(_cells(t.rows[0])[1:]) == header
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one table with header {header} and {row_count} rows, "
            f"found {len(matches)}"
        )
    return matches[0]


def extract(docx_path: Path) -> dict[str, Any]:
    """Read the three tables this project needs out of the source grammar."""
    document = docx.Document(str(docx_path))

    # The glide table numbers its own header row "1", so its numbers are offset
    # from its rules by one. Recorded as found; the ids are assigned elsewhere.
    glide_table = _find_table(document, HEADER_GLIDE, 18)
    verb_table = _find_table(document, HEADER_RULE, 83)
    nominal_table = _find_table(document, HEADER_RULE, 111)

    tables = {
        "glides": _read_table(glide_table, GLIDE_COLUMNS, skip_header=True),
        "verb_stems": _read_table(verb_table, RULE_COLUMNS, skip_header=True),
        "nominals": _read_table(nominal_table, RULE_COLUMNS, skip_header=True),
    }

    for name, records in tables.items():
        content = [r for r in records if not r["blank"]]
        expected = EXPECTED_CONTENT_ROWS[name]
        if len(content) != expected:
            raise ValueError(
                f"{name}: {len(content)} non-blank rows, expected {expected}"
            )

    return {
        "source_document": docx_path.name,
        "source_sha256": hashlib.sha256(docx_path.read_bytes()).hexdigest(),
        "note": (
            "Verbatim transcription. No interpretation, no rule ids. "
            "Blank rows are kept so the document's own numbering stays intact."
        ),
        "tables": tables,
    }


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path, help="path to the source grammar .docx")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("rules/source_rows.json"),
        help="where to write the dump (default: rules/source_rows.json)",
    )
    args = parser.parse_args(argv)

    dump = extract(args.docx)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(dump, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    for name, records in dump["tables"].items():
        content = sum(1 for r in records if not r["blank"])
        print(f"{name}: {len(records)} rows, {content} with content")
    print(f"written to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
