"""Write a precompute run into the ``derivations`` index.

The document id is the form plus its output class, which is the same key the
precompute merged on. Two writes with one id would be one word overwriting
itself, and that is why merging happens before this module is reached rather
than being left to Elasticsearch.

Everything about batching, versioned indices and rejected documents lives in
:mod:`murfulu.search.writer`, shared with the other two indices.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

from elasticsearch import Elasticsearch

from murfulu.scoring.records import Derivation
from murfulu.search.writer import BATCH_SIZE, WriteResult
from murfulu.search.writer import write as bulk_write

ALIAS = "derivations"


def _pairs(
    derivations: Iterable[Derivation],
) -> Iterator[tuple[str, dict[str, Any]]]:
    for derivation in derivations:
        yield derivation.id, derivation.as_document()


def write(
    client: Elasticsearch,
    version: str,
    derivations: Iterable[Derivation],
    batch_size: int = BATCH_SIZE,
) -> WriteResult:
    """Bulk-write derivations into the concrete index for one corpus version."""
    return bulk_write(client, ALIAS, version, _pairs(derivations), batch_size)
