"""The poem's metre as evidence for a word's Behnevis: an experiment, not served.

Classical Persian verse is quantitative: each verse half (hemistich) follows
the poem's metre, a fixed sequence of short (``U``) and long (``-``)
syllables. Ganjoor names the metre of most poems by its feet
(«مفاعیلن مفاعیلن فعولن»). A Behnevis reading fixes every vowel and so every
syllable's weight; so of a word's candidate readings, the metre can tell
which ones the line can hold — *bovad* (``U -``) where the line needs two
syllables, not the bank's noun *Bud* (one overlong syllable).

**What the metre cannot tell.** Weight depends on whether a vowel is there
and whether it is long, never on which short vowel it is: *kenār* and
*kanār*, *Del* and *Dal* weigh the same. The evaluation
(``tools/evaluate_behnevis_metre.py``) measures how much of the model's error
is of each kind instead of assuming it.

Three parts:

1. :func:`patterns` — Ganjoor's label → the syllable patterns it allows, with
   the classical variants (the first foot of فعلاتن may open long; a final
   فعلن may be فع لن; the رباعی's twelve patterns; in منسرح, مفتعلن may be
   مفاعلن). The foot table is the one of Sokhan's metre study (study 008).
2. :func:`shape` — the syllable weights of a Behnevis reading. Every
   syllable starts with at most one consonant; ``a e o`` are short, ``ā i u``
   long; a vowel alone is short, a short vowel closed by one consonant or a
   long vowel open is long, anything heavier is overlong (``-U``). An ``n``
   after a long vowel is not counted (*jān* is long, not overlong). The last
   syllable's weight waits for the next word.
3. :func:`fit` and :meth:`Metre.weigh` — the readings of a whole hemistich against
   its patterns, with the licences a reader of the poem allows (below), and
   from that a new order and confidence for each word.

**Licences, each with a cost** (:class:`Licences`; set beforehand, not tuned):
the last syllable of a hemistich counts long whatever it is; a word-final
consonant before a word that starts with a vowel may join that vowel (*vasl*:
*del az* is *de-laz*), which takes it from the syllable before; the
conjunction *o* always joins; است after a vowel may lose its *a*
(*xāne-st*); an ezafe *-e* / *-ye* may follow a word (cost); a word-final
short vowel may count long (cost); a word-final long vowel before a vowel may
count short (cost); and, for each word, *some other reading* taking a
guessed number of pattern positions, at a high cost — the reading the model
does not offer.

**How the fit moves a word** (:meth:`Metre.weigh`): each candidate keeps the mass
the model gave it (a probability for a measured one; for one offered without
a number a share of what is left, never more than the model's own reading
has), and is weighed by ``2 ** -extra``, where
``extra`` is how much more the best fit of the hemistich costs with that
candidate than with the word's best option. Readings the model did not offer
keep their mass at full weight — they might fit — so the metre raises a
word's confidence only by ruling out readings the model named, and lowers it
when the line cannot hold the reading the model preferred.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from functools import lru_cache

from murfulu.behnevis.letters import latin_key
from murfulu.behnevis.transcribe import Word

SHORT, LONG = "U", "-"
OVERLONG = LONG + SHORT

#: Spellings of است that may lose their *a* after a vowel.
ENCLITIC_AST = frozenset({"است", "ست"})

# -- 1. the metre's patterns ---------------------------------------------------

#: The U/- value of every foot Ganjoor's labels use (Sokhan study 008, from
#: the standard tables of Persian prosody). «فعلن» is فَعِلُن; Ganjoor writes
#: فَعْلُن as the two feet «فع لن». «فاع» is فاعُ inside a split foot; as the
#: last foot it is one overlong syllable, read long (:func:`patterns`).
FEET: dict[str, str] = {
    "فعولن": "U--",
    "فعول": "U-U",
    "فعل": "U-",
    "فع": "-",
    "لن": "-",
    "فاع": "-U",
    "لاتن": "--",
    "فاعلن": "-U-",
    "فاعلات": "-U-U",
    "فاعلاتن": "-U--",
    "فعلات": "UU-U",
    "فعلاتن": "UU--",
    "فعلن": "UU-",
    "مفاعیلن": "U---",
    "مفاعیل": "U--U",
    "مفاعلن": "U-U-",
    "مفاعلتن": "U-UU-",
    "مفعولن": "---",
    "مفعول": "--U",
    "مفعولات": "---U",
    "مفتعلن": "-UU-",
    "مستفعلن": "--U-",
    "مستفع": "--U",
    "مستفعلتن": "--UU-",
    "متفاعلن": "UU-U-",
    "متفاعلتن": "UU-UU-",
    "متفاعلاتن": "UU-U--",
    # A final foot with an extra consonant scans as the plain foot.
    "فاعلان": "-U-",
    "فعولان": "U--",
    "مفاعیلان": "U---",
    "فعلان": "UU-",
    "مستفعلان": "--U-",
    "مفعولان": "---",
    "فاعلاتان": "-U--",
}

#: The رباعی's patterns: its 24 traditional forms, twelve distinct weights.
ROBAI: frozenset[str] = frozenset(
    {
        "--UU--UU--UU-",
        "--UU--UU----",
        "--UU-U-U--UU-",
        "--UU-U-U----",
        "--UU-----UU-",
        "--UU-------",
        "-----UU--UU-",
        "-----UU----",
        "----U-U--UU-",
        "----U-U----",
        "--------UU-",
        "----------",
    }
)

_LABEL = re.compile(r"^(?P<feet>[^()]*?)\s*(?:\((?P<name>[^()]*)\))?\s*$")


def split_label(label: str) -> tuple[str, str]:
    """«مفاعیلن مفاعیلن فعولن (هزج مسدس محذوف)» → (the feet, the name)."""
    found = _LABEL.match((label or "").replace("‌", " ").strip())
    if not found:
        return " ".join((label or "").split()), ""
    return " ".join(found.group("feet").split()), (found.group("name") or "").strip()


@lru_cache(maxsize=1024)
def patterns(label: str) -> frozenset[str]:
    """Every syllable pattern a Ganjoor metre label allows; empty if unreadable."""
    feet, name = split_label(label)
    if "رباعی" in name or "رباعی" in feet:
        return ROBAI
    names = feet.split()
    if not names:
        return frozenset()
    # The licences of the metre study's catalogue, each where it applies
    # there: the first foot of فعلاتن may open long; a final فعلن may be
    # فع لن; in متدارک (فعلن four times) every foot may; مفتعلن and مفاعلن
    # take each other's place in the رجز of the two, and مفتعلن may take
    # مفاعلن's in منسرح (قلب). Broader licences the handbooks list (a
    # contraction inside the line, a long opening of فعلات) are left out, as
    # the catalogue left them out: each makes more wrong readings fit too.
    every_taskin = set(names) == {"فعلن"}
    qalb = set(names) == {"مفتعلن", "مفاعلن"}
    values: list[tuple[str, ...]] = []
    for i, foot in enumerate(names):
        if foot not in FEET:
            return frozenset()
        options = [FEET[foot]]
        if i == len(names) - 1 and options[0].endswith("-U"):
            # A line cannot end on a short: a last foot that seems to (فاع،
            # فعول، مفاعیل) ends on one overlong syllable, read long.
            options = [options[0][:-1]]
        if foot == "فعلاتن" and i == 0:
            options.append("-U--")  # the first foot may open long: فاعلاتن
        if foot == "فعلن" and (i == len(names) - 1 or every_taskin):
            options.append("--")  # فع لن
        if foot == "مفتعلن" and ("منسرح" in name or qalb):
            options.append(FEET["مفاعلن"])  # قلب
        if foot == "مفاعلن" and qalb:
            options.append(FEET["مفتعلن"])
        values.append(tuple(options))
    found = {""}
    for choices in values:
        found = {head + option for head in found for option in choices}
    return frozenset(found)


# -- 2. the weights of a reading -----------------------------------------------

SHORT_VOWELS = frozenset("aeo")
LONG_VOWELS = frozenset("āiu")
VOWELS = SHORT_VOWELS | LONG_VOWELS


@dataclass(frozen=True)
class Syllable:
    """A syllable's vowel length and its closing consonants, as counted.

    ``n`` is an ``n`` after a long vowel, which the metre does not count
    (*jān*), kept apart because a following vowel may still take it.
    """

    long: bool
    coda: int
    n: bool = False

    def weight(self) -> str:
        """``U``, ``-`` or ``-U`` (overlong)."""
        if not self.long and self.coda == 0:
            return SHORT
        if (not self.long and self.coda == 1) or (self.long and self.coda == 0):
            return LONG
        return OVERLONG

    def joined(self) -> Syllable:
        """The syllable once its last consonant goes to a following vowel."""
        if self.coda:
            return replace(self, coda=self.coda - 1)
        return replace(self, n=False)

    @property
    def open(self) -> bool:
        """Ends in its vowel."""
        return self.coda == 0 and not self.n


@dataclass(frozen=True)
class Shape:
    """A reading's weights, the last syllable apart.

    Whether it starts with a vowel, the weights of all its syllables but the
    last, and the last, whose weight the next word decides.
    """

    vowel_first: bool
    body: str
    last: Syllable

    def alone(self) -> str:
        """The weights of the word on its own, the last as it stands."""
        return self.body + self.last.weight()


GLOTTAL = "ʔ"

_DIPHTHONG = re.compile(r"(?<=[ae])i(?=[^aāeiou]|$)")


def spoken(reading: str, spelling: str = "") -> str:
    """A reading as the metre hears it: what its letters stand for, lower case.

    The word bank, and the letter model that learned from it, often write
    ع with a vowel letter: *jaafari* for جعفری, *aālam* for عالم, *šama*
    for شمع. A Persian word has no two vowels side by side, so where the
    reading has two and the spelling an ع, one of them may be the ع — a
    consonant (a glottal stop) to the metre: of two short vowels the second,
    where it would close a syllable before one consonant (*jaʔfari*,
    *baʔd*); a short vowel ending the word after a long
    one (*samāʔ*); a short vowel before a long one (*ʔālam*). Otherwise the
    ع stands unwritten between the two (*tabiʔat*, *tāʔat*). This is a rule
    of thumb about the bank's habit (UPSTREAM A18), not its data. A short
    vowel that ends the
    reading where the spelling ends in ع is the ع as well (*šamʔ*). The
    bank's *gāe* for گاه is *gāh*, and an *ai* or *ei* before a consonant
    is the diphthong (*hosain* is *hosayn*) unless the spelling writes a
    hamza there. Without a spelling the reading is taken as written.
    """
    latin = latin_key(reading).replace("ˈ", GLOTTAL)
    if not spelling:
        return latin
    chars = list(latin)
    ayn = spelling.count("ع")
    for i in range(len(chars) - 1):
        if not ayn:
            break
        first, second = chars[i], chars[i + 1]
        if first not in VOWELS or second not in VOWELS:
            continue
        run = ""
        for ch in chars[i + 2 :]:
            if ch in VOWELS:
                break
            run += ch
        end = i + 2 + len(run) == len(chars)
        if first in SHORT_VOWELS and second in SHORT_VOWELS:
            # jaʔfari, baʔd: the ع closes a syllable. Before two consonants
            # it is left alone: it opens one before a doubled letter
            # (moʔallem) and in a compound (āšofte-ʔaqli), and the rare
            # raʔdnāk is missed.
            if len(run) == 1 or (not run and end):
                chars[i + 1] = GLOTTAL
                ayn -= 1
        elif first in LONG_VOWELS and second in SHORT_VOWELS and not run and end:
            chars[i + 1] = GLOTTAL  # samāʔ, dāʔ
            ayn -= 1
        elif first in SHORT_VOWELS and second in LONG_VOWELS:
            chars[i] = GLOTTAL  # ʔālam: the ع opens a syllable
            ayn -= 1
        # Otherwise the two stay apart, the ع between them unwritten:
        # tabi-ʔat, jamā-ʔat, tā-ʔat.
    if (
        ayn
        and spelling.endswith("ع")
        and len(chars) >= 2
        and chars[-1] in SHORT_VOWELS
        and chars[-2] not in VOWELS
    ):
        chars[-1] = GLOTTAL
    latin = "".join(chars)
    if spelling.endswith("اه") and latin.endswith("āe"):
        latin = latin[:-1] + "h"
    if "ئ" not in spelling and "ء" not in spelling:
        latin = _DIPHTHONG.sub("y", latin)
    return latin


@lru_cache(maxsize=262_144)
def shape(reading: str, spelling: str = "", ezafe: bool = False) -> Shape | None:
    """The syllable weights of a Behnevis reading, or None if it cannot be syllabled.

    A reading cannot be syllabled when it has no vowel, starts with two
    consonants, or closes a syllable with three — *baxšm*, a letter guess
    for بخشم, is no Persian word. With the spelling, a vowel letter that
    stands for ع is read as the consonant it is (:func:`spoken`). With
    ``ezafe``, the reading as it is followed by an ezafe.
    """
    latin = spoken(reading, spelling)
    if ezafe:
        latin = with_ezafe(latin)
    at = [i for i, ch in enumerate(latin) if ch in VOWELS]
    if not at or at[0] > 1:
        return None
    syllables: list[Syllable] = []
    for k, i in enumerate(at):
        last = k + 1 == len(at)
        # Between two vowels the last consonant opens the next syllable.
        cluster = latin[i + 1 :] if last else latin[i + 1 : at[k + 1]]
        coda = cluster if last else cluster[:-1]
        # An i before a y that opens the next syllable is read short:
        # *siyāh* is si-yāh, U-U, as the prosodists scan سیاه.
        glide = latin[i] == "i" and not coda and not last and cluster == "y"
        long = latin[i] in LONG_VOWELS and not glide
        n = long and coda.startswith("n")
        counted = len(coda) - (1 if n else 0)
        if len(coda) > 2 or counted > 2:
            return None
        syllables.append(Syllable(long, counted, n))
    body = "".join(s.weight() for s in syllables[:-1])
    # A word that opens on ع opens on a glottal stop, as one that opens on a
    # vowel does: a consonant before it may join it alike.
    vowel_first = at[0] == 0 or latin[0] == GLOTTAL
    return Shape(vowel_first, body, syllables[-1])


#: What decides how a reading behaves in any line (:func:`behaviour`).
Behaviour = tuple[object, ...]


def behaviour(reading: str, spelling: str = "") -> Behaviour | None:
    """Everything the metre can see of a reading, in any line.

    Two readings with the same behaviour fit the same lines at the same
    costs, so no metre can tell them apart: *Del* and *Dal*, *Jur* and
    *Jowr* (both overlong, both long once a vowel takes the last
    consonant). *ju* and *Jav* differ: before a vowel *Jav* may lose its *v*
    to it and turn short. *ast* and *Est* differ for است: only *ast* may
    lose its *a* after a vowel.
    """
    found = shape(reading, spelling)
    if found is None:
        return None
    last = found.last
    key = latin_key(reading)
    # With the ezafe the last consonant opens a syllable of its own, so the
    # ezafe's shape is part of what a line can see.
    ezafe = None if key in ("va", "o") else shape(reading, spelling, ezafe=True)
    return (
        found.vowel_first,
        found.body,
        last.weight(),
        last.open,
        last.long if last.open else None,
        None if last.open else last.joined().weight(),
        None if ezafe is None else ezafe.alone(),
        spelling in ENCLITIC_AST and key in ("ast", "st"),
        spelling == "و" and key == "o",
    )


def weights(reading: str, spelling: str = "") -> str | None:
    """A reading's weights on its own (``U-`` for *bovad*), or None."""
    found = shape(reading, spelling)
    return None if found is None else found.alone()


