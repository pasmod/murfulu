"""Whether a word's own vowel signs rule a Behnevis reading out.

Many lines in the corpus carry harakat: Hafez's «تُرکِ شیرازی» has a damma on
its ت. The bank has three readings of ترک — *Tarak*, *Tark* and *tork* — and
the damma leaves only *tork*. The reading screen shows every reading, and
since 2026-11-14 (the project lead's choice, OPEN_QUESTIONS S44) it shows the
ones the text's own signs rule out paler: still there, because an edition's
harakat are sometimes wrong, but no longer equal.

**How.** The written word is lined up letter by letter against the reading:
each Persian letter stands for one of a few Latin spellings (ت for *t*, و for
*v*, *u*, *o*, *ow* or nothing), and a short vowel the script does not write —
*a*, *e*, *o* — may follow any letter. A sign then says which vowel comes
straight after its letter:

- fatha: *a* or *ā* (or the diphthongs *ow*, *ey*, which a fatha writes too);
- kasra: *e* or *i*;
- damma: *o* or *u*;
- sukun: no unwritten vowel. A vowel the next letter writes is allowed: in
  «سَرْآمد» the آ after the sukun is *sarāmad*'s *ā* (the review of
  2026-11-14).

A reading is **against** the signs when it can be lined up with the letters
but not with the letters and their signs. When it cannot be lined up at all —
a spelling this table does not foresee — nothing is said: the reading is
shown as before. Every choice here leans the same way, towards saying
nothing: a reading greyed out wrongly would mislead the reader, one left
alone only leaves things as they were.

**The last letter's signs are not read.** A kasra there is the ezafe
(تُرکِ شیرازی, دلِ من), not part of the word, and a tanwin or a sukun there
says nothing about the vowels inside it. A shadda is read only as allowing a
doubled letter, never as requiring one: Behnevis writes most doubled letters
single.
"""

from __future__ import annotations

import unicodedata
from functools import lru_cache

#: Arabic letters folded into Persian ones, exactly as the corpus counts them.
from murfulu.corpus.wordtypes import _FOLD

FATHA = "َ"
DAMMA = "ُ"
KASRA = "ِ"
SUKUN = "ْ"
SHADDA = "ّ"

#: The signs read here. Every other combining mark — tanwin, the hamza of
#: خانهٔ, a superscript alef, the tatweel — is passed over.
_READ = {FATHA, DAMMA, KASRA, SUKUN, SHADDA}

ZWNJ = "‌"


#: Each letter and the Latin it may stand for in Behnevis, lower case. The
#: vowel letters carry many: و is *v* in ورد, *u* in دور, *o* in تو, *ow* in
#: نو, and silent in خواب; ی is *y*, *i*, *ey*, and *iy* in زیادی.
LETTERS: dict[str, tuple[str, ...]] = {
    "ا": ("ā", "a", "e", "o", ""),
    "آ": ("ā", "ˈā"),  # Behnevis marks a hamza before it: *maˈāl*
    "ب": ("b",),
    "پ": ("p",),
    "ت": ("t",),
    "ث": ("s",),
    "ج": ("j",),
    "چ": ("č",),
    "ح": ("h",),
    "خ": ("x",),
    "د": ("d",),
    "ذ": ("z",),
    "ر": ("r",),
    "ز": ("z",),
    "ژ": ("ž",),
    "س": ("s",),
    "ش": ("š",),
    "ص": ("s",),
    "ض": ("z",),
    "ط": ("t",),
    "ظ": ("z",),
    "ع": ("", "a", "e", "o", "ˈ"),  # ˈ, the mark Behnevis writes: *tabˈ*
    "غ": ("q",),
    "ف": ("f",),
    "ق": ("q",),
    "ک": ("k",),
    "گ": ("g",),
    "ل": ("l",),
    "م": ("m",),
    "ن": ("n",),
    "و": ("v", "u", "o", "ow", "uv", "ov", "w", ""),
    "ه": ("h", "e", "a", ""),
    "ی": ("y", "i", "ey", "iy", "e", "ā", "ay", ""),
    "ئ": ("y", "", "e", "ˈ"),
    "ء": ("", "y", "ˈ"),
}

#: Short vowels the script leaves unwritten, which may follow any letter.
_UNWRITTEN = ("a", "e", "o")

_VOWELS = set("aāeiou")

#: What may come straight after a letter carrying each sign.
_AFTER = {
    FATHA: ("a", "ā", "ow", "ey", "aw", "ay"),
    KASRA: ("e", "i"),
    DAMMA: ("o", "u"),
}


