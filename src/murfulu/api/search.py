"""Search, one word, and what the corpus behind them is.

These three need Elasticsearch, and that is the only difference between them
and the rest of the API. The query language is parsed in
:mod:`murfulu.search.query`; this module turns the result into HTTP and
nothing more.

**A suffix search and an affix search are not the same question.** ``*nā``
returns *Sanā*, which merely ends in those letters, alongside *Tonoknā*, which
was formed with the affix. The results are split into the two groups rather
than mixed, because the difference is the whole reason the search exists.
"""

from __future__ import annotations

from typing import Any

from elasticsearch import ApiError, NotFoundError, TransportError
from fastapi import APIRouter, HTTPException, Query

from murfulu.search.citations import find as find_citations
from murfulu.search.facets import aggregations
from murfulu.search.facets import read as read_facets
from murfulu.search.indices import connect
from murfulu.search.query import QueryError, parse, to_elasticsearch

router = APIRouter(tags=["search"])

#: How many hits one page holds. The interface pages; nothing streams.
DEFAULT_SIZE = 50
MAX_SIZE = 500

_UNREACHABLE = "the search index is not reachable"


def _client() -> Any:
    return connect()


def _hits(response: dict[str, Any]) -> list[dict[str, Any]]:
    return [hit["_source"] for hit in response["hits"]["hits"]]


def _split(hits: list[dict[str, Any]], affix: str | None) -> dict[str, Any]:
    """Separate words formed with an affix from words that merely end in it.

    ``*nā`` returns *Sanā* as well as *Tonoknā*, and mixing them is exactly
    what makes a suffix search useless for studying an affix.

    A word type only knows it was formed with an affix if the derivation
    pipeline wrote that back onto it. **Nothing writes it yet** — see PLAN
    task 6.4 — so today every hit lands in the second group, which is the
    honest answer: we do not know how it was formed.
    """
    if not affix:
        return {"formed_with_affix": [], "string_match_only": hits}
    formed: list[dict[str, Any]] = []
    matched: list[dict[str, Any]] = []
    for hit in hits:
        (formed if affix in (hit.get("affixes") or []) else matched).append(hit)
    return {"formed_with_affix": formed, "string_match_only": matched}


@router.get("/search")
def search(
    q: str = Query(..., description="the query syntax in docs/SEARCH.md"),
    size: int = Query(DEFAULT_SIZE, ge=1, le=MAX_SIZE),
    affix: str | None = Query(None, description="split results on this affix"),
) -> dict[str, Any]:
    """Run one search and return the hits, split by how they matched.

    Searches ``word_types`` and only that. Every field the query language
    names — ``stem1``, ``type``, ``rule``, ``author``, ``count`` — is a
    ``word_types`` field, so pointing the same syntax at another index would
    silently match nothing.
    """
    index = "word_types"
    try:
        body = to_elasticsearch(parse(q))
    except QueryError as unreadable:
        # The body carries the fault by name as well as in English. The
        # interface is in Persian and cannot show `str(unreadable)` to a
        # reader; it reads `code` and says the sentence itself. The English
        # stays in `said`, which is what a log and a developer want.
        raise HTTPException(400, unreadable.as_json()) from None

    try:
        # Elasticsearch stops counting at 10,000 by default and reports that
        # as the total, so "how many words are hapaxes?" comes back 10,000
        # whatever the answer is. The count is the point of several of these
        # searches, so it is asked for exactly.
        # The facets come from Elasticsearch, never from the returned page:
        # counting the page would give a figure that changes with the page
        # size and looks exactly like a real one. See search/facets.py.
        response = _client().search(
            index=index,
            size=size,
            track_total_hits=True,
            aggs=aggregations(),
            **body,
        )
    except NotFoundError:
        raise HTTPException(503, f"index {index!r} has not been built") from None
    except (ApiError, TransportError, OSError) as unreachable:
        raise HTTPException(503, f"{_UNREACHABLE}: {unreachable}") from None

    body_out = dict(response)
    hits = _hits(body_out)
    return {
        "query": q,
        "index": index,
        "total": response["hits"]["total"]["value"],
        "returned": len(hits),
        "facets": read_facets(body_out),
        **_split(hits, affix),
    }


@router.get("/word/{word_id}")
def word(
    word_id: str,
    index: str = Query("derivations", description="word_types or derivations"),
    citations: int = Query(6, ge=0, le=20, description="lines to quote"),
) -> dict[str, Any]:
    """One word by its id, with every other reading of its spelling.

    **The readings are never merged.** مرد is *mard* and *mord*; showing one
    and calling it the word would invent a third. They come back as a list,
    with the one that was asked for marked.

    Citations are the actual lines. They are the only part of the evidence a
    reader can check, so they are fetched with the word rather than behind a
    second request nobody makes.
    """
    if index not in {"word_types", "derivations"}:
        raise HTTPException(400, f"{index!r} is not a searchable index")
    try:
        client = _client()
        found = client.get(index=index, id=word_id)
        source = dict(found["_source"])
        spelling = source.get("spelling_fa") or source.get("form_fa")
        siblings = _readings_of(client, index, spelling) if spelling else []
        quoted = (
            [one.as_dict() for one in find_citations(client, spelling, limit=citations)]
            if spelling and citations
            else []
        )
    except NotFoundError:
        raise HTTPException(404, f"no word {word_id!r} in {index}") from None
    except (ApiError, TransportError, OSError) as unreachable:
        raise HTTPException(503, f"{_UNREACHABLE}: {unreachable}") from None
    return {
        "id": word_id,
        "index": index,
        "word": source,
        "readings": siblings,
        "citations": quoted,
    }


def _readings_of(client: Any, index: str, spelling: str) -> list[dict[str, Any]]:
    """Every reading the corpus records for one spelling, never collapsed."""
    field = "spelling_fa" if index == "word_types" else "form_fa"
    response = client.search(index=index, size=20, query={"term": {field: spelling}})
    return _hits(dict(response))


@router.get("/corpus")
def corpus() -> dict[str, Any]:
    """Which corpus versions exist, which one is served, and what it holds.

    Every count in this system is true for one corpus version only, so the
    version an answer came from has to be askable.

    **The sizes and the coverage are read from what the ingest measured, not
    counted here.** Counting them from the index gives the wrong answer in two
    ways that both look right — see :mod:`murfulu.corpus.report`. The stored
    figures were counted exactly, by the pass that held the corpus in memory.

    A report describing a version other than the one being served is returned
    with ``describes_the_served_version: false`` rather than quietly presented
    as current.
    """
    from murfulu.corpus import report
    from murfulu.search.indices import IndexAdmin

    try:
        admin = IndexAdmin(_client())
        serving = {
            alias: admin.current_version(alias)
            for alias in ("documents", "word_types", "derivations")
        }
        built = {
            alias: sorted(admin.client.indices.get(index=f"{alias}-*").body)
            for alias in ("documents", "word_types", "derivations")
        }
    except (ApiError, TransportError, OSError) as unreachable:
        raise HTTPException(503, f"{_UNREACHABLE}: {unreachable}") from None

    measured = report.loaded()
    return {
        "serving": serving,
        "built": built,
        # None when no ingest has been reported on this machine. That is a
        # legitimate state and the screen says so, rather than showing zeros.
        "report": measured.as_dict() if measured.measured else None,
        "describes_the_served_version": (
            measured.measured and measured.corpus_version == serving["word_types"]
        ),
    }