def with_ezafe(reading: str) -> str:
    """The reading with the ezafe: *-e* after a consonant, *-ye* after a vowel."""
    latin = latin_key(reading)
    return latin + ("ye" if latin and latin[-1] in VOWELS else "e")


# -- 3. the fit ----------------------------------------------------------------


@dataclass(frozen=True)
class Licences:
    """What each licence costs a fit. Set beforehand, not tuned on the test."""

    ezafe: float = 0.5
    #: A word-final short vowel counted long (که، چه، خانه).
    lengthen: float = 0.5
    #: A word-final long vowel counted short before a vowel.
    shorten: float = 1.0
    #: A reading the model does not offer, for one word.
    other: float = 3.0
    #: How much less likely each unit of cost makes a candidate: 2 ** -cost.
    base: float = 2.0
    #: How many pattern positions a word's *other reading* may take beyond
    #: those its candidates take (an overlong syllable takes two).
    spread: int = 1


#: What comes after a syllable: another word starting with a consonant or a
#: vowel, the conjunction *o*, or the hemistich's end.
CONSONANT, VOWEL, CONJUNCTION = "consonant", "vowel", "conjunction"


def _resolve(last: Syllable, after: str, licences: Licences) -> list[tuple[str, float]]:
    """How a word's last syllable may weigh before what comes after it."""
    found: dict[str, float] = {}

    def add(weight: str, cost: float) -> None:
        found[weight] = min(cost, found.get(weight, math.inf))

    if after != CONJUNCTION or last.open:
        add(last.weight(), 0.0)  # the consonant stays (a glottal stop before a vowel)
    if after in (VOWEL, CONJUNCTION) and not last.open:
        add(last.joined().weight(), 0.0)  # vasl
    if last.open and not last.long:
        add(LONG, licences.lengthen)
    if last.open and last.long and after in (VOWEL, CONJUNCTION):
        add(SHORT, licences.shorten)
    return list(found.items())


