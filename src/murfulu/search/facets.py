"""The counts beside a result set: how it breaks down, not what is on the page.

A search returns a page of hits, and a page says nothing about the shape of
the whole answer. docs/SEARCH.md asks for the breakdown alongside every
search, and it is not a nicety: *is `-nā` alive or medieval?* is a question
about the result set, not about the fifty rows that fit on screen.

**These come from Elasticsearch, never from the page.** Counting the returned
hits would give a figure that changes with the page size and looks exactly
like a real one — which is the same trap the 10,000-hit cap set in task 4.7.
"""

from __future__ import annotations

from typing import Any

#: Each facet: what it is called in a request, which field it counts, and how
#: many buckets are worth showing. The names are the ``word_types`` fields, so
#: the interface and the index cannot drift apart.
FACETS: dict[str, tuple[str, int]] = {
    "population": ("population", 5),
    "category": ("lexicon_category", 12),
    "source": ("sources", 10),
    "author": ("authors", 12),
    "century": ("first_century", 25),
}


def aggregations(names: tuple[str, ...] = ()) -> dict[str, Any]:
    """The ``aggs`` body for the facets asked for, or for all of them."""
    wanted = names or tuple(FACETS)
    body: dict[str, Any] = {}
    for name in wanted:
        if name not in FACETS:
            raise KeyError(f"{name!r} is not a facet. Known: {', '.join(FACETS)}")
        field, size = FACETS[name]
        body[name] = {"terms": {"field": field, "size": size}}
    return body


def read(response: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Turn Elasticsearch's buckets into ``{facet: [{value, count}]}``.

    A facet with no buckets comes back as an empty list rather than being left
    out. "Nothing in this result set has a century" and "we did not ask about
    centuries" are different answers, and a missing key would merge them.
    """
    found = response.get("aggregations") or {}
    out: dict[str, list[dict[str, Any]]] = {}
    for name in FACETS:
        buckets = found.get(name, {}).get("buckets", []) if name in found else None
        if buckets is None:
            continue
        out[name] = [
            {"value": bucket["key"], "count": bucket["doc_count"]} for bucket in buckets
        ]
    return out
