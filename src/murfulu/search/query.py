"""Turn the search syntax in ``docs/SEARCH.md`` into Elasticsearch queries.

The syntax is deliberately small and maps one-to-one onto Elasticsearch, so a
user can predict what a query will do::

    *nā                ends with nā
    bar*               starts with bar
    *raft*             contains raft
    /g[ou]ft/          regular expression
    stem2:gu           kārbon-e do is gu
    type:karnam        word class
    tag:ja             semantic tag — "which affixes mean place?"
    count:>10          frequency band
    century:10-13
    *nā type:nam in:corpus count:>2

A bare term is matched against the Latin form. **Persian script is detected and
matched against the spelling instead**, because a reader typing روش means the
spelling, not a Latin string that happens to look like it.

Suffix search is the flagship query and the reason ``latin_reversed`` exists:
*ends with nā* becomes *starts with ān* on the reversed field, which is a cheap
prefix query rather than a leading wildcard.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from typing import Any

#: Any Arabic-script character. One is enough to switch fields.
_PERSIAN = re.compile(r"[؀-ۿ]")

#: field: the Elasticsearch field a `name:value` term filters on.
FIELDS = {
    "stem1": "stem_1_latin",
    "stem2": "stem_2_latin",
    "type": "word_class",
    # `type` and `category` are two different words for a word's class and both
    # are needed: `type` is the class **we** assigned when we built or analysed
    # the form, `category` is the one karbon's Dehkhoda entry carries. They
    # disagree often enough to be worth asking about separately. `category` was
    # missing until 2026-08-17, and the facet panel that counts it had been
    # writing `category:…` into the box since it was built — so every click on
    # a category value turned a working search into "this query was not read".
    "category": "lexicon_category",
    "rule": "rule_ids",
    "affix": "affixes",
    "tag": "semantic_tags",
    "in": "population",
    "author": "authors",
    "source": "sources",
}

#: Fields whose value is a number or a band rather than a word.
COUNT_FIELD = "total_count"
CENTURY_FIRST = "first_century"
CENTURY_LAST = "last_century"

_COUNT = re.compile(r"^(?P<operator>>=|<=|>|<)?(?P<value>\d+)$")
_CENTURY = re.compile(r"^(?P<low>\d+)(?:-(?P<high>\d+))?$")


class QueryError(ValueError):
    """Raised when a query cannot be read. The message says which part.

    **It carries a code as well as a sentence, and the code is the part the
    reader sees.** The sentence is English and always was, and the API handed
    it straight to the interface — so a Persian reader who mistyped a field got
    *poem: is not a searchable field* under a Persian heading. FRONTEND.md says
    the reader never sees English. The engine cannot write the Persian either,
    because it does not know what the interface calls these things, so it names
    the fault and the interface says it: ``code`` is the name, ``facts`` are
    the parts to put in the sentence.

    The English stays. It is what the logs and the API's own ``detail`` carry,
    and it is what a developer reads.
    """

    def __init__(self, code: str, message: str, **facts: str) -> None:
        super().__init__(message)
        self.code = code
        self.facts = facts

    def as_json(self) -> dict[str, Any]:
        """The machine-readable half, for the API's error body."""
        return {"code": self.code, "facts": self.facts, "said": str(self)}


@dataclass
class Query:
    """One parsed search, ready to be turned into Elasticsearch."""

    #: The bare pattern, if any: `*nā`, `bar*`, `/g[ou]ft/`, `gereft`.
    pattern: str | None = None
    filters: dict[str, list[str]] = field(default_factory=dict)
    count: dict[str, int] = field(default_factory=dict)
    centuries: tuple[int, int] | None = None

    @property
    def searches_persian(self) -> bool:
        """True when the pattern is written in Persian script."""
        return bool(self.pattern and _PERSIAN.search(self.pattern))