@dataclass(frozen=True)
class Option:
    """One way a word may be read in the line: its shapes, each with a cost.

    ``conjunction``: the reading is the conjunction *o*, which always joins
    the word before. ``ast``: the reading is است's *ast* or *st*, which after
    a vowel may lose its *a* and close that vowel's syllable.
    """

    shapes: tuple[tuple[Shape, float], ...]
    conjunction: bool = False
    ast: bool = False


@dataclass(frozen=True)
class Slot:
    """One word of the hemistich: its options and *some other reading*.

    ``other`` is the range of pattern positions that other reading may take
    (an overlong syllable takes two), around those of the readings offered.
    ``enclitic``: the word is است or ست, whose other reading may attach to
    the word before, as *ast* may.
    """

    options: tuple[Option, ...]
    other: tuple[int, int]
    enclitic: bool = False


#: A point in the fit: how much of the pattern is used, and the last syllable
#: still waiting for the next word (None at the start or after another reading).
State = tuple[int, Syllable | None]


def _consume(pattern: str, at: int, weights: str) -> int | None:
    end = at + len(weights)
    if end <= len(pattern) and pattern[at:end] == weights:
        return end
    return None


def _steps(
    slot: Slot, state: State, pattern: str, licences: Licences
) -> list[tuple[int, State, float]]:
    """Every way one word moves the fit on: (option index, new state, cost).

    The index ``len(slot.options)`` is the word's *other reading*.
    """
    at, waiting = state
    found: list[tuple[int, State, float]] = []
    for index, option in enumerate(slot.options):
        for one, shape_cost in option.shapes:
            after = (
                CONJUNCTION
                if option.conjunction
                else (VOWEL if one.vowel_first else CONSONANT)
            )
            resolved = (
                [("", 0.0)] if waiting is None else _resolve(waiting, after, licences)
            )
            for weight, cost in resolved:
                moved = _consume(pattern, at, weight)
                if moved is None:
                    continue
                moved = _consume(pattern, moved, one.body)
                if moved is not None:
                    found.append((index, (moved, one.last), cost + shape_cost))
        if option.ast and waiting is not None and waiting.open:
            # است after a vowel loses its a: the vowel's syllable takes *st*
            # (xāne-st, kojā-st), and the word adds nothing more.
            found.append((index, (at, Syllable(waiting.long, 2)), 0.0))
    lowest, highest = slot.other
    other = len(slot.options)
    if slot.enclitic and waiting is not None and waiting.open:
        found.append((other, (at, Syllable(waiting.long, 2)), licences.other))
    resolved = (
        [("", 0.0)]
        if waiting is None
        else _resolve(waiting, CONSONANT, licences) + _resolve(waiting, VOWEL, licences)
    )
    for weight, cost in resolved:
        moved = _consume(pattern, at, weight)
        if moved is None:
            continue
        for span in range(lowest, highest + 1):
            if moved + span > len(pattern):
                continue
            # Another reading may end in any syllable: its weight is then
            # left to the next word, as a reading offered leaves it.
            found.append((other, (moved + span, None), cost + licences.other))
            found += [
                (other, (moved + span - 1, last), cost + licences.other)
                for last in _ANY_LAST
            ]
    return found


