"""Transcribe the stem rules and their exception lists into a raw JSON dump.

The source is a second document — the stem-rules file indexed in
``docs/SOURCES.md`` — not the word-formation grammar. It states nine rules for
getting from an infinitive to its two stems, plus exception lists for rules
2 to 9.

Like ``extract_source_grammar.py``, this copies and does not interpret. A row
that cannot be read cleanly is marked ``needs_expert_check`` with a note rather
than repaired.

    python tools/extract_stem_rules.py <path-to-docx> [-o rules/stem_source_rows.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import docx

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

# "دستور ۱: …" is a rule. "دستور ۱-۴: …" is a sub-rule of rule 4 — the
# document divides stem 2 into "eight groups" (rules 2–9), so these two are
# parts of rule 4, not groups of their own.
_RULE = re.compile(r"^دستور\s+([۰-۹]+)\s*:\s*(.+)$")
_SUB_RULE = re.compile(r"^دستور\s+([۰-۹]+)-([۰-۹]+)\s*:\s*(.+)$")
_EXCEPTIONS = re.compile(r"^استثنا[ء]?\s+دستور\s+([۰-۹]+)\s*:\s*(.+)$")
_ENTRY = re.compile(r"([^()،]+?)\s*\(([^)]*)\)")

EXPECTED_RULES = 9
EXPECTED_SUB_RULES = 2


def _number(text: str) -> int:
    return int(text.translate(_DIGITS))


def _parse_exceptions(text: str, rule: int) -> list[dict[str, Any]]:
    """Split "آفریدن (آفرید، آفرین)، …" into one record per verb."""
    entries: list[dict[str, Any]] = []
    for infinitive, inside in _ENTRY.findall(text):
        stems = [part.strip() for part in inside.split("،") if part.strip()]
        record: dict[str, Any] = {
            "rule": rule,
            "infinitive_fa": infinitive.strip(),
            "stems_fa": stems,
            "raw": f"{infinitive.strip()} ({inside.strip()})",
        }
        # Three things the document leaves unresolved. Flagged, never repaired.
        if any("؟" in stem for stem in stems):
            record["needs_expert_check"] = True
            record["note"] = "the document writes ؟ for a stem it does not give"
        elif len(stems) != 2:
            record["needs_expert_check"] = True
            record["note"] = (
                f"expected two stems, the document gives {len(stems)}: "
                f"{'، '.join(stems)}"
            )
        entries.append(record)
    return entries


def extract(docx_path: Path) -> dict[str, Any]:
    """Read the nine stem rules, their two sub-rules and the exception lists."""
    document = docx.Document(str(docx_path))
    lines = [p.text.strip() for p in document.paragraphs if p.text.strip()]

    rules: list[dict[str, Any]] = []
    sub_rules: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []

    for line in lines:
        if sub_match := _SUB_RULE.match(line):
            part, parent, text = sub_match.groups()
            sub_rules.append(
                {
                    "parent_rule": _number(parent),
                    "part": _number(part),
                    "text_fa": text.strip(),
                }
            )
        elif rule_match := _RULE.match(line):
            number, text = rule_match.groups()
            rules.append({"rule": _number(number), "text_fa": text.strip()})
        elif exception_match := _EXCEPTIONS.match(line):
            number, text = exception_match.groups()
            exceptions.extend(_parse_exceptions(text, _number(number)))

    if len(rules) != EXPECTED_RULES:
        raise ValueError(f"found {len(rules)} rules, expected {EXPECTED_RULES}")
    if len(sub_rules) != EXPECTED_SUB_RULES:
        raise ValueError(
            f"found {len(sub_rules)} sub-rules, expected {EXPECTED_SUB_RULES}"
        )

    return {
        "source_document": docx_path.name,
        "source_sha256": hashlib.sha256(docx_path.read_bytes()).hexdigest(),
        "note": (
            "Verbatim transcription of the stem rules. The exception lists are "
            "in Persian script only; the document gives no Latin for them."
        ),
        "rules": rules,
        "sub_rules": sub_rules,
        "exceptions": exceptions,
    }


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path, help="path to the stem-rules .docx")
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("rules/stem_source_rows.json")
    )
    args = parser.parse_args(argv)

    dump = extract(args.docx)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(dump, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    flagged = [e for e in dump["exceptions"] if e.get("needs_expert_check")]
    print(f"rules: {len(dump['rules'])}, sub-rules: {len(dump['sub_rules'])}")
    print(f"exceptions: {len(dump['exceptions'])}, flagged: {len(flagged)}")
    for entry in flagged:
        print(f"  ? {entry['raw']} — {entry['note']}")
    print(f"written to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
