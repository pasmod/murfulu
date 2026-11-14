"""What to offer under the reading screen's box while a reader types.

The box finds a text by author, work, section and title at once, every word
typed in the text's ``heading`` (:func:`murfulu.search.texts.find`). A
suggestion finishes the last word half typed, and it is one of two things:

**A group of texts** — an author, a work of theirs, or a section of a work —
which fills the box and lists the group's texts, with how many it holds.
Offered only where the group's own name holds every word typed: «حافظ غز»
offers *حافظ · غزلیات*, never *حافظ* alone, because a suggestion that does not
contain what was typed reads as the box having misheard.

**One text**, which opens it. These come from the same search the list makes,
the best match first, so a suggestion never names a text the list would not.

One request answers both: the texts that match, and the authors, works and
sections they fall in, counted by the index. There are 237 authors, 366 works
and 801 sections in corpus v17, so the buckets asked for here hold the whole
of any group a prefix can reach.
"""

from __future__ import annotations

import re
from typing import Any

from elasticsearch import Elasticsearch

from murfulu.corpus.wordtypes import normalise
from murfulu.search.texts import DOCUMENTS

#: Most suggestions one answer may carry; the box shows eight.
MAX_SUGGESTIONS = 10

#: How many buckets each level of the count asks for. Generous on purpose: a
#: bucket is counted over every text that matches, and only some of those
#: groups hold the words in their own name, so a tight size could drop an
#: author the reader is half way through typing.
_AUTHORS = 40
_WORKS = 10
_SECTIONS = 10

#: What separates the words of a heading, as the index's standard tokeniser
#: splits them. The ZWNJ is not here: it stays inside a word, as it does in
#: the index.
_SPLIT = re.compile(r"[\s،,·؛;:.!?؟«»()\[\]{}\"'/\-–—]+")

#: The analyser's own foldings that :func:`normalise` does not make: the alef
#: with madda, the Arabic yeh and the heh with hamza, and the digits.
_FOLD = str.maketrans(
    {
        "آ": "ا",
        "ى": "ی",
        "ۀ": "ه",
        "ھ": "ه",
        "ٔ": None,
        **{persian: str(n) for n, persian in enumerate("۰۱۲۳۴۵۶۷۸۹")},
        **{arabic: str(n) for n, arabic in enumerate("٠١٢٣٤٥٦٧٨٩")},
    }
)


def words(text: str) -> list[str]:
    """A heading's words as the index compares them: folded, lower case."""
    folded = normalise(text).translate(_FOLD).lower()
    return [word for word in _SPLIT.split(folded) if word.strip("‌")]


def _typed(query: str) -> tuple[list[str], str | None]:
    """The words finished, and the one still being typed (None after a space)."""
    found = words(query)
    if not found:
        return [], None
    if _SPLIT.fullmatch(query[-1]):
        return found, None
    return found[:-1], found[-1]


def holds(name: str, done: list[str], partial: str | None) -> bool:
    """Whether a group's name holds every word typed, the last as a prefix."""
    own = words(name)
    if any(word not in own for word in done):
        return False
    return partial is None or any(word.startswith(partial) for word in own)


def _group(kind: str, parts: list[str], texts: int) -> dict[str, Any]:
    return {
        "kind": kind,
        "parts": parts,
        "query": " ".join(parts),
        "texts": texts,
        "document_id": None,
    }


def _groups(aggregations: dict[str, Any]) -> list[dict[str, Any]]:
    """Every author, work and section the matching texts fall in, biggest first."""
    found: list[dict[str, Any]] = []
    for author in aggregations.get("authors", {}).get("buckets", []):
        name = author["key"]
        found.append(_group("author", [name], author["doc_count"]))
        for work in author.get("works", {}).get("buckets", []):
            found.append(_group("work", [name, work["key"]], work["doc_count"]))
            for section in work.get("sections", {}).get("buckets", []):
                found.append(
                    _group(
                        "section",
                        [name, work["key"], section["key"]],
                        section["doc_count"],
                    )
                )
    return found


def _text(source: dict[str, Any]) -> dict[str, Any]:
    parts = [
        part
        for part in (
            source.get("author"),
            source.get("work"),
            *(source.get("section") or []),
            source.get("title"),
        )
        if part
    ]
    return {
        "kind": "text",
        "parts": parts,
        "query": " ".join(parts),
        "texts": 1,
        "document_id": source.get("document_id"),
    }


_ORDER = {"author": 0, "work": 1, "section": 2}


def suggest(
    client: Elasticsearch,
    query: str,
    *,
    limit: int = 8,
    index: str = DOCUMENTS,
) -> list[dict[str, Any]]:
    """Groups whose name holds what was typed, then single texts; at most ``limit``."""
    done, partial = _typed(query)
    if not done and partial is None:
        return []
    # The index is asked in the reader's own letters and folds them itself:
    # the folding here is only for comparing names below, and it is not the
    # analyser's — it reads ؤ as و, which the index keeps, so «سؤال» folded
    # would miss every heading that has it.
    asked = query.strip()
    # `match_bool_prefix` takes the last word as a prefix; after a space the
    # last word is finished, and a plain match says so.
    kind = "match_bool_prefix" if partial is not None else "match"
    response = client.search(
        index=index,
        size=limit,
        query={kind: {"heading": {"query": asked, "operator": "and"}}},
        sort=[
            "_score",
            {"order": {"order": "asc", "missing": "_last", "unmapped_type": "integer"}},
        ],
        source_includes=["document_id", "author", "work", "section", "title"],
        aggs={
            "authors": {
                "terms": {"field": "author", "size": _AUTHORS},
                "aggs": {
                    "works": {
                        "terms": {"field": "work.raw", "size": _WORKS},
                        "aggs": {
                            "sections": {
                                "terms": {"field": "section", "size": _SECTIONS}
                            }
                        },
                    }
                },
            }
        },
    )
    finished = " ".join(done) if partial is None else None
    groups = [
        one
        for one in _groups(response.get("aggregations") or {})
        if holds(one["query"], done, partial)
        # After a space the reader has a whole name and wants what is in it:
        # the name itself again is no suggestion.
        and " ".join(words(one["query"])) != finished
    ]
    groups.sort(key=lambda one: (_ORDER[one["kind"]], -one["texts"]))
    seen = {one["query"] for one in groups}
    texts = []
    for hit in response["hits"]["hits"]:
        one = _text(hit["_source"])
        if one["document_id"] and one["query"] not in seen:
            seen.add(one["query"])
            texts.append(one)
    # The groups first, but never all of the list while a text matches: a
    # reader who typed a title is looking for that text, not for its author.
    room = max(limit - min(len(texts), 3), 0)
    return [*groups[:room], *texts][:limit]
