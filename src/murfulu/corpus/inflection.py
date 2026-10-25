"""Which corpus spellings are inflections of a word we already hold.

Murfulu builds *new* words. Persian also **inflects** the words it already has
— رفتی is "you went", not a new word — and the corpus writes both without
telling them apart. Where the lexicon holds no reading for a spelling, nothing
in the data separates رفتی from گفتار, which is exactly the kind of word we
build. That is open question S8. **This module is the instrument for measuring
it, not a ruling on it.**

Nothing here is a linguistic decision:

* A pattern whose letters are also a **derivational** affix in the rule pack is
  reported as *shared* and counted apart. بلندی is the indefinite of بلند and
  it is also the noun "height"; only the linguist can say which a given
  spelling is, so both readings are kept and neither is dropped.
* A spelling the lexicon already holds is never called an inflection, however
  well it strips. مردم is a headword, so it is a word, not "my man".

Corpus spellings arrive already normalised by :mod:`murfulu.corpus.wordtypes`
— harakat stripped, Arabic letters folded, the zero-width non-joiner kept
inside a word. Everything compared against them is normalised the same way.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Literal

from murfulu.corpus.wordtypes import normalise
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import loaded

#: A word for our purposes may contain it: می‌رود is one spelling, not two.
ZWNJ = "‌"

#: What a stripped base has to be before it is looked up. One letter is a
#: preposition or a clitic, never a word we would hold.
MIN_BASE = 2

#: Where the base of a pattern has to be found.
BaseKind = Literal["headword", "past_stem", "present_stem"]


@dataclass(frozen=True)
class Pattern:
    """One inflectional shape, and where its base has to be found.

    ``id`` is a readable slug rather than a rule id. These are **not** rules —
    the pack's ids are permanent and describe word formation; these describe
    the inflection the corpus writes and Murfulu does not build.
    """

    id: str
    label_fa: str
    prefix: str = ""
    suffix: str = ""
    base_kind: BaseKind = "headword"

    def split(self, spelling: str) -> str | None:
        """The base this pattern would leave, or ``None`` if it does not fit."""
        if not spelling.startswith(self.prefix):
            return None
        rest = spelling[len(self.prefix) :]
        if not self.suffix:
            return rest if len(rest) >= MIN_BASE else None
        if not rest.endswith(self.suffix):
            return None
        base = rest[: -len(self.suffix)]
        return base if len(base) >= MIN_BASE else None


def _verbal() -> Iterator[Pattern]:
    """Prefixes and endings that conjugate a verb, in every combination.

    The base is a **stem**, never an infinitive: رفتی is built on رفت, not on
    رفتن. Both stems are held in the lexicon, so both are looked up.
    """
    prefixes = [
        ("", "", ""),
        ("mi", "می" + ZWNJ, "استمراری"),
        ("mi-joined", "می", "استمراری"),
        ("na", "ن", "منفی"),
        ("nami", "نمی" + ZWNJ, "منفی استمراری"),
        ("nami-joined", "نمی", "منفی استمراری"),
        ("be", "ب", "التزامی"),
    ]
    # The bare past stem is the third person singular: رفت is "he went".
    past = [("", "سوم‌شخص مفرد"), *(_person(e) for e in ("م", "ی", "یم", "ید", "ند"))]
    # The participle, and the participle with the copula written onto it.
    past += [
        (suffix, "وجه وصفی")
        for suffix in ("ه", "ه" + ZWNJ + "ام", "ه" + ZWNJ + "ای", "ه" + ZWNJ + "ایم")
    ]
    past += [
        (suffix, "وجه وصفی")
        for suffix in ("ه" + ZWNJ + "اید", "ه" + ZWNJ + "اند", "هاست", "هام")
    ]
    present = [_person(e) for e in ("م", "ی", "د", "یم", "ید", "ند")]

    stems: tuple[tuple[list[tuple[str, str]], BaseKind, str], ...] = (
        (past, "past_stem", "گذشته"),
        (present, "present_stem", "حال"),
    )
    for prefix_id, prefix, prefix_label in prefixes:
        for endings, kind, stem_label in stems:
            for suffix, suffix_label in endings:
                # A bare present stem with no prefix is an imperative at best
                # and a noun at worst; too weak to count as evidence.
                if not prefix and not suffix:
                    continue
                label = " ".join(
                    x for x in (prefix_label, stem_label, suffix_label) if x
                )
                yield Pattern(
                    id=f"verb:{prefix_id or 'bare'}:{kind}:{suffix or 'bare'}",
                    label_fa=label,
                    prefix=prefix,
                    suffix=suffix,
                    base_kind=kind,
                )


def _person(ending: str) -> tuple[str, str]:
    """An ending and the person it marks, for a readable label."""
    names = {"م": "اول مفرد", "ی": "دوم مفرد", "د": "سوم مفرد"}
    names |= {"یم": "اول جمع", "ید": "دوم جمع", "ند": "سوم جمع"}
    return ending, names[ending]


#: Endings that inflect a noun or an adjective. Several of them are also
#: derivational affixes in the pack; that collision is measured, not assumed.
NOMINAL: tuple[tuple[str, str], ...] = (
    ("ها", "جمع"),
    (ZWNJ + "ها", "جمع"),
    ("های", "جمع"),
    (ZWNJ + "های", "جمع"),
    ("هایی", "جمع"),
    (ZWNJ + "هایی", "جمع"),
    ("ان", "جمع"),
    ("ات", "جمع عربی"),
    ("ین", "جمع عربی"),
    ("ون", "جمع عربی"),
    ("تر", "برتر"),
    ("تری", "برتر"),
    ("ترین", "برترین"),
    ("ی", "نکره یا اضافه"),
    ("ا", "ندا"),
    ("م", "ضمیر پیوستهٔ اول مفرد"),
    ("ت", "ضمیر پیوستهٔ دوم مفرد"),
    ("ش", "ضمیر پیوستهٔ سوم مفرد"),
    ("مان", "ضمیر پیوستهٔ اول جمع"),
    ("تان", "ضمیر پیوستهٔ دوم جمع"),
    ("شان", "ضمیر پیوستهٔ سوم جمع"),
    ("ست", "فعل ربطی"),
    ("است", "فعل ربطی"),
)


def patterns() -> tuple[Pattern, ...]:
    """Every inflectional pattern this instrument knows."""
    nominal = (
        Pattern(id=f"noun:{suffix}", label_fa=label, suffix=suffix)
        for suffix, label in NOMINAL
    )
    return tuple([*_verbal(), *nominal])


@dataclass(frozen=True)
class Held:
    """The spellings Murfulu already holds, by where it holds them.

    A verb stem is held without being a headword: the lexicon has رفتن and
    carries رفت and رو on it, and no row in it is spelled رفت.
    """

    headwords: frozenset[str] = frozenset()
    past_stems: frozenset[str] = frozenset()
    present_stems: frozenset[str] = frozenset()

    @classmethod
    def of(
        cls,
        headwords: Iterable[str],
        past_stems: Iterable[str] = (),
        present_stems: Iterable[str] = (),
    ) -> Held:
        """Normalise every spelling on the way in, so lookups can be exact."""
        return cls(
            headwords=frozenset(normalise(one) for one in headwords if one),
            past_stems=frozenset(normalise(one) for one in past_stems if one),
            present_stems=frozenset(normalise(one) for one in present_stems if one),
        )

    def has(self, base: str, kind: BaseKind) -> bool:
        """Whether ``base`` is held in the place ``kind`` names."""
        if kind == "headword":
            return base in self.headwords
        if kind == "past_stem":
            return base in self.past_stems
        return base in self.present_stems

    def holds(self, spelling: str) -> bool:
        """Whether the spelling itself is a word we hold, in any of the three."""
        return (
            spelling in self.headwords
            or spelling in self.past_stems
            or spelling in self.present_stems
        )


def held_from(lexicon: Lexicon) -> Held:
    """Every spelling the lexicon holds, split by where it holds it."""
    headwords, past, present = [], [], []
    for reading in lexicon.all_readings():
        headwords.append(reading.spelling_fa)
        if reading.past_stem_fa:
            past.append(reading.past_stem_fa)
        if reading.present_stem_fa:
            present.append(reading.present_stem_fa)
    return Held.of(headwords, past, present)


def pack_suffixes() -> dict[str, tuple[str, ...]]:
    """Suffix spelling → the ids of the pack rules that write it.

    Retired rules are included on purpose. N-090 and N-099 are switched off and
    **unconfirmed**, so a pattern colliding with them is still one the linguist
    may rule is word formation after all.
    """
    found: dict[str, list[str]] = {}
    for rule in loaded().rules:
        if rule.kind != "suffix" or not rule.affix_fa:
            continue
        for spelling in (rule.affix_fa, *rule.affix_variants):
            if spelling:
                found.setdefault(normalise(spelling), []).append(rule.id)
    return {spelling: tuple(ids) for spelling, ids in found.items()}


@dataclass(frozen=True)
class Analysis:
    """One way of reading a spelling as an inflection of a held base."""

    spelling: str
    base: str
    pattern: Pattern
    #: Rule ids in the pack whose affix is spelled the same way. Non-empty
    #: means this pattern cannot be told from word formation by its letters.
    shared_with: tuple[str, ...] = ()

    @property
    def is_shared(self) -> bool:
        """Whether a derivational rule writes the same letters."""
        return bool(self.shared_with)


@dataclass
class Analyser:
    """Reads corpus spellings against what the lexicon holds."""

    held: Held
    #: Suffix spelling → the rule ids in the pack that write it. Supplied by
    #: the caller from the loaded pack, so the collision is measured rather
    #: than written down here and left to rot.
    pack_suffixes: dict[str, tuple[str, ...]] = field(default_factory=dict)
    _patterns: tuple[Pattern, ...] = field(default_factory=patterns)

    def analyse(self, spelling: str) -> list[Analysis]:
        """Every way this spelling reads as an inflection of a held word.

        Empty for a spelling we already hold: a word is not an inflection of
        itself, and مردم is "people" before it is "my man".
        """
        if self.held.holds(normalise(spelling)):
            return []
        return self.readings(spelling)

    def readings(self, spelling: str) -> list[Analysis]:
        """As :meth:`analyse`, without asking whether the spelling is held.

        This is what the control uses. Run over the lexicon's own headwords —
        every one of which is a word by definition — the share that comes back
        with a reading is how often this instrument mistakes a word for an
        inflection, measured rather than estimated.
        """
        spelling = normalise(spelling)
        found = []
        for pattern in self._patterns:
            base = pattern.split(spelling)
            if base is None or not self.held.has(base, pattern.base_kind):
                continue
            shared = (
                self.pack_suffixes.get(pattern.suffix, ()) if pattern.suffix else ()
            )
            found.append(Analysis(spelling, base, pattern, shared))
        return found

    def best(self, spelling: str) -> Analysis | None:
        """The strongest reading of a spelling, or ``None`` if there is none.

        Preference order, and every part of it is a measuring convention
        rather than a claim about Persian: a pattern no derivational rule
        shares beats one that is shared, then the longest base wins, then the
        pattern id, so the answer does not depend on dictionary order.
        """
        return self.strongest(self.analyse(spelling))

    def control(self, spelling: str) -> Analysis | None:
        """As :meth:`best`, ignoring whether the spelling is itself held."""
        return self.strongest(self.readings(spelling))

    @staticmethod
    def strongest(found: list[Analysis]) -> Analysis | None:
        """Pick one reading out of several by the preference order above."""
        if not found:
            return None
        return min(
            found, key=lambda one: (one.is_shared, -len(one.base), one.pattern.id)
        )
