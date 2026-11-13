"""The word bank: the whole lexicon, browsed by the linguist's groups.

    GET /bank/groups                         his twelve groups, counts, what each feeds
    GET /bank?group=نام&q=…&offset=0&limit=50  one page of words

Asked for by the linguist with the word bank (2026-11-09): every word of karbon
1.3.2 in his groups and under his names, searchable, with both stems shown for
a verb. Read straight from the lexicon snapshot — nothing here needs the corpus
or a build — so it works the moment the snapshot is configured.

**Order is Persian alphabetical order**, not code-point order: پ، چ، ژ، گ sit
outside the Arabic block, and a plain sort files them after ی. The list is
built once per process and snapshot (58,000 readings, half a second) and kept,
because the file behind it does not change while the app runs.

A loanword is listed like any other word and says that it builds nothing
(`in_word_formation: false`), which is how the linguist wants them: out of
word formation, visible in the bank.
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from murfulu.corpus.wordtypes import normalise
from murfulu.generation import bases_of
from murfulu.lexicon import bank
from murfulu.lexicon.entries import Reading
from murfulu.lexicon.snapshot import SnapshotMissingError, SnapshotNotConfiguredError
from murfulu.lexicon.store import Lexicon

router = APIRouter(tags=["bank"])

#: The Persian alphabet in dictionary order. Anything else sorts after it, in
#: code-point order; a ZWNJ or a space is skipped for the order and kept only
#: to break a tie.
_ALPHABET = "آاأإءبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیئ"
_RANK = {letter: rank for rank, letter in enumerate(_ALPHABET)}
_SKIP = {"\u200c", " ", "-"}

#: The combining hamza above and below (خامهٔ). The corpus normalisation keeps
#: them; for ordering and finding a word in the bank they are not letters.
_HAMZA_MARKS = {"\u0654", "\u0655"}

#: Most a page may hold. The list is for reading, not for downloading.
MAX_LIMIT = 200


def _plain(text: str) -> str:
    """What a search and the order compare: no ZWNJ, spaces or hamza marks."""
    return "".join(
        letter
        for letter in normalise(text)
        if letter not in _SKIP and letter not in _HAMZA_MARKS
    )


def sort_key(spelling: str) -> tuple[tuple[int, ...], str]:
    """Persian alphabetical order, then the spelling itself as the tie-break."""
    ranks = tuple(
        _RANK.get(letter, len(_ALPHABET) + ord(letter)) for letter in _plain(spelling)
    )
    return ranks, spelling


def _latin(text: str) -> str:
    """A Latin form as a search compares it: composed (NFC), lower case."""
    return unicodedata.normalize("NFC", text).lower()


@dataclass(frozen=True)
class Entry:
    """One reading of the bank, with what a search compares against."""

    reading: Reading
    persian: str
    latin: tuple[str, ...]

    def matches(self, query: str, exact: bool = False) -> bool:
        """Persian letters match the spelling; Latin, any reading or stem.

        ``exact`` asks for the word itself rather than every word holding the
        letters: the reading screen links a word to its entry, and «دل» as a
        substring is دلبر، دلدار and three hundred more before it.
        """
        if any("؀" <= letter <= "ۿ" for letter in query):
            return (
                _plain(query) == self.persian
                if exact
                else _plain(query) in self.persian
            )
        wanted = _latin(query)
        if exact:
            return wanted in self.latin
        return any(wanted in one for one in self.latin)


@dataclass(frozen=True)
class Shelf:
    """The whole bank of one snapshot, in order."""

    snapshot_id: str
    has_bank: bool
    entries: tuple[Entry, ...]
    #: Readings per group, in karbon's order: what the list will show, so a
    #: button and the list under it never disagree (6,454 loanword rows are
    #: 6,432 readings).
    counts: dict[str, int]
    labels: dict[str, str]


@lru_cache(maxsize=2)
def _shelf(snapshot_id: str) -> Shelf:
    del snapshot_id  # the cache key; the snapshot is reopened below
    with Lexicon.open() as lexicon:
        readings = sorted(
            lexicon.all_readings(), key=lambda one: sort_key(one.spelling_fa)
        )
        entries = tuple(
            Entry(
                reading=one,
                persian=_plain(one.spelling_fa),
                latin=tuple(
                    _latin(latin)
                    for latin in (
                        *one.all_latin,
                        one.past_stem_latin or "",
                        one.present_stem_latin or "",
                    )
                    if latin
                ),
            )
            for one in readings
        )
        order = list(lexicon.count_by_bank_group())
        counted = Counter(key for entry in entries for key in entry.reading.bank_groups)
        counts = {key: counted[key] for key in order if counted[key]}
        counts.update({key: n for key, n in counted.items() if key not in counts})
        return Shelf(
            snapshot_id=lexicon.snapshot_id,
            has_bank=lexicon.has_bank,
            entries=entries,
            counts=counts,
            labels=lexicon.bank_labels(),
        )


def _current() -> Shelf:
    try:
        with Lexicon.open() as lexicon:
            snapshot_id = lexicon.snapshot_id
    except (SnapshotNotConfiguredError, SnapshotMissingError) as missing:
        raise HTTPException(503, f"no lexicon snapshot: {missing}") from None
    return _shelf(snapshot_id)


def _as_json(reading: Reading, mapping: bank.BankMapping) -> dict[str, Any]:
    groups = [
        {
            "key": key,
            "label_fa": mapping.groups[key].label_fa if key in mapping.groups else key,
        }
        for key in reading.bank_groups
    ]
    verb = reading.is_infinitive
    return {
        "spelling_fa": reading.spelling_fa,
        "latin": reading.latin,
        "latin_variants": list(reading.latin_variants),
        "groups": groups,
        "lexicon_category": reading.lexicon_category,
        # Whether anything is built from it: false for a loanword, and for a
        # suffix, conjunction or interjection entry, which feed no rule — and,
        # on a snapshot from before the bank, for whatever its dictionary
        # category leaves unmapped. The same test the build screen makes.
        "in_word_formation": bool(bases_of(reading)),
        "needs_review": reading.needs_review,
        "definition_fa": reading.definition_fa,
        "definition_truncated": reading.definition_truncated,
        "past_stem_fa": reading.past_stem_fa if verb else None,
        "past_stem_latin": reading.past_stem_latin if verb else None,
        "present_stem_fa": reading.present_stem_fa if verb else None,
        "present_stem_latin": reading.present_stem_latin if verb else None,
        "sense_count": reading.sense_count,
    }


@router.get("/bank/groups")
def groups() -> dict[str, Any]:
    """The linguist's groups in his order, their sizes, and what each feeds."""
    shelf = _current()
    mapping = bank.loaded()
    return {
        "lexicon_snapshot_id": shelf.snapshot_id,
        "has_bank": shelf.has_bank,
        "total": len(shelf.entries),
        "stem_labels": {
            "past": shelf.labels.get("past_stem", ""),
            "present": shelf.labels.get("present_stem", ""),
        },
        "groups": [
            {
                "key": key,
                "label_fa": mapping.group(key).label_fa,
                "words": count,
                "word_classes": list(mapping.group(key).word_classes),
                "in_word_formation": mapping.group(key).in_word_formation,
            }
            for key, count in shelf.counts.items()
        ],
    }


@router.get("/bank")
def page(
    group: str | None = Query(None, description="one of the linguist's groups"),
    q: str | None = Query(None, max_length=60, description="Persian or Latin"),
    exact: bool = Query(False, description="the word itself, not words holding it"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=MAX_LIMIT),
) -> dict[str, Any]:
    """One page of the bank, in Persian alphabetical order."""
    shelf = _current()
    mapping = bank.loaded()
    if group and group not in mapping.groups:
        raise HTTPException(400, f"«{group}» is not a group of the word bank")
    query = (q or "").strip()
    found = [
        entry
        for entry in shelf.entries
        if (not group or group in entry.reading.bank_groups)
        and (not query or entry.matches(query, exact))
    ]
    shown = found[offset : offset + limit]
    return {
        "lexicon_snapshot_id": shelf.snapshot_id,
        "group": group,
        "q": query or None,
        "exact": exact,
        "total": len(found),
        "offset": offset,
        "limit": limit,
        "words": [_as_json(entry.reading, mapping) for entry in shown],
    }
