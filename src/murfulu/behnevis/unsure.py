"""The spellings the reading screen most often leaves to a person, ranked.

On the reading screen a word below 0.7 is red: a person decides it. Most of
those places are a few thousand spellings met again and again, so a reading
decided once for a spelling, and applied wherever it stands in like places,
saves the same decision at each of them (the project lead's request of
2026-11-21). This module counts the places as the screen reads them
(:func:`murfulu.behnevis.serve.annotate`, with the poem's metre where it is
served), ranks the spellings by how many running words they leave to a
person, and says what kind of decision each one needs:

- **choice**: the word bank holds several readings. Deciding picks one of
  them, and the model learns it at its next build.
- **one**: the bank holds one reading and the model still doubts it, because
  the marked corpus often fits none of the bank's readings (بود: the bank's
  *Bud*, the editions' «بُوَد»). Deciding confirms the bank's reading, which
  the model learns, or names one the bank lacks, which goes to karbon.
- **missing**: the bank holds no reading (inflected forms, words karbon
  lacks). Deciding names a reading for karbon's word bank; the model learns
  it only once the bank holds it (DECISIONS 2026-11-14, *a typed reading goes
  to karbon*).

``tools/measure_unsure_spellings.py`` reads the corpus, writes the list beside
the model (``behnevis-unsure-<version>.json``) and a report; the API serves
the list (``GET /texts/unsure``).
"""

from __future__ import annotations

import json
import zlib
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from murfulu.behnevis.transcribe import key
from murfulu.search import harakat

#: The reading screen's red edge (``serve.MID``): below it a person decides.
RED = 0.7

#: The three kinds of decision, in the order a report lists them.
CHOICE, ONE, MISSING = "choice", "one", "missing"
KINDS = (CHOICE, ONE, MISSING)

#: How many neighbours, readings and example places a listed spelling keeps.
NEIGHBOURS = 12
READINGS = 6
EXAMPLES = 3

#: Before or after the spelling, as a neighbour's side is written.
BEFORE, AFTER = "before", "after"


def kind_of(
    spelling: str,
    bank: dict[str, tuple[str, ...]],
    functions: dict[str, tuple[str, ...]],
) -> str:
    """What deciding this spelling means, by what the bank and the list hold."""
    held = set(functions.get(spelling, ())) | set(bank.get(spelling, ()))
    if len(held) >= 2:
        return CHOICE
    if held:
        return ONE
    return MISSING


def _rank(place: str) -> int:
    """A stable number for a place, so the examples spread over the corpus."""
    return zlib.crc32(place.encode("utf-8"))


