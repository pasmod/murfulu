"""Whether a built form also reads as an inflection of a word we already hold.

**Why this is a scoring concern and not a corpus one.**
:mod:`murfulu.corpus.inflection` is the instrument: it says that رفتی strips to
the stem رفت under a verbal pattern, and that گفتار strips to nothing. It was
built to *measure* S8 and was never asked at request time. This module is what
asks it, once per process, and hands the answer to the ranking.

**The problem it exists for.** Ranking sorts on the corpus count, and where the
lexicon has no reading for a spelling the count may not belong to the word we
built. رفتن's screen opened on رفتی — "you went" — above رفتار and روش, which
are exactly the words this project makes. Both are `unlinked`, and no condition
over the fields we hold separates them. This does separate them, and it is the
only thing that can: it asks whether the letters also read as an inflection of
something the dictionary already has.

**What is done with the answer, and what is not.** The form is **marked**, and
within its evidence bucket it is **ranked below** a form that reads as nothing
but itself. It is never dropped and its count is never hidden — a word the
corpus wrote is evidence whatever it is evidence of, and the standing rule is
that an absent word is ranked down and never removed.

**The 95.5% that share their letters are demoted too, deliberately.** Measured
2026-08-13, 6,730 of 7,047 inflection-shaped attested forms are `shared`,
meaning a derivational rule in the pack writes the same letters: آبادانی is the
indefinite of آبادان *and* the noun. Demoting only the clear ones would leave
رفتی above رفتار — the complaint this exists to answer — untouched, because
*-ی* is also N-095. So both are demoted and the reader is told which kind it
is, because that is a fact about the letters and not a ruling about the word.
Which reading is right stays the linguist's.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from murfulu.corpus.inflection import Analyser, held_from, pack_suffixes
from murfulu.lexicon.store import Lexicon


@dataclass(frozen=True)
class Inflection:
    """What a form reads as, besides the word we built."""

    base: str
    pattern_id: str
    label_fa: str
    #: Rule ids whose affix is spelled the same way. Non-empty means the
    #: letters cannot tell word formation from inflection, which is most of
    #: them.
    shared_with: tuple[str, ...]


@lru_cache(maxsize=1)
def _analyser() -> Analyser | None:
    """One analyser per process, or ``None`` where the lexicon is unreadable.

    Building it is one pass over the snapshot — 43,225 headwords in about a
    third of a second — and a lookup is then a few microseconds, so it is built
    once and shared rather than per request.

    ``None`` is *not checked*, never *not an inflection*. A run without a
    lexicon must leave the ranking exactly as it was rather than silently
    promoting every form.
    """
    try:
        with Lexicon.open() as lexicon:
            held = held_from(lexicon)
    except Exception:  # noqa: BLE001 - no lexicon is a state, not a failure
        return None
    return Analyser(held=held, pack_suffixes=pack_suffixes())


def reset() -> None:
    """Drop the cached analyser. For tests that swap the snapshot."""
    _analyser.cache_clear()


def reading(spelling_fa: str) -> Inflection | None:
    """How this spelling reads as an inflection, or ``None`` if it does not.

    ``None`` covers both *it is not one* and *we could not ask*. The two are
    the same for ranking — neither is a reason to sink a form — and keeping
    them apart here would suggest the caller should treat them differently.
    """
    found = _analyser()
    if found is None:
        return None
    best = found.best(spelling_fa)
    if best is None:
        return None
    return Inflection(
        base=best.base,
        pattern_id=best.pattern.id,
        label_fa=best.pattern.label_fa,
        shared_with=best.shared_with,
    )