#: The last syllables another reading may end in: open short, open long, closed.
_ANY_LAST = (Syllable(False, 0), Syllable(True, 0), Syllable(False, 1))


def _finish(state: State, pattern: str) -> float:
    """The cost of ending the hemistich here: its last syllable counts long."""
    at, waiting = state
    if waiting is None:
        return 0.0 if at == len(pattern) else math.inf
    return 0.0 if at == len(pattern) - 1 else math.inf


def fit(
    slots: Sequence[Slot], pattern_set: Iterable[str], licences: Licences
) -> list[list[float]]:
    """For each word and each option, the cheapest fit of the line that uses it.

    The last entry of each word's list is its *other reading*. ``inf`` where
    no fit uses the option. Exact: a forward and a backward pass over the
    words, the state being how much of the pattern is used and the syllable
    still waiting.
    """
    best = [[math.inf] * (len(slot.options) + 1) for slot in slots]
    for pattern in pattern_set:
        forward: list[dict[State, float]] = [{(0, None): 0.0}]
        moves: list[dict[State, list[tuple[int, State, float]]]] = []
        for slot in slots:
            here: dict[State, list[tuple[int, State, float]]] = {}
            nxt: dict[State, float] = {}
            for state, cost in forward[-1].items():
                here[state] = _steps(slot, state, pattern, licences)
                for _, new, step in here[state]:
                    if cost + step < nxt.get(new, math.inf):
                        nxt[new] = cost + step
            moves.append(here)
            forward.append(nxt)
        backward: dict[State, float] = {
            state: _finish(state, pattern) for state in forward[-1]
        }
        for i in range(len(slots) - 1, -1, -1):
            before: dict[State, float] = {}
            for state, steps in moves[i].items():
                for index, new, step in steps:
                    total = forward[i][state] + step + backward.get(new, math.inf)
                    if total < best[i][index]:
                        best[i][index] = total
                    rest = step + backward.get(new, math.inf)
                    if rest < before.get(state, math.inf):
                        before[state] = rest
            backward = before
    return best


