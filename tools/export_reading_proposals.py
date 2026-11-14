"""Readings proposed on the reading screen: gaps for karbon, picks for the model.

    python tools/export_reading_proposals.py > proposals.md          # for karbon
    python tools/export_reading_proposals.py --jsonl > picks.jsonl   # for the model

On the reading screen a reader may pick another of a word's readings, or type
one, where the automatic Behnevis was unsure (direction A, 2026-11-14). Each
is a record in the feedback store — ``verdict: good`` on a ``lexicon_entry``,
"this reading is right here" — and none of them changes the bank: the bank is
karbon's. This gathers them into **one list per run**, for one karbon issue
rather than one issue a word: each spelling with the readings proposed for
it, how often, what the model had read, and one place it was proposed.

**Two kinds, two places** (the project lead, 2026-11-14). A reading the bank
already has, picked for a word in a line, is a choice *in context* — the bank
needs nothing; the automatic Behnevis learns it at its next build
(``--jsonl``, read by ``tools/build_behnevis.py``). A reading typed that the
bank lacks is a gap in the bank, and only those go on karbon's list, the line
they were seen in as the evidence.

Read-only on the database.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from typing import Any

from sqlalchemy import select

from murfulu.db.models.review import ExpertFeedback
from murfulu.db.session import session_scope


def gather(rows: list[ExpertFeedback]) -> dict[str, dict[str, dict[str, Any]]]:
    """Spelling → proposed reading → how often, in the bank, the model, one place."""
    found: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        context = row.context or {}
        if context.get("screen") != "texts" or context.get("kind") != "reading_here":
            continue
        if context.get("in_bank") is True:
            continue  # a pick in context: the model's, not karbon's
        spelling = context.get("spelling_fa") or (row.target_id or "").partition(":")[0]
        latin = context.get("latin") or (row.target_id or "").partition(":")[2]
        entry = found[spelling].setdefault(
            latin,
            {
                "times": 0,
                "in_bank": context.get("in_bank"),
                "model": context.get("model_latin"),
                "place": context.get("heading") or context.get("document_id"),
                "written": context.get("written"),
            },
        )
        entry["times"] += 1
    return found


def report(found: dict[str, dict[str, dict[str, Any]]]) -> str:
    """The list as Markdown, the most proposed spellings first."""
    lines = [
        "# Readings proposed on murfulu's reading screen",
        "",
        "Each row: a spelling, a reading the bank lacks that readers said is right",
        "in a line, how often, what the automatic Behnevis had read, and one place.",
        "Proposals only — nothing here was written into the bank.",
        "",
        "| spelling | proposed | times | model read | written | one place |",
        "|---|---|---:|---|---|---|",
    ]
    order = sorted(
        found.items(), key=lambda kv: -sum(e["times"] for e in kv[1].values())
    )
    for spelling, readings in order:
        for latin, e in sorted(readings.items(), key=lambda kv: -kv[1]["times"]):
            lines.append(
                f"| {spelling} | {latin} | {e['times']} | {e['model'] or ''} "
                f"| {e['written'] or ''} | {e['place'] or ''} |"
            )
    return "\n".join(lines) + "\n"


def picks(rows: list[Any]) -> list[dict[str, Any]]:
    """Every proposal as the model build reads it, one dict per record."""
    found = []
    for row in rows:
        context = row.context or {}
        if context.get("screen") != "texts" or context.get("kind") != "reading_here":
            continue
        found.append(
            {
                key: context.get(key)
                for key in (
                    "spelling_fa",
                    "latin",
                    "in_bank",
                    "before",
                    "after",
                    "written",
                    "heading",
                )
            }
            | {"document_id": context.get("document_id")}
        )
    return found


def main(argv: list[str] | None = None) -> int:
    """Print the list, or every proposal as JSON lines."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--jsonl", action="store_true", help="every proposal, for the model"
    )
    args = parser.parse_args(argv)
    with session_scope() as session:
        rows = list(
            session.scalars(
                select(ExpertFeedback)
                .where(
                    ExpertFeedback.target_type == "lexicon_entry",
                    ExpertFeedback.verdict == "good",
                )
                .order_by(ExpertFeedback.id)
            )
        )
        if args.jsonl:
            for one in picks(rows):
                sys.stdout.write(json.dumps(one, ensure_ascii=False) + "\n")
        else:
            sys.stdout.write(report(gather(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