@dataclass
class Tally:
    """Running words per spelling, read as the reading screen reads them.

    Counts every counted word; keeps neighbours, readings and examples only
    for the spellings in ``watch`` (all when it is None), since the corpus
    has hundreds of thousands of spellings and only the frequent ones are
    listed.
    """

    watch: frozenset[str] | None = None
    words: int = 0
    unsure_words: int = 0
    places: Counter[str] = field(default_factory=Counter)
    unsure: Counter[str] = field(default_factory=Counter)
    #: Unsure places by where the reading came from (``Word.source``).
    sources: Counter[tuple[str, str]] = field(default_factory=Counter)
    #: The model's reading at unsure places.
    read_as: Counter[tuple[str, str]] = field(default_factory=Counter)
    #: Readings the panel offered at unsure places, how often each.
    offered: Counter[tuple[str, str]] = field(default_factory=Counter)
    #: The counted spelling as written (half-spaces kept), for display.
    written: Counter[tuple[str, str]] = field(default_factory=Counter)
    #: (spelling, side, neighbour) → places, and unsure places.
    near: Counter[tuple[str, str, str]] = field(default_factory=Counter)
    near_unsure: Counter[tuple[str, str, str]] = field(default_factory=Counter)
    #: spelling → up to EXAMPLES unsure places, those of lowest rank.
    examples: dict[str, list[tuple[int, dict[str, Any]]]] = field(default_factory=dict)

    def watched(self, spelling: str) -> bool:
        """Whether this spelling keeps its details."""
        return self.watch is None or spelling in self.watch

    def add_line(self, words: Sequence[dict[str, Any]], where: dict[str, Any]) -> None:
        """Count one line's words, each as ``serve.annotate`` left it.

        ``words`` is the line as the screen holds it, uncounted tokens
        included, so a place's word index is the screen's; ``where`` names
        the text, unit and line (and the heading) for the examples.
        """
        counted = [(i, w) for i, w in enumerate(words) if w.get("s")]
        keys = [key(w["s"]) for _, w in counted]
        text: str | None = None
        for at, ((index, word), spelling) in enumerate(zip(counted, keys, strict=True)):
            auto = word.get("auto")
            # The level the screen shows: the confidence it carries is rounded.
            red = auto is None or auto.get("level") == "unsure"
            self.words += 1
            self.places[spelling] += 1
            self.unsure_words += red
            self.unsure[spelling] += red
            if not self.watched(spelling):
                continue
            self.written[(spelling, word["s"])] += 1
            before = keys[at - 1] if at else None
            after = keys[at + 1] if at + 1 < len(keys) else None
            for side, near in ((BEFORE, before), (AFTER, after)):
                if near:
                    self.near[(spelling, side, near)] += 1
                    self.near_unsure[(spelling, side, near)] += red
            if not red:
                continue
            self.sources[(spelling, auto["source"] if auto else "none")] += 1
            if auto:
                self.read_as[(spelling, auto["latin"])] += 1
                for latin, _ in auto.get("candidates") or []:
                    self.offered[(spelling, latin)] += 1
            place = {**where, "word": index}
            rank = _rank(
                f"{place.get('document_id')}:{place.get('unit')}:"
                f"{place.get('line')}:{index}"
            )
            kept = self.examples.setdefault(spelling, [])
            if len(kept) < EXAMPLES or rank < kept[-1][0]:
                if text is None:
                    text = " ".join(w["fa"] + (w.get("after") or "") for w in words)
                kept.append((rank, {**place, "text": text}))
                kept.sort(key=lambda one: one[0])
                del kept[EXAMPLES:]

    def merge(self, other: Tally) -> None:
        """Add another tally's counts (one slice of the corpus) to this one."""
        self.words += other.words
        self.unsure_words += other.unsure_words
        pairs: tuple[tuple[Counter[Any], Counter[Any]], ...] = (
            (self.places, other.places),
            (self.unsure, other.unsure),
            (self.sources, other.sources),
            (self.read_as, other.read_as),
            (self.offered, other.offered),
            (self.written, other.written),
            (self.near, other.near),
            (self.near_unsure, other.near_unsure),
        )
        for mine, theirs in pairs:
            mine.update(theirs)
        for spelling, kept in other.examples.items():
            both = sorted(
                [*self.examples.get(spelling, []), *kept], key=lambda one: one[0]
            )
            self.examples[spelling] = both[:EXAMPLES]

    def ranked(self, top: int | None = None) -> list[str]:
        """Spellings by the places they leave to a person, the most first."""
        order = sorted(
            (s for s, n in self.unsure.items() if n),
            key=lambda s: (-self.unsure[s], -self.places[s], s),
        )
        return order if top is None else order[:top]


def _by_spelling(counts: Counter[Any], wanted: set[str]) -> dict[str, Counter[Any]]:
    """One counter per wanted spelling, read in one pass over a large counter."""
    out: dict[str, Counter[Any]] = {s: Counter() for s in wanted}
    for k, v in counts.items():
        if k[0] in out:
            out[k[0]][k[1:] if len(k) > 2 else k[1]] += v
    return out


def entries(
    tally: Tally,
    bank: dict[str, tuple[str, ...]],
    functions: dict[str, tuple[str, ...]],
    top: int,
) -> list[dict[str, Any]]:
    """The ``top`` spellings as the list keeps them, the most places first."""
    order = tally.ranked(top)
    wanted = set(order)
    sources = _by_spelling(tally.sources, wanted)
    read_as = _by_spelling(tally.read_as, wanted)
    offered = _by_spelling(tally.offered, wanted)
    written = _by_spelling(tally.written, wanted)
    near = _by_spelling(tally.near, wanted)
    near_unsure = _by_spelling(tally.near_unsure, wanted)
    out = []
    for rank, spelling in enumerate(order, start=1):

        def neighbours(side: str, spelling: str = spelling) -> list[list[Any]]:
            mine = [
                (w, n, near_unsure[spelling][(s, w)])
                for (s, w), n in near[spelling].items()
                if s == side
            ]
            mine.sort(key=lambda one: (-one[2], -one[1], one[0]))
            return [list(one) for one in mine[:NEIGHBOURS]]

        forms = written[spelling].most_common(1)
        out.append(
            {
                "rank": rank,
                "spelling": spelling,
                "written": forms[0][0] if forms else spelling,
                "places": tally.places[spelling],
                "unsure": tally.unsure[spelling],
                "kind": kind_of(spelling, bank, functions),
                "known": list(
                    dict.fromkeys(
                        (*functions.get(spelling, ()), *bank.get(spelling, ()))
                    )
                ),
                "sources": dict(sources[spelling].most_common()),
                "read_as": [list(kv) for kv in read_as[spelling].most_common(READINGS)],
                "offered": [list(kv) for kv in offered[spelling].most_common(READINGS)],
                BEFORE: neighbours(BEFORE),
                AFTER: neighbours(AFTER),
                "examples": [one for _, one in tally.examples.get(spelling, [])],
            }
        )
    return out


