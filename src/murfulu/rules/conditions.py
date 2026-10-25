"""What a rule says about its base, beyond the word class.

The source grammar states a condition for 186 of the 195 rules. For 164 of
them the condition is the word class again, which the engine already honours
by matching `input_types`. **Twelve say something more, and nothing was
reading them** — the text sat in `rules/*.yaml` and no code ever looked at it.

So V-010 says its stem *mostly* ends in ``-t`` or ``-d``, and the engine
happily ran it on stems that do not. That is the difference between *Raftār*,
which the corpus has 1,206 times, and forms nobody has written.

**Nothing here refuses to run a rule**, and that is deliberate:

*The source hedges.* V-010 says **bištar** — mostly. A tendency reported as a
prohibition would be a stronger claim than the grammar makes.

*Turning a tendency into a filter is a linguistic decision.* Whether a rule
should be stopped from firing when its condition fails is the linguist's
ruling, not an engineering default. What this module does is **record** it, so
a result can say the condition was not met and a reader can weigh that.

*A word never disappears.* The project's rule everywhere else — say what the
evidence is, never hide the word — applies here too.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

#: The file holding the authored table. Beside the rule pack, because it is
#: part of it.
CONDITIONS_FILE = "input_conditions.yaml"

#: How firmly the source states it. A *tendency* is what the grammar hedges
#: with **bištar**; a *stated* condition is written flatly. Neither refuses.
STRICTNESS = ("tendency", "stated")

#: The tests this module knows how to run. ``stem_group`` is declared and not
#: implemented — see OPEN_QUESTIONS S7 — so a rule using it reports *unknown*
#: rather than a verdict nobody has authorised.
TESTS = ("ends_with", "stem_group")


class ConditionError(ValueError):
    """Raised when the authored table does not make sense."""


@dataclass(frozen=True)
class Condition:
    """One rule's condition on its base."""

    rule_id: str
    #: The line from the source grammar, verbatim, so this can be checked by
    #: eye against the rule pack.
    source_text: str
    test: str
    values: tuple[str, ...]
    strictness: str
    note: str = ""
    #: True when the test cannot be run until somebody rules on something.
    needs_expert_check: bool = False

    @property
    def testable(self) -> bool:
        """False when the test is declared but cannot yet be run."""
        return self.test == "ends_with" and not self.needs_expert_check

    def met_by(self, base: str) -> bool | None:
        """Say whether this base satisfies the condition.

        ``None`` means *not established* — the condition exists and could not
        be tested. It is never the same answer as False, which is why the
        return is three-valued rather than a bare boolean.
        """
        if not self.testable or not base:
            return None
        return any(base.lower().endswith(value.lower()) for value in self.values)

    def describe_fa(self) -> str:
        """One line in Persian for a reader, from the source's own words."""
        listed = "، ".join(f"«{value}»" for value in self.values)
        what = f"پایانهٔ {listed}" if self.test == "ends_with" else f"گروهِ {listed}"
        hedge = "بیشتر " if self.strictness == "tendency" else ""
        return f"سرچشمه می‌گوید این دستور {hedge}پایه‌ای با {what} می‌گیرد."


def _load(document: dict[str, Any]) -> dict[str, Condition]:
    found: dict[str, Condition] = {}
    for raw in document.get("conditions", []):
        rule_id = raw.get("rule")
        if not rule_id:
            raise ConditionError("a condition with no rule id")
        if rule_id in found:
            raise ConditionError(f"{rule_id} has two conditions")
        test = raw.get("test")
        if test not in TESTS:
            raise ConditionError(f"{rule_id}: unknown test {test!r}")
        strictness = raw.get("strictness")
        if strictness not in STRICTNESS:
            raise ConditionError(f"{rule_id}: unknown strictness {strictness!r}")
        values = tuple(raw.get("values") or ())
        if not values:
            raise ConditionError(f"{rule_id}: a condition with nothing to test")
        if not (raw.get("source_text") or "").strip():
            raise ConditionError(
                f"{rule_id}: no source text — a condition nobody can check "
                f"against the grammar is not evidence of anything"
            )
        found[rule_id] = Condition(
            rule_id=rule_id,
            source_text=raw["source_text"],
            test=test,
            values=values,
            strictness=strictness,
            note=raw.get("note", ""),
            needs_expert_check=bool(raw.get("needs_expert_check")),
        )
    return found


def default_directory() -> Path:
    """Where the rule pack lives. Configuration, never a literal."""
    configured = os.environ.get("MURFULU_RULES_PATH")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / "rules"


def load(directory: Path | None = None) -> dict[str, Condition]:
    """Read the authored table."""
    path = (directory or default_directory()) / CONDITIONS_FILE
    if not path.is_file():
        return {}
    return _load(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


@lru_cache(maxsize=1)
def loaded() -> dict[str, Condition]:
    """The table, read once."""
    return load()


def check(rule_id: str, base: str) -> tuple[Condition | None, bool | None]:
    """The condition on a rule and whether this base meets it.

    ``(None, None)`` means the rule states nothing beyond its word class,
    which is the ordinary case — 183 of the 195 rules.
    """
    condition = loaded().get(rule_id)
    if condition is None:
        return None, None
    return condition, condition.met_by(base)
