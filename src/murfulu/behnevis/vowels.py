"""Put the short vowels on a Persian word, from its Behnevis reading.

**The project lead's decision of 2026-11-21**: show the short-vowel marks —
زبر، زیر، پیش — on the Persian words, as Dehkhoda and Moin do, now that every
word has a Latin reading. Three conditions came with it, and this module is
the second and third:

1. Search and matching ignore the marks. Nothing here is stored or matched:
   the plain spelling stays the key everywhere, and the marked form is for
   display only.
2. **The marks come from the reading, never by hand**, so the two scripts
   always agree. Each letter of the word is lined up with the piece of the
   reading it stands for (the alignment of :mod:`murfulu.behnevis.letters`
   and :mod:`murfulu.search.harakat`); a short vowel the script leaves
   unwritten after a letter becomes that letter's mark.
3. **The marks a reader needs, not every mark** (ours, unconfirmed —
   FOR_THE_LINGUIST L48):

   - zabar, zir or pish for every short vowel the script does not write —
     *a*, *e*, *o* after a letter, or carried by ا or ع themselves
     (اَندیشه، عَلی);
   - before a diphthong, whose و and ی the reader would otherwise read *u*
     and *i*, **the mark of the vowel the reading itself writes**: a zir
     before *ey* (وِی، پِیوَند), a pish before *ow* (نُو), a zabar before *ay*
     and *aw* (وَی read *vay*). Until 2026-11-22 a zabar stood before all
     four, as the old dictionaries often write them: the bank's *vey* (he)
     and *vay* (the cry) are two words and both were shown وَی, and a zabar
     stood over a reading that says *e* — which is what condition 2 rules
     out, and what the project lead saw on the reading screen;
   - a tashdid where the reading doubles a letter (*taxxt* is rare; *ammā*,
     *Hażrat* no) — only where Behnevis writes the letter twice;
   - **never** a sokun, a mark on a long vowel the script already writes (ا،
     و، ی), or a mark on the last letter: a kasra there is read as the
     ezafe, and the silent ه of *-e* carries nothing.

**Where it says nothing.** A spelling the letter table does not foresee, or a
reading that does not line up with the letters, is shown as written. Where
the letters line up with the reading in more than one way and the ways
disagree about a mark, that mark is left off: a missing mark only leaves the
word as it was, a wrong one misleads.
"""

from __future__ import annotations

import unicodedata
from functools import lru_cache

from murfulu.behnevis.letters import latin_key
from murfulu.corpus.wordtypes import _FOLD
from murfulu.search.harakat import _UNWRITTEN, _VOWELS, LETTERS

FATHA = "َ"
DAMMA = "ُ"
KASRA = "ِ"
SHADDA = "ّ"
ZWNJ = "‌"

#: The mark for each short vowel.
MARK = {"a": FATHA, "e": KASRA, "o": DAMMA}

#: Letters that may carry a short vowel themselves: ا of *andiše*, ع of *Ali*.
_CARRIERS = {"ا", "ع", "ئ", "ء"}

#: The diphthongs of و and ی, whose first letter is the vowel that is marked
#: on the letter before.
_DIPHTHONGS = ("ow", "ey", "ay", "aw")

#: One step of an alignment: the letter's piece of the reading, from position
#: ``start`` to ``end`` of the Latin.
Edge = tuple[int, str, int]


