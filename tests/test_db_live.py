"""The schema against a real Postgres.

Skips when ``MURFULU_DATABASE_URL`` names no reachable server, so the suite
still runs on a bare machine — the same arrangement the Elasticsearch tests
use. No credentials are written down here; the URL is configuration.

Everything runs in a scratch database that is created and dropped by the test,
so a developer's own data is never touched.

What only Postgres can prove: that ``alembic upgrade head`` really builds the
schema, and that ``expert_feedback`` is append-only in the database rather than
by agreement.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.exc import DatabaseError, OperationalError
from sqlalchemy.orm import Session

from murfulu.db import feedback
from murfulu.db.config import URL_VARIABLE, with_driver
from murfulu.db.models import Base, ExpertFeedback, User

REPO = Path(__file__).resolve().parents[1]
SCRATCH = "murfulu_schema_test"


def _configured_url() -> str:
    url = os.environ.get(URL_VARIABLE)
    if not url:
        pytest.skip(f"{URL_VARIABLE} is not set")
    resolved = with_driver(url)
    if not resolved.startswith("postgresql"):
        pytest.skip("the live schema test needs Postgres")
    return resolved


@pytest.fixture(scope="module")
def scratch_url() -> Iterator[str]:
    """A database of this test's own, created fresh and dropped afterwards."""
    admin = create_engine(_configured_url(), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as connection:
            connection.execute(text(f"DROP DATABASE IF EXISTS {SCRATCH}"))
            connection.execute(text(f"CREATE DATABASE {SCRATCH}"))
    except (OperationalError, DatabaseError) as unreachable:
        admin.dispose()
        pytest.skip(f"no Postgres to test against: {unreachable}")

    base, _, _ = _configured_url().rpartition("/")
    url = f"{base}/{SCRATCH}"
    yield url

    with admin.connect() as connection:
        connection.execute(text(f"DROP DATABASE IF EXISTS {SCRATCH} WITH (FORCE)"))
    admin.dispose()


@pytest.fixture(scope="module")
def migrated(scratch_url: str) -> Iterator[str]:
    """The scratch database with ``alembic upgrade head`` applied to it."""
    previous = os.environ.get(URL_VARIABLE)
    os.environ[URL_VARIABLE] = scratch_url
    try:
        command.upgrade(Config(str(REPO / "alembic.ini")), "head")
        yield scratch_url
    finally:
        if previous is None:
            del os.environ[URL_VARIABLE]
        else:
            os.environ[URL_VARIABLE] = previous


@pytest.fixture
def engine(migrated: str) -> Iterator[Engine]:
    made = create_engine(migrated)
    yield made
    made.dispose()


def test_upgrade_head_builds_every_table(engine: Engine):
    tables = set(inspect(engine).get_table_names())
    assert {
        "rules",
        "glide_rules",
        "users",
        "expert_feedback",
        "sources",
        "corpus_versions",
        "corpus_version_sources",
        "alembic_version",
    } <= tables


def test_the_migration_matches_the_models(engine: Engine):
    """A hand edit to a model without a migration would show up here."""
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []


def test_a_feedback_row_survives_the_round_trip(engine: Engine):
    with Session(engine) as session:
        author = User(username="expert-live")
        session.add(author)
        session.flush()
        written = feedback.record(
            session,
            author=author,
            category="linguistic",
            target_type="derivation",
            target_id="Raftorow:karnam",
            verdict="possible",
            note="ساخت درست است ولی کاربرد ندارد",
            context={"form_fa": "رفت‌ورو", "rule_chain": ["V-046"]},
            corpus_version="v3",
        )
        session.commit()
        written_id = written.id

    with Session(engine) as session:
        read_back = session.get(ExpertFeedback, written_id)
        assert read_back is not None
        assert read_back.verdict == "possible"
        assert read_back.note == "ساخت درست است ولی کاربرد ندارد"
        assert read_back.context["form_fa"] == "رفت‌ورو"
        assert read_back.owner == "murfulu"
        assert read_back.created_at is not None


def test_feedback_cannot_be_changed(engine: Engine):
    with Session(engine) as session:
        author = User(username="expert-append-only")
        session.add(author)
        session.flush()
        row = feedback.record(
            session,
            author=author,
            category="data",
            target_type="statistic",
            target_id="hapax-count",
            note="this figure looks wrong",
            context={},
        )
        session.commit()
        row_id = row.id

    for statement in (
        "UPDATE expert_feedback SET note = 'edited' WHERE id = :id",
        "DELETE FROM expert_feedback WHERE id = :id",
    ):
        with (
            engine.begin() as connection,
            pytest.raises(DatabaseError, match="append-only"),
        ):
            connection.execute(text(statement), {"id": row_id})
