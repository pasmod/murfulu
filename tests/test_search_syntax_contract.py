"""The interface writes queries; this file checks the parser can read them.

Three parts of the search screen compose query strings — the examples, the
facet panel and the builder — and the parser that reads them is in Python. The
screen's own tests mock the API, so a query the interface writes is never given
to the thing that reads it, and on 2026-08-17 that gap was a year old: the facet
panel had always written ``category:…`` and ``FIELDS`` had no ``category``, so
every click on a category value replaced a working search with *this query was
not read*.

The fix was one line. **This file is the part that keeps it fixed**, and it is
here rather than in Vitest because the authority on what parses is
``murfulu.search.query`` and nothing in TypeScript can ask it.

It reads ``syntax.ts`` as text on purpose. Exporting the list to JSON at build
time would put a build step between the two halves, and a contract test that
can be skipped by forgetting to run a generator is not a contract.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from murfulu.search.query import QueryError, parse

SYNTAX = Path(__file__).resolve().parents[1] / "web/src/screens/search/syntax.ts"

#: `{ name: "type", title: …` — one entry of the FIELDS list in syntax.ts.
_FIELD = re.compile(r"""\bname:\s*["'](?P<name>[a-z0-9_]+)["']""")

#: `{ query: "count:>10", hint: …` — one row of the REFERENCE list.
_REFERENCE = re.compile(r"""\bquery:\s*["'](?P<query>[^"']+)["']""")


def _source() -> str:
    assert SYNTAX.exists(), f"the interface's syntax list is missing: {SYNTAX}"
    return SYNTAX.read_text(encoding="utf-8")


def _names() -> list[str]:
    names = sorted({match["name"] for match in _FIELD.finditer(_source())})
    assert names, "no field names found in syntax.ts — has the shape changed?"
    return names


def _reference() -> list[str]:
    queries = [match["query"] for match in _REFERENCE.finditer(_source())]
    assert queries, "no reference queries found in syntax.ts"
    return queries


def test_every_field_the_interface_offers_is_a_field_the_parser_knows():
    """The exact drift that broke the category facet."""
    unreadable = []
    for name in _names():
        try:
            parse(f"{name}:x")
        except QueryError as error:
            unreadable.append(f"{name}: {error}")
    assert unreadable == []


def test_every_reference_row_is_a_query_that_parses():
    """Each row is offered to the reader as a working search, so it must be one."""
    broken = []
    for query in _reference():
        try:
            parse(query)
        except QueryError as error:
            broken.append(f"{query!r}: {error}")
    assert broken == []


def test_the_interface_offers_every_field_the_parser_has():
    """The other direction: a field nobody can reach is a field nobody uses.

    Not a style point. `stem1` and `tag` were both parseable and both unnamed
    anywhere in the interface, so *which affixes mean place?* — the question in
    the proposal that started the project — could not be asked from the app.
    """
    from murfulu.search.query import FIELDS

    missing = sorted(set(FIELDS) - set(_names()))
    assert missing == [], (
        f"the parser accepts these and the app never offers them: {missing}"
    )


#: `"unknown-field": (facts) =>` — one entry of UNREADABLE in Search.tsx.
_SENTENCE = re.compile(r"""^\s*["']?(?P<code>[a-z-]+)["']?:\s*\(""", re.MULTILINE)

SEARCH_SCREEN = (
    Path(__file__).resolve().parents[1] / "web/src/screens/search/Search.tsx"
)


def _codes_the_interface_can_say() -> set[str]:
    source = SEARCH_SCREEN.read_text(encoding="utf-8")
    body = source.split("const UNREADABLE", 1)[-1].split("};", 1)[0]
    return {match["code"] for match in _SENTENCE.finditer(body)}


def test_every_fault_the_parser_raises_has_a_persian_sentence():
    """The reader never sees English, so every code must have one.

    A code with no sentence falls back to a general line, which is correct but
    tells the reader nothing about *their* query — so a new fault added to the
    parser without one is a quiet downgrade rather than a failure.
    """
    raised = {
        "no-value",
        "bad-count",
        "bad-century",
        "century-backwards",
        "unknown-field",
        "two-patterns",
        "only-stars",
        "unbalanced-quotes",
        "empty",
    }
    # Every one of those is really raised by the parser.
    source = (
        Path(__file__).resolve().parents[1] / "src/murfulu/search/query.py"
    ).read_text(encoding="utf-8")
    for code in raised:
        assert f'"{code}"' in source, f"{code} is not raised by query.py any more"

    missing = sorted(raised - _codes_the_interface_can_say())
    assert missing == [], (
        f"the parser raises these and the app cannot say them: {missing}"
    )


def test_the_error_body_carries_the_code_and_the_parts():
    """What the interface reads to build the sentence."""
    with pytest.raises(QueryError) as raised:
        parse("count:abc")
    body = raised.value.as_json()
    assert body["code"] == "bad-count"
    assert body["facts"] == {"value": "abc"}
    # The English stays, for the log and the network tab.
    assert "not a number" in body["said"]


@pytest.mark.parametrize(
    "query",
    [
        "category:اسم ذات",  # the facet writes an unquoted Persian value
        "category:nam",
        "*nā category:nam",
    ],
)
def test_the_category_facet_writes_a_readable_query(query: str):
    """The bug itself, kept as a test.

    The value is written unquoted and may contain a space, which `shlex` splits
    — so the second word arrives as a bare pattern. That is a separate fault and
    it is recorded in OPEN_QUESTIONS; what must not regress is the field name.
    """
    assert parse(query).filters.get("category")
