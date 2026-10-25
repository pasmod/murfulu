"""The search syntax, and the Elasticsearch it turns into."""

import pytest

from murfulu.search.query import QueryError, build, parse

# -- the forms of a bare pattern ---------------------------------------------


def test_ends_with_becomes_a_prefix_on_the_reversed_field():
    """*nā is the flagship query, and the reason latin_reversed exists."""
    body = build("*nā")["query"]["bool"]["filter"]
    assert body == [{"prefix": {"latin_reversed": "ān"}}]


def test_starts_with_is_a_prefix():
    assert build("bar*")["query"]["bool"]["filter"] == [{"prefix": {"latin": "bar"}}]


def test_contains_uses_the_wildcard_field():
    assert build("*raft*")["query"]["bool"]["filter"] == [
        {"wildcard": {"latin_wild": "*raft*"}}
    ]


def test_a_bare_word_is_exact():
    assert build("gereft")["query"]["bool"]["filter"] == [{"term": {"latin": "gereft"}}]


def test_a_regex_is_passed_through():
    assert build("/g[ou]ft/")["query"]["bool"]["filter"] == [
        {"regexp": {"latin": "g[ou]ft"}}
    ]


def test_a_regex_may_contain_a_colon():
    """It must not be mistaken for a field:value term."""
    assert parse("/a:b/").pattern == "/a:b/"


# -- Persian input -----------------------------------------------------------


def test_persian_script_searches_the_spelling_not_the_latin():
    """Someone typing روش means the spelling, not a Latin lookalike."""
    assert parse("روش").searches_persian
    assert build("روش")["query"]["bool"]["filter"] == [{"term": {"spelling_fa": "روش"}}]


def test_persian_ends_with_uses_a_wildcard():
    """There is no reversed field for the Persian spelling."""
    assert build("*نا")["query"]["bool"]["filter"] == [
        {"wildcard": {"spelling_fa": "*نا"}}
    ]


def test_latin_is_the_default():
    assert not parse("raft").searches_persian


# -- the named fields --------------------------------------------------------


@pytest.mark.parametrize(
    ("term", "field", "value"),
    [
        ("stem1:goft", "stem_1_latin", "goft"),
        ("stem2:gu", "stem_2_latin", "gu"),
        ("type:karnam", "word_class", "karnam"),
        ("rule:V-010", "rule_ids", "V-010"),
        ("affix:-eš", "affixes", "-eš"),
        ("tag:ja", "semantic_tags", "ja"),
        ("in:corpus", "population", "corpus"),
        ("source:ganjoor", "sources", "ganjoor"),
    ],
)
def test_each_named_field_maps_to_its_index_field(term: str, field: str, value: str):
    assert build(term)["query"]["bool"]["filter"] == [{"terms": {field: [value]}}]


def test_the_same_field_twice_means_either():
    assert build("type:nam type:karnam")["query"]["bool"]["filter"] == [
        {"terms": {"word_class": ["nam", "karnam"]}}
    ]


# -- counts and centuries ----------------------------------------------------


def test_count_one_is_the_hapax_query():
    """count:1 means exactly once, not at least once."""
    assert build("count:1")["query"]["bool"]["filter"] == [
        {"range": {"total_count": {"gte": 1, "lte": 1}}}
    ]


@pytest.mark.parametrize(
    ("term", "expected"),
    [
        ("count:>10", {"gt": 10}),
        ("count:<5", {"lt": 5}),
        ("count:>=2", {"gte": 2}),
    ],
)
def test_a_frequency_band(term: str, expected: dict):
    assert build(term)["query"]["bool"]["filter"] == [
        {"range": {"total_count": expected}}
    ]


def test_a_century_range_matches_any_overlap():
    """A word used 9th-12th is inside a 10th-11th search."""
    assert build("century:10-11")["query"]["bool"]["filter"] == [
        {"range": {"last_century": {"gte": 10}}},
        {"range": {"first_century": {"lte": 11}}},
    ]


def test_a_single_century():
    assert parse("century:10").centuries == (10, 10)


# -- combining ---------------------------------------------------------------


def test_everything_combines():
    parsed = parse("*nā type:nam in:corpus count:>2 century:10-14")
    assert parsed.pattern == "*nā"
    assert parsed.filters == {"type": ["nam"], "in": ["corpus"]}
    assert parsed.count == {"gt": 2}
    assert parsed.centuries == (10, 14)
    # pattern, type, population, count, and two clauses for the century span
    clauses = build("*nā type:nam in:corpus count:>2 century:10-14")
    assert len(clauses["query"]["bool"]["filter"]) == 6


def test_the_plan_queries_all_parse():
    """The five PLAN task 4.6 names by hand."""
    for text in ("*nā", "stem2:gu", "type:karnam", "tag:ja", "count:1"):
        assert build(text)["query"]["bool"]["filter"]


# -- what is refused ---------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "complaint"),
    [
        ("", "empty query"),
        ("colour:red", "not a searchable field"),
        ("count:many", "not a number"),
        ("count:", "has no value"),
        ("century:13-10", "runs backwards"),
        ("century:x", "not a year"),
        ("*nā bar*", "two patterns"),
        ("*", "matches everything"),
        ('type:"nam', "unbalanced quotes"),
    ],
)
def test_an_unreadable_query_says_what_is_wrong(text: str, complaint: str):
    with pytest.raises(QueryError, match=complaint):
        build(text)
