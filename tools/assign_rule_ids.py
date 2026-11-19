"""Assign the permanent rule ids and write the id register.

Reads the raw transcription (``rules/source_rows.json``) and produces
``rules/rule_ids.json``: one id per source row, and the reason for every id
that is reserved rather than used.

The scheme is defined in ``docs/RULE_PACK.md`` and its three unbreakable rules
apply here — an id is permanent, new ids are appended never inserted, and
nothing is ever deleted or reused. This tool is therefore **not** rerun to
renumber. It exists so the register can be regenerated and checked, and it
fails if it would ever produce a different answer for an existing row.

    python tools/assign_rule_ids.py [-i rules/source_rows.json] [-o rules/rule_ids.json]

**The 2026-11-19 rules document** (``rules/affix_source_rows.json``) replaced
the August grammar's two rule tables. Which of its rows is which existing rule
is a judgement, authored in ``rules/affix_rows.yaml``; this tool checks that
judgement against both transcriptions and writes its consequences into the
register: the new ids, appended to their family with the new row as their
source, and the August ids that no row carries any more, marked retired. The
August entries themselves never change — an id keeps the row it was issued
for — so ``source`` always says where an id came from and the pack's own
``source`` says where its rule is written today.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

# Family prefix and id width per source table. The number in a V or N id is the
# document's own row number — see the worked examples in docs/RULE_PACK.md,
# where V-010, V-017 and V-053 are verb-table rows 10, 17 and 53.
FAMILIES = {"verb_stems": ("V", 3), "nominals": ("N", 3), "glides": ("G", 2)}

#: The stem rules come from a second document and are numbered 1–9 there, so
#: S-01 … S-09 mirror those numbers the same way V and N mirror theirs. The
#: document's two sub-rules (4-1 and 4-2) are parts of rule 4, not rules of
#: their own — it says stem 2 divides into "eight groups", meaning rules 2–9.
#: Exceptions are data attached to a rule, addressed as ``S-09/raftan``.
STEM_FAMILY = ("S", 2)


def _assign(table: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prefix, width = FAMILIES[table]
    assigned: list[dict[str, Any]] = []
    unnumbered: list[dict[str, Any]] = []
    reserved: list[dict[str, Any]] = []
    highest = 0

    for record in records:
        position = record["docx_row_position"]
        if record["blank"] and record["row"] is None:
            # A blank, unnumbered row is padding at the end of the table. It is
            # not a rule and there is no source number to reserve against it.
            continue
        if table == "glides":
            # The glide table numbers its own header row "1", so its numbers are
            # offset by one from its rules and cannot be mirrored. Ids follow
            # document order instead, which is the only assignment that yields
            # the G-01 … G-17 range docs/RULE_PACK.md states.
            number = len(assigned) + 1
        elif record["row"] is None:
            # The document forgot to number this row. Appended at the end of the
            # family, never inserted beside the row it sits next to.
            unnumbered.append(record)
            continue
        else:
            number = int(record["row"])

        if record["blank"]:
            reserved.append(
                {
                    "id": f"{prefix}-{number:0{width}d}",
                    "source": {"table": table, "row": record["row"]},
                    "reason": (
                        "the source row is empty; the id is reserved, never reused"
                    ),
                }
            )
            highest = max(highest, number)
            continue

        assigned.append(
            {
                "id": f"{prefix}-{number:0{width}d}",
                "source": {"table": table, "row": record["row"]},
                "docx_row_position": position,
            }
        )
        highest = max(highest, number)

    for record in unnumbered:
        highest += 1
        assigned.append(
            {
                "id": f"{prefix}-{highest:0{width}d}",
                "source": {
                    "table": table,
                    "row": None,
                    "follows_row": _preceding_row(records, record),
                },
                "docx_row_position": record["docx_row_position"],
                "note": "unnumbered in the source document; appended to the family",
            }
        )

    return assigned + reserved


def _preceding_row(records: list[dict[str, Any]], target: dict[str, Any]) -> str | None:
    previous: str | None = None
    for record in records:
        if record is target:
            return previous
        if record["row"]:
            previous = record["row"]
    return previous


def _assign_stem_rules(dump: dict[str, Any]) -> list[dict[str, Any]]:
    """One id per stem rule; sub-rules and exceptions attach to their rule."""
    prefix, width = STEM_FAMILY
    sub_rules: dict[int, list[str]] = {}
    for sub in dump["sub_rules"]:
        sub_rules.setdefault(sub["parent_rule"], []).append(
            f"{sub['parent_rule']}-{sub['part']}"
        )

    entries: list[dict[str, Any]] = []
    for rule in dump["rules"]:
        number = rule["rule"]
        attached = [e for e in dump["exceptions"] if e["rule"] == number]
        entries.append(
            {
                "id": f"{prefix}-{number:0{width}d}",
                "source": {"table": "stem_rules", "row": str(number)},
                "sub_rules": sorted(sub_rules.get(number, [])),
                "exception_count": len(attached),
                "exceptions_needing_check": [
                    e["infinitive_fa"] for e in attached if e.get("needs_expert_check")
                ],
            }
        )
    return entries


#: Which register family a V or N id belongs to.
FAMILY_TABLE = {"V": "verb_stems", "N": "nominals"}

#: Written into a new id's ``source`` so it can never be read as an August row.
AFFIX_DOCUMENT = "2026-11-19"

_ID = re.compile(r"^([VN])-(\d{3})$")


def affix_row_positions(
    affix_dump: dict[str, Any], row_map: dict[str, Any]
) -> list[dict[str, Any]]:
    """Every mapped row of the 2026-11-19 document, with its place in the table.

    Each content row must be mapped exactly once. A row is found by its number;
    where the document writes a number twice, ``position`` says which.
    """
    resolved: list[dict[str, Any]] = []
    for table, entries in row_map["rows"].items():
        records = [r for r in affix_dump["tables"][table] if not r["blank"]]
        for entry in entries:
            matches = [
                r
                for r in records
                if r["row"] == entry["row"]
                and entry.get("position", r["docx_row_position"])
                == r["docx_row_position"]
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"{table} row {entry['row']}: {len(matches)} rows match; "
                    "give its position"
                )
            resolved.append(
                {**entry, "table": table, "position": matches[0]["docx_row_position"]}
            )
        mapped = sorted(e["position"] for e in resolved if e["table"] == table)
        content = sorted(r["docx_row_position"] for r in records)
        if mapped != content:
            raise ValueError(f"{table}: not every row is mapped exactly once")
    return resolved


def apply_affix_rows(
    families: dict[str, list[dict[str, Any]]],
    affix_dump: dict[str, Any],
    row_map: dict[str, Any],
) -> None:
    """Append the new ids and mark the retired ones, checking every judgement."""
    rows = affix_row_positions(affix_dump, row_map)
    known = {
        e["id"]: e
        for table in FAMILY_TABLE.values()
        for e in families[table]
        if "reason" not in e
    }
    mapped = [r for r in rows if "id" in r]
    ids = [r["id"] for r in mapped]
    twice = sorted({i for i in ids if ids.count(i) > 1})
    if twice:
        raise ValueError(f"ids given to two rows: {twice}")

    for row in rows:
        if "same_as" in row and not any(
            r["table"] == row["table"] and r["row"] == row["same_as"] and "id" in r
            for r in rows
        ):
            raise ValueError(f"row {row['row']} repeats {row['same_as']}, unmapped")

    retired = {r["id"]: r for r in row_map.get("retired") or []}
    for rule_id in retired:
        if rule_id not in known:
            raise ValueError(f"{rule_id} is retired but was never issued")
        if rule_id in ids:
            raise ValueError(f"{rule_id} is retired and also given a row")
    unaccounted = sorted(set(known) - set(ids) - set(retired))
    if unaccounted:
        raise ValueError(f"neither given a row nor retired: {unaccounted}")

    for row in mapped:
        match = _ID.match(row["id"])
        if match is None:
            raise ValueError(f"{row['id']} is not a V or N id")
        if row.get("new"):
            if row["id"] in known:
                raise ValueError(f"{row['id']} is marked new but already issued")
            continue
        if row["id"] not in known:
            raise ValueError(f"{row['id']} is not an issued id; mark it new")
        known[row["id"]]["current_source"] = {
            "document": AFFIX_DOCUMENT,
            "table": row["table"],
            "row": row["row"],
            "docx_row_position": row["position"],
        }

    # New ids are appended to their family, in the order the document gives
    # them, with no gap and nothing inserted.
    for prefix, table in FAMILY_TABLE.items():
        highest = max(int(e["id"].split("-")[1]) for e in families[table])
        for row in (r for r in mapped if r.get("new") and r["id"][0] == prefix):
            highest += 1
            if row["id"] != f"{prefix}-{highest:03d}":
                raise ValueError(
                    f"{row['id']} is out of order: the next {prefix} id is "
                    f"{prefix}-{highest:03d}"
                )
            families[table].append(
                {
                    "id": row["id"],
                    "source": {
                        "document": AFFIX_DOCUMENT,
                        "table": row["table"],
                        "row": row["row"],
                    },
                    "docx_row_position": row["position"],
                }
            )

    for rule_id in retired:
        known[rule_id]["retired_on"] = AFFIX_DOCUMENT


def build_register(
    dump: dict[str, Any],
    stem_dump: dict[str, Any] | None = None,
    affix_dump: dict[str, Any] | None = None,
    row_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the full id register from the raw transcriptions."""
    families: dict[str, list[dict[str, Any]]] = {}
    for table in FAMILIES:
        families[table] = _assign(table, dump["tables"][table])
    if stem_dump is not None:
        families["stem_rules"] = _assign_stem_rules(stem_dump)
    if affix_dump is not None and row_map is not None:
        apply_affix_rows(families, affix_dump, row_map)

    ids = [entry["id"] for entries in families.values() for entry in entries]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"duplicate ids: {duplicates}")

    return {
        "scheme": "FAMILY-NNN, defined in docs/RULE_PACK.md",
        "source_document": dump["source_document"],
        "source_sha256": dump["source_sha256"],
        "stem_source_document": (stem_dump["source_document"] if stem_dump else None),
        "stem_source_sha256": stem_dump["source_sha256"] if stem_dump else None,
        "affix_source_document": (
            affix_dump["source_document"] if affix_dump else None
        ),
        "affix_source_sha256": affix_dump["source_sha256"] if affix_dump else None,
        "families": families,
        "retired_families": {
            "D": (
                "Dropped 2026-08-11. RULE_PACK.md planned a denominal-verb "
                "family of four rules. No such group exists: the whole Drive "
                "archive and the earlier prototype were searched, and the "
                "concept document names exactly two such rules, which are "
                "verb-table rows 3 and 4. They are V-003 and V-004, tagged "
                "makes_verb_from_nominal. No D id was ever issued."
            )
        },
    }


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-i", "--input", type=Path, default=Path("rules/source_rows.json")
    )
    parser.add_argument(
        "-s", "--stems", type=Path, default=Path("rules/stem_source_rows.json")
    )
    parser.add_argument(
        "-a", "--affixes", type=Path, default=Path("rules/affix_source_rows.json")
    )
    parser.add_argument(
        "-m", "--row-map", type=Path, default=Path("rules/affix_rows.yaml")
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("rules/rule_ids.json")
    )
    args = parser.parse_args(argv)

    dump = json.loads(args.input.read_text(encoding="utf-8"))
    stem_dump = (
        json.loads(args.stems.read_text(encoding="utf-8"))
        if args.stems.exists()
        else None
    )
    affix_dump = (
        json.loads(args.affixes.read_text(encoding="utf-8"))
        if args.affixes.exists()
        else None
    )
    row_map = (
        yaml.safe_load(args.row_map.read_text(encoding="utf-8"))
        if args.row_map.exists()
        else None
    )
    register = build_register(dump, stem_dump, affix_dump, row_map)

    if args.output.exists():
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        _check_ids_did_not_move(existing, register)

    args.output.write_text(
        json.dumps(register, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    for family, entries in register["families"].items():
        print(f"{family}: {len(entries)} ids")
    print(f"written to {args.output}")
    return 0


def _check_ids_did_not_move(existing: dict[str, Any], fresh: dict[str, Any]) -> None:
    """Refuse to write a register that moves an existing id to another row."""
    for table, entries in existing.get("families", {}).items():
        was = {e["id"]: e["source"] for e in entries}
        now = {e["id"]: e["source"] for e in fresh["families"].get(table, [])}
        moved = [i for i, source in was.items() if i in now and now[i] != source]
        if moved:
            raise ValueError(f"these ids would change meaning: {moved}")


if __name__ == "__main__":
    sys.exit(main())
