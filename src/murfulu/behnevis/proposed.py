"""Readings the bank lacks, gathered for karbon, and the linguist's word on each.

The reading screen collects three kinds of record that can name a reading the
bank does not hold: a reading typed for one word in a line (``reading_here``),
a reading decided for every like place of a spelling
(:mod:`murfulu.behnevis.decided`), and — held by this project, not by a
reader — the function-word list's own readings (و *va*, را *rā*), which the
bank reads as the content words written the same way or not at all.

**The project lead's rule of 2026-11-22**: what goes to karbon is what the
linguist confirmed, gathered with an example, and sent as one issue after a
while — both a spelling the bank lacks altogether and a reading it lacks for
a spelling it holds. So this module does two things:

- :func:`waiting` gathers every such reading, one row per spelling and
  reading, with how often it was proposed, what it was decided for, up to
  three places, and which of the two kinds it is;
- a **confirmation** (``kind: reading_confirmed``) is the linguist's word
  that a row is right. It is a feedback record like the others — append-only,
  ``verdict: good`` on ``spelling:latin``; one marked ``withdrawn`` (with
  ``verdict: unsure``) takes it back. :func:`confirmed` says which are in
  force.

**The app has one account** (2026-08-17), so a confirmation is a statement,
not an identity: whoever presses the button says the linguist confirmed. It
is kept apart from the proposals for exactly that reason — a reader trying a
reading out does not thereby send it to karbon.

Nothing here writes, and nothing here changes what the model learns: a pick
of a function word's own reading still teaches the model
(``tools/export_reading_proposals.py``, :func:`held_by`).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from murfulu.behnevis import decided as decisions
from murfulu.behnevis.transcribe import key

#: A reading picked or typed for one word in one line.
HERE = "reading_here"
#: The linguist's word that a reading the bank lacks is right.
CONFIRMED = "reading_confirmed"

#: The two kinds of gap: the bank has no reading for the spelling at all, or
#: it has readings and not this one.
MISSING, READING = "missing", "reading"

#: Where a row comes from: a reader's proposal, or the function-word list.
READER, FUNCTION = "reader", "function"

#: How many places a row keeps as its examples.
PLACES = 3

Bank = Mapping[str, tuple[str, ...]]


# -- which records count ---------------------------------------------------------


def good(row: Any) -> bool:
    """A `good` record, or one of the kinds taken back with `unsure`."""
    context = row.context or {}
    return row.verdict == "good" or context.get("kind") in (decisions.KIND, CONFIRMED)


def here(context: dict[str, Any]) -> bool:
    """Whether a record is a reading for one word in a line.

    A decision for every like place is not replaced by a later save at the
    place it was made from: its own scope says what replaces it
    (:func:`murfulu.behnevis.decided.current`). A confirmation names no place.
    """
    return context.get("kind") not in (decisions.KIND, CONFIRMED)


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
        if context.get("document_id") and here(context):
            newest[(_context(context), _position(context))] = at
    kept = set(newest.values())
    return [
        row
        for at, row in enumerate(rows)
        if not ((row.context or {}).get("document_id") and here(row.context or {}))
        or at in kept
    ]


# -- the linguist's confirmations ------------------------------------------------


@dataclass(frozen=True)
class Confirmation:
    """One confirmation, or one taken back, keyed as the model keys spellings."""

    spelling: str
    latin: str
    #: The store's id: the larger, the newer.
    order: int
    withdrawn: bool = False
    #: A confirmation taken back names the one it takes back.
    replaces: int | None = None


def confirmation_from(context: dict[str, Any], order: int) -> Confirmation | None:
    """A confirmation from a feedback record's context, or None if it is not one."""
    if context.get("kind") != CONFIRMED:
        return None
    spelling = key(context.get("spelling_fa") or "")
    latin = context.get("latin") or ""
    if not spelling or not latin:
        return None
    withdrawn = bool(context.get("withdrawn"))
    replaces = context.get("replaces") if withdrawn else None
    return Confirmation(
        spelling,
        latin,
        order,
        withdrawn,
        replaces if isinstance(replaces, int) else None,
    )


def confirmed(found: Iterable[Confirmation]) -> dict[tuple[str, str], int]:
    """The confirmations in force: (spelling, reading) → the store's id.

    The newest for a spelling and reading counts. One taken back that names
    the confirmation it takes back clears it only while that one is still the
    newest; one that names none clears it.
    """
    newest: dict[tuple[str, str], int] = {}
    for one in sorted(found, key=lambda c: c.order):
        at = (one.spelling, one.latin)
        held = newest.get(at)
        if not one.withdrawn:
            newest[at] = one.order
        elif held is not None and (one.replaces is None or one.replaces == held):
            del newest[at]
    return newest


