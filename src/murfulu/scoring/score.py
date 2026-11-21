"""Two values for a built word: how well it is built, and how far the corpus has it.

**The project lead's choice of 2026-11-21 (second)**, replacing the single
score of the same day. One number mixed two questions, and an unattested word
could reach at most 30 of 100 — so the words this project exists to find, good
coinages the old poetry never needed, sank to the bottom. The project lead:
«if the score is very low because they are not in corpus we might miss them.»
So the two are kept apart:

**How well it is built, 0 to 100** (``build``), from the rules alone and the
same for a word the corpus has and one it does not. It rests on the chain's
weakest rule — the project lead's choice of 2026-11-13, kept: a word is as
well backed as its least backed step. ``r`` is how often that rule builds a
word the corpus has (``types_attested / types_built``, the productivity run).
On a log scale from 1 in 10,000 (0) to 1 in 10 (100):
``100 · clamp((log10(r) + 4) / 3, 0, 1)``. A chain nobody measured counts at
the median measured rate (:func:`stored.neutral_realisation`): silence neither
lifts nor sinks a word.

**How far the corpus has it** (``corpus`` and ``texts``), said as what it is,
not as points:

- ``reading`` — the word under this reading, in ``texts`` texts;
- ``letters`` — only the letters, and nothing says they are another word (not
  the bank's headword under other readings only, not an inflection of a held
  word, not a function word): the word may be there;
- ``other`` — the letters, but as another word's: a function word, the bank's
  other headword, or an inflection;
- ``none`` — not in the corpus;
- ``None`` — the corpus was not asked.

**What it is not.** A rough measurement on a corpus of classical poetry, not a
verdict: a rule that rarely made a word the old poets used can make a good
word today. The productivity figures still credit some letters to the wrong
reading (FINDINGS 2026-11-19). Served with ``confirmed: false``
(FOR_THE_LINGUIST L36). The meaning (how typical the base is for its rule) is
shown beside the two and is in neither; :data:`MEANING_MARKS` folds it to
three dots.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from murfulu.engine.affix import Step
from murfulu.scoring import stored
from murfulu.scoring.attestation import Attestation, Level

#: The build value's scale, as realisation rates: nothing at or below the
#: first, everything at or above the second.
RATE_NONE = 1e-4
RATE_FULL = 1e-1

#: Ours until the linguist rules (FOR_THE_LINGUIST L36).
CONFIRMED = False

#: The typicality bands of `scoring.spread`, folded to three dots for the
#: meaning field: the lowest 30% one, the middle 40% two, the top 30% three.
MEANING_MARKS = {"lowest": 1, "low": 1, "middle": 2, "high": 3, "highest": 3}

#: How strongly each corpus answer speaks for the word, for sorting only:
#: under its reading, then letters that may be it, then another word's
#: letters, then nothing, then not asked.
CORPUS_ORDER = {"reading": 0, "letters": 1, "other": 2, "none": 3, None: 4}


@dataclass(frozen=True)
class RuleRecord:
    """One rule on the chain, with what the productivity run measured."""

    rule_id: str
    affix: str
    #: Words the rule built, and how many of them the corpus has. ``None``
    #: where the run never measured the rule.
    types: int | None
    attested: int | None

    @property
    def rate(self) -> float | None:
        """How often the rule builds a word the corpus has; ``None`` unmeasured."""
        if self.types is None or self.attested is None or self.types <= 0:
            return None
        return self.attested / self.types


@dataclass(frozen=True)
class Score:
    """One form's two values, and the rule the build value rests on."""

    build: int
    corpus: str | None
    texts: int | None
    #: The chain's measured rule with the lowest rate; ``None`` when no rule on
    #: the chain was measured and the build value is the neutral fill.
    weakest: RuleRecord | None
    meaning_mark: int | None
    #: True when an unmeasured step, counted at the median rate, is what
    #: limits the build value — so the sentence can say so.
    unmeasured_step: bool = False

    def as_json(self) -> dict[str, Any]:
        """What the build route serves for one form."""
        weakest = self.weakest
        return {
            "build": self.build,
            "corpus": self.corpus,
            "texts": self.texts,
            "confirmed": CONFIRMED,
            "weakest_rule": None
            if weakest is None
            else {
                "rule_id": weakest.rule_id,
                "affix": weakest.affix,
                "types": weakest.types,
                "attested": weakest.attested,
            },
            "meaning_mark": self.meaning_mark,
            "unmeasured_step": self.unmeasured_step,
        }


def corpus_kind(found: Attestation | None, inflected: bool = False) -> str | None:
    """What the corpus says about the word, as one of five answers."""
    if found is None:
        return None
    if found.level is Level.NONE:
        return "none"
    if not found.credited:
        return "other"
    if found.level is Level.READING:
        return "reading"
    return "other" if inflected else "letters"


def build_points(rate: float | None) -> int:
    """How well built, 0 to 100, from a realisation rate.

    ``None`` — nothing on the chain measured — takes the median measured rate,
    and where nothing at all was measured, the middle of the scale.
    """
    if rate is None:
        rate = stored.neutral_realisation()
        if rate is None:
            return 50
    if rate <= 0:
        return 0
    span = math.log10(RATE_FULL) - math.log10(RATE_NONE)
    share = (math.log10(rate) - math.log10(RATE_NONE)) / span
    return round(100 * max(0.0, min(1.0, share)))


def chain_of(steps: Sequence[Step]) -> list[RuleRecord]:
    """Each step's rule with what the configured productivity run measured."""
    measured = stored.loaded()
    chain = []
    for step in steps:
        row = measured.for_rule(step.rule_id) or {}
        counted = bool(row.get("measured"))
        chain.append(
            RuleRecord(
                rule_id=step.rule_id,
                affix=step.affix,
                types=row.get("types_built") if counted else None,
                attested=row.get("types_attested") if counted else None,
            )
        )
    return chain


def weakest(chain: Sequence[RuleRecord]) -> RuleRecord | None:
    """The measured rule with the lowest rate; the first of equals."""
    measured = [one for one in chain if one.rate is not None]
    if not measured:
        return None
    return min(measured, key=lambda one: one.rate or 0.0)


def assess(
    found: Attestation | None,
    chain: Sequence[RuleRecord],
    inflected: bool = False,
    typicality_band: str | None = None,
) -> Score:
    """The two values of one form, from its evidence and its chain's rules."""
    low = weakest(chain)
    # An unmeasured rule on the chain counts at the median measured rate, so
    # it can be the weakest too: skipping it gave کمروه, built with *kam-*
    # which the run never measured, a full 100 from its one measured step.
    neutral = stored.neutral_realisation()
    unmeasured = any(one.rate is None for one in chain)
    if (
        unmeasured
        and neutral is not None
        and (low is None or (low.rate is not None and neutral < low.rate))
    ):
        low = None
    limited = unmeasured and low is None
    rate = low.rate if low else None
    return Score(
        build=build_points(rate),
        corpus=corpus_kind(found, inflected),
        texts=None if found is None else found.doc_count,
        weakest=low,
        meaning_mark=MEANING_MARKS.get(typicality_band or ""),
        unmeasured_step=limited,
    )


def order(score: Score) -> tuple[int, int, int]:
    """The default order, best first: how well built, then the corpus.

    **Built first** (the project lead's choice of 2026-11-21): a coiner looking
    for a word wants the best-made ones whether or not the poets used them,
    and the corpus column says which are known. Between equal build values the
    word the corpus has under its reading comes first, then by texts.
    """
    return (-score.build, CORPUS_ORDER[score.corpus], -(score.texts or 0))
