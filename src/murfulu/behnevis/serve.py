"""The automatic Behnevis on the reading screen: one reading per word, and a level.

The project lead's direction A (2026-11-14): under each word the screen shows
the model's reading, coloured by how sure the model is — **sure**, **mid** or
**unsure** — and a press lets the reader pick another of the word's readings
or type one. What the reader picks is collected as a proposal for karbon
(the feedback store, owned by karbon); it never changes the bank or the model.

The model file is configured like every other data file
(``MURFULU_BEHNEVIS_PATH``); without it the screen shows what it showed before,
every reading of the bank alike.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from murfulu.behnevis.inflect import Inflector
from murfulu.behnevis.transcribe import Transcriber, bank_from, key
from murfulu.corpus.inflection import Analyser, held_from
from murfulu.lexicon.store import Lexicon

#: Where the model lives. Never a literal in the code.
PATH_VARIABLE = "MURFULU_BEHNEVIS_PATH"

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


def annotate(units: list[dict[str, Any]], transcriber: Transcriber) -> None:
    """Give each counted word of a window its reading, confidence and level.

    Sets ``auto`` on the word's dict, read line by line so each word has its
    neighbours. A note's lines carry no words and are passed over.
    """
    for unit in units:
        # Verse or prose decides how و is read; a unit of unknown kind says nothing.
        verse = {"couplet": True, "half": True, "prose": False}.get(
            unit.get("kind") or ""
        )
        for line in unit.get("lines") or []:
            words = [w for w in line.get("words") or [] if w.get("s")]
            keys = [key(w["s"]) for w in words]
            for i, word in enumerate(words):
                read = transcriber.word(
                    word["fa"],
                    keys[i],
                    keys[i - 1] if i else None,
                    keys[i + 1] if i + 1 < len(words) else None,
                    verse=verse,
                    first=i == 0,
                )
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
                }
