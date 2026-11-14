"""The evidence list against a real Elasticsearch.

The stand-in in ``test_evidence.py`` cannot say whether a cluster accepts what
the module sends: a terms aggregation ordered on two keys with a ``missing``
bucket, a sort on a field some indices lack, ``search_after`` with no source.
This sends them to one, against an index of its own with the real mapping.

**No alias is moved.** The index is named outside the ``documents-*`` pattern
and is asked for by name, so a running site never sees it. Skips when no
cluster is reachable.
"""

import os
from collections.abc import Iterator
from typing import Any

import pytest
from elasticsearch import Elasticsearch

from murfulu.search.evidence import line_count, page, summary
from murfulu.search.indices import connect
from murfulu.search.mappings import DOCUMENTS, SETTINGS

from .test_evidence import TEXTS

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

INDEX = "evidence-test-fixture"


@pytest.fixture
def cluster() -> Iterator[Elasticsearch]:
    url = os.environ.get("MURFULU_ELASTICSEARCH_URL", "http://localhost:9200")
    client = connect(url)
    try:
        reachable = client.ping()
    except Exception:  # noqa: BLE001 - any failure means "not reachable"
        reachable = False
    if not reachable:
        pytest.skip(f"no Elasticsearch at {url}")
    client.indices.delete(index=INDEX, ignore_unavailable=True)
    client.indices.create(index=INDEX, mappings=DOCUMENTS, settings=SETTINGS)
    try:
        for one in TEXTS:
            stored: dict[str, Any] = {k: v for k, v in one.items() if v is not None}
            client.index(index=INDEX, id=one["document_id"], document=stored)
        client.indices.refresh(index=INDEX)
        yield client
    finally:
        client.indices.delete(index=INDEX, ignore_unavailable=True)


def test_a_real_cluster_ranks_pages_and_counts_the_same_way(cluster: Elasticsearch):
    found = summary(cluster, "دل", index=INDEX)
    assert found.total == 5
    assert found.authors == (("الف", 3), ("", 1), ("ب", 1))
    assert found.corpus_version == "v-test"
    seen = [
        one.document_id
        for number in range(3)
        for one in page(cluster, "دل", found, number=number, size=2, index=INDEX)
    ]
    assert seen == ["t:a:10", "t:a:20", "t:a:30", "t:-:1", "t:b:5"]
    assert line_count(cluster, "دل", 5, index=INDEX) == 6


def test_a_real_cluster_is_walked_past_the_window(cluster: Elasticsearch):
    found = summary(cluster, "دل", index=INDEX)
    shown = page(
        cluster, "دل", found, author="الف", number=1, size=2, index=INDEX, window=1
    )
    assert [one.document_id for one in shown] == ["t:a:30"]
    unnamed = page(cluster, "دل", found, author="", index=INDEX)
    assert [one.document_id for one in unnamed] == ["t:-:1"]
