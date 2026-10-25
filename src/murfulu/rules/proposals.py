"""Applying proposed changes to the rule pack, as data.

Pure: it takes the loaded YAML as dictionaries and a list of proposals, and
returns the YAML with the proposals applied plus a report of what happened to
each. Reading and writing the files is the exporting command's job — this
module keeps ``rules/`` free of I/O beyond loading, as ENGINEERING requires.

**Nothing is applied silently.** Every proposal comes back in one of four
states, and three of them are reasons *not* to write:

``applied``    the rule said what the proposal expected, and now says the new
               value
``already``    the pack already says it — accepted earlier, or two people
               proposed the same thing
``moved``      the rule no longer says what the proposal was written against.
               Applying it would quietly undo whoever changed it since
``unknown``    no rule with that id

The ``moved`` case is the reason a proposal stores the old value at all. It is
also the one that would do damage if it were guessed at, so it is reported and
skipped.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

__all__ = ["Applied", "Outcome", "PROPOSABLE_FIELDS", "apply"]

#: What may be proposed, and it is defined here because the pack owns what its
#: own fields are — the table in ``db/`` imports this rather than repeating it.
#:
#: The affix and its Persian spelling, the strength, the meaning tags, the
#: Farsi label and explanation, the examples, the notes, whether the rule is
#: active and whether it still needs checking. **Not** the id, which is
#: permanent; not the source row, which is a fact about the document; not the
#: input and output types, which change what the engine does rather than what
#: the grammar says.
PROPOSABLE_FIELDS = (
    "affix",
    "affix_fa",
    "strength",
    "semantic_tags",
    "label_fa",
    "explanation_fa",
    "examples",
    "notes",
    "active",
    "needs_expert_check",
)

OUTCOMES = ("applied", "already", "moved", "unknown")


@dataclass(frozen=True)
class Outcome:
    """What happened to one proposal."""

    proposal_id: int
    rule_id: str
    field: str
    outcome: str
    #: What the pack actually said, when that is the point of the outcome.
    found: Any = None

    def __str__(self) -> str:
        """One line for the command's output."""
        line = f"{self.rule_id}.{self.field}: {self.outcome}"
        if self.outcome == "moved":
            line += f" (the pack says {self.found!r})"
        return line


@dataclass
class Applied:
    """The changed tables, and what happened to every proposal."""

    tables: dict[str, dict[str, Any]] = field(default_factory=dict)
    outcomes: list[Outcome] = field(default_factory=list)

    def counted(self, outcome: str) -> int:
        """How many proposals ended in one state."""
        return sum(1 for one in self.outcomes if one.outcome == outcome)

    @property
    def changed_tables(self) -> list[str]:
        """Which files the caller has to write back."""
        applied = {one.rule_id for one in self.outcomes if one.outcome == "applied"}
        return sorted(
            name
            for name, table in self.tables.items()
            if any(rule["id"] in applied for rule in table.get("rules", []))
        )

    def summary(self) -> str:
        """One line, for the command's output."""
        return (
            f"{self.counted('applied')} applied, "
            f"{self.counted('already')} already in the pack, "
            f"{self.counted('moved')} skipped because the rule moved, "
            f"{self.counted('unknown')} for a rule that is not there"
        )


def _index(tables: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Every rule in every table, by its permanent id."""
    found: dict[str, dict[str, Any]] = {}
    for table in tables.values():
        for rule in table.get("rules", []):
            found[rule["id"]] = rule
    return found


def _held(rule: dict[str, Any], name: str) -> Any:
    """What the rule says for one field, with absent and null the same thing.

    A key the builder left out and a key it wrote as ``null`` mean the same to
    every reader of the pack, and a proposal should not turn on which one the
    file happens to have.
    """
    return rule.get(name)


def apply(
    tables: dict[str, dict[str, Any]], proposals: list[dict[str, Any]]
) -> Applied:
    """Apply proposals to a loaded rule pack, oldest first.

    ``tables`` maps a file name — ``verb_stems``, ``nominals`` — to the
    document loaded from it. It is not modified; a copy comes back.
    """
    changed = copy.deepcopy(tables)
    rules = _index(changed)
    result = Applied(tables=changed)

    for proposal in sorted(proposals, key=lambda one: one["id"]):
        rule_id = proposal["rule_id"]
        name = proposal["field"]
        rule = rules.get(rule_id)
        if rule is None:
            result.outcomes.append(Outcome(proposal["id"], rule_id, name, "unknown"))
            continue

        holds = _held(rule, name)
        if holds == proposal["proposed"]:
            result.outcomes.append(
                Outcome(proposal["id"], rule_id, name, "already", holds)
            )
            continue
        if holds != proposal["was"]:
            # Somebody changed it since. Applying now would revert them, and
            # a revert nobody asked for is worse than a proposal not applied.
            result.outcomes.append(
                Outcome(proposal["id"], rule_id, name, "moved", holds)
            )
            continue

        rule[name] = proposal["proposed"]
        result.outcomes.append(Outcome(proposal["id"], rule_id, name, "applied"))

    return result
