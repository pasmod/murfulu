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
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

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


def build_register(
    dump: dict[str, Any], stem_dump: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build the full id register from the raw transcriptions."""
    families: dict[str, list[dict[str, Any]]] = {}
    for table in FAMILIES:
        families[table] = _assign(table, dump["tables"][table])
    if stem_dump is not None:
        families["stem_rules"] = _assign_stem_rules(stem_dump)

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
        "-o", "--output", type=Path, default=Path("rules/rule_ids.json")
    )
    args = parser.parse_args(argv)

    dump = json.loads(args.input.read_text(encoding="utf-8"))
    stem_dump = (
        json.loads(args.stems.read_text(encoding="utf-8"))
        if args.stems.exists()
        else None
    )
    register = build_register(dump, stem_dump)

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
