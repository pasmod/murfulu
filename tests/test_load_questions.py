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


def test_l17d_names_every_group_of_the_word_bank(data: dict) -> None:
    """L17d asks how his twelve groups feed the rules; it must name all twelve."""
    groups = yaml.safe_load(
        (ROOT / "rules" / "bank_groups.yaml").read_text(encoding="utf-8")
    )["groups"]
    (asked,) = [q for q in data["questions"] if q["reference"] == "L17d"]
    for one in groups:
        assert one["label_fa"] in asked["question_fa"], one["key"]


def test_every_asked_question_ends_with_our_proposal(data: dict) -> None:
    """The project lead's rule of 2026-11-12: one marked option, and why."""
    for one in data["questions"]:
        suggested = [c for c in one["choices"] if c.get("suggested")]
        if one.get("defer"):
            assert not suggested, f"{one['reference']} is deferred; no proposal yet"
            continue
        assert len(suggested) == 1, one["reference"]
        assert suggested[0].get("settles", True), one["reference"]
        text = one["question_fa"]
        assert text.count("پیشنهاد ما:") == 1, one["reference"]
        # The proposal follows the question, as the last paragraph.
        assert text.index("پیشنهاد ما:") > text.index("پرسش:"), one["reference"]
        assert text.rstrip().split("\n\n")[-1].startswith("پیشنهاد ما:")


def test_the_old_stem_names_are_gone_from_every_question(data: dict) -> None:
    """Only where L17d says they were replaced."""
    replaced = "به جای کاربن یک و کاربن دو"
    for one in data["questions"]:
        text = one["question_fa"] + " ".join(c["text_fa"] for c in one["choices"])
        text = text.replace(replaced, "")
        assert "کاربن یک" not in text and "کاربن دو" not in text, one["reference"]


def test_a_dry_run_writes_nothing(session: Session, data: dict) -> None:
    tool.load(session, data)
    session.rollback()
    assert store.by_reference(session, "L5").state == "open"
    with pytest.raises(store.UnknownQuestionError):
        store.by_reference(session, "L26")


def test_apply_adds_rewords_and_withdraws(session: Session, data: dict) -> None:
    plan = tool.load(session, data)
    session.commit()

    deferred = store.by_reference(session, "L26")
    assert deferred.state == "deferred" and deferred.blocks_work
    assert deferred.context["covers"] == ["L18", "L26", "L35"]
    assert deferred.context["deferred_because"].strip()
    assert [c["id"] for c in store.choices_of(deferred)][0] == "nam_or_karnam"

    reworded = store.by_reference(session, "L2")
    assert reworded.state == "blocked"
    assert reworded.context["from_document"] == "evidence", "evidence is kept"
    assert reworded.context["reworded"][0]["question_fa"] == "پرسش 2"

    withdrawn = store.by_reference(session, "L5")
    assert withdrawn.state == "withdrawn"
    assert withdrawn.context["withdrawn_because"].strip()
    assert store.by_reference(session, "L13").state == "withdrawn"

    assert plan.withdrawn == 10  # L1 L5 L6 L7 L8 L9 L12 L13 L14 L15
    assert plan.reworded == 3  # L2 L3 L10
    assert plan.deferred == 1  # L26
    assert plan.added == len(data["questions"]) - 3


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


def test_a_blocking_question_listed_for_withdrawal_is_withdrawn(
    session: Session, data: dict
) -> None:
    """L17 blocked work; his own group name settled it. Listing it decides."""
    store.ask(session, reference="L17", question_fa="پرسش ۱۷", blocks_work=True)
    tool.load(session, data)
    closed = store.by_reference(session, "L17")
    assert closed.state == "withdrawn"
    assert "جانام" in closed.context["withdrawn_because"]


def test_a_deferred_question_comes_back_when_its_deferral_is_lifted(
    session: Session, data: dict
) -> None:
    tool.load(session, data)
    assert store.by_reference(session, "L26").state == "deferred"
    lifted = dict(data)
    lifted["questions"] = [
        {key: value for key, value in one.items() if key != "defer"}
        for one in data["questions"]
    ]
    tool.load(session, lifted)
    back = store.by_reference(session, "L26")
    assert back.state == "blocked"
    assert "deferred_because" not in back.context


def test_a_deferral_without_a_reason_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "questions.yaml"
    path.write_text(
        "questions:\n"
        "  - reference: L99\n"
        "    question_fa: پرسش\n"
        "    defer: ''\n"
        "    choices: [{id: a, text_fa: یک}]\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="deferred without a reason"):
        tool.read(path)


def test_the_store_refuses_to_defer_an_answered_question_or_without_reason(
    session: Session,
) -> None:
    with pytest.raises(store.RulingRefusedError):
        store.defer(session, store.by_reference(session, "L16"), why="بعداً")
    with pytest.raises(store.RulingRefusedError):
        store.defer(session, store.by_reference(session, "L2"), why="  ")
    store.defer(session, store.by_reference(session, "L2"), why="بعداً")
    assert store.by_reference(session, "L2").state == "deferred"
    # Not waiting: the list of what blocks work leaves it out.
    assert "L2" not in {q.reference for q in store.questions(session, state="blocked")}


def test_a_deferred_question_takes_no_ruling_and_does_not_block(
    session: Session, data: dict
) -> None:
    tool.load(session, data)
    deferred = store.by_reference(session, "L26")
    author = session.query(User).first()
    with pytest.raises(store.RulingRefusedError, match="deferred"):
        store.rule_on(session, author=author, question=deferred, ruling_fa="بله")
    blocking = {q.reference for q in store.questions(session, blocking_only=True)}
    assert "L26" not in blocking and "L13" not in blocking


def test_a_deferred_question_can_be_withdrawn_by_listing_it(
    session: Session, data: dict
) -> None:
    tool.load(session, data)
    moved = dict(data)
    moved["questions"] = [q for q in data["questions"] if q["reference"] != "L26"]
    moved["withdraw"] = {**data["withdraw"], "L26": "دیگر لازم نیست."}
    tool.load(session, moved)
    assert store.by_reference(session, "L26").state == "withdrawn"
