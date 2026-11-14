"""Suggestions while a reader types: words from the bank, texts from the corpus.

    GET /suggest/words?q=دل&limit=8            spellings, or Latin readings
    GET /suggest/words?q=raf&builds=true       only words the rules build from
    GET /suggest/words?q=ken&primary=true      only a word's first reading
    GET /suggest/texts?q=حافظ غز&limit=8        authors, works, sections, texts

Asked for by the project lead (2026-11-14): *every search field should
suggest while typing*. Both answers are small and fast, because they are asked
for on every pause in typing: at most :data:`MAX_LIMIT` suggestions, and the
words come out of an index built once per lexicon snapshot rather than a scan.

**A word is suggested in the script it was typed in.** Persian letters are
matched against the spelling and come back one suggestion per spelling, with
its readings beside it — دل is *del*, *dal* and *dol*, and that is one word to
pick, not three. Latin is matched against every reading (not the stems, which
are not words) and comes back one suggestion per reading, with its spellings.
What the reader picks goes into the box exactly as shown.

**What starts with the letters comes first**, in the bank's own order for
Persian and in alphabetical order for Latin; words that only hold them follow,
and only if there is room. Latin is compared without its marks, so *kar*
reaches *kār*: a phone keyboard has no macron.

**The bank's order and matching are the bank's** (:mod:`murfulu.api.bank`):
the same spellings, folded the same way, so a suggestion always finds itself
when the bank is searched for it.
"""

from __future__ import annotations

import bisect
import itertools
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from elasticsearch import ApiError, NotFoundError, TransportError
from fastapi import APIRouter, HTTPException, Query

from murfulu.api import bank as bank_api
from murfulu.generation import bases_of
from murfulu.search import suggest as texts_suggest
from murfulu.search.indices import connect

router = APIRouter(tags=["suggest"])

#: Most suggestions one answer may carry.
MAX_LIMIT = texts_suggest.MAX_SUGGESTIONS

#: The marks a Latin reading carries that a phone keyboard does not: what a
#: comparison drops, beside the combining marks NFD splits off.
_APOSTROPHES = {"'", "’", "ʾ", "ʿ", "`"}


def fold_latin(text: str) -> str:
    """A Latin form as a suggestion compares it: no marks, lower case."""
    split = unicodedata.normalize("NFD", text)
    return "".join(
        letter
        for letter in split
        if not unicodedata.combining(letter) and letter not in _APOSTROPHES
    ).lower()


def _is_persian(text: str) -> bool:
    return any("؀" <= letter <= "ۿ" for letter in text)


@dataclass(frozen=True)
class WordIndex:
    """The bank's readings, sorted twice: by Persian letters and by Latin."""

    shelf: bank_api.Shelf
    #: (letters, position on the shelf), in code-point order for bisecting.
    persian: tuple[tuple[str, int], ...]
    #: (folded reading, the reading as written, position on the shelf).
    latin: tuple[tuple[str, str, int], ...]


@lru_cache(maxsize=2)
def _index(snapshot_id: str) -> WordIndex:
    shelf = bank_api._shelf(snapshot_id)
    persian = sorted((entry.persian, at) for at, entry in enumerate(shelf.entries))
    latin = sorted(
        {
            (fold_latin(form), form, at)
            for at, entry in enumerate(shelf.entries)
            for form in entry.reading.all_latin
            if form
        }
    )
    return WordIndex(shelf=shelf, persian=tuple(persian), latin=tuple(latin))


def _current() -> WordIndex:
    return _index(bank_api._current().snapshot_id)


class _Builds:
    """Whether a reading feeds a rule, asked once per reading."""

    def __init__(self, shelf: bank_api.Shelf) -> None:
        self.shelf = shelf
        self.known: dict[int, bool] = {}

    def __call__(self, at: int) -> bool:
        if at not in self.known:
            self.known[at] = bool(bases_of(self.shelf.entries[at].reading))
        return self.known[at]


