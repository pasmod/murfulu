"""Reading a text: finding one, and laying it out word by word with its readings.

The reading screen (2026-11-13, the project lead's direction A) shows a text
from the corpus with each Persian word over its Behnevis. This module does the
three things that needs, and nothing that shows them:

**Find a text** by author, work, section or title, all at once: every word
typed must be in the text's ``heading`` (corpus v17 on). The best match comes
first, and texts that match equally come in the source's own order, so
«حافظ» lists the divan as it is printed.

**Lay a text out.** Each unit — a couplet, a verse half, a prose paragraph —
becomes its lines, and each line its words *as written*, harakat and all, each
paired with the spelling the corpus counted it under. The split is the
counting's own (:func:`tokens`, tested against ``wordtypes.tokenise``), so a
word on screen is always the word whose count it shows. A note is kept as text
and never split: it was never counted.

**Say what the bank knows of each spelling**: every reading, the linguist's
groups, the dictionary's definition, and the spelling's corpus count. Readings
come in alphabetical order and none is marked as the one meant — **which
reading a line needs is not something the letters say**, and the placeholder
rule the drafts used put *dall* under دل. A spelling with no reading comes
back with an empty list, never with a guess.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from elasticsearch import Elasticsearch

from murfulu.corpus.wordtypes import _FOLD, _MARKS, _WORD

DOCUMENTS = "documents"
WORD_TYPES = "word_types"

#: How many units one read returns. Ganjoor's longest page has 1,250
#: couplets; nearly all have fewer than this, and a longer one is paged.
DEFAULT_UNITS = 200
MAX_UNITS = 500

#: How many spellings one terms query asks for, so a long page of prose does
#: not send one enormous query.
_CHUNK = 500

ZWNJ = "‌"

#: What a word type is asked for. Counts are the spelling's, the rest the
#: reading's.
_WORD_FIELDS = [
    "id",
    "spelling_fa",
    "latin",
    "latin_variants",
    "bank_groups",
    "definition_fa",
    "total_count",
    "doc_count",
    "function_word",
    "corpus_version",
    "lexicon_snapshot_id",
]


@dataclass(frozen=True)
class Token:
    """One word as written, the spelling it was counted under, and what follows."""

    fa: str
    #: The counted spelling. None for what is not a counted word: an opening
    #: «, a number, a Latin name.
    spelling: str | None
    #: Punctuation written straight after the word, without a space between.
    after: str = ""

    def as_dict(self) -> dict[str, Any]:
        """The shape the API returns: short keys, a long text has thousands."""
        shown: dict[str, Any] = {"fa": self.fa, "s": self.spelling}
        if self.after:
            shown["after"] = self.after
        return shown


def tokens(line: str) -> list[Token]:
    """A line's words as written, each with the spelling the corpus counted.

    ``wordtypes.tokenise`` normalises first and then finds the words, so the
    surface a word came from is lost. Here the normalised text keeps a map back
    to the written one; a word's surface runs from its first letter to its last
    and takes the marks written after it (a kasra, the hamza of خانهٔ). The
    spellings come out exactly as ``tokenise`` gives them.
    """
    text = unicodedata.normalize("NFC", line)
    folded: list[str] = []
    origin: list[int] = []
    for index, char in enumerate(text):
        if _MARKS.match(char):
            continue
        folded.append(char.translate(_FOLD))
        origin.append(index)
    plain = "".join(folded)

    found: list[Token] = []
    written_to = 0
    for match in _WORD.finditer(plain):
        word = match.group()
        spelling = word.strip(ZWNJ)
        if not spelling:
            continue
        first = match.start() + (len(word) - len(word.lstrip(ZWNJ)))
        last = match.end() - (len(word) - len(word.rstrip(ZWNJ)))
        start, end = origin[first], origin[last - 1] + 1
        while end < len(text) and (
            unicodedata.combining(text[end]) or _MARKS.match(text[end])
        ):
            end += 1
        _between(found, text[written_to:start])
        found.append(Token(text[start:end], spelling))
        written_to = end
    _between(found, text[written_to:])
    return found


def _between(found: list[Token], gap: str) -> None:
    """Place what stands between two words: attached punctuation, or text.

    What touches the previous word with no space between — a comma, a
    closing guillemet — is written after it. Anything else that is not a word
    of the count — a number, a Latin name, an opening «, a run with spaces in
    it — becomes a part of its own, its spaces kept, so «سال ۱۲۳۴ خورشیدی»
    is not shown as «سال۱۲۳۴».
    """
    if not gap.strip():
        return
    rest = gap
    if found and not gap[0].isspace():
        attached = gap.split(maxsplit=1)[0] if gap.split() else ""
        found[-1] = Token(found[-1].fa, found[-1].spelling, found[-1].after + attached)
        rest = gap[len(attached) :]
    if rest.strip():
        found.append(Token(rest.strip(), None))


def _source_line(line: dict[str, Any]) -> list[str]:
    """A stored line's text, as text_fa holds it: a line break makes two."""
    return [one.strip() for one in (line.get("text") or "").splitlines() if one.strip()]


def _units(source: dict[str, Any]) -> list[dict[str, Any]]:
    """The stored units, or one unit per line for a text stored before v17."""
    stored = source.get("units") or []
    if stored:
        return list(stored)
    return [
        {"kind": "line", "lines": [{"text": line, "position": None}]}
        for line in (source.get("text_fa") or "").splitlines()
        if line.strip()
    ]


