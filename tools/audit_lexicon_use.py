"""Every column karbon holds, against what Murfulu actually uses.

    python tools/audit_lexicon_use.py
    python tools/audit_lexicon_use.py --lexicon data/lexicon-20260808.sqlite

**Why this exists.** برنا is read `barnā` and the same lexicon row also says
`bornā`. The reading carried it, the API sent it, the TypeScript type declared
it, and no screen drew it — so a reader who heard *bornā* had no way to tell
whether we knew it. The fault was not that the data was missing. It was that
nobody had ever listed what karbon holds beside what we consume.

This does that listing, and it is meant to be **re-run against every new
snapshot**, because a column added upstream is silently unused by default.

Three questions per column, answered from the code rather than from memory:

``read``    does :mod:`murfulu.lexicon.store` select it
``carried`` does it land on a :class:`~murfulu.lexicon.entries.Reading` field
``fill``    how many active rows actually have a value

A column that is full and unread is the interesting row. The tool does not say
what to do about one — that is a decision about what the app should show, and
some of these carry a person's name or raw dictionary prose.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from murfulu.lexicon.snapshot import open_snapshot
from murfulu.lexicon.store import _COLUMNS, NOT_SHIPPED_SINCE_1_2_0

#: Column → the ``Reading`` field it lands on. A column can be read by the
#: query and still be dropped before anything downstream can see it, which is
#: the failure this tool exists to make visible.
CARRIED: dict[str, str] = {
    "headword": "spelling_fa",
    "headword_normalized": "spelling_normalized",
    "phonemic": "latin",
    "phonemic_variants": "latin_variants",
    "pos": "lexicon_categories",
    "past_stem_fa": "past_stem_fa",
    "past_stem_lat": "past_stem_latin",
    "present_stem_fa": "present_stem_fa",
    "present_stem_lat": "present_stem_latin",
    "transitivity": "transitivity",
    "confidence": "phonemic_confidence",
    "needs_review": "needs_review",
    "stem_rule": "karbon_stem_rule",
    "definition_preview": "definition_fa",
    "id": "source_entry_ids",
    "deleted_at": "— filtered on, never carried",
}


@dataclass
class Column:
    """One column of the snapshot, and how far into the app it gets."""

    name: str
    type: str
    filled: int
    distinct: int
    example: str
    read: bool
    carried: str | None

    @property
    def unused(self) -> bool:
        """Held by karbon and reaching nothing of ours."""
        return not self.read and not self.carried

    def share(self, total: int) -> float:
        """How many active rows have a value, as a percentage."""
        return 100 * self.filled / total if total else 0.0

    def as_row(self, total: int) -> dict[str, object]:
        """The column as it is written out."""
        return {
            "column": self.name,
            "filled": self.filled,
            "share": round(self.share(total), 1),
            "distinct": self.distinct,
            "read": self.read,
            "carried_as": self.carried,
            "unused": self.unused,
        }


def _selected() -> set[str]:
    """The columns `Lexicon` asks SQLite for, parsed from the query itself."""
    return {part.strip() for part in _COLUMNS.replace("\n", " ").split(",")}


def audit(path: Path) -> tuple[list[Column], int]:
    """Read the snapshot's schema and measure how full each column is."""
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        total = connection.execute(
            "SELECT count(*) FROM infinitives WHERE deleted_at IS NULL"
        ).fetchone()[0]
        selected = _selected()
        columns = []
        for row in connection.execute("PRAGMA table_info(infinitives)").fetchall():
            name, type_name = row[1], row[2]
            filled, distinct, example = _measure(connection, name)
            columns.append(
                Column(
                    name=name,
                    type=type_name,
                    filled=filled,
                    distinct=distinct,
                    example=example,
                    read=name in selected,
                    carried=CARRIED.get(name),
                )
            )
        return columns, total
    finally:
        connection.close()


def _measure(connection: sqlite3.Connection, name: str) -> tuple[int, int, str]:
    """How many active rows have a value, how many values, and one of them."""
    active = 'deleted_at IS NULL AND "{0}" IS NOT NULL AND "{0}" != \'\''
    where = active.format(name)
    filled = connection.execute(
        f"SELECT count(*) FROM infinitives WHERE {where}"
    ).fetchone()[0]
    distinct = connection.execute(
        f'SELECT count(DISTINCT "{name}") FROM infinitives WHERE {where}'
    ).fetchone()[0]
    found = connection.execute(
        f'SELECT "{name}" FROM infinitives WHERE {where} LIMIT 1'
    ).fetchone()
    example = str(found[0]).replace("\n", " ")[:40] if found else ""
    return filled, distinct, example


def _report(columns: list[Column], total: int) -> None:
    """Print the whole schema, unused and fullest first."""
    print(f"{total:,} active rows, {len(columns)} columns\n")
    unused = sorted((one for one in columns if one.unused), key=lambda one: -one.filled)
    used = [one for one in columns if not one.unused]

    print(f"UNUSED — karbon holds it and nothing of ours reads it ({len(unused)})\n")
    print(f"  {'column':26} {'filled':>9} {'share':>7} {'values':>8}  example")
    for one in unused:
        print(
            f"  {one.name:26} {one.filled:>9,} {one.share(total):>6.1f}% "
            f"{one.distinct:>8,}  {one.example}"
        )

    print(f"\nUSED ({len(used)})\n")
    print(f"  {'column':26} {'filled':>9} {'share':>7}  reading field")
    for one in used:
        # A column can be selected by the query and still land nowhere. That
        # is the shape of the برنا fault and it should be visible here.
        carried = one.carried or "read, then dropped"
        print(f"  {one.name:26} {one.filled:>9,} {one.share(total):>6.1f}%  {carried}")

    # Columns an earlier release shipped and this one does not: nothing here
    # reads them, but a reader comparing two audits should not have to wonder.
    present = {one.name for one in columns}
    gone = [name for name in NOT_SHIPPED_SINCE_1_2_0 if name not in present]
    if gone:
        print(
            f"\nGONE — shipped before karbon 1.2.0, not in this one: {', '.join(gone)}"
        )


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lexicon", type=Path, help="a snapshot other than default")
    parser.add_argument("--out", type=Path, help="where to write the audit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Audit one snapshot against the code that reads it."""
    arguments = _parse(argv)
    snapshot = open_snapshot(arguments.lexicon)
    print(f"snapshot {snapshot.snapshot_id}\n")
    columns, total = audit(snapshot.path)
    _report(columns, total)

    if arguments.out:
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(
            json.dumps(
                {
                    "lexicon_snapshot_id": snapshot.snapshot_id,
                    "active_rows": total,
                    "columns": [one.as_row(total) for one in columns],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        print(f"\nwritten to {arguments.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