def _persian(
    index: WordIndex, query: str, limit: int, builds: bool
) -> list[dict[str, Any]]:
    letters = bank_api._plain(query)
    if not letters:
        return []
    shelf = index.shelf
    feeds = _Builds(shelf)
    start = bisect.bisect_left(index.persian, (letters, -1))
    starting = []
    for plain, at in index.persian[start:]:
        if not plain.startswith(letters):
            break
        starting.append(at)
    # Back into the bank's own order, where one spelling's readings stand
    # together: the first new spelling after the list is full ends it.
    starting.sort()
    chosen: dict[str, list[int]] = {}

    def take(positions: list[int]) -> None:
        for at in positions:
            spelling = shelf.entries[at].reading.spelling_fa
            if spelling not in chosen and len(chosen) >= limit:
                return
            if not builds or feeds(at):
                chosen.setdefault(spelling, []).append(at)

    take(starting)
    if len(chosen) < limit:
        take(
            [
                at
                for at, entry in enumerate(shelf.entries)
                if letters in entry.persian and not entry.persian.startswith(letters)
            ]
        )
    return [
        {
            "value": spelling,
            "spellings": [spelling],
            "latin": list(
                dict.fromkeys(shelf.entries[at].reading.latin for at in positions)
            ),
        }
        for spelling, positions in chosen.items()
    ]


def _latin(
    index: WordIndex, query: str, limit: int, builds: bool, primary: bool = False
) -> list[dict[str, Any]]:
    wanted = fold_latin(query.strip())
    if not wanted:
        return []
    shelf = index.shelf
    feeds = _Builds(shelf)
    chosen: dict[str, list[int]] = {}

    def take(form: str, at: int) -> bool:
        """Add one row; False once the list is full and this is a new reading."""
        if form not in chosen and len(chosen) >= limit:
            return False
        if primary and shelf.entries[at].reading.latin != form:
            return True
        if not builds or feeds(at):
            chosen.setdefault(form, []).append(at)
        return True

    # Sorted, so the readings that start with the letters are one run, and the
    # rows of one reading stand together inside it: the first new reading
    # after the list is full ends the run.
    start = bisect.bisect_left(index.latin, (wanted,))
    for folded, form, at in itertools.islice(index.latin, start, None):
        if not folded.startswith(wanted) or not take(form, at):
            break
    if len(chosen) < limit:
        holding = (
            (form, at)
            for folded, form, at in index.latin
            if wanted in folded and not folded.startswith(wanted)
        )
        for form, at in holding:
            if not take(form, at):
                break
    return [
        {
            "value": form,
            "spellings": list(
                dict.fromkeys(shelf.entries[at].reading.spelling_fa for at in positions)
            ),
            "latin": [form],
        }
        for form, positions in chosen.items()
    ]


def suggest_words(
    query: str, limit: int = 8, builds: bool = False, primary: bool = False
) -> list[dict[str, Any]]:
    """Words of the bank that start with, then hold, what was typed."""
    index = _current()
    query = query.strip()
    if _is_persian(query):
        return _persian(index, query, limit, builds)
    return _latin(index, query, limit, builds, primary)


@router.get("/suggest/words")
def words(
    q: str = Query(..., min_length=1, max_length=60, description="Persian or Latin"),
    limit: int = Query(8, ge=1, le=MAX_LIMIT),
    builds: bool = Query(False, description="only words the rules build from"),
    primary: bool = Query(
        False,
        description="Latin: only a word's first reading, which /search matches",
    ),
) -> dict[str, Any]:
    """Up to ``limit`` words of the bank for what was typed so far."""
    found = suggest_words(q, limit, builds, primary)
    return {
        "q": q,
        "script": "fa" if _is_persian(q) else "latin",
        "suggestions": found,
    }


@router.get("/suggest/texts")
def texts(
    q: str = Query(
        ..., min_length=1, max_length=120, description="author, work, title"
    ),
    limit: int = Query(8, ge=1, le=MAX_LIMIT),
) -> dict[str, Any]:
    """Up to ``limit`` authors, works, sections and texts for what was typed."""
    try:
        found = texts_suggest.suggest(connect(), q, limit=limit)
    except NotFoundError:
        raise HTTPException(503, "index 'documents' has not been built") from None
    except (ApiError, TransportError, OSError) as unreachable:
        raise HTTPException(
            503, f"the search index is not reachable: {unreachable}"
        ) from None
    return {"q": q, "suggestions": found}
