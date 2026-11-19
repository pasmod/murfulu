"""Transcribe the linguist's affix tables of 2026-11-19 into a raw JSON dump.

The corrected word-formation rules arrived as a new document on 2026-11-19
(``Dasturhāyeé Vāžesāzi.docx``). It replaces the August grammar's two rule
tables — and only those: it has no glide table, no stem rules and no theory,
which keep their own sources (``rules/source_rows.json`` for the glides,
``rules/stem_source_rows.json`` for the stems). Its rows are ordered by affix,
not by input, so verb-stem and nominal rules are mixed in one table.

Three tables, each under a heading of its own:

* ``prefixes`` — *Vāžesāzi bā Pišvand*, rows 1–64;
* ``suffixes`` — *Vāžesāzi bā Pasvand*, rows 65–211;
* ``no_affix`` — *Vāžesāzi bi Vand*, rows 212–229: compounding and the zero
  affix.

Columns, left to right as Word stores them: example · result class
(*Barsāxte*) · what it attaches to (*Afzudan be*) · affix · the linguist's
running number. Like ``tools/extract_source_grammar.py`` this does **no
interpretation**: every cell is copied as written, the linguist's number is
kept as the row id exactly as he wrote it (one row is numbered 46 a second
time, and nothing here corrects that), and blank cells stay blank.

    python tools/extract_affix_tables.py <docx> [-o rules/affix_source_rows.json]

The document is not in the repository. The dump it produces *is* committed,
which is what lets the rest of the build run without the document.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import docx

#: Left to right, as python-docx returns the cells of this document.
COLUMNS = ["examples", "produces", "attaches_to", "affix", "row"]

#: Each table is found by its header cells, never by position, so a re-saved
#: document cannot silently shift the extraction. The last cell (the number
#: column) has no header in any of the three.
HEADERS = {
    "prefixes": ("Nemune", "Barsāxte", "Afzudan be", "Pišvand", ""),
    "suffixes": ("Nemune", "Barsāxte", "Afzudan be", "Pasvand", ""),
    "no_affix": ("Nemune", "Barsāxte", "Afzudan be", "", ""),
}

#: The heading paragraph that stands above each table, verbatim.
HEADINGS = {
    "prefixes": "Vāžesāzi bā Pišvand",
    "suffixes": "Vāžesāzi bā Pasvand",
    "no_affix": "Vāžesāzi bi Vand",
}

#: What each table yields. A mismatch is an error, not a warning: a changed
#: count means the document changed and the row map no longer lines up.
EXPECTED_CONTENT_ROWS = {"prefixes": 64, "suffixes": 147, "no_affix": 18}


def _cells(row: Any) -> list[str]:
    return [cell.text.strip() for cell in row.cells]


def _find_table(document: Any, name: str) -> Any:
    header = HEADERS[name]
    matches = [t for t in document.tables if tuple(_cells(t.rows[0])) == header]
    if len(matches) != 1:
        raise ValueError(
            f"{name}: expected exactly one table with header {header}, "
            f"found {len(matches)}"
        )
    return matches[0]


def _read_table(table: Any) -> list[dict[str, Any]]:
    """Copy one table verbatim, header row skipped, the linguist's number kept."""
    records: list[dict[str, Any]] = []
    for position, row in enumerate(table.rows):
        if position == 0:
            continue
        values = _cells(row)
        if len(values) != len(COLUMNS):
            raise ValueError(
                f"row {position} has {len(values)} cells, expected {len(COLUMNS)}"
            )
        record: dict[str, Any] = dict(zip(COLUMNS, values, strict=True))
        record["row"] = record["row"] or None
        record["docx_row_position"] = position
        record["blank"] = not any(
            record[column] for column in COLUMNS if column != "row"
        )
        records.append(record)
    return records


def extract(docx_path: Path) -> dict[str, Any]:
    """Read the three tables of the 2026-11-19 rules document."""
    document = docx.Document(str(docx_path))
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    missing = [h for h in HEADINGS.values() if h not in paragraphs]
    if missing:
        raise ValueError(f"headings not found: {missing}")

    tables = {name: _read_table(_find_table(document, name)) for name in HEADERS}
    for name, records in tables.items():
        content = [r for r in records if not r["blank"]]
        if len(content) != EXPECTED_CONTENT_ROWS[name]:
            raise ValueError(
                f"{name}: {len(content)} non-blank rows, "
                f"expected {EXPECTED_CONTENT_ROWS[name]}"
            )

    return {
        "source_document": docx_path.name,
        "source_sha256": hashlib.sha256(docx_path.read_bytes()).hexdigest(),
        "received": "2026-11-19",
        "note": (
            "Verbatim transcription of the linguist's corrected affix tables. "
            "No interpretation, no rule ids. The row is the linguist's own "
            "running number, as written."
        ),
        "headings": HEADINGS,
        "tables": tables,
    }


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path, help="path to the 2026-11-19 .docx")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("rules/affix_source_rows.json"),
        help="where to write the dump (default: rules/affix_source_rows.json)",
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
