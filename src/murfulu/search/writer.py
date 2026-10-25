"""Bulk-write into a versioned index, and say what did not go in.

Shared by all three indices, because the rule is the same for each: a run
fills ``<alias>-<version>`` and the alias only swaps across when the run is
complete. Nothing ever writes to what the app is serving.

The one thing this module refuses to do is swallow a rejection. A bulk request
that half-succeeds leaves an index that looks exactly like a complete one, and
the counts drawn from it would be wrong with no sign that anything happened.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from murfulu.search.indices import index_name

#: How many documents go in one request. Large enough to be fast, small enough
#: that one failure does not take a million documents with it.
BATCH_SIZE = 2_000


@dataclass
class WriteResult:
    """What a write did, and everything that refused to go in."""

    written: int = 0
    #: Documents Elasticsearch rejected, with its reason. Never swallowed: a
    #: silently short index looks exactly like a complete one.
    failures: list[dict[str, Any]] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        """True when every document was accepted."""
        return not self.failures

    def summary(self) -> str:
        """One line for the ingest log."""
        if self.complete:
            return f"{self.written:,} written"
        return f"{self.written:,} written, {len(self.failures):,} rejected"


def actions(
    index: str, documents: Iterable[tuple[str, dict[str, Any]]]
) -> Iterator[dict[str, Any]]:
    """Turn ``(id, source)`` pairs into bulk actions for one index."""
    for identifier, source in documents:
        yield {"_index": index, "_id": identifier, "_source": source}


def write(
    client: Elasticsearch,
    alias: str,
    version: str,
    documents: Iterable[tuple[str, dict[str, Any]]],
    batch_size: int = BATCH_SIZE,
) -> WriteResult:
    """Bulk-write ``(id, source)`` pairs into one alias's concrete index.

    The index must already exist — creating it is ``IndexAdmin.create``, and
    keeping the two apart is what lets a run be resumed without re-creating
    what it is filling.
    """
    index = index_name(alias, version)
    written, errors = bulk(
        client,
        actions(index, documents),
        chunk_size=batch_size,
        raise_on_error=False,
        stats_only=False,
    )
    rejected = errors if isinstance(errors, list) else []
    return WriteResult(
        written=int(written),
        failures=[error for error in rejected if isinstance(error, dict)],
    )
