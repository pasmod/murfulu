"""How well a compound is built: what its second half has made before.

The build screen's «ساخت» rests on a rule's realisation rate, and a noun's
whole compound page is built by three rules — دل's 4,685 words are V-078,
V-079 and V-016 — so it would give every row the same number. What separates
دلدار from دلدوز is the second half, which works like a suffix. So the value
is measured per slot rule and per second half: how many of the rule's nouns
it joins into a word **the dictionary labels a compound under exactly the
joined reading, and the corpus has** (``tools/measure_compounding.py
--heads``; FINDINGS 2026-11-21, *a build value for compounds*).

**A scale of its own** — the project lead's choice of 2026-11-21 (OPEN_QUESTIONS
S51). On the build screen's scale the best half reached 51 and 97% of a page
stayed under 10, so compounds read as badly built. Here 100 is the best half
measured, «‑دار» after a noun (73 compounds), on a log scale over the counts:
one confirmed compound is 16, none is 0. **One scale for every slot rule**,
anchored once: V-016 holds only 30 confirmed compounds in all, and a scale per
rule would give its three-compound halves the same 100 as «‑دار». Rates are
counted against the largest pool, so a rule with fewer nouns is not
penalised for it.

**Not measured is never zero.** A template rule (both halves from one verb),
a one-letter half (ر، ش، م: too many words end that way to tell), or a stem
the measurement never saw gets no value — the cell says so — rather than the
zero of a half that was measured and made nothing.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Any

from murfulu.corpus.wordtypes import normalise

PATH_VARIABLE = "MURFULU_COMPOUND_HEADS_PATH"


@dataclass(frozen=True)
class HeadValue:
    """One row's value and the two numbers it comes from."""

    #: 0 to 100 on the compounds' own scale.
    build: int
    #: Compounds this half made under this rule, confirmed by the dictionary
    #: and the corpus.
    confirmed: int
    #: Nouns (or other fronts) the rule joins it to.
    fronts: int


@dataclass(frozen=True)
class Heads:
    """The measured figures, as ``--heads`` wrote them."""

    corpus_version: str = ""
    rules: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: stem class → spelling → the readings measured.
    halves: dict[str, dict[str, set[str]]] = field(default_factory=dict)
    set_aside: frozenset[str] = frozenset()

    @cached_property
    def reference(self) -> int:
        """The largest pool of fronts: what every rate is counted against."""
        return max((int(rule["fronts"]) for rule in self.rules.values()), default=0)

    @cached_property
    def best(self) -> float:
        """The highest rate measured, over every rule and half: the scale's 100."""
        rates = [
            count / int(rule["fronts"])
            for rule in self.rules.values()
            if rule.get("fronts")
            for latins in rule.get("by_behind", {}).values()
            for count in latins.values()
        ]
        return max(rates, default=0.0)

    def points(self, rate: float) -> int:
        """A rate on the compounds' own scale, 0 to 100."""
        if rate <= 0 or self.best <= 0:
            return 0
        top = math.log10(1 + self.best * self.reference)
        return round(100 * min(1.0, math.log10(1 + rate * self.reference) / top))

    def value(
        self, rule_id: str, behind_fa: str, behind_latin: str
    ) -> HeadValue | None:
        """The value of a compound whose second half is this, or None: not measured."""
        rule = self.rules.get(rule_id)
        if rule is None or not rule.get("fronts"):
            return None
        spelling = normalise(behind_fa)
        if spelling in self.set_aside:
            return None
        latin = behind_latin.lower()
        measured = any(
            latin in self.halves.get(name, {}).get(spelling, ())
            for name in rule.get("stem_classes", ())
        )
        if not measured:
            return None
        count = int(rule.get("by_behind", {}).get(spelling, {}).get(latin, 0))
        fronts = int(rule["fronts"])
        return HeadValue(
            build=self.points(count / fronts), confirmed=count, fronts=fronts
        )


def read(document: dict[str, Any]) -> Heads:
    """The figures from a parsed ``--heads`` file."""
    return Heads(
        corpus_version=str(document.get("corpus_version", "")),
        rules=dict(document.get("rules", {})),
        halves={
            name: {spelling: set(latins) for spelling, latins in found.items()}
            for name, found in document.get("halves", {}).items()
        },
        set_aside=frozenset(document.get("set_aside", {}).get("halves", ())),
    )


def path() -> Path | None:
    """The configured file, if there is one and it exists."""
    configured = os.environ.get(PATH_VARIABLE)
    if not configured:
        return None
    found = Path(configured).expanduser()
    return found if found.is_file() else None


@lru_cache(maxsize=1)
def loaded() -> Heads:
    """The figures, read once. Empty where none is configured: no value at all."""
    found = path()
    if found is None:
        return Heads()
    return read(json.loads(found.read_text(encoding="utf-8")))