def _add(query: Query, name: str, value: str) -> None:
    if not value:
        raise QueryError("no-value", f"{name}: has no value", name=name)
    if name == "count":
        match = _COUNT.match(value)
        if not match:
            raise QueryError(
                "bad-count",
                f"count: {value!r} is not a number or a band",
                value=value,
            )
        operator = match.group("operator")
        number = int(match.group("value"))
        # count:1 means exactly one — the hapax query.
        query.count = (
            {"gte": number, "lte": number}
            if operator is None
            else {{">": "gt", "<": "lt", ">=": "gte", "<=": "lte"}[operator]: number}
        )
        return
    if name == "century":
        match = _CENTURY.match(value)
        if not match:
            raise QueryError(
                "bad-century",
                f"century: {value!r} is not a year or a range",
                value=value,
            )
        low = int(match.group("low"))
        high = int(match.group("high") or low)
        if high < low:
            raise QueryError(
                "century-backwards",
                f"century: {value!r} runs backwards",
                value=value,
            )
        query.centuries = (low, high)
        return
    if name not in FIELDS:
        raise QueryError(
            "unknown-field", f"{name}: is not a searchable field", name=name
        )
    query.filters.setdefault(name, []).append(value)


def parse(text: str) -> Query:
    """Read a query string. Raises :class:`QueryError` on anything unreadable."""
    query = Query()
    try:
        terms = shlex.split(text.strip())
    except ValueError as error:
        raise QueryError("unbalanced-quotes", f"unbalanced quotes: {error}") from error

    for term in terms:
        # A regex is written /…/ and may contain a colon, so it is checked
        # before the field split.
        if term.startswith("/") and term.endswith("/") and len(term) > 1:
            _set_pattern(query, term)
        elif ":" in term:
            name, _, value = term.partition(":")
            _add(query, name.strip(), value.strip())
        else:
            _set_pattern(query, term)
    return query


def _set_pattern(query: Query, term: str) -> None:
    if query.pattern is not None:
        raise QueryError(
            "two-patterns",
            f"two patterns given: {query.pattern!r} and {term!r}. Use one.",
            first=query.pattern,
            second=term,
        )
    query.pattern = term


def _pattern_clause(query: Query) -> dict[str, Any]:
    pattern = query.pattern or ""
    field_name = "spelling_fa" if query.searches_persian else "latin"

    if pattern.startswith("/") and pattern.endswith("/"):
        return {"regexp": {field_name: pattern[1:-1]}}

    starts, ends = pattern.startswith("*"), pattern.endswith("*")
    body = pattern.strip("*")
    if not body:
        raise QueryError(
            "only-stars", "a pattern of only * matches everything; drop it instead"
        )

    if starts and ends:
        # Leading wildcards are what the wildcard field type is built for.
        wild = "latin_wild" if field_name == "latin" else "spelling_fa"
        return {"wildcard": {wild: f"*{body}*"}}
    if starts:
        # Ends with X: a prefix query on the reversed form, not a wildcard.
        if field_name == "latin":
            return {"prefix": {"latin_reversed": body[::-1]}}
        return {"wildcard": {field_name: f"*{body}"}}
    if ends:
        return {"prefix": {field_name: body}}
    return {"term": {field_name: body}}


def to_elasticsearch(query: Query) -> dict[str, Any]:
    """Build the Elasticsearch query body for a parsed search."""
    must: list[dict[str, Any]] = []
    if query.pattern:
        must.append(_pattern_clause(query))
    for name, values in query.filters.items():
        must.append({"terms": {FIELDS[name]: values}})
    if query.count:
        must.append({"range": {COUNT_FIELD: query.count}})
    if query.centuries:
        low, high = query.centuries
        # A word counts as inside the range if its span overlaps it at all.
        must.append({"range": {CENTURY_LAST: {"gte": low}}})
        must.append({"range": {CENTURY_FIRST: {"lte": high}}})

    if not must:
        raise QueryError("empty", "empty query")
    return {"query": {"bool": {"filter": must}}}


def build(text: str) -> dict[str, Any]:
    """Parse a query string and return the Elasticsearch body."""
    return to_elasticsearch(parse(text))
