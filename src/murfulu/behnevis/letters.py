"""Guess the Behnevis of a word the bank does not hold, letter by letter.

**Learning.** Every word of the bank is lined up with its reading, letter by
letter (:func:`align`): each letter takes the Latin it stands for, plus the
short vowel the script leaves unwritten after it, if any. ت in *tork* takes
*to*, ر takes *r*, ک takes *k*. Then, for every letter, the model counts which
piece of Latin it took **in which surroundings**: the letter alone, with one
neighbour on each side, with two, with three. That is an n-gram model over
letters — counting, not a neural network.

**Guessing.** For each letter of a new word the model looks for the widest
surroundings it has seen at least ``min_count`` times and takes the piece of
Latin seen most often there. Its share of those cases is that letter's
probability; the word's **confidence** is the product over its letters. A
word whose every letter was decided by a clear majority comes out near 1;
one hard letter brings it down.

**What it cannot know.** Behnevis writes nouns with a capital; nothing in the
letters says which word is a noun, so a guess is lower case. Measured on the
bank's own words, held out from learning (2026-11-14): about 55 % of words
come out right as a whole; where the confidence is 0.7 or more, 84 %.
"""

from __future__ import annotations

import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from murfulu.corpus.wordtypes import normalise
from murfulu.search.harakat import _UNWRITTEN, _VOWELS, LETTERS

#: What a letter may stand for, as :mod:`murfulu.search.harakat` has it, with
#: the mark Behnevis writes for ع and ء (*tabˈ*, *masˈul*). The reading screen
#: does not need it: a mark is never a vowel.
SPELLED: dict[str, tuple[str, ...]] = {
    **LETTERS,
    "ع": (*LETTERS["ع"], "ˈ"),
    "ء": (*LETTERS["ء"], "ˈ"),
    "ئ": (*LETTERS["ئ"], "ˈ"),
}

#: Left and right of a word, so the first and last letters have surroundings.
EDGE = "#"

ZWNJ = "‌"


def latin_key(reading: str) -> str:
    """A reading as the model compares it: lower case, no accents."""
    plain = unicodedata.normalize("NFC", reading).casefold()
    plain = plain.replace("é", "e").replace("í", "i")
    return "".join(ch for ch in plain if ch.isalpha() or ch == "ˈ")


def shape(spelling: str) -> tuple[str, ...]:
    """A spelling's letters, normalised as the corpus counts them, without joiners."""
    return tuple(ch for ch in normalise(spelling) if ch not in (ZWNJ, " "))


def align(letters: tuple[str, ...], latin: str) -> list[str] | None:
    """The piece of a reading each letter stands for, or None if none lines up.

    A piece is the letter's own Latin (possibly nothing, possibly doubled)
    and then, optionally, one unwritten short vowel. When several alignments
    exist, the one found first is taken; they spell the same reading.
    """
    if any(letter not in SPELLED for letter in letters):
        return None
    stack: list[tuple[int, int, tuple[str, ...]]] = [(0, 0, ())]
    seen: set[tuple[int, int]] = set()
    while stack:
        i, j, pieces = stack.pop()
        if i == len(letters):
            if j == len(latin):
                return list(pieces)
            continue
        for spelled in SPELLED[letters[i]]:
            ways = [spelled]
            if spelled and spelled[0] not in _VOWELS and spelled != "ˈ":
                ways.append(spelled[0] + spelled)  # a doubled letter
            for way in ways:
                if not latin.startswith(way, j):
                    continue
                k = j + len(way)
                nexts = [(k, way)]
                if k < len(latin) and latin[k] in _UNWRITTEN:
                    nexts.append((k + 1, way + latin[k]))
                for n, piece in nexts:
                    if (i + 1, n) in seen:
                        continue
                    seen.add((i + 1, n))
                    stack.append((i + 1, n, (*pieces, piece)))
    return None


def _around(letters: tuple[str, ...], i: int, width: int) -> str:
    """The letter at ``i`` with ``width`` neighbours on each side, as a key."""
    padded = (EDGE,) * width + letters + (EDGE,) * width
    return "".join(padded[i : i + 2 * width + 1])


@dataclass
class LetterModel:
    """Counts of what each letter stood for, in surroundings of every width."""

    width: int = 3
    min_count: int = 2
    #: One table per width: surroundings → piece of Latin → how often.
    tables: list[dict[str, Counter[str]]] = field(default_factory=list)
    #: How many of the training pairs lined up, and how many did not.
    trained_on: int = 0
    not_aligned: int = 0

    @classmethod
    def train(
        cls, pairs: Iterable[tuple[str, str]], width: int = 3, min_count: int = 2
    ) -> LetterModel:
        """Learn from (spelling, reading) pairs, such as the word bank's."""
        tables: list[dict[str, Counter[str]]] = [
            defaultdict(Counter) for _ in range(width + 1)
        ]
        trained = missed = 0
        seen: set[tuple[tuple[str, ...], str]] = set()
        for spelling, reading in pairs:
            letters, latin = shape(spelling), latin_key(reading)
            if not letters or not latin or (letters, latin) in seen:
                continue
            seen.add((letters, latin))
            pieces = align(letters, latin)
            if pieces is None:
                missed += 1
                continue
            trained += 1
            for i, piece in enumerate(pieces):
                for w in range(width + 1):
                    tables[w][_around(letters, i, w)][piece] += 1
        return cls(width, min_count, [dict(t) for t in tables], trained, missed)

    def guess(self, spelling: str) -> tuple[str, float] | None:
        """The likeliest reading and how sure; None if a letter is unknown."""
        letters = shape(spelling)
        if not letters or any(letter not in SPELLED for letter in letters):
            return None
        out: list[str] = []
        confidence = 1.0
        for i in range(len(letters)):
            counts: Counter[str] | None = None
            for w in range(self.width, -1, -1):
                found = self.tables[w].get(_around(letters, i, w))
                if found and (sum(found.values()) >= self.min_count or w == 0):
                    counts = found
                    break
            if not counts:
                return None
            piece, n = counts.most_common(1)[0]
            out.append(piece)
            confidence *= n / sum(counts.values())
        return "".join(out), confidence

    def to_dict(self) -> dict[str, Any]:
        """A plain form for JSON."""
        return {
            "width": self.width,
            "min_count": self.min_count,
            "trained_on": self.trained_on,
            "not_aligned": self.not_aligned,
            "tables": [{k: dict(v) for k, v in t.items()} for t in self.tables],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> LetterModel:
        """Read back what :meth:`to_dict` wrote."""
        return cls(
            raw["width"],
            raw["min_count"],
            [{k: Counter(v) for k, v in t.items()} for t in raw["tables"]],
            raw.get("trained_on", 0),
            raw.get("not_aligned", 0),
        )
