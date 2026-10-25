"""Index mappings, and the alias swap that releases a corpus version.

The mapping tests are pure. The alias tests need a real Elasticsearch and skip
when none is reachable, so the suite still runs on a machine with nothing up.
"""

import os
from collections.abc import Iterator

import pytest

from murfulu.search.indices import (
    IndexAdmin,
    UnknownIndexError,
    connect,
    index_name,
)
from murfulu.search.mappings import ANALYZER, MAPPINGS, SETTINGS

from .conftest import aliases_restored

#: Every index this file creates carries it, and nothing without it is ever
#: deleted. A corpus version is a free-form token, so "v1" is a name a real
#: ingest uses.
PREFIX = "test-indices-"
FIRST = f"{PREFIX}a"
SECOND = f"{PREFIX}b"

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


# -- mappings, no cluster needed ---------------------------------------------


def test_the_three_indices_the_architecture_defines():
    assert set(MAPPINGS) == {"documents", "word_types", "derivations"}


@pytest.mark.parametrize("alias", sorted(MAPPINGS))
def test_nothing_is_indexed_by_accident(alias: str):
    """A typo in a field name must fail the write, not invent a field."""
    assert MAPPINGS[alias]["dynamic"] == "strict"


def test_suffix_search_has_a_field_to_use():
    """*-nā* becomes a prefix query on the reversed form. That is the point."""
    properties = MAPPINGS["word_types"]["properties"]
    assert properties["latin_reversed"]["type"] == "keyword"
    assert properties["latin_wild"]["type"] == "wildcard"


def test_the_three_notions_of_word_class_stay_apart():
    properties = MAPPINGS["word_types"]["properties"]
    assert properties["lexicon_category"]["type"] == "keyword"
    assert properties["word_class"]["type"] == "keyword"
    assert properties["pos_observed"]["type"] == "object"


def test_every_reading_can_reach_its_dictionary_entries():
    properties = MAPPINGS["word_types"]["properties"]
    assert properties["source_entry_ids"]["type"] == "keyword"
    assert properties["sense_count"]["type"] == "integer"


def test_counts_are_tied_to_the_version_that_produced_them():
    for alias in ("word_types", "derivations"):
        assert "corpus_version" in MAPPINGS[alias]["properties"]


def _analysed_fields() -> list[dict]:
    """Every field in every mapping that analyses text."""
    return [
        field
        for mapping in MAPPINGS.values()
        for field in mapping["properties"].values()
        if field.get("type") == "text"
    ]


def test_no_field_uses_the_analyzer_that_drops_the_commonest_words():
    """Lucene's stock ``persian`` analyzer eats رفت، گفت، شد، بود."""
    fields = _analysed_fields()
    assert fields, "there should be Persian text fields to check"
    for field in fields:
        assert field["analyzer"] == ANALYZER


def test_the_analyser_is_defined_where_the_indices_can_see_it():
    assert SETTINGS["analysis"]["analyzer"][ANALYZER]["tokenizer"] == "standard"
    assert "persian_stop" not in SETTINGS["analysis"]["analyzer"][ANALYZER]["filter"]


@pytest.mark.parametrize(
    ("alias", "version", "expected"),
    [
        ("word_types", "v3", "word_types-v3"),
        ("documents", "2026-08-11", "documents-2026-08-11"),
    ],
)
def test_index_names_carry_their_version(alias: str, version: str, expected: str):
    assert index_name(alias, version) == expected


def test_an_unknown_alias_is_rejected():
    with pytest.raises(UnknownIndexError):
        index_name("poems", "v1")


@pytest.mark.parametrize("version", ["V1", "-v1", "v 1", ""])
def test_a_bad_version_is_rejected(version: str):
    with pytest.raises(ValueError, match="corpus version"):
        index_name("word_types", version)


# -- alias swap, needs a cluster ---------------------------------------------