def _edges(letters: tuple[str, ...], latin: str) -> list[list[Edge]] | None:
    """Every step that lies on some complete alignment, letter by letter.

    **Polynomial, not a search of every alignment.** The first draft listed
    whole alignments and stopped at 64, which was exponential on a reading
    that does not line up and gave a false agreement where there were more
    (the review of 2026-11-21). Here the positions reachable from the start
    and the positions the end can be reached from are worked out once each;
    a step is kept when both of its ends are. ``None`` when nothing lines up.
    """
    if any(letter not in LETTERS for letter in letters):
        return None
    n, m = len(letters), len(latin)

    def steps(i: int, j: int) -> list[Edge]:
        out: list[Edge] = []
        for spelled in LETTERS[letters[i]]:
            ways = [spelled]
            if spelled and spelled[0] not in _VOWELS and spelled != "ˈ":
                ways.append(spelled[0] + spelled)  # a doubled letter
            for way in ways:
                if not latin.startswith(way, j):
                    continue
                k = j + len(way)
                out.append((j, way, k))
                if k < m and latin[k] in _UNWRITTEN:
                    out.append((j, way + latin[k], k + 1))
        return out

    forward: list[set[int]] = [set() for _ in range(n + 1)]
    forward[0].add(0)
    every: list[list[Edge]] = []
    for i in range(n):
        here = [edge for j in sorted(forward[i]) for edge in steps(i, j)]
        every.append(here)
        forward[i + 1].update(edge[2] for edge in here)
    if m not in forward[n]:
        return None
    backward: set[int] = {m}
    kept: list[list[Edge]] = [[] for _ in range(n)]
    for i in range(n - 1, -1, -1):
        kept[i] = [edge for edge in every[i] if edge[2] in backward]
        backward = {edge[0] for edge in kept[i]}
    return kept


def _split(letter: str, piece: str) -> tuple[str, str]:
    """A piece as the letter's own Latin and the unwritten vowel after it."""
    if piece and piece[-1] in _UNWRITTEN and piece not in LETTERS[letter]:
        return piece[:-1], piece[-1]
    return piece, ""


def _gives_vowel_away(
    letter: str, piece: str, nxt: tuple[str, str, bool] | None
) -> bool:
    """Whether this letter's unwritten vowel is read as the next letter's.

    A vowel before a silent ا or ع that **starts a part** of the word is the
    carrier's: *ham·andiš*, the ا of the joined word. A vowel before a silent
    ه is the ه's: *kappe·duz*, the *e* of کپه. A silent ع inside a part keeps
    nothing: whether *lal* is لَعل or لعَل the letters cannot say, so the two
    alignments disagree and the mark is left off (the review of 2026-11-21).
    """
    _, vowel = _split(letter, piece)
    if not vowel or nxt is None:
        return False
    after, after_piece, starts_part = nxt
    if after_piece != "":
        return False
    return after == "ه" or (after in _CARRIERS and starts_part)


def _marks_at(
    prev: tuple[str, str] | None,
    cur: tuple[str, str, bool],
    nxt: tuple[str, str, bool] | None,
) -> frozenset[str]:
    """The marks one letter takes, given its own piece and its neighbours'."""
    letter, piece, _ = cur
    marks: set[str] = set()
    if letter in _CARRIERS and len(piece) == 1 and piece in MARK:
        # ا or ع read as the short vowel itself.
        return frozenset({MARK[piece]})
    if prev is not None and letter != "ه" and _gives_vowel_away(*prev, cur):
        # A silent carrier that took the vowel of the letter before it.
        return frozenset({MARK[_split(*prev)[1]]})
    body, vowel = _split(letter, piece)
    own = LETTERS[letter]
    if (
        len(body) >= 2
        and body[0] == body[1]
        and body[0] not in _VOWELS
        and body[1:] in own
    ):
        marks.add(SHADDA)
    if vowel and _gives_vowel_away(letter, piece, nxt):
        vowel = ""
    if vowel:
        # Also before و read *w* or ی read *y*: the mark is the vowel's own.
        marks.add(MARK[vowel])
    elif (
        nxt is not None
        and nxt[0] in ("و", "ی")
        and nxt[1][:2] in _DIPHTHONGS
        and body
        and body[-1] not in _VOWELS
    ):
        # و read *ow*, ی read *ey*: the consonant before takes the mark of the
        # diphthong's vowel — also a consonantal و, as in وِی (*vey*).
        marks.add(MARK[nxt[1][0]])
    return frozenset(marks)


