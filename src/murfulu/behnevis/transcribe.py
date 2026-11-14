"""Write a line of Persian in Behnevis, word by word, each with its confidence.

Each word is read from the first source that has something to say
(:mod:`murfulu.behnevis`): a function word, the bank, the marked corpus's
choice among the bank's readings, or a guess from the letters. Where the word
itself carries vowel signs, the readings they rule out are dropped first
(:mod:`murfulu.search.harakat`), so «تُرکِ» is *tork* whatever the counts say.

A word whose confidence is at or above the threshold is taken as written; one
below it goes to a person, with the reading as a proposal. The threshold is
the project lead's to set (``tools/evaluate_behnevis.py`` shows what each one
costs in work and in errors).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from murfulu.behnevis.choice import ChoiceModel, ranked
from murfulu.behnevis.inflect import Inflector
from murfulu.behnevis.letters import LetterModel
from murfulu.corpus.inflection import Analyser
from murfulu.corpus.wordtypes import normalise
from murfulu.search import harakat
from murfulu.search.texts import tokens

#: Where a word's reading came from.
FUNCTION, BANK, CHOICE, LETTERS, NONE = "function", "bank", "choice", "letters", "none"
#: A guess from the letters for a word that reads as an inflected form.
INFLECTED = "inflected"

RULES = Path(__file__).resolve().parents[3] / "rules" / "function_word_readings.yaml"

ZWNJ = "‌"


def key(spelling: str) -> str:
    """A spelling as every table here is keyed: normalised, without joiners.

    The bank writes some compounds with a half-space and some without; so
    does the corpus. Both are one key.
    """
    return normalise(spelling).replace(ZWNJ, "")


@dataclass(frozen=True)
class Word:
    """One word of a line, as written, and its Behnevis."""

    written: str
    spelling: str
    latin: str | None
    confidence: float
    source: str
    #: Every reading considered, likeliest first, with its probability — or
    #: None for an alternative offered but not measured (an inflected form
    #: built from the bank's stems).
    candidates: tuple[tuple[str, float | None], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """The shape a report or the API gives."""
        return {
            "written": self.written,
            "spelling": self.spelling,
            "latin": self.latin,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "candidates": [
                [c, None if p is None else round(p, 3)] for c, p in self.candidates
            ],
        }


def load_function_readings(path: Path = RULES) -> dict[str, tuple[str, ...]]:
    """Spelling → the function word's readings, the usual one first."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        key(spelling): (entry["latin"], *entry.get("also", []))
        for spelling, entry in raw["readings"].items()
    }


