"""Readings for inflected forms, built from the bank's stems and headwords.

The bank holds headwords, and verbs with their two stems; the texts write
بخشم, رود, شیرازی. :mod:`murfulu.corpus.inflection` already says how such a
spelling splits — a base the bank holds, and a prefix or an ending — and this
module writes the Behnevis for each split: the base's reading and the
affix's. بخشم is the present stem بخش *baxš* plus م *-am*: *baxšam*.

These readings are **offered, never measured**: the reading screen shows them
as alternatives a reader may pick (the project lead, 2026-11-14), and the
transcriber may propose one for an inflected word, still held below every
threshold. A stem that ends in *ow* — رو *row*, شو *šow*, بو *bow* — takes
*av* or *ov* before a vowel (*ravad*, *šavad*, *bovad*); both are offered.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from murfulu.corpus.inflection import Analyser, Analysis
from murfulu.corpus.wordtypes import normalise

ZWNJ = "‌"

#: A verb's prefix, as the patterns spell it, and its Behnevis.
PREFIX = {"": "", "می": "mi", "ن": "na", "نمی": "nemi", "ب": "be"}

#: An ending, as the patterns spell it, and its Behnevis. Verbal endings
#: first, then the nominal ones of ``corpus.inflection.NOMINAL``.
SUFFIX = {
    "": "",
    "م": "am",
    "ی": "i",
    "د": "ad",
    "یم": "im",
    "ید": "id",
    "ند": "and",
    "ه": "e",
    "هام": "eam",
    "هاست": "east",
    "ها": "hā",
    "های": "hāy",
    "هایی": "hāyi",
    "ان": "ān",
    "ات": "āt",
    "ین": "in",
    "ون": "un",
    "تر": "tar",
    "تری": "tari",
    "ترین": "tarin",
    "ا": "ā",
    "ت": "at",
    "ش": "aš",
    "مان": "emān",
    "تان": "etān",
    "شان": "ešān",
    "ست": "st",
    "است": "ast",
}

#: The participle with the copula written on with a half-space: ه‌ام …
PARTICIPLE = {"ام": "eam", "ای": "ei", "ایم": "eim", "اید": "eid", "اند": "eand"}

VOWELS = set("aāeiou")


def _plain(affix: str) -> str:
    return affix.replace(ZWNJ, "")


def _suffix_latin(suffix: str) -> str | None:
    if suffix.startswith("ه" + ZWNJ):
        return PARTICIPLE.get(suffix[2:])
    return SUFFIX.get(_plain(suffix))


def _join(base: str, ending: str) -> list[str]:
    """A base's reading and an ending's, joined as Persian joins them."""
    if not ending or base[-1:].lower() not in VOWELS and not base.endswith("ow"):
        return [base + ending]
    if ending[0] not in VOWELS:
        return [base + ending]
    if base.endswith("ow"):
        return [base[:-2] + "av" + ending, base[:-2] + "ov" + ending]
    return [base + "y" + ending]


def family(pattern_id: str) -> str:
    """The family a pattern's reliability is measured for.

    A verb by its prefix — none, می, ن, نمی, ب — and every nominal ending
    together, because the corpus marks too few of each to measure it alone.
    """
    parts = pattern_id.split(":")
    if parts[0] == "verb":
        return "verb:" + parts[1].replace("-joined", "")
    return "noun"


def _frozen(table: dict[str, list[str]]) -> dict[str, tuple[str, ...]]:
    return {k: tuple(v) for k, v in table.items()}


class Inflector:
    """Builds readings of inflected spellings from what the bank holds."""

    def __init__(
        self,
        analyser: Analyser,
        headwords: dict[str, tuple[str, ...]],
        past_stems: dict[str, tuple[str, ...]],
        present_stems: dict[str, tuple[str, ...]],
    ) -> None:
        self.analyser = analyser
        self.bases = {
            "headword": headwords,
            "past_stem": past_stems,
            "present_stem": present_stems,
        }

    @classmethod
    def from_readings(cls, readings: Iterable[object], analyser: Analyser) -> Inflector:
        """From the lexicon's readings (anything with the stem attributes)."""
        heads: dict[str, list[str]] = {}
        past: dict[str, list[str]] = {}
        present: dict[str, list[str]] = {}
        for r in readings:
            # Every reading of a headword: رخ is *rex*, and *rox* too.
            spelling = getattr(r, "spelling_fa", None)
            for latin_one in getattr(r, "all_latin", ()) or ():
                if spelling and latin_one:
                    known = heads.setdefault(normalise(spelling), [])
                    if latin_one not in known:
                        known.append(latin_one)
            for table, fa, latin in (
                (
                    past,
                    getattr(r, "past_stem_fa", None),
                    getattr(r, "past_stem_latin", None),
                ),
                (
                    present,
                    getattr(r, "present_stem_fa", None),
                    getattr(r, "present_stem_latin", None),
                ),
            ):
                if fa and latin:
                    known = table.setdefault(normalise(fa), [])
                    if latin not in known:
                        known.append(latin)
        return cls(analyser, _frozen(heads), _frozen(past), _frozen(present))

    def readings(self, spelling: str) -> list[str]:
        """Every reading the splits of a spelling give, without repeats."""
        return [latin for latin, _ in self.analyses(spelling)]

    def analyses(self, spelling: str) -> list[tuple[str, str]]:
        """Each reading with the family of the pattern that built it."""
        found: list[tuple[str, str]] = []
        seen: set[str] = set()
        for analysis in self.analyser.readings(spelling):
            kind = family(analysis.pattern.id)
            for latin in self._of(analysis):
                if latin not in seen:
                    seen.add(latin)
                    found.append((latin, kind))
        return found

    def _of(self, analysis: Analysis) -> list[str]:
        pattern = analysis.pattern
        prefix = PREFIX.get(_plain(pattern.prefix))
        suffix = _suffix_latin(pattern.suffix)
        if prefix is None or suffix is None:
            return []
        bases = self.bases[pattern.base_kind].get(analysis.base, ())
        plain = _plain(pattern.suffix)
        out: list[str] = []
        for base in bases:
            stem = base if not prefix else base[:1].lower() + base[1:]
            ending = suffix
            glide = (
                stem[-1:].lower() in VOWELS
                and not analysis.base.endswith("ی")
                and plain.startswith("ی")
            )
            if glide:
                # After a vowel the written ی is the glide: گویم is گو + y + م,
                # *guyam*, not the plural *guyim* (the review of 2026-11-14).
                # A stem written with its own ی (زی *zi*) carries the glide
                # already: زییم is *ziyim*, the ending's ی its own.
                rest = SUFFIX.get(plain[1:])
                if rest is None:
                    continue
                joined = [stem + "y" + rest]
            else:
                joined = _join(stem, ending)
            out += [prefix + one if prefix else one for one in joined]
        return out

    def measure(
        self,
        marked: Iterable[dict[str, str]],
        known: Callable[[str], bool],
    ) -> dict[str, tuple[int, int]]:
        """Per pattern family: how often its one built reading fits the signs.

        ``marked`` are marked words (``written``, ``spelling``) as
        ``tools/build_behnevis.py`` writes them; a spelling ``known`` already
        reads (the bank, a function word) is passed over. Shared by the build
        and the held-out evaluation, so both measure the same thing.
        """
        from murfulu.search import harakat

        fitted: dict[str, list[int]] = {}
        for m in marked:
            if known(m["spelling"]):
                continue
            forms = {normalise(m["written"]).strip(ZWNJ), m["spelling"]}
            built: dict[str, str] = {}
            for form in sorted(forms):
                for latin, kind in self.analyses(form):
                    built.setdefault(latin, kind)
            if len(built) != 1:
                continue
            ((latin, kind),) = built.items()
            verdict = harakat.fits(m["written"], latin)
            if verdict is not None:
                tally = fitted.setdefault(kind, [0, 0])
                tally[0] += verdict
                tally[1] += 1
        return {k: (v[0], v[1]) for k, v in fitted.items()}
