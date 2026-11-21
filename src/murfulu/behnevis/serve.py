"""The automatic Behnevis on the reading screen: one reading per word, and a level.

The project lead's direction A (2026-11-14): under each word the screen shows
the model's reading, coloured by how sure the model is — **sure**, **mid** or
**unsure** — and a press lets the reader pick another of the word's readings
or type one. What the reader picks is collected as a proposal for karbon
(the feedback store, owned by karbon); it never changes the bank or the model.

The model file is configured like every other data file
(``MURFULU_BEHNEVIS_PATH``); without it the screen shows what it showed before,
every reading of the bank alike.

**The poem's metre** (the project lead's decision of 2026-11-21, DECISIONS):
where a verse text's metre is known, each verse half's words are weighed
against it before they are shown (:mod:`murfulu.behnevis.metre`). The labels
are a file beside the model, ``behnevis-metre-<version>.json`` beside
``behnevis-<version>.json`` (``tools/extract_metre_lines.py``), so a release
of another version takes its own. ``MURFULU_BEHNEVIS_METRE=off`` turns the
step off without removing anything; without the file it is off too.
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from murfulu.behnevis.inflect import Inflector
from murfulu.behnevis.metre import Metre, patterns
from murfulu.behnevis.transcribe import Transcriber, Word, bank_from, key
from murfulu.behnevis.vowels import vocalise_written
from murfulu.corpus.inflection import Analyser, held_from
from murfulu.lexicon.store import Lexicon

_log = logging.getLogger(__name__)

#: Where the model lives. Never a literal in the code.
PATH_VARIABLE = "MURFULU_BEHNEVIS_PATH"
#: ``off`` turns the metre step off; anything else, or nothing, leaves it on
#: wherever the labels file is there.
METRE_VARIABLE = "MURFULU_BEHNEVIS_METRE"

#: The levels' lower edges. At 0.9 and above a reading is *sure*; from 0.7
#: *mid*; below, *unsure*. Measured on held-out data (data/behnevis-eval-v17.md):
#: at 0.9 the choice among several readings is 94 % right and a guessed
#: unknown word 91 %; at 0.7, 90 % and 84 %. The project lead may move them
#: (OPEN_QUESTIONS S47).
SURE, MID = 0.9, 0.7

#: How many readings a word's panel offers to pick from.
OFFERED = 5


def level(confidence: float) -> str:
    """The level a confidence falls in."""
    if confidence >= SURE:
        return "sure"
    if confidence >= MID:
        return "mid"
    return "unsure"


def path() -> Path | None:
    """The configured model file, if there is one and it exists."""
    configured = os.environ.get(PATH_VARIABLE)
    if not configured:
        return None
    found = Path(configured).expanduser()
    return found if found.is_file() else None


@lru_cache(maxsize=2)
def _load(model: str, changed: float, snapshot_id: str) -> Transcriber:
    # `changed` and `snapshot_id` are the cache key: a model file rebuilt in
    # place (`deploy/server.sh data`) or a new lexicon is read again without
    # restarting the api.
    del changed, snapshot_id
    with Lexicon.open() as lexicon:
        readings = list(lexicon.all_readings())
        bank = bank_from(
            (r.spelling_fa, latin) for r in readings for latin in r.all_latin if latin
        )
        inflection = Analyser(held_from(lexicon))
    transcriber = Transcriber.load(Path(model), bank, inflection)
    transcriber.inflector = Inflector.from_readings(readings, inflection)
    return transcriber


def loaded() -> Transcriber | None:
    """The model with the bank it reads, or None when none is configured."""
    model = path()
    if model is None:
        return None
    try:
        with Lexicon.open() as lexicon:
            snapshot_id = lexicon.snapshot_id
    except Exception:  # no lexicon: the screen goes without, as before
        return None
    return _load(str(model), model.stat().st_mtime, snapshot_id)


def metre_path() -> Path | None:
    """The metre labels beside the model, if the step is on and the file is there."""
    if os.environ.get(METRE_VARIABLE, "").strip().lower() == "off":
        return None
    model = path()
    if model is None:
        return None
    found = model.with_name(model.name.replace("behnevis-", "behnevis-metre-", 1))
    return found if found.is_file() and found != model else None


@lru_cache(maxsize=2)
def _metres(table: str, changed: float) -> dict[str, str]:
    del changed  # the cache key: a file replaced in place is read again
    raw = json.loads(Path(table).read_text(encoding="utf-8"))
    labels = raw["labels"]
    if not all(isinstance(label, str) for label in labels):
        raise ValueError("a metre label is not text")
    return {str(document): labels[i] for document, i in raw["documents"].items()}


def metre_of(document_id: str) -> str | None:
    """The metre label of a text, or None when the step is off or it has none.

    A labels file that cannot be read is logged and treated as absent: the
    metre is an addition, and the reading screen must not fail for it.
    """
    table = metre_path()
    if table is None:
        return None
    try:
        return _metres(str(table), table.stat().st_mtime).get(document_id)
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError):
        _log.warning("metre labels unreadable, metre off: %s", table, exc_info=True)
        return None


def annotate(
    units: list[dict[str, Any]], transcriber: Transcriber, metre: str | None = None
) -> None:
    """Give each counted word of a window its reading, confidence and level.

    Sets ``auto`` on the word's dict, read line by line so each word has its
    neighbours. A note's lines carry no words and are passed over. With the
    text's ``metre`` label, each verse half's words are weighed against it.
    """
    allowed = patterns(metre) if metre else frozenset()
    weigher = Metre(functions=frozenset(transcriber.functions)) if allowed else None
    for unit in units:
        # Verse or prose decides how و is read; a unit of unknown kind says nothing.
        verse = {"couplet": True, "half": True, "prose": False}.get(
            unit.get("kind") or ""
        )
        for line in unit.get("lines") or []:
            words = [w for w in line.get("words") or [] if w.get("s")]
            keys = [key(w["s"]) for w in words]
            reads: list[Word] = [
                transcriber.word(
                    word["fa"],
                    keys[i],
                    keys[i - 1] if i else None,
                    keys[i + 1] if i + 1 < len(words) else None,
                    verse=verse,
                    first=i == 0,
                )
                for i, word in enumerate(words)
            ]
            if weigher is not None and verse:
                reads = _weighed(weigher, reads, allowed)
            for i, (word, read) in enumerate(zip(words, reads, strict=True)):
                if read.latin is None:
                    continue
                word["auto"] = {
                    "latin": read.latin,
                    "confidence": round(read.confidence, 3),
                    "level": level(read.confidence),
                    "source": read.source,
                    # An alternative built from the stems carries no estimate.
                    "candidates": [
                        [latin, None if p is None else round(p, 3)]
                        for latin, p in read.candidates[:OFFERED]
                    ],
                    # The readings the bank or the function-word list holds: a
                    # pick of one teaches the model; any other is for karbon.
                    "known": [
                        latin
                        for latin in dict.fromkeys(
                            (
                                *transcriber.functions.get(keys[i], ()),
                                *transcriber.bank.get(keys[i], ()),
                            )
                        )
                    ],
                }
                # The word with this reading's short vowels, for display only,
                # and only where it adds a mark (DECISIONS 2026-11-21).
                marked = vocalise_written(word["fa"], read.latin)
                if marked != word["fa"]:
                    word["auto"]["fa_marked"] = marked


def _weighed(metre: Metre, reads: list[Word], allowed: frozenset[str]) -> list[Word]:
    """The line's words weighed by the metre, the screen's numbers kept as they mean.

    A reading the model offered without a number (one built from the stems)
    still shows none: the panel says it carries no estimate. The word's own
    confidence, which sets its level, is the metre's.
    """
    out: list[Word] = []
    for before, after in zip(reads, metre.weigh(reads, allowed), strict=True):
        unnumbered = {latin for latin, p in before.candidates if p is None}
        word = after.word
        out.append(
            Word(
                word.written,
                word.spelling,
                word.latin,
                word.confidence,
                word.source,
                tuple(
                    (latin, None if latin in unnumbered else p)
                    for latin, p in word.candidates
                ),
            )
        )
    return out
