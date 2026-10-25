"""The authored schema, without a database server.

SQLite here, Postgres in ``test_db_live.py``. What these check is the part that
is the same on both: that the tables build, that the rules the documents state
are refused by the database rather than by a comment, and that the store puts
a record together the way ``docs/REVIEW.md`` describes.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from murfulu.db import feedback, rulesync
from murfulu.db.models import Base, ExpertFeedback, User
from murfulu.db.models.review import owner_for
from murfulu.rules import pack as rulepack


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path / 'authored.sqlite'}")
    Base.metadata.create_all(engine)
    with Session(engine) as open_session:
        yield open_session
    engine.dispose()


@pytest.fixture
def expert(session: Session) -> User:
    account = User(username="expert-1")
    session.add(account)
    session.flush()
    return account


@pytest.fixture
def reader(session: Session) -> User:
    account = User(username="reader-1")
    session.add(account)
    session.flush()
    return account


def test_every_table_is_created(session: Session):
    expected = {
        "rules",
        "glide_rules",
        "users",
        "expert_feedback",
        "sources",
        "corpus_versions",
        "corpus_version_sources",
    }
    assert expected <= set(Base.metadata.tables)


def test_a_feedback_row_is_written_and_read_back(session: Session, expert: User):
    row = feedback.record(
        session,
        author=expert,
        category="linguistic",
        target_type="derivation",
        target_id="Raftorow:karnam",
        verdict="wrong",
        note="این واژه نیست",
        context={"form_latin": "Raftorow", "rule_chain": ["V-046"]},
        corpus_version="v3",
    )
    session.commit()

    stored = feedback.for_target(session, "derivation", "Raftorow:karnam")
    assert [item.id for item in stored] == [row.id]
    assert stored[0].verdict == "wrong"
    assert stored[0].context["rule_chain"] == ["V-046"]
    assert stored[0].corpus_version == "v3"
    assert stored[0].created_at is not None


def test_anyone_may_report_a_bug(session: Session, reader: User):
    row = feedback.record(
        session,
        author=reader,
        category="bug",
        target_type="app",
        note="the search button does nothing",
        context={"screen": "search"},
    )
    session.commit()
    assert row.verdict is None
    assert row.owner == "murfulu"


def test_feedback_about_the_lexicon_is_marked_for_karbon(
    session: Session, expert: User
):
    feedback.record(
        session,
        author=expert,
        category="data",
        target_type="lexicon_entry",
        target_id="پهن",
        note="the reading should be pahn, not pen",
        context={},
    )
    session.commit()
    assert [row.target_id for row in feedback.owned_by(session, "karbon")] == ["پهن"]
    assert feedback.owned_by(session, "murfulu") == []


def test_owner_follows_the_target_type():
    assert owner_for("lexicon_entry") == "karbon"
    assert owner_for("stem_derivation") == "karbon"
    assert owner_for("derivation") == "murfulu"
    assert owner_for("app") == "murfulu"


def test_a_graded_verdict_on_a_bug_is_refused(session: Session, expert: User):
    session.add(
        ExpertFeedback(
            author_id=expert.id,
            category="bug",
            target_type="app",
            verdict="good",
            context={},
            owner="murfulu",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_a_linguistic_note_without_a_verdict_is_refused(session: Session, expert: User):
    session.add(
        ExpertFeedback(
            author_id=expert.id,
            category="linguistic",
            target_type="derivation",
            target_id="Raftorow:karnam",
            context={},
            owner="murfulu",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_an_unknown_verdict_is_refused(session: Session, expert: User):
    session.add(
        ExpertFeedback(
            author_id=expert.id,
            category="linguistic",
            target_type="derivation",
            target_id="X",
            verdict="excellent",
            context={},
            owner="murfulu",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_the_rule_pack_loads_into_the_tables(session: Session):
    loaded = rulepack.loaded()
    report = rulesync.sync(session, loaded)
    session.commit()

    assert report.rules_written == len(loaded.rules)
    assert report.glides_written == len(loaded.glides)
    assert report.unknown_ids == []

    stored = session.execute(text("SELECT COUNT(*) FROM rules")).scalar_one()
    assert stored == len(loaded.rules)


def test_loading_twice_updates_rather_than_duplicates(session: Session):
    loaded = rulepack.loaded()
    rulesync.sync(session, loaded)
    rulesync.sync(session, loaded)
    session.commit()
    stored = session.execute(text("SELECT COUNT(*) FROM rules")).scalar_one()
    assert stored == len(loaded.rules)


def test_a_loaded_rule_keeps_what_the_yaml_said(session: Session):
    loaded = rulepack.loaded()
    rulesync.sync(session, loaded)
    session.commit()

    original = next(rule for rule in loaded.rules if rule.id == "V-010")
    row = session.execute(
        text(
            "SELECT family, kind, affix, affix_fa, examples, explanation_fa "
            "FROM rules WHERE id = 'V-010'"
        )
    ).one()
    assert row.family == "V"
    assert row.kind == original.kind
    assert row.affix == original.affix
    assert row.affix_fa == original.affix_fa
    assert row.explanation_fa == original.explanation_fa


def test_an_id_the_pack_no_longer_holds_is_reported_not_deleted(session: Session):
    loaded = rulepack.loaded()
    rulesync.sync(session, loaded)
    session.execute(
        text(
            "INSERT INTO rules (id, family, kind, source, input_types, "
            "output_types, affix_variants, semantic_tags, examples, slots, "
            "exceptions, needs_expert_check, active, rule_pack_version) "
            "VALUES ('V-999', 'V', 'suffix', '{}', '[]', '[]', '[]', '[]', "
            "'[]', '[]', '[]', 0, 1, 'made-up')"
        )
    )
    report = rulesync.sync(session, loaded)
    assert report.unknown_ids == ["V-999"]
    still_there = session.execute(
        text("SELECT COUNT(*) FROM rules WHERE id = 'V-999'")
    ).scalar_one()
    assert still_there == 1


def test_a_linguistic_verdict_is_never_about_the_application(session: Session):
    """*Is this app good, possible or wrong* is not a question.

    docs/REVIEW.md's own table maps the app to a bug report, and the schema
    had disagreed with it since it was written. Found by using the widget.
    """
    expert = User(username="expert-app")
    session.add(expert)
    session.flush()
    with pytest.raises(feedback.FeedbackRefusedError):
        feedback.record(
            session,
            author=expert,
            category="linguistic",
            target_type="app",
            verdict="wrong",
            note="بد است",
        )
