"""Choose among a spelling's readings by counting what the marked corpus chose.

The bank reads ترک three ways — *Tark*, *Tarak*, *tork* — and the letters do
not say which a line needs. But 1.65 % of the corpus's words carry vowel signs
(the editions'), and where the signs leave exactly one of the readings, the
corpus has answered the question: «تُرکِ شیرازی» is *tork*. Those answers,
about 19,000 of them in corpus v17, are what this model counts:

- how often each reading was the answer for the spelling;
- how often, **after the same word**, and **before the same word** — a
  bigram on each side, the n-gram of :mod:`murfulu.behnevis`.

A reading's probability starts from a prior (all readings alike, or a
function word's reading at ``function_prior``), moves towards what the
spelling's answers say, and then towards what the neighbours' say, each in
proportion to how many answers it rests on. The largest probability is the
**confidence**. A spelling the marked corpus never answered keeps its prior:
two readings alike come out at 0.5, which is below any useful threshold, so a
person sees it.

Measured on poets the model never saw (2026-11-14): 79 % right; where the
confidence is 0.9 or more (about half the cases), 95 %.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Answered:
    """One place where the text's own signs leave exactly one reading."""

    spelling: str
    reading: str
    before: str | None = None
    after: str | None = None
    #: Where it came from, for holding out whole poets when measuring.
    author: str = ""


@dataclass
class ChoiceModel:
    """What the marked corpus chose, per spelling and per neighbour."""

    #: Pseudo-answers the prior is worth: how quickly real answers outweigh it.
    prior_strength: float = 1.0
    #: How many answers a neighbour needs before it counts at all.
    min_context: int = 2
    #: The prior of a function word's own reading (rules/function_word_readings.yaml).
    #: Not measured: the function-word list admits a spelling only where that
    #: use "plainly dominates", which this states as a number.
    function_prior: float = 0.9
    alone: dict[str, Counter[str]] = field(default_factory=dict)
    before: dict[str, Counter[str]] = field(default_factory=dict)
    after: dict[str, Counter[str]] = field(default_factory=dict)

    @classmethod
    def train(cls, answered: Iterable[Answered], **settings: Any) -> ChoiceModel:
        """Count the answers."""
        alone: dict[str, Counter[str]] = defaultdict(Counter)
        before: dict[str, Counter[str]] = defaultdict(Counter)
        after: dict[str, Counter[str]] = defaultdict(Counter)
        for one in answered:
            alone[one.spelling][one.reading] += 1
            if one.before:
                before[f"{one.before} {one.spelling}"][one.reading] += 1
            if one.after:
                after[f"{one.spelling} {one.after}"][one.reading] += 1
        return cls(
            alone=dict(alone), before=dict(before), after=dict(after), **settings
        )

    def probabilities(
        self,
        spelling: str,
        candidates: Sequence[str],
        before: str | None = None,
        after: str | None = None,
        function_reading: str | None = None,
    ) -> dict[str, float]:
        """Each candidate's probability for this spelling between these neighbours."""
        unique = list(dict.fromkeys(candidates))
        if not unique:
            return {}
        if len(unique) == 1:
            return {unique[0]: 1.0}
        if function_reading in unique:
            rest = (1 - self.function_prior) / (len(unique) - 1)
            prior = {
                c: self.function_prior if c == function_reading else rest
                for c in unique
            }
        else:
            prior = {c: 1 / len(unique) for c in unique}

        seen = self.alone.get(spelling, Counter())
        total = sum(seen[c] for c in unique)
        probs = {
            c: (seen[c] + self.prior_strength * prior[c])
            / (total + self.prior_strength)
            for c in unique
        }
        for table, key in (
            (self.before, f"{before} {spelling}" if before else None),
            (self.after, f"{spelling} {after}" if after else None),
        ):
            near = table.get(key) if key else None
            n = sum(near[c] for c in unique) if near else 0
            if not near or n < self.min_context:
                continue
            weight = n / (n + 2)
            probs = {c: (1 - weight) * probs[c] + weight * near[c] / n for c in unique}
        norm = sum(probs.values())
        return {c: p / norm for c, p in probs.items()}

    def to_dict(self) -> dict[str, Any]:
        """A plain form for JSON."""
        return {
            "prior_strength": self.prior_strength,
            "min_context": self.min_context,
            "function_prior": self.function_prior,
            "alone": {k: dict(v) for k, v in self.alone.items()},
            "before": {k: dict(v) for k, v in self.before.items()},
            "after": {k: dict(v) for k, v in self.after.items()},
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ChoiceModel:
        """Read back what :meth:`to_dict` wrote."""
        return cls(
            prior_strength=raw["prior_strength"],
            min_context=raw["min_context"],
            function_prior=raw["function_prior"],
            alone={k: Counter(v) for k, v in raw["alone"].items()},
            before={k: Counter(v) for k, v in raw["before"].items()},
            after={k: Counter(v) for k, v in raw["after"].items()},
        )
