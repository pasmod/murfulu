"""How much evidence a built word has, said as one score from 0 to 100.

**The project lead's choice of 2026-11-21**, replacing the three levels of
2026-11-13 (familiar, well-formed, weakly backed). The levels read as names a
reader had to learn, and a list could not be sorted or filtered by them in any
useful way. A score can be: the build screen sorts on it and filters by its
range. It is built from the same evidence the levels were, in two parts that
the screen shows separately behind «شواهد»:

**The corpus, up to 70 points.**

- The corpus has the word **under this reading**: ``30 + 40 · t``, where
  ``t = min(1, log10(texts) / 3)``. One text gives 30, ten give 43, a hundred
  57, a thousand or more 70.
- The corpus has **only the letters**, and nothing says they are another
  word — not the bank's headword under other readings only (a reading in
  another case or a recorded alternate is this word), not an inflection of a
  held word, not a function word: half of that, ``15 + 20 · t``.
- Otherwise 0: not written, or written as another word, whose count is not
  this word's (DECISIONS 2026-11-19).

**The rule, up to 30 points**, from the chain's weakest rule — the project
lead's choice of 2026-11-13, kept: a word is as well backed as its least
backed step. ``r`` is how often that rule builds a word the corpus has
(``types_attested / types_built``, the productivity run). On a log scale
from 1 in 10,000 (0 points) to 1 in 10 (30 points):
``30 · clamp((log10(r) + 4) / 3, 0, 1)``. A rule nobody measured counts at
the median of the measured ones (:func:`stored.neutral_realisation`), so
silence neither lifts nor sinks a word.

**Why 70 and 30.** Any word the corpus has under its reading (30 or more)
then stands above every word it does not have (30 at most): what the corpus
shows outranks what the rules promise, as it did under the levels. The
corpus line is 70 at a thousand texts so that the commonest words do not all
tie.

**What it is not.** A rough measurement on a corpus of classical poetry, not a
verdict on the word. A low score means little evidence, never a wrong word: a
modern word can be missing from old poetry. The figures in it are the
productivity run's, which still credit some letters to the wrong reading
(FINDINGS 2026-11-19). Served with ``confirmed: false``, like the levels were
(FOR_THE_LINGUIST L36). **No score at all** where the corpus was not asked: a
familiar word cannot be told from a new one then, and a number would be a
guess.

The meaning (how typical the base is for its rule) is shown beside the score
and is not part of it, as before; :data:`MEANING_MARKS` folds it to three dots.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from murfulu.engine.affix import Step
from murfulu.scoring import stored
from murfulu.scoring.attestation import Attestation, Level

#: The two parts' ceilings. Their sum is the scale.
CORPUS_MAX = 70
RULE_MAX = 30
#: What a word the corpus has under its reading gets for being there at all.
CORPUS_FLOOR = 30
#: Texts at which the corpus part is full: log10(1000) = 3.
TEXTS_FULL = 1000
#: The rule part's scale, as realisation rates: nothing at or below the first,
#: everything at or above the second.
RATE_NONE = 1e-4
RATE_FULL = 1e-1

#: Ours until the linguist rules (FOR_THE_LINGUIST L36).
CONFIRMED = False

#: The typicality bands of `scoring.spread`, folded to three dots for the
#: meaning field: the lowest 30% one, the middle 40% two, the top 30% three.
MEANING_MARKS = {"lowest": 1, "low": 1, "middle": 2, "high": 3, "highest": 3}


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
    """One form's score, its two parts, and the rule the rule part rests on."""

    value: int | None
    corpus: float | None
    rule: float
    #: The chain's measured rule with the lowest rate; ``None`` when no rule on
    #: the chain was measured and the rule part is the neutral fill.
    weakest: RuleRecord | None
    meaning_mark: int | None

    def as_json(self) -> dict[str, Any]:
        """What the build route serves for one form."""
        weakest = self.weakest
        return {
            "value": self.value,
            "corpus": None if self.corpus is None else round(self.corpus),
            "rule": round(self.rule),
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
        }


def _texts_share(texts: int) -> float:
    """0 at one text, 1 at :data:`TEXTS_FULL` and above, on a log scale."""
    return min(1.0, math.log10(max(texts, 1)) / math.log10(TEXTS_FULL))


def _letters_are_ours(found: Attestation) -> bool:
    """Whether a spelling-level count may be this word's.

    Not when the letters are a function word, and not when the bank reads them
    only as other words (``headword_homograph``). That test already counts a
    reading in another case (گفت is *Goft* to us, *goft* in the lexicon) and an
    alternate the bank records (*jehān* beside *jahān*) as this word, so it is
    asked here rather than repeated on ``other_readings``, which lists only the
    bank's main readings.
    """
    return found.credited


def corpus_points(found: Attestation | None, inflected: bool = False) -> float | None:
    """The corpus part, 0 to :data:`CORPUS_MAX`; ``None`` if not asked."""
    if found is None:
        return None
    if found.level is Level.READING and found.credited:
        return CORPUS_FLOOR + (CORPUS_MAX - CORPUS_FLOOR) * _texts_share(
            found.doc_count
        )
    if found.level is Level.SPELLING and not inflected and _letters_are_ours(found):
        return (
            CORPUS_FLOOR + (CORPUS_MAX - CORPUS_FLOOR) * _texts_share(found.doc_count)
        ) / 2
    return 0.0


def rule_points(rate: float | None) -> float:
    """The rule part, 0 to :data:`RULE_MAX`, from a realisation rate.

    ``None`` — nothing on the chain measured — takes the median measured rate,
    and where nothing at all was measured, the middle of the scale.
    """
    if rate is None:
        rate = stored.neutral_realisation()
        if rate is None:
            return RULE_MAX / 2
    if rate <= 0:
        return 0.0
    span = math.log10(RATE_FULL) - math.log10(RATE_NONE)
    share = (math.log10(rate) - math.log10(RATE_NONE)) / span
    return RULE_MAX * max(0.0, min(1.0, share))


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
    """The score of one form, from its evidence and its chain's rules."""
    low = weakest(chain)
    corpus = corpus_points(found, inflected)
    rule = rule_points(low.rate if low else None)
    return Score(
        value=None if corpus is None else round(corpus + rule),
        corpus=corpus,
        rule=rule,
        weakest=low,
        meaning_mark=MEANING_MARKS.get(typicality_band or ""),
    )


def order(value: int | None) -> int:
    """Sort key, best first. No score sorts last: there is nothing to rank by.

    Only a whole answer goes without a score — the corpus is asked for every
    form of a request or for none — so this never puts an unscored word below
    a scored one in the same list.
    """
    return -(value if value is not None else -1)