def lay_out(
    source: dict[str, Any], start: int = 0, limit: int = DEFAULT_UNITS
) -> tuple[list[dict[str, Any]], set[str], int]:
    """A window of a text's units, word by word, and the spellings in it.

    Each unit carries its ``index`` in the text and, if it is counted, its
    ``number`` among the counted units — the number a reader sees beside it.
    Returns the window, every spelling in it, and how many units the text has.
    """
    units = _units(source)
    spellings: set[str] = set()
    shown: list[dict[str, Any]] = []
    number = 0
    for index, unit in enumerate(units):
        counted = unit.get("kind") != "note"
        number += 1 if counted else 0
        if index < start or index >= start + limit:
            continue
        lines: list[dict[str, Any]] = []
        for line in unit.get("lines") or []:
            if not counted:
                lines.append({"position": line.get("position"), "text": line["text"]})
                continue
            words = [token for piece in _source_line(line) for token in tokens(piece)]
            spellings.update(t.spelling for t in words if t.spelling)
            lines.append(
                {
                    "position": line.get("position"),
                    "words": [t.as_dict() for t in words],
                }
            )
        shown.append(
            {
                "index": index,
                "number": number if counted else None,
                "kind": unit.get("kind"),
                "lines": lines,
            }
        )
    return shown, spellings, len(units)


def _reading(source: dict[str, Any], labels: dict[str, str]) -> dict[str, Any]:
    return {
        "id": source.get("id"),
        "latin": source["latin"],
        "latin_variants": list(source.get("latin_variants") or []),
        "groups": [labels.get(key, key) for key in source.get("bank_groups") or []],
        "definition_fa": source.get("definition_fa"),
    }


def look_up(
    client: Elasticsearch,
    spellings: Iterable[str],
    labels: dict[str, str],
    index: str = WORD_TYPES,
) -> tuple[dict[str, dict[str, Any]], str | None]:
    """What the bank and the corpus say of each spelling, and the bank's id.

    Every spelling asked for comes back, with no readings where the bank has
    none — the screen shows «؟» and never a guess.
    """
    wanted = sorted(set(spellings))
    words: dict[str, dict[str, Any]] = {
        spelling: {
            "readings": [],
            "total_count": None,
            "doc_count": None,
            "function_word": None,
        }
        for spelling in wanted
    }
    snapshot: str | None = None
    for at in range(0, len(wanted), _CHUNK):
        chunk = wanted[at : at + _CHUNK]
        response = client.search(
            index=index,
            size=10_000,
            query={"terms": {"spelling_fa": chunk}},
            source_includes=_WORD_FIELDS,
        )
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            entry = words.get(source.get("spelling_fa", ""))
            if entry is None:
                continue
            if source.get("total_count") is not None:
                # The spelling's count. A function word's reading carries
                # none; its spelling's own document does.
                entry["total_count"] = source["total_count"]
                entry["doc_count"] = source.get("doc_count")
            if source.get("function_word"):
                entry["function_word"] = source["function_word"]
            if source.get("latin"):
                entry["readings"].append(_reading(source, labels))
                snapshot = snapshot or source.get("lexicon_snapshot_id")
    for entry in words.values():
        # Alphabetical, so no order says which reading is meant.
        entry["readings"].sort(key=lambda one: (one["latin"].casefold(), one["latin"]))
    return words, snapshot


#: Words a heading search ignores: the joiners a reader types between names.
_SPLIT = re.compile(r"[\s،,·]+")


def find(
    client: Elasticsearch,
    query: str,
    *,
    offset: int = 0,
    size: int = 20,
    index: str = DOCUMENTS,
) -> dict[str, Any]:
    """Texts whose heading holds every word typed, the best first."""
    words = [one for one in _SPLIT.split(query.strip()) if one]
    response = client.search(
        index=index,
        from_=offset,
        size=size,
        track_total_hits=True,
        query={"match": {"heading": {"query": " ".join(words), "operator": "and"}}},
        # `unmapped_type`, or a corpus from before v17 — which has no `order`
        # — refuses the whole search instead of finding nothing.
        sort=[
            "_score",
            {"order": {"order": "asc", "missing": "_last", "unmapped_type": "integer"}},
        ],
        source_includes=[
            "document_id",
            "author",
            "work",
            "section",
            "title",
            "century",
            "corpus_version",
        ],
    )
    hits = [hit["_source"] for hit in response["hits"]["hits"]]
    return {
        "total": response["hits"]["total"]["value"],
        "texts": [
            {
                "document_id": one.get("document_id"),
                "author": one.get("author"),
                "work": one.get("work"),
                "section": list(one.get("section") or []),
                "title": one.get("title"),
                "century": one.get("century"),
            }
            for one in hits
        ],
        "corpus_version": hits[0].get("corpus_version") if hits else None,
    }


def read(
    client: Elasticsearch,
    document_id: str,
    labels: dict[str, str],
    *,
    start: int = 0,
    limit: int = DEFAULT_UNITS,
    index: str = DOCUMENTS,
) -> dict[str, Any]:
    """One text: where it sits, a window of its units, and its words' readings.

    Raises Elasticsearch's ``NotFoundError`` for an id the index does not hold.
    """
    source = dict(client.get(index=index, id=document_id)["_source"])
    units, spellings, total = lay_out(source, start, limit)
    words, snapshot = look_up(client, spellings, labels)
    return {
        "document_id": source.get("document_id", document_id),
        "source_id": source.get("source_id"),
        "author": source.get("author"),
        "work": source.get("work"),
        "section": list(source.get("section") or []),
        "title": source.get("title"),
        "century": source.get("century"),
        "corpus_version": source.get("corpus_version"),
        "lexicon_snapshot_id": snapshot,
        "units_total": total,
        "start": start,
        "limit": limit,
        "units": units,
        "words": words,
    }
