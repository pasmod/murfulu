"""Asking the linguist a question, and recording what he rules.

The rules that make a ruling worth having live here rather than in the route,
so they hold however one arrives — from the API, a script or a test.

**Anyone behind the password wall may do this**, as of 2026-08-17. It used
to need the expert role, and there are no roles now — the site password is
the whole of the authentication. See :mod:`murfulu.db.site` for what that
gives up.

**A ruling is never edited.** A later one that reverses it is a new row saying
so, and on Postgres the migration installs a trigger that refuses every UPDATE
and DELETE — the same protection the expert feedback table has, for the same
reason: this is work no job can recreate.

**A question is answered in Persian.** He works in Persian, and translating an
answer on the way in would make our reading of it the record instead of his.

**And carried in Behnevis beside it**, because that is the form the project
holds and the examples inside a question are already in it.

**A question may offer options**, as of 2026-10-18 (see ``CHOICES_KEY``). A
ruling then chooses one, writes free text, or both — and is refused only when
it does neither. Whatever was chosen, ``ruling_fa`` is never empty: an option
chosen with nothing written is recorded in that option's own Persian.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from murfulu.db.models.people import User
from murfulu.db.models.rulings import (
    CHOICES_KEY,
    LinguistQuestion,
    LinguistQuestionFile,
    LinguistRuling,
)

#: What a choice id may look like: short, ASCII, and safe in a URL or a log.
CHOICE_ID = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


class RulingRefusedError(PermissionError):
    """Raised when the account may not rule, or the ruling says nothing."""


class UnknownQuestionError(KeyError):
    """Raised for a question the store does not hold."""


def ask(
    session: Session,
    *,
    reference: str,
    question_fa: str,
    question_latin: str | None = None,
    question_en: str | None = None,
    context: Any = None,
    origin: str = "app",
    blocks_work: bool = False,
) -> LinguistQuestion:
    """Record a question. Returns the stored row.

    The reference is the handle the documents and the git history already use
    — L13, S11 — so a question can be followed between them.
    """
    if not question_fa.strip():
        raise RulingRefusedError("a question has to be asked in Persian")

    row = LinguistQuestion(
        reference=reference,
        question_fa=question_fa,
        question_latin=question_latin,
        question_en=question_en,
        context=context,
        origin=origin,
        state="blocked" if blocks_work else "open",
        blocks_work=blocks_work,
    )
    session.add(row)
    session.flush()
    return row


def check_choices(choices: Any) -> list[dict[str, Any]]:
    """The options for a question, checked, in the shape the store keeps.

    Refuses what would make an answer ambiguous: two options under one id, an
    id a ruling could not safely carry, or an option with no Persian.
    """
    if not isinstance(choices, list):
        raise RulingRefusedError("choices must be a list")
    seen: set[str] = set()
    checked: list[dict[str, Any]] = []
    for one in choices:
        if not isinstance(one, dict):
            raise RulingRefusedError("each choice must be a mapping")
        choice_id = str(one.get("id") or "")
        text_fa = str(one.get("text_fa") or "").strip()
        if not CHOICE_ID.match(choice_id):
            raise RulingRefusedError(f"choice id {choice_id!r} is not a short ASCII id")
        if choice_id in seen:
            raise RulingRefusedError(f"choice id {choice_id!r} is given twice")
        if not text_fa:
            raise RulingRefusedError(f"choice {choice_id!r} says nothing in Persian")
        seen.add(choice_id)
        checked.append(
            {
                "id": choice_id,
                "text_fa": text_fa,
                "suggested": bool(one.get("suggested", False)),
                "settles": bool(one.get("settles", True)),
            }
        )
    return checked


def choices_of(question: LinguistQuestion) -> list[dict[str, Any]]:
    """The options a question offers, or an empty list for a free-text one."""
    context = question.context
    if not isinstance(context, dict):
        return []
    found = context.get(CHOICES_KEY)
    return list(found) if isinstance(found, list) else []


def rule_on(
    session: Session,
    *,
    author: User,
    question: LinguistQuestion,
    ruling_fa: str = "",
    choice_id: str | None = None,
    ruling_latin: str | None = None,
    ruling_en: str | None = None,
    affects: Any = None,
    supersedes_earlier: bool = False,
) -> LinguistRuling:
    """Append one ruling and mark its question answered.

    **An option, free text, or both — never neither.** With an option and no
    text, the option's Persian becomes ``ruling_fa``, so every ruling reads as
    a sentence on its own. With both, his words are ``ruling_fa`` and the option
    is kept beside them.

    **An option that does not settle** — «نمی‌دانم» — is recorded like any
    other, and the question goes back to waiting rather than to answered.
    """
    written = (ruling_fa or "").strip()
    if question.state == "withdrawn":
        raise RulingRefusedError(
            f"{question.reference} was withdrawn; it is not waiting on an answer"
        )

    chosen: dict[str, Any] | None = None
    if choice_id:
        chosen = next(
            (one for one in choices_of(question) if one.get("id") == choice_id), None
        )
        if chosen is None:
            raise RulingRefusedError(
                f"{question.reference} has no option {choice_id!r}"
            )
    if not written and chosen is None:
        raise RulingRefusedError("a ruling has to choose an option or say something")

    choice_fa = str(chosen["text_fa"]) if chosen is not None else None
    row = LinguistRuling(
        question_id=question.id,
        author_id=author.id,
        ruling_fa=written or choice_fa,
        choice_id=chosen["id"] if chosen is not None else None,
        choice_fa=choice_fa,
        ruling_latin=ruling_latin,
        ruling_en=ruling_en,
        affects=affects,
        supersedes_earlier=supersedes_earlier,
    )
    session.add(row)
    # The question's state is derived from having been answered, so it cannot
    # drift out of step with the rulings pointing at it.
    if chosen is not None and chosen.get("settles") is False:
        question.state = "blocked" if question.blocks_work else "open"
    else:
        question.state = "answered"
    session.flush()
    return row


def reword(
    session: Session,
    question: LinguistQuestion,
    *,
    question_fa: str,
    question_en: str | None = None,
    choices: Any = None,
    blocks_work: bool | None = None,
    extra: dict[str, Any] | None = None,
    on: date | None = None,
) -> bool:
    """Revise how a question that has **never been answered** is worded.

    Returns whether anything changed.

    **Only while nobody has answered it.** A question's wording is ours until
    he rules on it; after that it is what his answer was an answer *to*, and
    rewording it would quietly change the meaning of the record. So a question
    with any ruling is refused, and a new question has to be asked instead.

    **The old Persian is kept**, under ``context["reworded"]``, so what was
    once on screen can still be read. A withdrawn question that is reworded is
    waiting again.
    """
    if not question_fa.strip():
        raise RulingRefusedError("a question has to be asked in Persian")
    if rulings_on(session, question):
        raise RulingRefusedError(
            f"{question.reference} has been answered; ask a new question instead"
        )

    context = dict(question.context) if isinstance(question.context, dict) else {}
    before = (question.question_fa, question.question_en, question.blocks_work)
    before_context = dict(context)

    if choices is not None:
        context[CHOICES_KEY] = check_choices(choices)
    for key, value in (extra or {}).items():
        context[key] = value
    if question.question_fa != question_fa:
        earlier = list(context.get("reworded") or [])
        earlier.append(
            {
                "until": (on or date.today()).isoformat(),
                "question_fa": question.question_fa,
            }
        )
        context["reworded"] = earlier

    question.question_fa = question_fa
    if question_en is not None:
        question.question_en = question_en
    if blocks_work is not None:
        question.blocks_work = blocks_work
    context.pop("withdrawn_because", None)
    question.context = context or None
    waiting = "blocked" if question.blocks_work else "open"
    changed = (
        before != (question.question_fa, question.question_en, question.blocks_work)
        or before_context != context
        or question.state != waiting
    )
    question.state = waiting
    session.flush()
    return changed


def by_reference(session: Session, reference: str) -> LinguistQuestion:
    """One question by its handle, or :class:`UnknownQuestionError`."""
    found = session.scalars(
        select(LinguistQuestion).where(LinguistQuestion.reference == reference)
    ).one_or_none()
    if found is None:
        raise UnknownQuestionError(f"no question {reference!r}")
    return found


def questions(
    session: Session, *, state: str | None = None, blocking_only: bool = False
) -> list[LinguistQuestion]:
    """Every question, newest last, optionally narrowed.

    **Blocking questions come first when they are asked for**, because the
    whole point of the flag is that somebody is waiting on the answer.
    """
    query = select(LinguistQuestion)
    if state:
        query = query.where(LinguistQuestion.state == state)
    if blocking_only:
        query = query.where(LinguistQuestion.blocks_work.is_(True))
    found = list(session.scalars(query))
    # **Natural order, not alphabetical.** Sorted as text, L10 lands between L1
    # and L2 and the list reads as though it were shuffled.
    return sorted(found, key=lambda one: (not one.blocks_work, _handle(one.reference)))


#: A handle — ``L13``, and since 2026-10-18 ``L17b``: one question split into
#: parts keeps its number and adds a lower-case letter.
_HANDLE = re.compile(r"^(?P<letters>[A-Z]+)(?P<number>\d+)(?P<part>[a-z]*)$")


def _handle(reference: str) -> tuple[str, int, str]:
    """A handle split into letter, number and part, so L2 < L10 < L10b < L11."""
    found = _HANDLE.match(reference)
    if found:
        return (found["letters"], int(found["number"]), found["part"])
    digits = "".join(ch for ch in reference if ch.isdigit())
    letters = "".join(ch for ch in reference if not ch.isdigit())
    return (letters, int(digits) if digits else 0, "")


def rulings_on(session: Session, question: LinguistQuestion) -> list[LinguistRuling]:
    """Every ruling on one question, oldest first.

    The last is what stands; the ones before it are how it got there. A
    reversal is a fact about the grammar and hiding it would hide that anything
    ever changed.
    """
    return list(
        session.scalars(
            select(LinguistRuling)
            .where(LinguistRuling.question_id == question.id)
            .order_by(LinguistRuling.id)
        )
    )


def standing(session: Session, question: LinguistQuestion) -> LinguistRuling | None:
    """The ruling that currently stands, or ``None`` if it is unanswered."""
    found = rulings_on(session, question)
    return found[-1] if found else None


def withdraw(session: Session, question: LinguistQuestion, *, why: str) -> None:
    """Stop waiting on a question, without deleting it.

    *We asked and then stopped caring* is worth knowing — usually it means the
    answer arrived from a measurement instead, as question L's did.
    """
    question.state = "withdrawn"
    context = dict(question.context or {}) if isinstance(question.context, dict) else {}
    context["withdrawn_because"] = why
    question.context = context
    session.flush()


def attach(
    session: Session,
    *,
    question: LinguistQuestion,
    filename: str,
    content: bytes,
    description_fa: str,
    media_type: str = "application/octet-stream",
) -> LinguistQuestionFile:
    """Attach a file to a question, replacing one of the same name.

    Replacing rather than refusing, because the attachments are regenerated
    from measurements: a list of twenty-one words is rebuilt whenever the
    measurement is re-run, and the newer one is the one he should be reading.
    """
    if not description_fa.strip():
        raise RulingRefusedError("a file has to say what it is, in Persian")

    existing = session.scalars(
        select(LinguistQuestionFile).where(
            LinguistQuestionFile.question_id == question.id,
            LinguistQuestionFile.filename == filename,
        )
    ).one_or_none()
    if existing is not None:
        session.delete(existing)
        session.flush()

    row = LinguistQuestionFile(
        question_id=question.id,
        filename=filename,
        media_type=media_type,
        description_fa=description_fa,
        content=content,
        byte_size=len(content),
    )
    session.add(row)
    session.flush()
    return row


def files_for(
    session: Session, question: LinguistQuestion
) -> list[LinguistQuestionFile]:
    """Everything attached to one question, in the order it was attached."""
    return list(
        session.scalars(
            select(LinguistQuestionFile)
            .where(LinguistQuestionFile.question_id == question.id)
            .order_by(LinguistQuestionFile.id)
        )
    )


def file_named(
    session: Session, question: LinguistQuestion, filename: str
) -> LinguistQuestionFile:
    """One attachment by name, or :class:`UnknownQuestionError`.

    **By name and scoped to the question**, never by a path from the caller —
    the file is a row, so there is no directory to walk out of.
    """
    found = session.scalars(
        select(LinguistQuestionFile).where(
            LinguistQuestionFile.question_id == question.id,
            LinguistQuestionFile.filename == filename,
        )
    ).one_or_none()
    if found is None:
        raise UnknownQuestionError(
            f"{question.reference} has no attachment named {filename!r}"
        )
    return found
