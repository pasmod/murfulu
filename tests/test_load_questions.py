"""Loading the reviewed question wording into the store.

The wording is written and proofread in `rules/questions_fa.yaml`; the store
stays the record. What matters here is what the loader must never do: write on
a dry run, reword a question that has been answered, delete a question, or
withdraw one that blocks work.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from murfulu.db import rulings as store
from murfulu.db.models import Base, User

ROOT = Path(__file__).resolve().parent.parent


def _tool(name: str = "load_questions") -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Registered before running, because a dataclass looks its module up.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


tool = _tool()


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    """A store shaped like the app's on 2026-10-17: L1–L16, L16 answered."""
    engine = create_engine(f"sqlite:///{tmp_path / 'authored.sqlite'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        author = User(username="site", display_name="site")
        session.add(author)
        session.flush()
        for number in (1, 2, 3, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16):
            store.ask(
                session,
                reference=f"L{number}",
                question_fa=f"پرسش {number}",
                context={"from_document": "evidence"},
                origin="document",
            )
        store.ask(session, reference="L11", question_fa="پرسش ۱۱")
        store.withdraw(session, store.by_reference(session, "L11"), why="قدیمی")
        store.rule_on(
            session,
            author=author,
            question=store.by_reference(session, "L16"),
            ruling_fa="پاسخ داده شد.",
        )
        session.commit()
        yield session
    engine.dispose()


@pytest.fixture
def data() -> dict:
    return tool.read()


def test_the_file_reads_and_every_question_offers_options(data: dict) -> None:
    for one in data["questions"]:
        assert one["choices"], f"{one['reference']} offers no options"
        assert (
            any(c.get("settles") is False for c in one["choices"])
            or len(one["choices"]) >= 2
        )


def test_no_one_is_named_in_the_file() -> None:
    """The repository is public; people are referred to by role.

    The names come from the clone's ``.denylist`` (never committed), so this
    test names no one itself; a clone without one skips it.
    """
    denylist = ROOT / ".denylist"
    if not denylist.exists():
        pytest.skip("no .denylist in this clone (docs/ENGINEERING.md)")
    check = _tool("public_check")
    denied = check.denylist_patterns(denylist.read_text(encoding="utf-8"))
    path = "rules/questions_fa.yaml"
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    found = [
        finding.rule
        for number, line in enumerate(lines, 1)
        for finding in check.check_line(path, number, line, denied)
    ]
    assert not found


def test_the_explanations_asked_about_are_the_ones_on_screen(data: dict) -> None:
    """L17d quotes the twelve explanations; it must quote what the app shows."""
    classes = yaml.safe_load(
        (ROOT / "rules" / "word_classes.yaml").read_text(encoding="utf-8")
    )["classes"]
    (asked,) = [q for q in data["questions"] if q["reference"] == "L17d"]
    for one in classes:
        assert one["explanation_fa"] in asked["question_fa"], one["name"]


def test_a_dry_run_writes_nothing(session: Session, data: dict) -> None:
    tool.load(session, data)
    session.rollback()
    assert store.by_reference(session, "L5").state == "open"
    with pytest.raises(store.UnknownQuestionError):
        store.by_reference(session, "L26")


def test_apply_adds_rewords_and_withdraws(session: Session, data: dict) -> None:
    plan = tool.load(session, data)
    session.commit()

    added = store.by_reference(session, "L26")
    assert added.state == "blocked" and added.blocks_work
    assert added.context["covers"] == ["L18", "L26"]
    assert [c["id"] for c in store.choices_of(added)][0] == "nam_or_karnam"

    reworded = store.by_reference(session, "L13")
    assert reworded.state == "blocked"
    assert reworded.context["from_document"] == "evidence", "evidence is kept"
    assert reworded.context["reworded"][0]["question_fa"] == "پرسش 13"

    withdrawn = store.by_reference(session, "L5")
    assert withdrawn.state == "withdrawn"
    assert withdrawn.context["withdrawn_because"].strip()

    assert plan.withdrawn == 9  # L1 L5 L6 L7 L8 L9 L12 L14 L15
    assert plan.reworded == 4  # L2 L3 L10 L13
    assert plan.added == len(data["questions"]) - 4


def test_an_answered_question_is_left_alone(session: Session, data: dict) -> None:
    data = dict(data)
    data["questions"] = [
        *data["questions"],
        {
            "reference": "L16",
            "question_fa": "پرسش بازنویسی‌شده",
            "choices": [{"id": "a", "text_fa": "یک"}],
        },
    ]
    plan = tool.load(session, data)
    question = store.by_reference(session, "L16")
    assert question.state == "answered"
    assert question.question_fa == "پرسش 16"
    assert plan.kept == 1


def test_loading_twice_changes_nothing_the_second_time(
    session: Session, data: dict
) -> None:
    tool.load(session, data)
    session.commit()
    again = tool.load(session, data)
    assert again.added == again.reworded == again.withdrawn == 0
    assert again.unchanged == len(data["questions"])


def test_a_blocking_question_not_in_the_file_is_not_withdrawn(
    session: Session, data: dict
) -> None:
    store.ask(session, reference="S9", question_fa="پرسش", blocks_work=True)
    plan = tool.load(session, data)
    assert store.by_reference(session, "S9").state == "blocked"
    assert any(line.startswith("blocking  S9") for line in plan.lines)


def test_nothing_is_deleted(session: Session, data: dict) -> None:
    before = {q.reference for q in store.questions(session)}
    tool.load(session, data)
    session.commit()
    after = {q.reference for q in store.questions(session)}
    assert before <= after


def test_the_proofreading_export_carries_every_option(data: dict) -> None:
    text = tool.markdown(data)
    for one in data["questions"]:
        assert f"## {one['reference']}" in text
        for choice in one["choices"]:
            assert choice["text_fa"].strip() in text