def _agreed(plain: str, reading: str) -> list[frozenset[str]] | None:
    """The marks every alignment of one reading agrees on, letter by letter.

    ``None`` where the reading does not line up with the letters.
    """
    latin = latin_key(reading)
    at: list[int] = []
    letters: list[str] = []
    #: Letters that end a part of the word — before a joiner or a space — and
    #: letters that start one. A part's last letter carries nothing, like the
    #: word's: a vowel there is a linking one. The tatweel, a stretch of the
    #: line, is neither.
    ends: set[int] = set()
    starts: set[int] = {0}
    for index, ch in enumerate(plain):
        if ch == "ـ":
            continue
        if ch in (ZWNJ, " "):
            if letters:
                ends.add(len(letters) - 1)
                starts.add(len(letters))
            continue
        at.append(index)
        letters.append(ch.translate(_FOLD))
    if not letters or not latin:
        return None
    shape = tuple(letters)
    edges = _edges(shape, latin)
    if edges is None:
        return None
    n = len(shape)
    last = n - 1
    agreed: list[frozenset[str]] = []
    for i in range(n):
        if i == last or i in ends:
            agreed.append(frozenset())
            continue
        seen: frozenset[str] | None = None
        for start, piece, end in edges[i]:
            befores: list[Edge | None] = (
                [e for e in edges[i - 1] if e[2] == start] if i else [None]
            )
            afters = [e for e in edges[i + 1] if e[0] == end]
            for before in befores:
                for after in afters:
                    prev = (
                        (shape[i - 1], before[1], (i - 1) in starts) if before else None
                    )
                    marks = _marks_at(
                        prev[:2] if prev else None,
                        (shape[i], piece, i in starts),
                        (shape[i + 1], after[1], (i + 1) in starts),
                    )
                    # Each mark on its own: a disputed vowel must not take an
                    # agreed tashdid with it (the review of 2026-11-21).
                    seen = marks if seen is None else seen & marks
        agreed.append(seen or frozenset())
    return agreed


@lru_cache(maxsize=65_536)
def vocalise(spelling: str, reading: str, variants: tuple[str, ...] = ()) -> str:
    """The spelling with the short vowels its reading has, or the spelling itself.

    The spelling's own characters are kept — joiners, Arabic letter forms —
    and any marks it already carries are taken off first, so the result says
    what the reading says and nothing else.

    **With the variants the screen shows beside the reading**, only the marks
    every one of them agrees on: برنا is *barnā* or *bornā*, so its ب takes
    nothing rather than a zabar that contradicts the second (the review of
    2026-11-21). A variant that does not line up leaves the word as written.
    """
    plain = "".join(
        ch
        for ch in unicodedata.normalize("NFC", spelling)
        if not unicodedata.combining(ch)
    )
    agreed = _agreed(plain, reading)
    for variant in variants:
        if agreed is None:
            break
        other = _agreed(plain, variant)
        agreed = (
            None
            if other is None
            else [mine & theirs for mine, theirs in zip(agreed, other, strict=True)]
        )
    if agreed is None:
        return plain
    at = [index for index, ch in enumerate(plain) if ch not in ("ـ", ZWNJ, " ")]
    out = list(plain)
    for position, marks in sorted(zip(at, agreed, strict=True), reverse=True):
        if marks:
            ordered = "".join(m for m in (SHADDA, FATHA, KASRA, DAMMA) if m in marks)
            out.insert(position + 1, ordered)
    # In Unicode's own order (a zabar before a tashdid), so the same word is
    # always the same string, whatever order the marks were put on in.
    return unicodedata.normalize("NFC", "".join(out))


def vocalise_written(written: str, reading: str, variants: tuple[str, ...] = ()) -> str:
    """A word as a text writes it, with its reading's marks, or as written.

    For the reading screen, where a word stands as its source wrote it. **A
    source's own marks are never replaced**: a word written with a mark inside
    it is left exactly as written — its marks are evidence, and they are what
    rules a reading out. Marks written after the last letter (the kasra or the
    hamza of the ezafe, دلِ، خانهٔ) are kept and put back after the vowels.
    """
    text = unicodedata.normalize("NFC", written)
    end = len(text)
    while end and unicodedata.combining(text[end - 1]):
        end -= 1
    body, tail = text[:end], text[end:]
    if not body or any(unicodedata.combining(ch) for ch in body):
        return written
    marked = vocalise(body, reading, variants)
    return written if marked == body else unicodedata.normalize("NFC", marked + tail)


def strip(text: str) -> str:
    """A marked word as it is matched: the marks taken off."""
    return "".join(ch for ch in text if not unicodedata.combining(ch))
