"""The actual lines a word was written in.

A count says a word exists. A line says what it meant, who used it and when,
and it is the only part of the evidence a reader can check for themselves.

Three things this module is careful about.

**One citation per author, not per hit.** Thirty occurrences in one text is a
rhyme or a habit; one occurrence each in thirty authors is a word.
Elasticsearch collapses the result on the author so the citations shown are as
many different voices as possible — the same ordering principle the sister
forms already use.

**A citation is as long as a line of verse, whatever the text is.** A verse
half is short; a prose paragraph can run to thousands of words. So a line of
prose is cut to the sentence that holds the word, and a long sentence to the
words around it, marked with «…» where it was cut. Until 2026-11-13 the whole
paragraph was quoted, and the corpus has 82,499 of them.

**The line is found by the same normalisation the counting used.** The corpus
was counted after folding Arabic ي ك ة to Persian ی ک ه and stripping harakat,
so a citation looked up any other way would sometimes fail to find the word in
the very text the count came from.

Each citation names the unit it came from — its place in the text's units — so
the reading screen can open the text straight at it. A text stored before
corpus v17 has no units, and its citation names none.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

from elasticsearch import Elasticsearch

from murfulu.corpus.wordtypes import normalise, tokenise

#: How many citations are worth showing. More is a concordance, which is its
#: own screen.
DEFAULT_LIMIT = 6

INDEX = "documents"

#: The longest citation, in words. A couplet's half is eight to twelve words;
#: a quotation much longer than two of them stops being a line.
MAX_WORDS = 24

#: How many words either side of the word a cut sentence keeps.
CONTEXT_WORDS = 10

#: Where a sentence of prose ends: after its closing mark, at the space.
_SENTENCE_END = re.compile(r"(?<=[.!?؟؛:])\s+")

ELLIPSIS = "…"


@dataclass(frozen=True)
class Citation:
    """One line, and where it comes from."""

    document_id: str
    author: str | None
    title: str | None
    century: int | None
    line: str
    #: The book and the sections the text sits in, where the source says.
    work: str | None = None
    section: tuple[str, ...] = ()
    #: The unit's index in the text's units, and what kind it is. None for a
    #: text stored before units existed.
    unit: int | None = None
    kind: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """The shape the API returns."""
        return {
            "document_id": self.document_id,
            "author": self.author,
            "title": self.title,
            "century": self.century,
            "line": self.line,
            "work": self.work,
            "section": list(self.section),
            "unit": self.unit,
            "kind": self.kind,
        }


def _same(spelling: str) -> str:
    return spelling


def _holds(text: str, wanted: str, fold: Callable[[str], str] = _same) -> bool:
    return any(fold(one) == wanted for one in tokenise(text))


def excerpt(line: str, spelling: str, *, fold: Callable[[str], str] = _same) -> str:
    """The part of a line worth quoting: all of a short one, a sentence of prose.

    A sentence still longer than :data:`MAX_WORDS` is cut to the words around
    the first occurrence, with «…» where it was cut. ``fold`` is applied to the
    spelling and to every word before they are compared, for a line that holds
    the word only in a near spelling (:mod:`murfulu.search.evidence`).
    """
    if len(line.split()) <= MAX_WORDS:
        return line
    wanted = fold(normalise(spelling))
    sentence = next(
        (one for one in _SENTENCE_END.split(line) if _holds(one, wanted, fold)), line
    )
    words = sentence.split()
    if len(words) <= MAX_WORDS:
        return sentence
    at = next((i for i, word in enumerate(words) if _holds(word, wanted, fold)), 0)
    start = max(0, at - CONTEXT_WORDS)
    end = min(len(words), at + CONTEXT_WORDS + 1)
    cut = " ".join(words[start:end])
    return (
        (ELLIPSIS + " " if start > 0 else "")
        + cut
        + (" " + ELLIPSIS if end < len(words) else "")
    )


def lines(source: dict[str, Any]) -> Iterator[tuple[int | None, str | None, str]]:
    """Every counted line of a stored text, with its unit and the unit's kind."""
    units = source.get("units") or []
    if units:
        for index, unit in enumerate(units):
            if unit.get("kind") == "note":
                continue
            for one in unit.get("lines") or []:
                yield index, unit.get("kind"), one.get("text") or ""
        return
    for line in (source.get("text_fa") or "").splitlines():
        yield None, None, line


def locate(
    source: dict[str, Any], spelling: str
) -> tuple[int | None, str | None, str] | None:
    """The first line of a text containing this word: its unit, kind and words."""
    wanted = normalise(spelling)
    for unit, kind, line in lines(source):
        stripped = line.strip()
        if stripped and _holds(stripped, wanted):
            return unit, kind, stripped
    return None


def find(
    client: Elasticsearch,
    spelling_fa: str,
    *,
    index: str = INDEX,
    limit: int = DEFAULT_LIMIT,
) -> list[Citation]:
    """Lines quoting one spelling, at most one per author."""
    response = client.search(
        index=index,
        size=limit,
        query={"match_phrase": {"text_fa": spelling_fa}},
        # One voice per citation. Without this a prolific author fills the list
        # and the reader cannot tell a common word from a favourite one.
        collapse={"field": "author"},
        source_includes=[
            "document_id",
            "author",
            "title",
            "century",
            "text_fa",
            "work",
            "section",
            "units",
        ],
    )

    found: list[Citation] = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        located = locate(source, spelling_fa)
        if located is None:
            # The phrase matched on the analysed text but no single line holds
            # the word as written — a compound split across a line break, most
            # often. Skipped rather than shown wrong.
            continue
        unit, kind, line = located
        found.append(
            Citation(
                document_id=source.get("document_id", ""),
                author=source.get("author"),
                title=source.get("title"),
                century=source.get("century"),
                line=excerpt(line, spelling_fa),
                work=source.get("work"),
                section=tuple(source.get("section") or ()),
                unit=unit,
                kind=kind,
            )
        )
    return found
