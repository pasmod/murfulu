"""The actual lines a word was written in.

A count says a word exists. A line says what it meant, who used it and when,
and it is the only part of the evidence a reader can check for themselves.

Two things this module is careful about.

**One line per poet, not per hit.** Thirty occurrences in one poem is a rhyme;
one occurrence each in thirty poets is a word. Elasticsearch collapses the
result on the author so the citations shown are as many different voices as
possible — the same ordering principle the sister forms already use.

**The line is found by the same normalisation the counting used.** The corpus
was counted after folding Arabic ي ك ة to Persian ی ک ه and stripping harakat,
so a citation looked up any other way would sometimes fail to find the word in
the very poem the count came from.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from elasticsearch import Elasticsearch

from murfulu.corpus.wordtypes import normalise

#: How many citations are worth showing. More is a concordance, which is its
#: own screen.
DEFAULT_LIMIT = 6

INDEX = "documents"


@dataclass(frozen=True)
class Citation:
    """One line, and where it comes from."""

    document_id: str
    author: str | None
    title: str | None
    century: int | None
    line: str

    def as_dict(self) -> dict[str, Any]:
        """The shape the API returns."""
        return {
            "document_id": self.document_id,
            "author": self.author,
            "title": self.title,
            "century": self.century,
            "line": self.line,
        }


def _line_with(text: str, spelling: str) -> str | None:
    """The first line of a poem containing this word, as it is written."""
    wanted = normalise(spelling)
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if wanted in normalise(stripped).split():
            return stripped
    return None


def find(
    client: Elasticsearch,
    spelling_fa: str,
    *,
    index: str = INDEX,
    limit: int = DEFAULT_LIMIT,
) -> list[Citation]:
    """Lines quoting one spelling, at most one per poet."""
    response = client.search(
        index=index,
        size=limit,
        query={"match_phrase": {"text_fa": spelling_fa}},
        # One voice per citation. Without this a prolific poet fills the list
        # and the reader cannot tell a common word from a favourite one.
        collapse={"field": "author"},
        source_includes=["document_id", "author", "title", "century", "text_fa"],
    )

    found: list[Citation] = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        line = _line_with(source.get("text_fa") or "", spelling_fa)
        if line is None:
            # The phrase matched on the analysed text but no single line holds
            # the word as written — a compound split across a line break, most
            # often. Skipped rather than shown wrong.
            continue
        found.append(
            Citation(
                document_id=source.get("document_id", ""),
                author=source.get("author"),
                title=source.get("title"),
                century=source.get("century"),
                line=line,
            )
        )
    return found