@pytest.fixture
def admin() -> Iterator[IndexAdmin]:
    """An admin against a live cluster, or skip."""
    url = os.environ.get("MURFULU_ELASTICSEARCH_URL", "http://localhost:9200")
    client = connect(url)
    try:
        reachable = client.ping()
    except Exception:  # noqa: BLE001 - any failure means "not reachable"
        reachable = False
    if not reachable:
        pytest.skip(f"no Elasticsearch at {url}")

    # Only what this file made. The first version of this fixture cleaned
    # `{alias}-*`, which deleted **an ingested corpus** — 133,148 poems and
    # 411,166 word types, ninety seconds to rebuild — every time the suite ran
    # on a machine with a live cluster. A test may not delete what it did not
    # create.
    def clean() -> None:
        for alias in MAPPINGS:
            found = client.indices.get(
                index=f"{alias}-{PREFIX}*", ignore_unavailable=True
            )
            for name in found.body:
                assert PREFIX in name, f"refusing to delete {name}"
                client.indices.delete(index=name)

    with aliases_restored(client, list(MAPPINGS)):
        clean()
        yield IndexAdmin(client)
        clean()


def test_indices_are_created_from_code(admin: IndexAdmin):
    created = admin.create_all(FIRST)
    assert created == [
        f"derivations-{FIRST}",
        f"documents-{FIRST}",
        f"word_types-{FIRST}",
    ]
    for name in created:
        assert admin.client.indices.exists(index=name)


def test_the_mappings_survive_the_round_trip(admin: IndexAdmin):
    """What the cluster stores must be what we asked for."""
    admin.create("word_types", FIRST)
    name = f"word_types-{FIRST}"
    stored = admin.client.indices.get_mapping(index=name)
    properties = stored[name]["mappings"]["properties"]
    assert properties["latin_wild"]["type"] == "wildcard"
    assert properties["latin_reversed"]["type"] == "keyword"
    assert stored[name]["mappings"]["dynamic"] == "strict"


def test_the_alias_swap_works(admin: IndexAdmin):
    admin.create_all(FIRST)
    admin.release_all(FIRST)
    assert admin.current_version("word_types") == FIRST

    admin.create_all(SECOND)
    assert admin.current_version("word_types") == FIRST, "building must not release"

    admin.release_all(SECOND)
    assert admin.current_version("word_types") == SECOND
    assert admin.indices_behind("word_types") == [f"word_types-{SECOND}"]


def test_the_old_version_stays_queryable_after_a_swap(admin: IndexAdmin):
    """A release must not destroy what it replaces."""
    admin.create_all(FIRST)
    admin.release_all(FIRST)
    admin.create_all(SECOND)
    admin.release_all(SECOND)
    assert admin.client.indices.exists(index=f"word_types-{FIRST}")


def test_dropping_an_old_version_is_deliberate(admin: IndexAdmin):
    admin.create("word_types", FIRST)
    admin.drop("word_types", FIRST)
    assert not admin.client.indices.exists(index=f"word_types-{FIRST}")


def _tokens(admin: IndexAdmin, index: str, text: str) -> list[str]:
    found = admin.client.indices.analyze(index=index, analyzer=ANALYZER, text=text)
    return [token["token"] for token in found["tokens"]]


def test_the_commonest_words_survive_the_analyser(admin: IndexAdmin):
    """The whole of corpus version v2.

    The stock ``persian`` analyzer drops all four of these, so a phrase query
    for رفت found nothing in a corpus holding it hundreds of thousands of
    times and ``/word`` quoted no line for the words most worth quoting.
    """
    admin.create("documents", FIRST)
    tokens = _tokens(admin, f"documents-{FIRST}", "رفت گفت شد بود")
    assert len(tokens) == 4


def test_a_word_joined_by_a_zero_width_non_joiner_stays_one_word(admin: IndexAdmin):
    """``wordtypes`` counts می‌رود as one word, so the analyser must too.

    Otherwise the phrase query and the counting disagree, and a citation
    cannot be found in the very poem its count came from.
    """
    admin.create("documents", FIRST)
    assert len(_tokens(admin, f"documents-{FIRST}", "می‌رود")) == 1
    assert len(_tokens(admin, f"documents-{FIRST}", "گفت‌وگو")) == 1


def test_a_phrase_query_finds_a_stopword(admin: IndexAdmin):
    """End to end: index a line with رفت in it and search for it."""
    admin.create("documents", FIRST)
    name = f"documents-{FIRST}"
    admin.client.index(
        index=name,
        document={
            "source_id": "fixture",
            "document_id": "fixture:1",
            "text_fa": "به صحرا شدم عشق باران بود\nیکی رفت و دیگر نگفت",
        },
        refresh=True,
    )
    for word in ("رفت", "بود"):
        found = admin.client.search(
            index=name, query={"match_phrase": {"text_fa": word}}
        )
        assert found["hits"]["total"]["value"] == 1, word