# -- what waits for karbon -------------------------------------------------------


def held_by(bank: Bank, functions: Bank, spelling: str, latin: str) -> bool:
    """Whether the model can learn a reading: the bank or the function list holds it."""
    k = key(spelling)
    return latin in bank.get(k, ()) or latin in functions.get(k, ())


def _place(context: dict[str, Any]) -> dict[str, Any] | None:
    """Where a proposal was made, as an example for karbon; None if it names no text."""
    if not context.get("document_id"):
        return None
    return {
        "document_id": context.get("document_id"),
        "unit": context.get("unit"),
        "line": context.get("line"),
        "word": context.get("word"),
        "heading": context.get("heading"),
        "written": context.get("written"),
        "before": context.get("before"),
        "after": context.get("after"),
        # The line's own words, sent with a save since 2026-11-22.
        "text": context.get("line_text"),
    }


def _reach(one: decisions.Decision, context: dict[str, Any]) -> dict[str, Any]:
    """What a decision in force was for."""
    return {
        "scope": one.scope,
        # As the screen sent it, half-spaces and all, for display.
        "word": context.get("scope_word") if one.word else None,
    }


def waiting(rows: Iterable[Any], bank: Bank, functions: Bank) -> list[dict[str, Any]]:
    """Every reading the bank lacks, one row per spelling and reading.

    ``rows`` are the feedback records on ``lexicon_entry``, oldest first, after
    :func:`latest`. A reader's reading counts when neither the bank nor the
    function-word list holds it — the same line the model's build draws
    (:func:`held_by`); the function-word list's own readings the bank lacks
    are rows of their own, whether or not a reader ever picked them.

    Ordered for the screen: the most proposed first, then by spelling.
    """
    rows = list(rows)
    in_force = {
        one.order: one
        for one in decisions.current(
            one
            for one in (
                decisions.from_record(row.context or {}, row.id) for row in rows
            )
            if one is not None
        )
    }
    said = confirmed(
        one
        for one in (confirmation_from(row.context or {}, row.id) for row in rows)
        if one is not None
    )
    stamped = {row.id: getattr(row, "created_at", None) for row in rows}
    found: dict[tuple[str, str], dict[str, Any]] = {}

    def entry(spelling_fa: str, latin: str, origin: str) -> dict[str, Any]:
        k = key(spelling_fa)
        held = bank.get(k, ())
        return found.setdefault(
            (k, latin),
            {
                "spelling": k,
                "spelling_fa": spelling_fa,
                "latin": latin,
                "kind": READING if held else MISSING,
                "bank": list(held),
                "origin": origin,
                "times": 0,
                "model": None,
                "decided": [],
                "places": [],
            },
        )

    for row in rows:
        context = row.context or {}
        kind = context.get("kind")
        if context.get("screen") != "texts":
            continue
        if kind == decisions.KIND:
            if row.id not in in_force:
                continue  # replaced by a newer decision, or taken back
        elif kind != HERE:
            continue
        spelling = context.get("spelling_fa") or (row.target_id or "").partition(":")[0]
        latin = context.get("latin") or (row.target_id or "").partition(":")[2]
        if not spelling or not latin or held_by(bank, functions, spelling, latin):
            continue  # the model's: a pick in context, nothing for karbon
        one = entry(spelling, latin, READER)
        one["times"] += 1
        one["model"] = one["model"] or context.get("model_latin")
        if kind == decisions.KIND:
            one["decided"].append(_reach(in_force[row.id], context))
        place = _place(context)
        if place is not None and len(one["places"]) < PLACES:
            at = (place["document_id"], place["unit"], place["line"], place["word"])
            if all(
                (p["document_id"], p["unit"], p["line"], p["word"]) != at
                for p in one["places"]
            ):
                one["places"].append(place)

    for k, readings in functions.items():
        for latin in readings:
            if latin not in bank.get(k, ()):
                entry(k, latin, FUNCTION)

    for (k, latin), one in found.items():
        order = said.get((k, latin))
        when = stamped.get(order) if order is not None else None
        one["confirmed"] = (
            None
            if order is None
            else {"id": order, "created_at": when.isoformat() if when else None}
        )
    return sorted(
        found.values(), key=lambda one: (-one["times"], one["spelling"], one["latin"])
    )
