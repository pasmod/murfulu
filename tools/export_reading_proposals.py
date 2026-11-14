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

**The newest save for a word in a line counts.** The reading screen lets a
reader save again where they changed their mind, and shows the newest; the
store keeps every record (it is append-only), and this export passes only the
newest one for each place on, to the model and to karbon alike (the review of
2026-11-14).

Read-only on the database.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from sqlalchemy import select

from murfulu.db.models.review import ExpertFeedback
from murfulu.db.session import session_scope


def gather(
    rows: list[Any], in_bank: Callable[[str, str], bool | None] | None = None
) -> dict[str, dict[str, dict[str, Any]]]:
    """Spelling → proposed reading → how often, the model, one place.

    ``in_bank`` asks the current bank whether it has a reading; without it the
    flag saved with the proposal decides, which goes stale when karbon adds a
    reading (the review of 2026-11-14).
    """
    found: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        context = row.context or {}
        if context.get("screen") != "texts" or context.get("kind") != "reading_here":
            continue
        spelling = context.get("spelling_fa") or (row.target_id or "").partition(":")[0]
        latin = context.get("latin") or (row.target_id or "").partition(":")[2]
        now = in_bank(spelling, latin) if in_bank is not None else None
        if (context.get("in_bank") is True) if now is None else now:
            continue  # the bank has it: a pick in context, the model's, not karbon's
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


def current_bank() -> Callable[[str, str], bool | None] | None:
    """Whether the current bank holds a reading, or None without a lexicon.

    A function word's own reading counts as held (و *o*, به *be*): the model
    learns a pick of it, and karbon is not asked for it.
    """
    try:
        from murfulu.behnevis.transcribe import bank_from, key, load_function_readings
        from murfulu.lexicon.store import Lexicon

        with Lexicon.open() as lexicon:
            bank = bank_from(
                (r.spelling_fa, latin)
                for r in lexicon.all_readings()
                for latin in r.all_latin
                if latin
            )
    except Exception:  # no lexicon here: the saved flag decides
        return None
    functions = load_function_readings()

    def held(spelling: str, latin: str) -> bool:
        k = key(spelling)
        return latin in bank.get(k, ()) or latin in functions.get(k, ())

    return held


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


def _context(context: dict[str, Any]) -> tuple[Any, ...]:
    """The word a proposal was for: its text, unit, spelling, form and neighbours."""
    return (
        context.get("document_id"),
        context.get("unit"),
        context.get("spelling_fa"),
        context.get("written"),
        context.get("before"),
        context.get("after"),
    )


def _position(context: dict[str, Any]) -> tuple[Any, ...] | None:
    """Its line and place in the line, sent since 2026-11-14."""
    line, word = context.get("line"), context.get("word")
    return None if line is None or word is None else (line, word)


def latest(rows: list[Any]) -> list[Any]:
    """Only the newest proposal for each word in a line, in the order given.

    ``rows`` come oldest first. A later save replaces an earlier one only for
    the same word — same text, unit, spelling, form and neighbours — at the
    same position, so a word a corpus revision moved under old coordinates is
    not taken for the one saved there. A save from before positions were sent
    cannot say which of two like words it was for, and this export cannot see
    the text, so a positioned save never replaces it (the review of
    2026-11-14; the server held no such save when positions came in). A
    proposal that names no text is kept as it is: nothing says it was replaced.
    """
    newest: dict[tuple[Any, ...], int] = {}
    for at, row in enumerate(rows):
        context = row.context or {}
        if context.get("document_id"):
            newest[(_context(context), _position(context))] = at
    kept = set(newest.values())
    return [
        row
        for at, row in enumerate(rows)
        if not (row.context or {}).get("document_id") or at in kept
    ]


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
        rows = latest(rows)
        if args.jsonl:
            for one in picks(rows):
                sys.stdout.write(json.dumps(one, ensure_ascii=False) + "\n")
        else:
            sys.stdout.write(report(gather(rows, current_bank())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
