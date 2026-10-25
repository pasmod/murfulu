"""The feedback set as a released dataset.

PLAN 8.3. What is checked is what leaves and what does not: the evidence a
record needs to be usable, and the things that must never be in a file that
goes to somebody outside this project.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from murfulu.db import feedback as store
from murfulu.db.dataset import FIELDS, Dataset, build
from murfulu.db.models import Base, User

EXPORTED_ON = "2026-08-12"


@pytest.fixture
def written() -> Iterator[Session]:
    """A store with three records: a verdict, a bug, and karbon's share."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        expert = User(username="expert-1")
        reader = User(username="reader-1")
        session.add_all([expert, reader])
        session.flush()

        store.record(
            session,
            author=expert,
            category="linguistic",
            target_type="derivation",
            target_id="Raftorow:karnam",
            verdict="wrong",
            note="این واژه نیست",
            context={"form_latin": "Raftorow", "rule_chain": ["V-046"]},
            corpus_version="v1",
        )
        store.record(
            session,
            author=reader,
            category="bug",
            target_type="app",
            note="دکمه کار نمی‌کند",
            context={"screen": "/build"},
        )
        store.record(
            session,
            author=expert,
            category="data",
            target_type="lexicon_entry",
            target_id="پهن",
            note="خوانش نادرست است",
            context={},
        )
        session.commit()
        yield session
    engine.dispose()


def _dataset(session: Session) -> Dataset:
    from sqlalchemy import select

    from murfulu.db.models.review import ExpertFeedback

    rows = list(session.scalars(select(ExpertFeedback)))
    return build(rows, exported_on=EXPORTED_ON)


# -- what a record carries ---------------------------------------------------


def test_every_record_has_every_field(written: Session):
    dataset = _dataset(written)
    assert len(dataset) == 3
    for record in dataset.records:
        assert set(record) == set(FIELDS)


def test_a_verdict_keeps_its_note_and_its_context(written: Session):
    """The structured context is what makes the record reusable."""
    record = _dataset(written).records[0]
    assert record["verdict"] == "wrong"
    assert record["note"] == "این واژه نیست"
    assert record["context"]["rule_chain"] == ["V-046"]
    assert record["corpus_version"] == "v1"


def test_the_role_no_longer_travels_because_there_is_no_role(written: Session):
    """The dataset no longer says what role an author had.

    It used to carry `author_role`, because only an expert could grade a word
    and a reader of the dataset needed to know which records those were. There
    is one account and no roles as of 2026-08-17, so the field would have
    been a constant — and a constant in a research dataset reads as a
    distinction somebody measured.
    """
    records = _dataset(written).records

    assert records
    assert all("author_role" not in record for record in records)
    # The pseudonym stays: it is what the manifest promises and what any
    # future comparison would need.
    assert all(record["author"].startswith("author-") for record in records)


def test_karbon_s_share_is_marked_not_dropped(written: Session):
    """We mount that lexicon read-only and cannot fix it. It goes upstream."""
    owners = {record["owner"] for record in _dataset(written).records}
    assert owners == {"murfulu", "karbon"}


# -- what does not leave ------------------------------------------------------


def test_no_account_name_leaves(written: Session):
    """A pseudonym is all inter-rater agreement needs."""
    body = "\n".join(_dataset(written).lines())
    assert "expert-1" not in body
    assert "reader-1" not in body
    assert "author-1" in body


def test_two_authors_stay_distinguishable(written: Session):
    """Otherwise agreement between reviewers cannot be computed at all."""
    authors = {record["author"] for record in _dataset(written).records}
    assert len(authors) == 2


def test_the_same_author_gets_the_same_label_every_time(written: Session):
    records = _dataset(written).records
    assert records[0]["author"] == records[2]["author"]


def test_no_token_or_hash_leaves(written: Session):
    body = "\n".join(_dataset(written).lines())
    assert "token" not in body
    assert "hash" not in body


# -- the file itself ----------------------------------------------------------


def test_it_is_one_json_object_per_line(written: Session):
    for line in _dataset(written).lines():
        assert json.loads(line)["id"]
        assert "\n" not in line


def test_persian_is_written_as_persian_not_as_escapes(written: Session):
    """A dataset nobody can read in a text editor is a worse dataset."""
    assert "این واژه نیست" in "\n".join(_dataset(written).lines())


def test_the_manifest_says_what_it_is_and_counts_it(written: Session):
    manifest = _dataset(written).manifest()
    assert "records: 3" in manifest
    assert EXPORTED_ON in manifest
    assert "linguistic 1" in manifest
    assert "karbon 1" in manifest
    for name in FIELDS:
        assert f"`{name}`" in manifest


def test_the_manifest_does_not_hand_the_records_on(written: Session):
    """The repository is Apache-2.0; these records are not.

    They are judgements experts made about the language rather than anything
    this project wrote, and they were not given to us to give away. The
    manifest guessed no licence while 8.4 was open and must not acquire one by
    inheritance now that it is closed — so it names the code's licence only to
    say that it stops here.
    """
    manifest = _dataset(written).manifest()
    assert "Ask before redistributing" in manifest
    assert "does not reach this file" in manifest
    # Named, and only in the sentence that excludes it.
    licence_lines = [line for line in manifest.splitlines() if "Apache" in line]
    assert licence_lines, "the code's licence is named, so the limit is legible"
    for line in licence_lines:
        assert "not" in line, f"reads as a grant: {line}"


def test_the_manifest_says_there_are_no_screenshots(written: Session):
    """The app captures none. A dataset that implied otherwise would mislead."""
    assert "No screenshots" in _dataset(written).manifest()


def test_an_empty_store_produces_an_empty_dataset_not_an_error():
    """The state this project is in until the reviewers have used the app."""
    empty = build([], exported_on=EXPORTED_ON)
    assert len(empty) == 0
    assert list(empty.lines()) == []
    assert "records: 0" in empty.manifest()


def test_the_export_is_reproducible(written: Session):
    """The same rows and the same date give the same file, byte for byte."""
    first = "\n".join(_dataset(written).lines())
    second = "\n".join(_dataset(written).lines())
    assert first == second


def test_the_command_takes_the_date_rather_than_reading_the_clock():
    """So a test and a rerun produce the same file."""
    source = (
        Path(__file__).resolve().parents[1] / "src/murfulu/db/dataset.py"
    ).read_text(encoding="utf-8")
    assert "datetime.now" not in source
