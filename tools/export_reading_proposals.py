"""Readings proposed on the reading screen: gaps for karbon, picks for the model.

    python tools/export_reading_proposals.py > proposals.md          # for karbon
    python tools/export_reading_proposals.py --jsonl > picks.jsonl   # for the model
    python tools/export_reading_proposals.py --confirmed > issue.md  # the linguist's

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

**A reading decided for every like place** (2026-11-21, :mod:`murfulu.behnevis.decided`)
is passed on whole, with its scope and store id, for the build to keep the
newest for each spelling and scope; karbon's list takes the decisions in
force whose reading the bank lacks, with what they were decided for.

**Only what the linguist confirmed** (``--confirmed``; the project lead,
2026-11-22, :mod:`murfulu.behnevis.proposed`) is the text of one karbon issue:
the readings confirmed on the reading screen's list for karbon, in two parts —
spellings the bank lacks altogether, and readings it lacks for a spelling it
holds — each with what the bank has, what it was decided for and an example.
It needs the lexicon, to say which of the two a reading is.

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

from murfulu.behnevis import decided as decisions
from murfulu.behnevis import proposed
from murfulu.behnevis.proposed import HERE, latest
from murfulu.db.models.review import ExpertFeedback
from murfulu.db.session import session_scope

# The kinds of record this export reads — a reading for one word in a line
# (`HERE`), a reading decided for every like place, and the linguist's
# confirmation — and which records count (`latest`) live in
# :mod:`murfulu.behnevis.proposed`, shared with the reading screen's list.
_good = proposed.good


def gather(
    rows: list[Any], in_bank: Callable[[str, str], bool | None] | None = None
) -> dict[str, dict[str, dict[str, Any]]]:
    """Spelling → proposed reading → how often, the model, one place.

    ``in_bank`` asks the current bank whether it has a reading; without it the
    flag saved with the proposal decides, which goes stale when karbon adds a
    reading (the review of 2026-11-14).
    """
    found: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    in_force = {
        one.order: one
        for one in decisions.current(
            one
            for one in (
                decisions.from_record(row.context or {}, row.id)
                for row in rows
                if (row.context or {}).get("kind") == decisions.KIND
            )
            if one is not None
        )
    }
    for row in rows:
        context = row.context or {}
        if context.get("screen") != "texts":
            continue
        if context.get("kind") == decisions.KIND:
            if row.id not in in_force:
                continue  # replaced by a newer decision, or taken back
        elif context.get("kind") != HERE:
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
                "decided": [],
            },
        )
        entry["times"] += 1
        if context.get("kind") == decisions.KIND:
            entry["decided"].append(_reach(in_force[row.id]))
    return found


def _reach(one: decisions.Decision) -> str:
    """What a decision was for, in a few words for karbon's list."""
    if one.scope == decisions.AFTER_WORD:
        return f"after {one.word}"
    if one.scope == decisions.BEFORE_WORD:
        return f"before {one.word}"
    return "everywhere"


def bank_and_functions() -> (
    tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]] | None
):
    """The current bank and the function-word list, or None without a lexicon."""
    try:
        from murfulu.behnevis.transcribe import bank_from, load_function_readings
        from murfulu.lexicon.store import Lexicon

        with Lexicon.open() as lexicon:
            bank = bank_from(
                (r.spelling_fa, latin)
                for r in lexicon.all_readings()
                for latin in r.all_latin
                if latin
            )
    except Exception:  # no lexicon here
        return None
    return bank, load_function_readings()


def snapshot_id() -> str | None:
    """Which lexicon the bank was read from, for the issue's first line."""
    try:
        from murfulu.lexicon.store import Lexicon

        with Lexicon.open() as lexicon:
            return lexicon.snapshot_id
    except Exception:  # no lexicon here
        return None


def current_bank() -> Callable[[str, str], bool | None] | None:
    """Whether the current bank holds a reading, or None without a lexicon.

    A function word's own reading counts as held (و *o*, به *be*): the model
    learns a pick of it. Where the bank lacks it, it is on the linguist's
    list for karbon all the same (:func:`murfulu.behnevis.proposed.waiting`).
    """
    found = bank_and_functions()
    if found is None:
        return None  # the saved flag decides
    bank, functions = found

    def held(spelling: str, latin: str) -> bool:
        return proposed.held_by(bank, functions, spelling, latin)

    return held


def report(found: dict[str, dict[str, dict[str, Any]]]) -> str:
    """The list as Markdown, the most proposed spellings first."""
    lines = [
        "# Readings proposed on murfulu's reading screen",
        "",
        "Each row: a spelling, a reading the bank lacks that readers said is right",
        "in a line, how often, what the automatic Behnevis had read, and one place.",
        "*Decided for* says where a reader decided it for every like place:",
        "everywhere, or after or before one word. Proposals only — nothing here",
        "was written into the bank.",
        "",
        "| spelling | proposed | times | model read | written | one place "
        "| decided for |",
        "|---|---|---:|---|---|---|---|",
    ]
    order = sorted(
        found.items(), key=lambda kv: -sum(e["times"] for e in kv[1].values())
    )
    for spelling, readings in order:
        for latin, e in sorted(readings.items(), key=lambda kv: -kv[1]["times"]):
            reach = "; ".join(e["decided"])
            lines.append(
                f"| {spelling} | {latin} | {e['times']} | {e['model'] or ''} "
                f"| {e['written'] or ''} | {e['place'] or ''} | {reach} |"
            )
    return "\n".join(lines) + "\n"


