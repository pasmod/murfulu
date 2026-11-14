"""Every text a spelling is written in, a page at a time, with every line.

The word page quotes six lines, one per author, on purpose: thirty hits in one
poem are often a rhyme (:mod:`murfulu.search.citations`). This is the rest of
the evidence, for a reader who wants all of it — every text the corpus holds
the spelling in, and in each text every line that holds it.

**The order is the same on every reload.** Authors by how many of the texts
are theirs, most first, ties by name; within an author the source's own order
— Ganjoor's poem id, ``documents.order``, the order the reading screen lists
an author's texts in — and then the document id.

**Paged by author, so no page lies past Elasticsearch's window.** A search
refuses ``from + size`` past 10,000, and و is in 101,972 texts. The authors'
counts come from one aggregation, so where the n-th text of the list falls —
which author, how far into their texts — is arithmetic, and a page asks each
author it covers for a slice of that author's own texts. An author with more
texts than the window is walked with ``search_after``; in corpus v17 none
has, since the author with the most texts of all, صائب تبریزی, has 9,874.

**The texts are the search index's, the lines are the counting's.** The index
folds a few letters the counting keeps apart (آ and ا, ۀ and ه) and keeps a
trailing ZWNJ the counting strips, so its number of texts can differ slightly
from the word page's count: رفت is in 10,641 texts here and 10,682 counted,
and the 41 the index misses all write رفت‌ with the ZWNJ. Exact agreement
would mean reading every text the index finds, which for و is the whole
corpus. The lines are found by :mod:`murfulu.search.evidence_lines` with the
counting's own tokeniser.

**Texts with no author** are one more author in the list, by their count, and
are chosen with the empty name: stored without an author or with an empty one.

**Lines are evidence for a spelling, not a reading.** مرد is *mard* and
*mord*, and the same lines serve both; which one a line means is not said.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from elasticsearch import Elasticsearch

from murfulu.search.evidence_lines import Text, found, text_of

INDEX = "documents"

#: Texts per page, and the most one page may ask for.
PAGE_SIZE = 20
MAX_PAGE_SIZE = 50

#: Elasticsearch's ``index.max_result_window``, left at its default.
WINDOW = 10_000

#: A list this long or shorter also has its lines counted. Counting reads
#: every text in the list, which for a few hundred is a fraction of a second
#: and for و would be the whole corpus.
LINE_COUNT_LIMIT = 1_000

#: Far more authors than any corpus here has (v17: 237), so the aggregation
#: never leaves one out.
MAX_AUTHORS = 5_000

_FIELDS = ["document_id", "author", "title", "century", "work", "section"]
_LINE_FIELDS = ["units", "text_fa"]

#: Ganjoor's poem id, then the document id. A corpus from before v17 has no
#: ``order``; ``unmapped_type`` keeps the search from refusing it.
_SORT: list[dict[str, Any]] = [
    {"order": {"order": "asc", "missing": "_last", "unmapped_type": "integer"}},
    {"document_id": "asc"},
]


def _matching(spelling: str, author: str | None = None) -> dict[str, Any]:
    """The texts holding the spelling, as the citations find them.

    ``author`` narrows them to one author; the empty name to texts with none.
    """
    phrase: dict[str, Any] = {"match_phrase": {"text_fa": spelling}}
    if author is None:
        return phrase
    only: dict[str, Any] = (
        {"term": {"author": author}}
        if author
        else {
            "bool": {
                "should": [
                    {"bool": {"must_not": {"exists": {"field": "author"}}}},
                    {"term": {"author": ""}},
                ],
                "minimum_should_match": 1,
            }
        }
    )
    return {"bool": {"must": [phrase], "filter": [only]}}


@dataclass(frozen=True)
class Summary:
    """How many texts hold the spelling, by author, and in which corpus."""

    total: int
    #: (author, texts) in the list's order; "" for texts with no author.
    authors: tuple[tuple[str, int], ...]
    corpus_version: str | None

    def texts(self, author: str | None = None) -> int:
        """How many texts the list holds: every author's, or one author's."""
        if author is None:
            return self.total
        return sum(count for name, count in self.authors if name == author)


def summary(client: Elasticsearch, spelling: str, *, index: str = INDEX) -> Summary:
    """Count the texts and rank their authors, in one aggregation."""
    response = client.search(
        index=index,
        size=0,
        track_total_hits=True,
        query=_matching(spelling),
        aggs={
            "authors": {
                "terms": {
                    "field": "author",
                    "size": MAX_AUTHORS,
                    "missing": "",
                    "order": [{"_count": "desc"}, {"_key": "asc"}],
                }
            },
            "version": {"terms": {"field": "corpus_version", "size": 1}},
        },
    )
    found = response["aggregations"]
    authors = sorted(
        ((one["key"], one["doc_count"]) for one in found["authors"]["buckets"]),
        key=lambda one: (-one[1], one[0]),
    )
    versions = found["version"]["buckets"]
    return Summary(
        total=response["hits"]["total"]["value"],
        authors=tuple(authors),
        corpus_version=versions[0]["key"] if versions else None,
    )


def slices(
    authors: tuple[tuple[str, int], ...], start: int, size: int
) -> list[tuple[str, int, int]]:
    """Which authors a stretch of the list covers: (author, from, how many)."""
    covered: list[tuple[str, int, int]] = []
    before = 0
    for name, count in authors:
        if before >= start + size:
            break
        if before + count > start:
            first = max(0, start - before)
            last = min(count, start + size - before)
            covered.append((name, first, last - first))
        before += count
    return covered


def _walk(
    client: Elasticsearch,
    index: str,
    query: dict[str, Any],
    *,
    offset: int,
    size: int,
    window: int,
) -> list[dict[str, Any]]:
    """Hits ``offset`` to ``offset + size`` of a sorted search, past any window."""
    if offset + size <= window:
        response = client.search(
            index=index,
            from_=offset,
            size=size,
            query=query,
            sort=_SORT,
            source_includes=_FIELDS + _LINE_FIELDS,
        )
        return list(response["hits"]["hits"])
    # Past the window: step over the first `offset` hits by their sort values
    # alone, a window at a time, then read the page from where they end.
    after: list[Any] | None = None
    skipped = 0
    while skipped < offset:
        response = client.search(
            index=index,
            size=min(window, offset - skipped),
            query=query,
            sort=_SORT,
            source=False,
            search_after=after,
        )
        hits = response["hits"]["hits"]
        if not hits:
            return []
        after = hits[-1]["sort"]
        skipped += len(hits)
    response = client.search(
        index=index,
        size=size,
        query=query,
        sort=_SORT,
        search_after=after,
        source_includes=_FIELDS + _LINE_FIELDS,
    )
    return list(response["hits"]["hits"])


def page(
    client: Elasticsearch,
    spelling: str,
    found: Summary,
    *,
    author: str | None = None,
    number: int = 0,
    size: int = PAGE_SIZE,
    index: str = INDEX,
    window: int = WINDOW,
) -> list[Text]:
    """One page of the list, from the start of the whole list or of one author."""
    authors = (
        tuple(one for one in found.authors if one[0] == author)
        if author is not None
        else found.authors
    )
    texts: list[Text] = []
    for name, first, count in slices(authors, number * size, size):
        hits = _walk(
            client,
            index,
            _matching(spelling, name),
            offset=first,
            size=count,
            window=window,
        )
        texts.extend(text_of(hit["_source"], spelling) for hit in hits)
    return texts


def _every(
    client: Elasticsearch, index: str, query: dict[str, Any]
) -> Iterator[dict[str, Any]]:
    after: list[Any] | None = None
    while True:
        response = client.search(
            index=index,
            size=500,
            query=query,
            sort=_SORT,
            source_includes=_LINE_FIELDS,
            search_after=after,
        )
        hits = response["hits"]["hits"]
        if not hits:
            return
        yield from (hit["_source"] for hit in hits)
        after = hits[-1]["sort"]


def line_count(
    client: Elasticsearch,
    spelling: str,
    texts: int,
    *,
    author: str | None = None,
    index: str = INDEX,
) -> int | None:
    """How many lines the list shows in all, or None for a list too long to read."""
    if texts > LINE_COUNT_LIMIT:
        return None
    return sum(
        len(found(source, spelling)[0])
        for source in _every(client, index, _matching(spelling, author))
    )
