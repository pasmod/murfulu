"""How plausible a built word is, said as one of three levels.

The build screen showed three separate figures for every word — the corpus
count, how often the chain's rules make words the corpus has, how typical the
base is for its rule — and a reader who is not a linguist could not tell from
them, at a glance, whether a word is one Persian already has, a well-made
coinage, or a long shot. **The project lead chose on 2026-11-13** to say it as
one of three levels, with a sentence of reason, and to keep the three figures
behind a button. This module decides the level; the screen writes the words.

=====  ===============  ====================================================
level  name             when
=====  ===============  ====================================================
3      familiar         the corpus has the word *under this reading* in at
                        least :data:`MIN_TEXTS` texts
2      well-formed      not familiar, and no rule on the chain is in the
                        lowest third of all measured rules
1      weakly backed    not familiar, and some rule on the chain is in the
                        lowest third — it almost never makes a word the
                        corpus has
=====  ===============  ====================================================

**Unconfirmed.** The names, the ten texts and the lowest third are ours,
built and served while the linguist's ruling is open (FOR_THE_LINGUIST L36).
The response says so with ``confirmed: false``. When he rules: the names and
their explanations live in `web/src/screens/build/levels.ts`; the ten texts
are :data:`MIN_TEXTS` here, said again there; the lowest third is the
productivity run's division (`Productivity.bands`), so another line for
*weakly backed* is a rate tested here in place of the band.

**What it deliberately does not use.** Whether the chain stands on a written
intermediate: the project lead moved that test down the ranking on 2026-08-17
because it is wrong about prefixed verbs (*bāzguyande*). A spelling-level hit
does not make a word familiar either — دانست, in 1,273 texts, is "he knew", not
the noun the rule built. And *not measured* is never a level: an unasked
corpus or a chain with no measured rule gives no level at all, and the ranking
puts that between well-formed and weakly backed, never at the bottom.

The three **marks** are the figures behind the button, each as up to three
dots: the corpus by texts (1–9, 10–999, 1,000 and more), the rule by the third
its weakest rule falls in, the meaning by the typicality band (lowest 30%,
middle 40%, top 30%). They are decided here so the thresholds live in one
place.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from murfulu.engine.affix import Step
from murfulu.scoring import stored
from murfulu.scoring.attestation import Attestation, Level

FAMILIAR = 3
WELL_FORMED = 2
WEAK = 1

#: Texts a word must appear in, under its own reading, to be familiar.
MIN_TEXTS = 10

#: The levels are ours until the linguist rules (FOR_THE_LINGUIST L36).
CONFIRMED = False

#: The thirds `scoring.productivity` puts each measured rule in.
_BAND_RANK = {"low": 1, "middle": 2, "high": 3}

#: The typicality bands of `scoring.spread`, folded to three marks: the lowest
#: 30% one, the middle 40% two, the top 30% three.
_MEANING_MARKS = {"lowest": 1, "low": 1, "middle": 2, "high": 3, "highest": 3}

#: Where each level sorts. Unknown sits above weakly backed: silence must not
#: sink a word below one that was measured and found weak.
_ORDER = {FAMILIAR: 0, WELL_FORMED: 1, None: 2, WEAK: 3}


@dataclass(frozen=True)
class RuleRecord:
    """One rule on the chain, with what the productivity run measured."""

    rule_id: str
    affix: str
    #: Words the rule built, and how many of them the corpus has. ``None``
    #: where the run never measured the rule.
    types: int | None
    attested: int | None
    #: ``low``, ``middle`` or ``high``; ``None`` where not measured.
    band: str | None


@dataclass(frozen=True)
class Assessment:
    """The level of one form, and what it rests on."""

    level: int | None
    #: The chain's weakest measured rule — the one the reason sentence names.
    weakest: RuleRecord | None
    corpus_mark: int | None
    rule_mark: int | None
    meaning_mark: int | None

    def as_json(self) -> dict[str, Any]:
        """What the build route serves for one form."""
        weakest = self.weakest
        return {
            "level": self.level,
            "confirmed": CONFIRMED,
            "weakest_rule": None
            if weakest is None
            else {
                "rule_id": weakest.rule_id,
                "affix": weakest.affix,
                "types": weakest.types,
                "attested": weakest.attested,
                "band": weakest.band,
            },
            "marks": {
                "corpus": self.corpus_mark,
                "rule": self.rule_mark,
                "meaning": self.meaning_mark,
            },
        }


def corpus_mark(found: Attestation | None) -> int | None:
    """Up to three dots for the corpus: 0 not in it, then by texts.

    ``None`` where nothing can be said: the corpus was not asked, or the
    letters are a function word's and their count is that word's.
    """
    if found is None or found.function_word:
        return None
    if found.level is Level.NONE:
        return 0
    if found.doc_count >= 1000:
        return 3
    return 2 if found.doc_count >= MIN_TEXTS else 1


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
                band=measured.band(step.rule_id),
            )
        )
    return chain


def weakest(chain: Sequence[RuleRecord]) -> RuleRecord | None:
    """The measured rule in the lowest third; the first of equals."""
    measured = [one for one in chain if one.band in _BAND_RANK]
    if not measured:
        return None
    return min(measured, key=lambda one: _BAND_RANK[one.band or ""])


def assess(
    found: Attestation | None,
    chain: Sequence[RuleRecord],
    typicality_band: str | None = None,
) -> Assessment:
    """The level of one form, from its evidence and its chain's rules."""
    low = weakest(chain)
    rule_mark = _BAND_RANK[low.band or ""] if low else None
    meaning_mark = _MEANING_MARKS.get(typicality_band or "")
    if found is None:
        # The corpus was not asked: a familiar word cannot be told from a new
        # one, so no level is given rather than a guess.
        level: int | None = None
    elif (
        found.level is Level.READING
        and not found.function_word
        and found.doc_count >= MIN_TEXTS
    ):
        level = FAMILIAR
    elif low is None:
        level = None
    else:
        level = WEAK if low.band == "low" else WELL_FORMED
    return Assessment(
        level=level,
        weakest=low,
        corpus_mark=corpus_mark(found),
        rule_mark=rule_mark,
        meaning_mark=meaning_mark,
    )


def order(level: int | None) -> int:
    """Where a level sorts: familiar first, weakly backed last."""
    return _ORDER.get(level, _ORDER[None])