def _latin(reading: str) -> str:
    """A reading lower-cased, its accents and stress marks taken off."""
    plain = unicodedata.normalize("NFC", reading).casefold()
    plain = plain.replace("é", "e").replace("í", "i")
    return "".join(ch for ch in plain if ch.isalpha())


def letters(written: str) -> tuple[tuple[str, frozenset[str]], ...]:
    """A written word's letters, each with the signs written on it."""
    found: list[tuple[str, set[str]]] = []
    for char in unicodedata.normalize("NFC", written):
        if unicodedata.combining(char) or char == "ـ":
            if char in _READ and found:
                found[-1][1].add(char)
            continue
        if char == ZWNJ or not char.strip():
            continue
        found.append((char.translate(_FOLD), set()))
    return tuple((letter, frozenset(signs)) for letter, signs in found)


def has_signs(written: str) -> bool:
    """Whether a word carries a sign that can rule a reading out."""
    shape = letters(written)
    return any(signs - {SHADDA} for _, signs in shape[:-1])


def _fits_sign(signs: frozenset[str], latin: str, at: int) -> bool:
    """Whether what follows position ``at`` is what the signs ask for."""
    following = latin[at:]
    # A sukun is read where the alignment inserts a vowel (`_lines_up`): a
    # vowel the next letter writes does not contradict it.
    return all(
        sign not in signs or following.startswith(allowed)
        for sign, allowed in _AFTER.items()
    )


@lru_cache(maxsize=65_536)
def _lines_up(
    shape: tuple[tuple[str, frozenset[str]], ...], latin: str, with_signs: bool
) -> bool | None:
    """Whether the letters line up with the reading, or None for an unknown letter."""
    if any(letter not in LETTERS for letter, _ in shape):
        return None
    last = len(shape) - 1
    reached = {(0, 0)}
    stack = [(0, 0)]
    while stack:
        i, j = stack.pop()
        if i == len(shape):
            if j == len(latin):
                return True
            continue
        letter, signs = shape[i]
        for spelled in LETTERS[letter]:
            ways = [spelled]
            if spelled and spelled[0] not in _VOWELS:
                ways.append(spelled[0] + spelled)  # a doubled letter
            for way in ways:
                if not latin.startswith(way, j):
                    continue
                k = j + len(way)
                if (
                    with_signs
                    and i != last
                    and signs
                    and not _fits_sign(signs, latin, k)
                ):
                    continue
                nexts = [k]
                # A sukun: no vowel the script leaves unwritten after its letter.
                silent = with_signs and i != last and SUKUN in signs
                if not silent and k < len(latin) and latin[k] in _UNWRITTEN:
                    nexts.append(k + 1)
                for n in nexts:
                    if (i + 1, n) not in reached:
                        reached.add((i + 1, n))
                        stack.append((i + 1, n))
    return False


def against(written: str, reading: str, variants: tuple[str, ...] = ()) -> bool:
    """Whether the word's own signs rule this reading out, and all its variants.

    False whenever nothing can be said: no sign that counts, or a reading
    that does not line up with the letters even without them.
    """
    shape = letters(written)
    if not any(signs - {SHADDA} for _, signs in shape[:-1]):
        return False
    said = False
    for one in (reading, *variants):
        latin = _latin(one)
        if not latin:
            continue
        if not _lines_up(shape, latin, False):
            return False  # one spelling cannot be lined up at all: say nothing
        if _lines_up(shape, latin, True):
            return False  # one spelling of the reading fits the signs
        said = True
    return said


def fits(written: str, reading: str, variants: tuple[str, ...] = ()) -> bool | None:
    """Whether the word's own signs confirm a reading, rule it out, or say nothing.

    True when one of the reading's spellings lines up with the letters and
    their signs; False when its spellings line up with the letters but not
    with the signs; None when there is no sign that counts or no spelling
    lines up at all. :func:`against` answers only the second question, and
    its False means "nothing can be said" as often as "fits" — which is not
    enough to treat a reading as confirmed (the review of 2026-11-14).
    """
    shape = letters(written)
    if not any(signs - {SHADDA} for _, signs in shape[:-1]):
        return None
    said: bool | None = None
    for one in (reading, *variants):
        latin = _latin(one)
        if not latin or not _lines_up(shape, latin, False):
            continue
        if _lines_up(shape, latin, True):
            return True
        said = False
    return said
