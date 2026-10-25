"""Put the corpus into Elasticsearch: the documents, and the word types.

Everything before this module happens in memory. The adapter yields poems, the
word-type pass counts every spelling, the link pass attaches readings — and
none of it was reaching the index, so a search had nothing to search. This is
the step that was missing.

Two shapes, from two sources:

**A document** is one poem, and it carries its own licence and corpus version.
Text is indexed with the Persian analyser so a phrase can be found in it.

**A word type** is one *reading*, not one spelling. مرد the man and مرد the
dead are two documents with the same evidence, because the corpus cannot tell
them apart and choosing one would be a guess. A spelling with no reading at
all still gets a document, with ``latin: null`` — that pile is the coverage
gap and the review list, and dropping it would hide the thing worth measuring.

**A reading of a function word's letters carries no count.** که is the
conjunction 609,699 times, and the lexicon's only reading of it is the
adjective *keh*; the count is not the adjective's (``rules/function_words.yaml``).
So the reading's document says ``function_word`` and leaves the counts empty,
and the count moves to a document of the spelling itself — ``latin: null``,
``function_word`` set — which is what those occurrences are. Nothing is
dropped: the letters keep their count, the reading keeps its document, and
neither claims the other's.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

from elasticsearch import Elasticsearch

from murfulu.corpus.adapter import SourceAdapter
from murfulu.corpus.function_words import FunctionWords
from murfulu.corpus.function_words import loaded as function_words
from murfulu.corpus.link import LinkedWordType, LinkResult
from murfulu.lexicon.categories import UnmappableCategoryError, word_classes_for
from murfulu.search.backfill import AffixMap
from murfulu.search.writer import BATCH_SIZE, WriteResult
from murfulu.search.writer import write as bulk_write

DOCUMENTS = "documents"
WORD_TYPES = "word_types"


def _word_classes(category: str | None) -> list[str]:
    """What the rules should match this lexicon category on.

    A category we deliberately did not map yields an empty list, not a
    default. "We decided not to" and "there happen to be none" have to look
    the same in the index only because both mean *no rule matches* — and the
    reason stays readable in ``rules/lexicon_categories.yaml``.
    """
    try:
        return list(word_classes_for(category))
    except (UnmappableCategoryError, LookupError):
        return []


def document_source(document: Any, corpus_version: str, licence: str) -> dict[str, Any]:
    """One poem as the ``documents`` index stores it."""
    return {
        "source_id": document.source_id,
        "document_id": document.document_id,
        "author": document.author,
        "title": document.title,
        "century": document.century,
        "text_fa": document.text_fa,
        "licence": licence,
        "corpus_version": corpus_version,
        "extra": dict(document.extra),
    }


def word_type_source(
    item: LinkedWordType,
    corpus_version: str,
    snapshot_id: str,
    formed_by: AffixMap | None = None,
    listed: FunctionWords | None = None,
) -> dict[str, Any]:
    """One reading of one corpus spelling, with all of its evidence.

    ``listed`` is the function-word list. Where the spelling is on it, the
    document says so, and a *reading's* document carries no count: the
    occurrences are the function word's, written onto the spelling's own
    document by :func:`_word_type_pairs`.
    """
    word = item.word
    reading = item.reading
    population = ["corpus"] + (["lexicon"] if reading else [])
    latin = item.latin
    source: dict[str, Any] = {
        "id": item.id,
        "spelling_fa": word.spelling_fa,
        "latin": latin,
        # *Ends with nā* is a prefix query on the reversed form. That is the
        # only reason this field exists.
        "latin_reversed": latin[::-1] if latin else None,
        "latin_wild": latin,
        "total_count": word.total_count,
        "doc_count": word.doc_count,
        "author_count": word.author_count,
        "first_century": word.first_century,
        "last_century": word.last_century,
        "counts_by_century": {str(c): n for c, n in word.counts_by_century.items()},
        "authors": word.top_authors,
        "sources": sorted(word.sources),
        "population": population,
        "corpus_version": corpus_version,
        # What the precompute showed formed this word, when a precompute has
        # been run. Empty otherwise — the field always exists, so a search on
        # it returns nothing rather than failing.
        **(
            formed_by.fields_for(item.id)
            if formed_by
            else {"affixes": [], "rule_ids": [], "semantic_tags": []}
        ),
    }
    homograph = listed.get(word.spelling_fa) if listed is not None else None
    if homograph is not None:
        source["function_word"] = homograph.word_class
    if reading is None:
        return source

    if homograph is not None:
        # Unknown, not zero: the letters are written, as another word.
        source.update(
            {
                "total_count": None,
                "doc_count": None,
                "author_count": None,
                "first_century": None,
                "last_century": None,
                "counts_by_century": {},
                "authors": [],
            }
        )
    source.update(
        {
            "reading_id": reading.latin,
            # Shown beside the primary, never chosen between: which
            # pronunciation is right is the linguist's. See FINDINGS, برنا.
            "latin_variants": list(reading.latin_variants),
            # The dictionary's own definition. A preview and shown as one.
            "definition_fa": reading.definition_fa,
            "source_entry_ids": [str(i) for i in reading.source_entry_ids],
            "sense_count": reading.sense_count,
            "lexicon_category": reading.lexicon_category,
            "word_class": _word_classes(reading.lexicon_category),
            "stem_1_fa": reading.past_stem_fa,
            "stem_1_latin": reading.past_stem_latin,
            "stem_2_fa": reading.present_stem_fa,
            "stem_2_latin": reading.present_stem_latin,
            "karbon_stem_rule": reading.karbon_stem_rule,
            "transitivity": reading.transitivity,
            "phonemic_confidence": reading.phonemic_confidence,
            "needs_review": reading.needs_review,
            "lexicon_snapshot_id": reading.snapshot_id or snapshot_id,
        }
    )
    return source


def _document_pairs(
    adapter: SourceAdapter, corpus_version: str
) -> Iterator[tuple[str, dict[str, Any]]]:
    licence = adapter.licence
    for document in adapter.documents():
        yield (
            document.document_id,
            document_source(document, corpus_version, licence),
        )


def _word_type_pairs(
    linked: Iterable[LinkedWordType],
    corpus_version: str,
    snapshot_id: str,
    formed_by: AffixMap | None,
    listed: FunctionWords | None = None,
) -> Iterator[tuple[str, dict[str, Any]]]:
    spelled: set[str] = set()
    for item in linked:
        yield (
            item.id,
            word_type_source(item, corpus_version, snapshot_id, formed_by, listed),
        )
        # A function word's letters that the lexicon also reads: the readings
        # carry no count, so the count gets a document of its own, once.
        spelling = item.word.spelling_fa
        if (
            item.reading is not None
            and listed is not None
            and spelling in listed
            and spelling not in spelled
        ):
            spelled.add(spelling)
            bare = LinkedWordType(word=item.word)
            yield (
                bare.id,
                word_type_source(bare, corpus_version, snapshot_id, formed_by, listed),
            )


def write_documents(
    client: Elasticsearch,
    version: str,
    adapter: SourceAdapter,
    batch_size: int = BATCH_SIZE,
) -> WriteResult:
    """Stream one corpus into ``documents-<version>``.

    Streamed from the adapter, never collected: Ganjoor is 133,148 poems and
    three million verses, and holding the text of all of them at once buys
    nothing.
    """
    return bulk_write(
        client, DOCUMENTS, version, _document_pairs(adapter, version), batch_size
    )


def write_word_types(
    client: Elasticsearch,
    version: str,
    result: LinkResult,
    formed_by: AffixMap | None = None,
    batch_size: int = BATCH_SIZE,
    listed: FunctionWords | None = None,
) -> WriteResult:
    """Write every counted spelling, linked or not, into ``word_types``.

    ``formed_by`` comes from a previous precompute and says which rule built
    each attested word. It is written **into a new corpus version**, never
    added to a live index: the alias moves once, when the version is whole.
    """
    return bulk_write(
        client,
        WORD_TYPES,
        version,
        _word_type_pairs(
            result.linked,
            version,
            result.lexicon_snapshot_id,
            formed_by,
            listed if listed is not None else function_words(),
        ),
        batch_size,
    )
