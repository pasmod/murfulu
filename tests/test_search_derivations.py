"""Writing a precompute run into the ``derivations`` index.

Needs a live Elasticsearch and skips when none is reachable, so the suite
still runs on a bare machine. The mapping is ``dynamic: strict``, which makes
this the real check that the stored document and the mapping agree — a field
the mapping does not declare fails the write instead of being ignored.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import load
from murfulu.scoring.precompute import Precompute, input_readings, run
from murfulu.search import derivations as writer
from murfulu.search.indices import IndexAdmin, connect

from .conftest import aliases_restored

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

VERSION = "test-derivations"


@pytest.fixture
def admin() -> Iterator[IndexAdmin]:
    """A clean ``derivations`` index on a live cluster, or skip."""
    url = os.environ.get("MURFULU_ELASTICSEARCH_URL", "http://localhost:9200")
    client = connect(url)
    try:
        reachable = client.ping()
    except Exception:  # noqa: BLE001 - any failure means "not reachable"
        reachable = False
    if not reachable:
        pytest.skip(f"no Elasticsearch at {url}")

    def clean() -> None:
        found = client.indices.get(
            index=f"derivations-{VERSION}", ignore_unavailable=True
        )
        for name in found.body:
            client.indices.delete(index=name)

    with aliases_restored(client, ["derivations"]):
        clean()
        admin = IndexAdmin(client)
        admin.create("derivations", VERSION)
        yield admin
        clean()


@pytest.fixture
def job(lexicon_snapshot: Path) -> Precompute:
    """A small precompute run over the fixture lexicon."""
    pack = load()
    with Lexicon.open(lexicon_snapshot) as lexicon:
        return run(
            pack,
            input_readings(lexicon),
            depth=2,
            corpus_version=VERSION,
            generated_at="2026-08-11T12:00:00+00:00",
        )


def test_a_run_is_written_whole(admin: IndexAdmin, job: Precompute):
    result = writer.write(admin.client, VERSION, job.derivations())
    assert result.complete, result.failures
    assert result.written == job.report.forms_unique

    admin.client.indices.refresh(index=f"derivations-{VERSION}")
    counted = admin.client.count(index=f"derivations-{VERSION}")["count"]
    assert counted == job.report.forms_unique


def test_a_stored_word_keeps_its_derivation(admin: IndexAdmin, job: Precompute):
    writer.write(admin.client, VERSION, job.derivations())
    admin.client.indices.refresh(index=f"derivations-{VERSION}")

    stored = admin.client.get(index=f"derivations-{VERSION}", id="Raftār:karnam")
    source = stored["_source"]
    assert source["form_fa"] == "رفتار"
    assert source["paths"][0]["rule_ids"] == source["built_by"]
    assert source["paths"][0]["source_spelling_fa"] == "رفتن"


def test_a_run_with_no_timestamp_still_writes(
    admin: IndexAdmin, lexicon_snapshot: Path
):
    """An empty string is not a date, and the cluster rightly refuses one."""
    pack = load()
    with Lexicon.open(lexicon_snapshot) as lexicon:
        untimed = run(pack, input_readings(lexicon), depth=1)
    result = writer.write(admin.client, VERSION, untimed.derivations())
    assert result.complete, result.failures


def test_the_alias_only_moves_when_the_run_is_complete(
    admin: IndexAdmin, job: Precompute
):
    """A half-written index must never be what the app is serving.

    What is asserted is that the alias does not move **to this run** while it
    is being written — not that no alias exists. The first version asserted
    the latter, which quietly assumed a machine that had never run a
    precompute, and failed the moment one had.
    """
    before = admin.current_version("derivations")
    result = writer.write(admin.client, VERSION, job.derivations())
    assert result.complete
    assert admin.current_version("derivations") == before, "writing must not release"

    admin.release("derivations", VERSION)
    assert admin.current_version("derivations") == VERSION