def test_a_strict_mapping_rejects_an_unknown_field(admin: IndexAdmin):
    from elasticsearch import BadRequestError

    admin.create("documents", FIRST)
    with pytest.raises(BadRequestError):
        admin.client.index(
            index=f"documents-{FIRST}",
            document={"source_id": "fixture", "titel": "typo"},
        )


# -- the query language, run against a real cluster ---------------------------

SAMPLE = [
    # Tonoknā and Derāznā really end in -nā; Sanā only looks like it does.
    {
        "id": "تنکنا:Tonoknā",
        "spelling_fa": "تنکنا",
        "latin": "Tonoknā",
        "latin_reversed": "ānkonoT",
        "latin_wild": "Tonoknā",
        "word_class": "nam",
        "semantic_tags": ["ja"],
        "total_count": 1,
        "first_century": 10,
        "last_century": 10,
        "population": ["generated"],
    },
    {
        "id": "درازنا:Derāznā",
        "spelling_fa": "درازنا",
        "latin": "Derāznā",
        "latin_reversed": "ānzāreD",
        "latin_wild": "Derāznā",
        "word_class": "nam",
        "total_count": 12,
        "first_century": 11,
        "last_century": 14,
        "population": ["corpus"],
    },
    {
        "id": "ثنا:Sanā",
        "spelling_fa": "ثنا",
        "latin": "Sanā",
        "latin_reversed": "ānaS",
        "latin_wild": "Sanā",
        "word_class": "nam",
        "total_count": 40,
        "first_century": 10,
        "last_century": 20,
        "population": ["corpus"],
    },
    {
        "id": "گویش:Guyeš",
        "spelling_fa": "گویش",
        "latin": "Guyeš",
        "latin_reversed": "šeyuG",
        "latin_wild": "Guyeš",
        "word_class": "karnam",
        "stem_2_latin": "gu",
        "total_count": 5,
        "first_century": 12,
        "last_century": 20,
        "population": ["corpus"],
    },
]


@pytest.fixture
def searchable(admin: IndexAdmin) -> IndexAdmin:
    """word_types filled with a handful of documents, refreshed."""
    admin.create("word_types", FIRST)
    for document in SAMPLE:
        admin.client.index(
            index=f"word_types-{FIRST}", id=document["id"], document=document
        )
    admin.client.indices.refresh(index=f"word_types-{FIRST}")
    return admin


def _hits(admin: IndexAdmin, text: str) -> set[str]:
    from murfulu.search.query import build as build_query

    found = admin.client.search(index=f"word_types-{FIRST}", **build_query(text))
    return {hit["_source"]["latin"] for hit in found["hits"]["hits"]}


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        # The five PLAN task 4.6 names by hand.
        ("*nā", {"Tonoknā", "Derāznā", "Sanā"}),
        ("stem2:gu", {"Guyeš"}),
        ("type:karnam", {"Guyeš"}),
        ("tag:ja", {"Tonoknā"}),
        ("count:1", {"Tonoknā"}),
        # …and combinations.
        ("*nā count:>10", {"Derāznā", "Sanā"}),
        ("*nā in:corpus", {"Derāznā", "Sanā"}),
        ("*nā century:11-12", {"Derāznā", "Sanā"}),
        ("*nā type:nam count:>10 century:10-11", {"Derāznā", "Sanā"}),
        # Other shapes of pattern.
        ("Guyeš", {"Guyeš"}),
        ("Der*", {"Derāznā"}),
        ("*rāz*", {"Derāznā"}),
        ("/.*n[āa]/", {"Tonoknā", "Derāznā", "Sanā"}),
        ("گویش", {"Guyeš"}),
    ],
)
def test_the_query_language_returns_the_right_words(
    searchable: IndexAdmin, query: str, expected: set[str]
):
    assert _hits(searchable, query) == expected


def test_ends_with_na_also_catches_words_that_merely_look_like_it(
    searchable: IndexAdmin,
):
    """Sanā is not formed with -nā. SEARCH.md splits these into two groups."""
    assert "Sanā" in _hits(searchable, "*nā")
