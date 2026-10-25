"""Seeding the store from the document, and writing the document from the store.

The switch only works if seeding loses nothing and the export carries the
evidence. A question without the measurement behind it cannot be answered, so
an export that dropped it would be a worse document than the one it replaced.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from murfulu.db import rulings as store
from murfulu.db.models import Base, User

ROOT = Path(__file__).resolve().parent.parent


def _tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "export_rulings", ROOT / "tools" / "export_rulings.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TOOL = _tool()

DOCUMENT = """# For the linguist

Some preamble that is not a question.

## L1. The first question

Evidence for the first, with a number: 4,968.

## L10. The tenth question

Evidence for the tenth.

## L2. The second question

Evidence for the second.
"""


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path / 'authored.sqlite'}")
    Base.metadata.create_all(engine)
    with Session(engine) as opened:
        yield opened
    engine.dispose()


@pytest.fixture
def document(tmp_path: Path) -> Path:
    path = tmp_path / "FOR_THE_LINGUIST.md"
    path.write_text(DOCUMENT, encoding="utf-8")
    return path


def test_every_question_in_the_document_reaches_the_store(
    session: Session, document: Path
):
    created, skipped = TOOL.seed(session, document)
    assert (created, skipped) == (3, 0)
    assert {q.reference for q in store.questions(session)} == {"L1", "L2", "L10"}


def test_the_evidence_travels_with_the_question(session: Session, document: Path):
    """The number is the question. Seeding without it would be seeding nothing."""
    TOOL.seed(session, document)
    first = store.by_reference(session, "L1")
    assert "4,968" in first.context["from_document"]


def test_seeding_twice_creates_nothing(session: Session, document: Path):
    """The store is the newer of the two the moment it exists."""
    TOOL.seed(session, document)
    created, skipped = TOOL.seed(session, document)
    assert (created, skipped) == (0, 3)


def test_seeding_never_overwrites_an_answer(session: Session, document: Path):
    """A ruling given in the app must survive the next seed run."""
    TOOL.seed(session, document)
    author = User(username="expert-1")
    session.add(author)
    session.flush()
    store.rule_on(
        session,
        author=author,
        question=store.by_reference(session, "L1"),
        ruling_fa="بله.",
    )

    TOOL.seed(session, document)
    assert store.by_reference(session, "L1").state == "answered"
    answered = store.by_reference(session, "L1")
    assert store.standing(session, answered).ruling_fa == "بله."


def test_the_handles_are_ordered_naturally(session: Session, document: Path):
    """Sorted as text, L10 lands between L1 and L2 and the list reads shuffled."""
    TOOL.seed(session, document)
    assert [q.reference for q in store.questions(session)] == ["L1", "L2", "L10"]


def test_the_export_carries_the_evidence_through(session: Session, document: Path):
    TOOL.seed(session, document)
    written = TOOL._render(session)
    assert "4,968" in written, "an export that drops the evidence is a worse document"


def test_the_export_says_which_questions_have_no_persian_yet(
    session: Session, document: Path
):
    """Seeding cannot invent the wording he reads.

    The document is in English; translating it automatically would make our
    English the original. So the export marks them rather than hiding it.
    """
    TOOL.seed(session, document)
    written = TOOL._render(session)
    assert "no Persian yet" in written
    assert written.count("⚠") >= 3


def test_the_export_says_not_to_edit_it(session: Session, document: Path):
    """The rule pack learned this the hard way; the export says it up front."""
    TOOL.seed(session, document)
    assert "Do not edit by hand" in TOOL._render(session)


def test_an_answered_question_shows_its_ruling(session: Session, document: Path):
    TOOL.seed(session, document)
    author = User(username="expert-1")
    session.add(author)
    session.flush()
    store.rule_on(
        session,
        author=author,
        question=store.by_reference(session, "L2"),
        ruling_fa="پاسخ من.",
        ruling_en="My answer.",
    )

    written = TOOL._render(session)
    assert "پاسخ من." in written
    assert "My answer." in written
    assert "2 waiting, 1 answered" in written


def test_a_reversal_is_visible_in_the_export(session: Session, document: Path):
    """A changed answer must not read as though it had always said this."""
    TOOL.seed(session, document)
    author = User(username="expert-1")
    session.add(author)
    session.flush()
    question = store.by_reference(session, "L2")
    store.rule_on(session, author=author, question=question, ruling_fa="بله.")
    store.rule_on(
        session,
        author=author,
        question=question,
        ruling_fa="خیر.",
        supersedes_earlier=True,
    )

    written = TOOL._render(session)
    assert "خیر." in written
    assert "the answer changed" in written
