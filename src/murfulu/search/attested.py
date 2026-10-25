"""Ask the corpus about forms nobody has precomputed.

The batch pipeline attests by building the whole link pass in memory, which is
right for 1.7 million forms and impossible for one HTTP request. This asks the
``word_types`` index instead, in one query for every form at once.

**The answer comes out of the same class the batch job uses.** The three
levels of evidence — reading, spelling, none — are decided in
:mod:`murfulu.scoring.attestation`, and this module only fills that index from
a different source. A second implementation of "is this word attested" would
drift from the first, and the two would disagree about the same word.

This is the **read** half of what live generation needs. Writing live results
back into the ``derivations`` index is a separate question, still open — see
OPEN_QUESTIONS S2.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Any

from elasticsearch import Elasticsearch

from murfulu.corpus.wordtypes import WordType, normalise
from murfulu.scoring.attestation import Index

INDEX = "word_types"

#: Spellings per request. A generated family is a few hundred forms; a batch
#: this size keeps that to one or two queries without building a term query so
#: large that Elasticsearch refuses it.
BATCH = 1_000


def _word_type(source: dict[str, Any]) -> WordType:
    """Rebuild the counted word type from its stored document."""
    word = WordType(spelling_fa=source.get("spelling_fa", ""))
    word.total_count = int(source.get("total_count") or 0)
    # Only the sizes of these sets are ever read back, and the stored document
    # keeps the counts rather than the members, so they are filled with as
    # many placeholders as the count says.
    word.documents = {str(n) for n in range(int(source.get("doc_count") or 0))}
    word.authors = Counter({name: 1 for name in (source.get("authors") or [])})
    counted = int(source.get("author_count") or 0)
    for extra in range(len(word.authors), counted):
        word.authors[f"__{extra}"] = 1
    word.counts_by_century = Counter(
        {int(k): int(v) for k, v in (source.get("counts_by_century") or {}).items()}
    )
    word.sources = set(source.get("sources") or [])
    return word


def look_up(
    client: Elasticsearch,
    spellings: Iterable[str],
    *,
    index: str = INDEX,
    corpus_version: str = "",
) -> Index:
    """Build an attestation index covering exactly these spellings.

    Spellings are normalised the way the corpus was counted, because that is
    how they were stored; asking any other way finds nothing for a word the
    corpus certainly has.
    """
    wanted = sorted({normalise(one) for one in spellings if one})
    found = Index(corpus_version=corpus_version)
    if not wanted:
        return found

    for start in range(0, len(wanted), BATCH):
        batch = wanted[start : start + BATCH]
        response = client.search(
            index=index,
            size=len(batch) * 4,
            query={"terms": {"spelling_fa": batch}},
            track_total_hits=False,
        )
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            found.add(_word_type(source), source.get("latin"))
            if not found.corpus_version:
                found.corpus_version = source.get("corpus_version", "")
    return found