def _cell(text: Any) -> str:
    """A value in a Markdown table cell."""
    return str(text or "").replace("|", "\\|").replace("\n", " ")


def _example(one: dict[str, Any]) -> str:
    """One place a reading was proposed: its line, or the words around it, and where."""
    for place in one["places"]:
        said = place.get("text") or " ".join(
            part
            for part in (place.get("before"), place.get("written"), place.get("after"))
            if part
        )
        where = place.get("heading") or place.get("document_id") or ""
        return f"{said} — {where}" if said and where else said or where
    return ""


def _decided_for(one: dict[str, Any]) -> str:
    """What a reading was decided for, in a few words."""
    said = []
    for reach in one["decided"]:
        if reach["scope"] == decisions.AFTER_WORD:
            said.append(f"after {reach['word']}")
        elif reach["scope"] == decisions.BEFORE_WORD:
            said.append(f"before {reach['word']}")
        else:
            said.append("everywhere")
    return "; ".join(said)


def confirmed_report(rows: list[dict[str, Any]], snapshot: str | None = None) -> str:
    """What the linguist confirmed, as the text of one karbon issue.

    ``rows`` are :func:`murfulu.behnevis.proposed.waiting`'s; only those with
    a confirmation in force are written, in two parts.
    """
    said = [one for one in rows if one["confirmed"]]
    missing = [one for one in said if one["kind"] == proposed.MISSING]
    reading = [one for one in said if one["kind"] == proposed.READING]
    lines = [
        "# Readings the linguist confirmed on murfulu's reading screen",
        "",
        f"{len(said)} reading{'' if len(said) == 1 else 's'} the bank lacks"
        + (f" (`{snapshot}`)" if snapshot else "")
        + ", each confirmed by the linguist on murfulu's list for karbon.",
        "*Proposed* counts the places readers saved it; *decided for* says where a",
        "reader decided it for every like place. A reading marked *function word*",
        "is one murfulu's own list reads the spelling as in running text.",
        "Proposals only — nothing here was written into the bank.",
        "",
        f"## Spellings the bank does not hold ({len(missing)})",
        "",
    ]
    if missing:
        lines += [
            "| spelling | reading | proposed | decided for | example |",
            "|---|---|---:|---|---|",
        ]
        lines += [
            f"| {_cell(one['spelling_fa'])} | {_cell(one['latin'])}"
            f"{' (function word)' if one['origin'] == proposed.FUNCTION else ''} "
            f"| {one['times']} | {_cell(_decided_for(one))} | {_cell(_example(one))} |"
            for one in missing
        ]
    else:
        lines.append("None.")
    lines += [
        "",
        f"## Spellings the bank holds, without this reading ({len(reading)})",
        "",
    ]
    if reading:
        lines += [
            "| spelling | reading | the bank has | proposed | decided for | example |",
            "|---|---|---|---:|---|---|",
        ]
        lines += [
            f"| {_cell(one['spelling_fa'])} | {_cell(one['latin'])}"
            f"{' (function word)' if one['origin'] == proposed.FUNCTION else ''} "
            f"| {_cell(', '.join(one['bank']))} | {one['times']} "
            f"| {_cell(_decided_for(one))} | {_cell(_example(one))} |"
            for one in reading
        ]
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def picks(rows: list[Any]) -> list[dict[str, Any]]:
    """Every proposal as the model build reads it, one dict per record."""
    found = []
    for row in rows:
        context = row.context or {}
        kind = context.get("kind")
        if context.get("screen") != "texts" or kind not in (HERE, decisions.KIND):
            continue
        one = {
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
        } | {"document_id": context.get("document_id"), "kind": kind}
        if kind == decisions.KIND:
            # The build keeps the newest for each spelling and scope: it
            # needs the scope, whether it was taken back, and the order.
            one |= {
                "scope": context.get("scope"),
                "scope_word": context.get("scope_word"),
                "withdrawn": bool(context.get("withdrawn")),
                "replaces": context.get("replaces"),
                "id": row.id,
            }
        found.append(one)
    return found


def main(argv: list[str] | None = None) -> int:
    """Print the list, or every proposal as JSON lines."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    kind = parser.add_mutually_exclusive_group()
    kind.add_argument(
        "--jsonl", action="store_true", help="every proposal, for the model"
    )
    kind.add_argument(
        "--confirmed",
        action="store_true",
        help="only what the linguist confirmed, as the text of one karbon issue",
    )
    args = parser.parse_args(argv)
    held = bank_and_functions() if args.confirmed else None
    if args.confirmed and held is None:
        sys.stderr.write("no lexicon: set MURFULU_LEXICON_PATH\n")
        return 2
    with session_scope() as session:
        rows = list(
            session.scalars(
                select(ExpertFeedback)
                .where(
                    ExpertFeedback.target_type == "lexicon_entry",
                    # A decision taken back is stored with `unsure`; every
                    # other record read here is a `good` one (`_good`).
                    ExpertFeedback.verdict.in_(("good", "unsure")),
                )
                .order_by(ExpertFeedback.id)
            )
        )
        rows = latest([row for row in rows if _good(row)])
        if args.jsonl:
            for one in picks(rows):
                sys.stdout.write(json.dumps(one, ensure_ascii=False) + "\n")
        elif held is not None:
            sys.stdout.write(
                confirmed_report(proposed.waiting(rows, *held), snapshot_id())
            )
        else:
            sys.stdout.write(report(gather(rows, current_bank())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