@dataclass(frozen=True)
class Covered:
    """What the ``top`` spellings leave to a person, in running words."""

    top: int
    spellings: int
    unsure: int
    by_kind: dict[str, int]


def coverage(
    tally: Tally,
    bank: dict[str, tuple[str, ...]],
    functions: dict[str, tuple[str, ...]],
    tops: Iterable[int],
) -> list[Covered]:
    """For each ``top``: the unsure running words its spellings hold, by kind."""
    order = tally.ranked()
    kinds = {s: kind_of(s, bank, functions) for s in order}
    out = []
    for top in tops:
        chosen = order[:top]
        by_kind = Counter({k: 0 for k in KINDS})
        for s in chosen:
            by_kind[kinds[s]] += tally.unsure[s]
        out.append(Covered(top, len(chosen), sum(by_kind.values()), dict(by_kind)))
    return out


@dataclass(frozen=True)
class Fit:
    """One spelling's marked places, read against its readings.

    ``fitted`` places have their signs fit at least one of the readings the
    list names for the spelling; ``best`` of them fit the one reading that
    fits most often; in ``none`` the signs fit no reading named.
    """

    fitted: int
    best: int
    none: int
    reading: str | None


def single_reading_fit(
    listed: Iterable[dict[str, Any]], marked: Iterable[dict[str, Any]]
) -> dict[str, Fit]:
    """How often one reading per spelling would be right, on the marked places.

    The question a decision *everywhere* raises: does the spelling read one
    way wherever it stands? Answered where the corpus's editions marked it:
    for each place, which of the readings the list names (the bank's, what
    the model read, what it offered) the signs fit. Editions mark the hard
    places, and the signs check only the letters they mark, so this is a
    rough reading of the question, not its answer.
    """
    readings = {
        one["spelling"]: list(
            dict.fromkeys(
                [
                    *one["known"],
                    *(latin for latin, _ in one["read_as"]),
                    *(latin for latin, _ in one["offered"]),
                ]
            )
        )
        for one in listed
    }
    counts: dict[str, Counter[str]] = {s: Counter() for s in readings}
    fitted: Counter[str] = Counter()
    none: Counter[str] = Counter()
    for row in marked:
        spelling = row.get("spelling") or ""
        if spelling not in readings:
            continue
        written = row["written"]
        fits = [r for r in readings[spelling] if harakat.fits(written, r) is True]
        if fits:
            fitted[spelling] += 1
            counts[spelling].update(fits)
        else:
            none[spelling] += 1
    out = {}
    for spelling, seen in counts.items():
        best = seen.most_common(1)
        out[spelling] = Fit(
            fitted[spelling],
            best[0][1] if best else 0,
            none[spelling],
            best[0][0] if best else None,
        )
    return out


#: How many marked places a spelling needs before its marks are read as a
#: sign of which reading it has (section 3 of the report).
MIN_MARKED = 5


def marks_another(one: dict[str, Any]) -> bool:
    """Whether the editions mark a listed *one* spelling for a reading the bank lacks.

    بود: the bank holds *Bud*; the editions' 1,464 marked places fit *bovad*.
    Deciding such a spelling names a reading for karbon, not one the model
    can learn now.
    """
    marked = one.get("marked") or {}
    return (
        one.get("kind") == ONE
        and (marked.get("fitted") or 0) >= MIN_MARKED
        and marked.get("reading") not in one.get("known", [])
    )


# -- the list on disk, as the API reads it ------------------------------------


def path_beside(model: Path) -> Path:
    """The list that goes with a model file: ``behnevis-unsure-v22.json``.

    A model named otherwise gets ``<name>.unsure.json`` beside it: never the
    model's own path, which writing the list would overwrite.
    """
    if model.name.startswith("behnevis-"):
        return model.with_name(model.name.replace("behnevis-", "behnevis-unsure-", 1))
    return model.with_name(f"{model.stem}.unsure.json")


def write(path: Path, meta: dict[str, Any], listed: list[dict[str, Any]]) -> None:
    """The list as one JSON file."""
    path.write_text(
        json.dumps({"meta": meta, "spellings": listed}, ensure_ascii=False),
        encoding="utf-8",
    )


def read(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The list as :func:`write` wrote it."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw["meta"], raw["spellings"]
