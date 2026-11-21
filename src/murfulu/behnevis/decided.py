"""Readings a person decided once for every like place of a spelling.

A pick on the reading screen is for one word in one line: the model learns it
as one more answer (:mod:`.picks`), and one answer moves a word little. A
**decision** says more (the project lead's request of 2026-11-21, to cut the
work on the most frequent unsure words): this spelling reads so **wherever it
stands**, or wherever it stands **after** one word, or **before** one word.
At the model's next build (``tools/build_behnevis.py``) every such place takes
the decided reading, at :attr:`Transcriber.decided_confidence`.

**Where they live.** Like picks, in the feedback store, owned by karbon and
append-only: ``verdict: good`` on ``spelling:latin``, with ``kind:
reading_decided`` and the scope in ``context``. A decision is never edited;
a newer one for the same spelling and scope replaces it, and one marked
``withdrawn`` takes it back (:func:`current`).

**What the model learns.** Only a reading the bank or the function-word list
holds, as with picks: a decided reading the bank lacks goes on karbon's list
(``tools/export_reading_proposals.py``) and teaches nothing until the bank
has it (DECISIONS 2026-11-14).

**Which decision wins.** A word's own vowel signs first: a decision they rule
out does not apply there. Then the narrower scope: after or before a word
over everywhere; between an *after* and a *before* decision that both apply,
the newer.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from murfulu.behnevis.transcribe import key

#: The kind of feedback record a decision is.
KIND = "reading_decided"

#: How far a decision reaches.
EVERYWHERE, AFTER_WORD, BEFORE_WORD = "everywhere", "after_word", "before_word"
SCOPES = (EVERYWHERE, AFTER_WORD, BEFORE_WORD)


@dataclass(frozen=True)
class Decision:
    """One decision, as the store holds it, keyed as the model keys spellings."""

    spelling: str
    #: The decided reading; None for a decision taken back.
    latin: str | None
    scope: str
    #: The word it follows (``after_word``) or precedes (``before_word``).
    word: str | None
    #: The store's id: the larger, the newer.
    order: int

    @property
    def reach(self) -> tuple[str, str, str | None]:
        """What a newer decision replaces: the same spelling and scope."""
        return (self.spelling, self.scope, self.word)


def from_record(context: dict[str, Any], order: int) -> Decision | None:
    """A decision from a feedback record's context, or None if it is not one.

    A record whose scope is unknown, or that names no word where its scope
    needs one, is not a decision: it is passed over rather than guessed at.
    """
    if context.get("kind") != KIND:
        return None
    spelling = key(context.get("spelling_fa") or "")
    scope = context.get("scope")
    word = context.get("scope_word")
    withdrawn = bool(context.get("withdrawn"))
    latin = None if withdrawn else (context.get("latin") or None)
    if not spelling or scope not in SCOPES or (latin is None and not withdrawn):
        return None
    if scope == EVERYWHERE:
        word = None
    elif not word:
        return None
    else:
        word = key(word)
    return Decision(spelling, latin, scope, word, order)


def current(decisions: Iterable[Decision]) -> list[Decision]:
    """The decisions in force: the newest per spelling and scope, none taken back."""
    newest: dict[tuple[str, str, str | None], Decision] = {}
    for one in decisions:
        held = newest.get(one.reach)
        if held is None or one.order > held.order:
            newest[one.reach] = one
    return sorted(
        (one for one in newest.values() if one.latin is not None),
        key=lambda one: -one.order,
    )


@dataclass
class Decided:
    """The decisions in force, as the transcriber looks them up."""

    #: spelling → (scope, word) → (reading, order)
    table: dict[str, dict[tuple[str, str | None], tuple[str, int]]] = field(
        default_factory=dict
    )

    @classmethod
    def of(cls, decisions: Iterable[Decision]) -> Decided:
        """The table of the decisions in force among these."""
        table: dict[str, dict[tuple[str, str | None], tuple[str, int]]] = {}
        for one in current(decisions):
            assert one.latin is not None
            table.setdefault(one.spelling, {})[(one.scope, one.word)] = (
                one.latin,
                one.order,
            )
        return cls(table)

    def __len__(self) -> int:
        """How many decisions are in force."""
        return sum(len(scopes) for scopes in self.table.values())

    def lookup(
        self,
        spelling: str,
        before: str | None,
        after: str | None,
        allowed: Callable[[str], bool] | None = None,
    ) -> str | None:
        """The decided reading for a spelling between these neighbours, if any.

        ``allowed`` says whether a reading may stand here at all (the word's
        own signs): a decision it rules out is passed over before the
        narrower-first choice, so a wider decision the signs allow still holds.
        """
        mine = self.table.get(spelling)
        if not mine:
            return None
        near = [
            found
            for found in (
                mine.get((AFTER_WORD, before)) if before else None,
                mine.get((BEFORE_WORD, after)) if after else None,
            )
            if found is not None and (allowed is None or allowed(found[0]))
        ]
        if near:
            return max(near, key=lambda one: one[1])[0]
        everywhere = mine.get((EVERYWHERE, None))
        if everywhere and (allowed is None or allowed(everywhere[0])):
            return everywhere[0]
        return None

    def to_dict(self) -> dict[str, Any]:
        """A plain form for the model file."""
        return {
            spelling: [
                [scope, word, latin, order]
                for (scope, word), (latin, order) in scopes.items()
            ]
            for spelling, scopes in self.table.items()
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Decided:
        """Read back what :meth:`to_dict` wrote."""
        return cls(
            {
                spelling: {
                    (scope, word): (latin, order) for scope, word, latin, order in rows
                }
                for spelling, rows in raw.items()
            }
        )


def decisions_from(
    rows: Iterable[dict[str, Any]],
    bank: dict[str, tuple[str, ...]],
    functions: dict[str, tuple[str, ...]],
) -> tuple[Decided, list[Decision]]:
    """What the model learns from the exported decisions, and what waits for karbon.

    ``rows`` are the export's lines (``export_reading_proposals.py --jsonl``):
    each a record's context, with its store id as ``id``. The decisions in
    force whose reading the current bank or the function-word list holds are
    learned; the rest are returned, for karbon's list.
    """
    found = [
        one
        for one in (from_record(row, int(row.get("id") or 0)) for row in rows)
        if one is not None
    ]
    learned: list[Decision] = []
    waiting: list[Decision] = []
    for one in current(found):
        held = (*functions.get(one.spelling, ()), *bank.get(one.spelling, ()))
        (learned if one.latin in held else waiting).append(one)
    # Taken-back decisions stay in the table's history only by not being
    # there: `current` already dropped them.
    return Decided.of(learned), waiting
