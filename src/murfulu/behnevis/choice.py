"""Choose among a spelling's readings by counting what the marked corpus chose.

The bank reads ترک three ways — *Tark*, *Tarak*, *tork* — and the letters do
not say which a line needs. But 1.65 % of the corpus's words carry vowel signs
(the editions'), and where the signs leave exactly one of the readings, the
corpus has answered the question: «تُرکِ شیرازی» is *tork*. Those answers,
14,341 of them in corpus v17's Persian lines, are what this model counts:

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

Measured on poets the model never saw (2026-11-14): 81 % right; where the
confidence is 0.9 or more (about half the cases), 94 %.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any


def ranked(probs: dict[str, float]) -> list[tuple[str, float]]:
    """Readings likeliest first; a tie goes to the alphabetically first."""
    return sorted(probs.items(), key=lambda kv: (-kv[1], kv[0]))


@dataclass(frozen=True)
class Answered:
    """One place where the text's own signs leave exactly one reading."""

    spelling: str
    reading: str
    before: str | None = None
    after: str | None = None
    #: Where it came from, for holding out whole poets when measuring.
    author: str = ""
    #: A person chose it on the reading screen, rather than an edition's signs
    #: leaving it. Counted apart: it may move even a function word.
    by_person: bool = False


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
    #: The same three, for readings people picked on the reading screen.
    #: Editions mark a function word where it is the exception, so their
    #: marks never move its prior; a person's pick does (the review of
    #: 2026-11-14): به picked as *Beh* between the same words often enough
    #: becomes *Beh* there.
    person_alone: dict[str, Counter[str]] = field(default_factory=dict)
    person_before: dict[str, Counter[str]] = field(default_factory=dict)
    person_after: dict[str, Counter[str]] = field(default_factory=dict)

    @classmethod
    def train(cls, answered: Iterable[Answered], **settings: Any) -> ChoiceModel:
        """Count the answers."""
        tables: dict[bool, tuple[dict[str, Counter[str]], ...]] = {
            flag: (defaultdict(Counter), defaultdict(Counter), defaultdict(Counter))
            for flag in (False, True)
        }
        for one in answered:
            alone, before, after = tables[one.by_person]
            alone[one.spelling][one.reading] += 1
            if one.before:
                before[f"{one.before} {one.spelling}"][one.reading] += 1
            if one.after:
                after[f"{one.spelling} {one.after}"][one.reading] += 1
        corpus, people = tables[False], tables[True]
        return cls(
            alone=dict(corpus[0]),
            before=dict(corpus[1]),
            after=dict(corpus[2]),
            person_alone=dict(people[0]),
            person_before=dict(people[1]),
            person_after=dict(people[2]),
            **settings,
        )

    def probabilities(
        self,
        spelling: str,
        candidates: Sequence[str],
        before: str | None = None,
        after: str | None = None,
        function_reading: str | None = None,
        function_prior: float | None = None,
    ) -> dict[str, float]:
        """Each candidate's probability for this spelling between these neighbours.

        ``function_prior`` overrides the model's for one call: the verse rule
        for و starts at its own, lower confidence.
        """
        unique = list(dict.fromkeys(candidates))
        if not unique:
            return {}
        if len(unique) == 1:
            return {unique[0]: 1.0}
        if function_reading in unique:
            # A function word keeps its prior against the editions' marks:
            # they mark به where it is *bah*, almost never where it is *be*,
            # so its marked places are the exceptions, and counting them made
            # به *bah* (2026-11-14). People's picks still move it, below.
            start = self.function_prior if function_prior is None else function_prior
            rest = (1 - start) / (len(unique) - 1)
            probs = {c: start if c == function_reading else rest for c in unique}
        else:
            prior = {c: 1 / len(unique) for c in unique}
            seen = self.alone.get(spelling, Counter())
            total = sum(seen[c] for c in unique)
            probs = {
                c: (seen[c] + self.prior_strength * prior[c])
                / (total + self.prior_strength)
                for c in unique
            }
            probs = self._near(
                probs,
                unique,
                self.before,
                self.after,
                spelling,
                before,
                after,
                self.min_context,
            )
        probs = self._near(
            probs,
            unique,
            self.person_before,
            self.person_after,
            spelling,
            before,
            after,
            1,
            self.person_alone,
        )
        norm = sum(probs.values())
        return {c: p / norm for c, p in probs.items()}

    @staticmethod
    def _near(
        probs: dict[str, float],
        unique: list[str],
        before_table: dict[str, Counter[str]],
        after_table: dict[str, Counter[str]],
        spelling: str,
        before: str | None,
        after: str | None,
        needed: int,
        alone_table: dict[str, Counter[str]] | None = None,
    ) -> dict[str, float]:
        """Move the probabilities towards what these tables counted.

        Each table weighs in proportion to how many answers it holds for the
        candidates (n / (n + 2)), and only from ``needed`` answers on. People's
        picks pass their own table for the spelling alone as well.
        """
        steps: list[tuple[dict[str, Counter[str]], str | None]] = []
        if alone_table is not None:
            steps.append((alone_table, spelling))
        steps += [
            (before_table, f"{before} {spelling}" if before else None),
            (after_table, f"{spelling} {after}" if after else None),
        ]
        for table, key in steps:
            near = table.get(key) if key else None
            n = sum(near[c] for c in unique) if near else 0
            if not near or n < needed:
                continue
            weight = n / (n + 2)
            probs = {c: (1 - weight) * probs[c] + weight * near[c] / n for c in unique}
        return probs

    def to_dict(self) -> dict[str, Any]:
        """A plain form for JSON."""
        return {
            "prior_strength": self.prior_strength,
            "min_context": self.min_context,
            "function_prior": self.function_prior,
            "alone": {k: dict(v) for k, v in self.alone.items()},
            "before": {k: dict(v) for k, v in self.before.items()},
            "after": {k: dict(v) for k, v in self.after.items()},
            "person_alone": {k: dict(v) for k, v in self.person_alone.items()},
            "person_before": {k: dict(v) for k, v in self.person_before.items()},
            "person_after": {k: dict(v) for k, v in self.person_after.items()},
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
            person_alone={
                k: Counter(v) for k, v in raw.get("person_alone", {}).items()
            },
            person_before={
                k: Counter(v) for k, v in raw.get("person_before", {}).items()
            },
            person_after={
                k: Counter(v) for k, v in raw.get("person_after", {}).items()
            },
        )