@dataclass
class Transcriber:
    """The four sources, put together."""

    #: Normalised spelling → the bank's readings (distinct, case kept).
    bank: dict[str, tuple[str, ...]]
    letters: LetterModel
    choice: ChoiceModel
    functions: dict[str, tuple[str, ...]] = field(
        default_factory=load_function_readings
    )
    #: Spelling → (times a candidate fitted the text's signs, times none did).
    #: Measured by ``tools/build_behnevis.py`` wherever the corpus marks the
    #: spelling: بود is marked «بُوَد» again and again, *bovad*, and the bank
    #: holds only the noun *Bud* — so بود must not be trusted as a word with
    #: one sure reading.
    covered: dict[str, tuple[int, int]] = field(default_factory=dict)
    #: For a spelling the corpus never marks: how likely its candidates hold
    #: the right reading. **Not measured** — no unbiased sample exists yet
    #: (editions mark the hard words); the timed sample of the linguist's
    #: transcription is what can replace it.
    covered_prior: float = 0.9
    #: How many marked places the prior is worth.
    covered_strength: float = 2.0
    #: Reads a spelling as a bank word plus an ending (``corpus/inflection.py``).
    #: The letter model learned from headwords, so it is sure of بخشم as
    #: *baxšm*, like چشم *čašm* — wrong; an inflected form is guessed but its
    #: confidence held at ``inflected_cap`` until the bank's stems give it a
    #: reading of its own.
    inflection: Analyser | None = None
    inflected_cap: float = 0.4
    #: Per pattern family (``inflect.family``): (fits, total) of the corpus's
    #: marked inflected words whose one built reading the signs judged. A
    #: built reading's confidence is its family's share, smoothed and divided
    #: among the word's other built readings; a family never marked keeps
    #: ``inflected_cap``. Measured on marked words — the hard ones — so low.
    inflected_fit: dict[str, tuple[int, int]] = field(default_factory=dict)
    #: Builds readings of inflected forms from the bank's stems, offered as
    #: alternatives (:mod:`.inflect`). Without it only the bank and the
    #: letter model's next-best guesses are offered.
    inflector: Inflector | None = None
    #: How many alternatives a word offers at most.
    offered: int = 5
    #: How sure the verse rule for و is: *o* inside a verse half, *va* at its
    #: start and in prose. A rule of thumb, not measured, so mid at most.
    conjunction_confidence: float = 0.8

    def fitted(self, kind: str) -> float:
        """The measured share of a pattern family's built readings that fit."""
        found = self.inflected_fit.get(kind)
        if not found:
            return self.inflected_cap
        fits, total = found
        return (fits + 1) / (total + 2)

    def coverage(self, spelling: str) -> float:
        """How likely the right reading is among this spelling's candidates."""
        hits, misses = self.covered.get(spelling, (0, 0))
        return (hits + self.covered_strength * self.covered_prior) / (
            hits + misses + self.covered_strength
        )

    def word(
        self,
        written: str,
        spelling: str,
        before: str | None,
        after: str | None,
        *,
        use_signs: bool = True,
        verse: bool | None = None,
        first: bool = False,
    ) -> Word:
        """Read one word between its neighbours, all three keyed by :func:`key`.

        ``use_signs=False`` reads the word as if it carried no vowel signs:
        how the model is measured against the signs it would otherwise use.
        """
        function = self.functions.get(spelling, ())
        if spelling == "و" and verse is not None and {"va", "o"} <= set(function):
            # In verse و is mostly the short *o* bound to the word before it
            # («نگشود و نگشاید»); at the start of a verse half, and in prose,
            # *va*. Mid at most: a rule of thumb (the project lead, 2026-11-14).
            said = "o" if verse and not first else "va"
            other = "va" if said == "o" else "o"
            if self.choice.person_alone.get(spelling):
                # People have picked و's reading on the reading screen: their
                # picks move the rule's reading, as they move any function
                # word's (the review of 2026-11-14).
                probs = self.choice.probabilities(
                    spelling, [said, other], before, after, function_reading=said
                )
                order = tuple(ranked(probs))
                return Word(
                    written, spelling, order[0][0], order[0][1], FUNCTION, order
                )
            sure = self.conjunction_confidence
            return Word(
                written,
                spelling,
                said,
                sure,
                FUNCTION,
                ((said, sure), (other, 1 - sure)),
            )
        candidates = list(dict.fromkeys((*function, *self.bank.get(spelling, ()))))
        # The analyser keeps half-spaces (بی‌کسان); the key drops them.
        forms = {normalise(written).strip(ZWNJ), spelling}
        built = self._built(forms, written, use_signs)
        if not candidates:
            guessed = self.letters.guess(spelling)
            if guessed is None and not built:
                return Word(written, spelling, None, 0.0, NONE)
            latin, confidence = guessed or (built[0][0], 0.0)
            source = LETTERS
            if self.inflection is not None and any(
                self.inflection.best(form) for form in forms
            ):
                source, confidence = INFLECTED, min(confidence, self.inflected_cap)
                # A reading built from the bank's stems beats a letter guess:
                # بخشم is *baxšam*, not *baxšm*; it is as sure as its pattern
                # family has measured, shared among the word's built readings.
                if built:
                    latin, kind = built[0]
                    confidence = self.fitted(kind) / len(built)
            if use_signs and harakat.fits(written, latin) is False:
                confidence = 0.0  # the text's own signs rule the guess out
            offered: list[tuple[str, float | None]] = [(latin, confidence)]
            offered += [(b, None) for b, _ in built]
            guessed_too = self._guessed(spelling, written, use_signs)
            if source == INFLECTED:
                # The letter model was measured on headwords; on an inflected
                # form its numbers would mislead (*baxšm* 93 %), so its other
                # guesses are offered without them.
                guessed_too = [(g, None) for g, _ in guessed_too]
            offered += guessed_too
            return Word(
                written, spelling, latin, confidence, source, self._unique(offered)
            )

        # A function word's marked places are its exceptions — که marked where
        # it is *koh*, در where it is *dorr* — so its coverage is not learned
        # from them: its prior is its whole uncertainty (2026-11-14).
        coverage = 1.0 if function else self.coverage(spelling)
        if use_signs and harakat.has_signs(written):
            verdicts = {c: harakat.fits(written, c) for c in candidates}
            confirmed = [c for c, v in verdicts.items() if v is True]
            undecided = [c for c, v in verdicts.items() if v is None]
            if confirmed:
                # The text itself confirms one of them: no doubt left about
                # coverage. A reading the signs cannot judge stays a candidate.
                candidates, coverage = confirmed + undecided, 1.0
            elif undecided:
                candidates = undecided
            else:
                # The text's signs fit none of the bank's readings: a person decides.
                coverage = 0.0

        probs = self.choice.probabilities(
            spelling, candidates, before, after, function[0] if function else None
        )
        order: list[tuple[str, float | None]] = [
            (c, p * coverage) for c, p in ranked(probs)
        ]
        latin, best = order[0]
        confidence = best or 0.0
        if latin in function:
            source = FUNCTION
        else:
            source = BANK if len(candidates) == 1 else CHOICE
        # The bank's readings first, then what the stems build (رود *ravad*
        # beside the bank's *Rud*): alternatives to pick, not to propose.
        order += [(b, None) for b, _ in built]
        return Word(written, spelling, latin, confidence, source, self._unique(order))

    def _built(
        self, forms: set[str], written: str, use_signs: bool
    ) -> list[tuple[str, str]]:
        """Readings the stems build, with their pattern family, the signs allowing."""
        if self.inflector is None:
            return []
        found: list[tuple[str, str]] = []
        seen: set[str] = set()
        for form in sorted(forms):
            for latin, kind in self.inflector.analyses(form):
                if use_signs and harakat.fits(written, latin) is False:
                    continue
                if latin not in seen:
                    seen.add(latin)
                    found.append((latin, kind))
        return found

    def _guessed(
        self, spelling: str, written: str, use_signs: bool
    ) -> list[tuple[str, float | None]]:
        """The letter model's next-best readings, the signs allowing."""
        return [
            (latin, p)
            for latin, p in self.letters.guesses(spelling, k=self.offered)
            if not (use_signs and harakat.fits(written, latin) is False)
        ]

    def _unique(
        self, offered: list[tuple[str, float | None]]
    ) -> tuple[tuple[str, float | None], ...]:
        """Each reading once, the first mention kept, at most ``offered``."""
        seen: set[str] = set()
        out: list[tuple[str, float | None]] = []
        for latin, p in offered:
            if latin not in seen:
                seen.add(latin)
                out.append((latin, p))
        return tuple(out[: self.offered])

    def line(
        self, text: str, *, use_signs: bool = True, verse: bool | None = None
    ) -> list[Word]:
        """Every counted word of a line, with the words beside it as context."""
        counted = [(t.fa, key(t.spelling)) for t in tokens(text) if t.spelling]
        return [
            self.word(
                written,
                spelling,
                counted[i - 1][1] if i else None,
                counted[i + 1][1] if i + 1 < len(counted) else None,
                use_signs=use_signs,
                verse=verse,
                first=i == 0,
            )
            for i, (written, spelling) in enumerate(counted)
        ]

    # -- keeping it ------------------------------------------------------------

    def save(self, path: Path, meta: dict[str, Any] | None = None) -> None:
        """Write the learned parts to one JSON file (the bank stays the lexicon's)."""
        path.write_text(
            json.dumps(
                {
                    "meta": meta or {},
                    "covered_prior": self.covered_prior,
                    "covered_strength": self.covered_strength,
                    "covered": {k: list(v) for k, v in self.covered.items()},
                    "inflected_fit": {
                        k: list(v) for k, v in self.inflected_fit.items()
                    },
                    "letters": self.letters.to_dict(),
                    "choice": self.choice.to_dict(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(
        cls,
        path: Path,
        bank: dict[str, tuple[str, ...]],
        inflection: Analyser | None = None,
    ) -> Transcriber:
        """Read a model file back, with the bank (and analyser) it was built beside."""
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            bank=bank,
            inflection=inflection,
            letters=LetterModel.from_dict(raw["letters"]),
            choice=ChoiceModel.from_dict(raw["choice"]),
            covered={k: (v[0], v[1]) for k, v in raw["covered"].items()},
            covered_prior=raw["covered_prior"],
            covered_strength=raw["covered_strength"],
            inflected_fit={
                k: (v[0], v[1]) for k, v in raw.get("inflected_fit", {}).items()
            },
        )


def bank_from(readings: Iterable[tuple[str, str]]) -> dict[str, tuple[str, ...]]:
    """(spelling, reading) pairs, such as the lexicon's, as the transcriber's bank."""
    found: dict[str, list[str]] = {}
    for spelling, latin in readings:
        if not latin:
            continue
        known = found.setdefault(key(spelling), [])
        if latin not in known:
            known.append(latin)
    return {k: tuple(v) for k, v in found.items()}
