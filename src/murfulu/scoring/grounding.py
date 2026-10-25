"""Whether a chain rests on written ground, step by step.

Measured on رفتن, and the reason this module exists: of its 510 words, 476 are
two-step, and **231 of those are built on an intermediate form nobody ever
wrote** — *Raftbān* is unattested, and the engine then builds 67 more words on
top of it. Three unwritten step-one forms account for over 150 step-two forms.

A form's own attestation already ranks the list. What it cannot see is the
ground under a deeper form: *Raftāri* (attested, 122 occurrences) and
*DošRaftbān* (built on the unwritten *Raftbān*) are both two-step words, and
at level *none* a form built on *Raftār* — written 1,206 times — still stands
on firmer ground than one built on air.

**This is evidence, not a verdict.** A chain through an unwritten base is how
genuinely new words get coined, and the corpus is a thousand years of poetry —
*pišrafte* is fine Persian and absent from it. So the answer ranks and is
shown; nothing is hidden or refused, the same rule as everywhere else.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from murfulu.engine.affix import Step

#: Answers whether one Latin form counts as written ground. The caller decides
#: what that means — usually "attested in the corpus, or one of the bases the
#: generation started from".
IsGrounded = Callable[[str], bool]


class _StoredPath(Protocol):
    """What :func:`stored_grounded` needs of a stored path.

    Declared here rather than importing ``scoring.records``, which imports
    this: the shape is two attributes and naming them is cheaper than a cycle.
    """

    @property
    def base_latin(self) -> str: ...

    @property
    def depth(self) -> int: ...


def path_grounded(path: Sequence[Step], is_grounded: IsGrounded) -> bool:
    """Whether every intermediate step of one path is written ground.

    The first step's base is what the generation started from — a dictionary
    stem or the word itself — so only the bases of the later steps are
    intermediates. A one-step path has none and is grounded by definition.
    """
    return all(is_grounded(step.base_latin) for step in path[1:])


def stored_grounded(
    paths: Sequence[_StoredPath], is_grounded: IsGrounded
) -> bool | None:
    """The same question of a **stored** derivation, which keeps less.

    A stored path records the base of its *last* step and not of the ones in
    between, so it can answer for one and two steps and no further: at two
    steps the base of the last step *is* the only intermediate. The precompute
    runs at two, which is why this is enough for the index.

    Three answers, and the third is the point. A path deeper than two cannot be
    read this way, so a form whose every route is that deep comes back
    ``None`` — *not established* — rather than ``False``. A stored ``False``
    would say the corpus was asked and answered no.
    """
    unreadable = False
    for path in paths:
        if path.depth <= 1:
            # Nothing in between. The base it started from is the dictionary's
            # own, and judging that would judge the dictionary.
            return True
        if path.depth == 2:
            if is_grounded(path.base_latin):
                return True
        else:
            unreadable = True
    return None if unreadable or not paths else False


def grounded(paths: Sequence[Sequence[Step]], is_grounded: IsGrounded) -> bool:
    """Whether **some** path to this form rests on written ground throughout.

    Any grounded path is enough: a form reachable both through *Raftār* and
    through *Raftbān* is grounded, because the first route is real. Only a form
    every one of whose routes passes over unwritten ground comes back False.
    """
    return any(path_grounded(path, is_grounded) for path in paths)