def scans(
    slots: Sequence[Slot], pattern_set: Iterable[str], licences: Licences
) -> bool:
    """Whether the line fits a pattern with the readings offered, none other."""
    bare = [Slot(slot.options, (1, 0)) for slot in slots]  # no other reading
    for pattern in pattern_set:
        states: dict[State, float] = {(0, None): 0.0}
        for slot in bare:
            states = {
                new: 0.0
                for state in states
                for index, new, _ in _steps(slot, state, pattern, licences)
                if index < len(slot.options)
            }
        if any(_finish(state, pattern) == 0.0 for state in states):
            return True
    return False


# -- 4. a hemistich's words, weighed by the metre ------------------------------


@dataclass(frozen=True)
class Weighed:
    """What the metre did to one word."""

    word: Word
    #: The line could be fitted without any word's *other reading*.
    scanned: bool
    #: How much more the best fit costs with the model's first reading.
    extra: float


@dataclass
class Metre:
    """The metre as a switchable step after the transcriber; off unless used.

    Nothing served calls it: ``serve.annotate`` reads words without it, so
    the reading screen is unchanged until the project lead decides otherwise.
    """

    licences: Licences = field(default_factory=Licences)
    #: Spellings whose readings are function words: they take no ezafe.
    functions: frozenset[str] = frozenset()

    def slots(self, words: Sequence[Word]) -> list[Slot]:
        """Each word's options in the line, from the readings the model offers."""
        out: list[Slot] = []
        for i, word in enumerate(words):
            last = i == len(words) - 1
            options: list[Option] = []
            counts: list[int] = []
            for latin, _ in word.candidates:
                plain = shape(latin, word.spelling)
                found: list[tuple[Shape, float]] = []
                if plain is not None:
                    found.append((plain, 0.0))
                    counts.append(len(plain.alone()))
                key = latin_key(latin)
                enclitic = word.spelling in ENCLITIC_AST
                if (
                    plain is not None
                    and not last
                    and not enclitic
                    and word.spelling not in self.functions
                    and key not in ("va", "o")
                ):
                    joined = shape(latin, word.spelling, ezafe=True)
                    if joined is not None:
                        found.append((joined, self.licences.ezafe))
                options.append(
                    Option(
                        tuple(found),
                        conjunction=word.spelling == "و" and key == "o",
                        ast=enclitic and key in ("ast", "st"),
                    )
                )
            if counts:
                span = (
                    max(1, min(counts) - self.licences.spread),
                    max(counts) + self.licences.spread,
                )
            else:
                span = (1, max(1, len(word.spelling)))
            out.append(
                Slot(tuple(options), span, enclitic=word.spelling in ENCLITIC_AST)
            )
        return out

    def weigh(self, words: Sequence[Word], pattern_set: Iterable[str]) -> list[Weighed]:
        """The words again, re-ordered and re-weighed by the metre."""
        pattern_set = list(pattern_set)
        if not words or not pattern_set:
            return [Weighed(w, False, 0.0) for w in words]
        slots = self.slots(words)
        costs = fit(slots, pattern_set, self.licences)
        scanned = scans(slots, pattern_set, self.licences)
        return [
            self._weigh_one(word, cost, scanned)
            for word, cost in zip(words, costs, strict=True)
        ]

    def _weigh_one(self, word: Word, costs: list[float], scanned: bool) -> Weighed:
        """One word's candidates weighed by how well the line holds each."""
        lowest = min(costs)
        if not word.candidates or lowest == math.inf:
            return Weighed(word, scanned, math.nan)
        known = [max(0.0, p) for _, p in word.candidates if p is not None]
        # Numbers that add up past one are read as shares of one.
        scale = 1.0 / sum(known) if sum(known) > 1.0 else 1.0
        unknown = sum(1 for _, p in word.candidates if p is None)
        left = max(0.0, 1.0 - sum(known) * scale)
        latins = [latin for latin, _ in word.candidates]
        chosen = latins.index(word.latin) if word.latin in latins else None
        # A reading offered without a number takes an equal share of what the
        # numbered ones leave.
        share = left / (unknown + 1)
        masses = [
            share if p is None else max(0.0, p) * scale for _, p in word.candidates
        ]
        if chosen is not None:
            # No rival weighs more than the model's own reading, so that
            # without the metre's word the order and the confidence stay as
            # the model made them (the letter model's beam can give a rival
            # more than its own first guess).
            mine = masses[chosen]
            masses = [m if k == chosen else min(m, mine) for k, m in enumerate(masses)]
        # What is left over is the share of the readings not offered at all.
        rest = max(0.0, 1.0 - sum(masses))
        likely = [self.licences.base ** -(c - lowest) for c in costs[:-1]]
        weighed = [m * f for m, f in zip(masses, likely, strict=True)]
        total = sum(weighed) + rest
        extra = costs[chosen] - lowest if chosen is not None else math.nan
        if total <= 0:
            # Every reading offered is ruled out and the model left nothing
            # for others: the line holds none of them, so a person decides.
            ruled_out = tuple((latin, 0.0) for latin in latins)
            return Weighed(
                replace(word, confidence=0.0, candidates=ruled_out), scanned, extra
            )
        order = sorted(range(len(weighed)), key=lambda k: (-weighed[k], k))
        candidates = tuple((word.candidates[k][0], weighed[k] / total) for k in order)
        latin, confidence = candidates[0]
        return Weighed(
            replace(word, latin=latin, confidence=confidence, candidates=candidates),
            scanned,
            extra,
        )
