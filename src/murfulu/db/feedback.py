"""Writing and reading expert feedback.

One rule is enforced here rather than left to the route that calls it, so it
holds however the record arrives — from the API, from a script, from a test.

**There used to be a second, and it went on 2026-08-17.** Only an expert could
leave a linguistic verdict, because a verdict becomes the evaluation set the
scoring weights are fitted against. There is now one account and no roles: the
site password is the whole of the authentication, and everyone who passes it
may say anything. What that gives up is stated in :mod:`murfulu.db.site` and is
not small — with one identity, inter-rater agreement cannot be measured on
anything recorded from now on.

**A linguistic verdict is never about the application.** *Is this app good,
possible or wrong* is not a question; ``docs/REVIEW.md``'s own table maps the
app to a bug report. The two had disagreed since the schema was written and
nobody noticed until the widget was used.

**Feedback about karbon's data is recorded, not dropped.** We mount its
lexicon read-only and cannot fix a wrong reading. The record is marked
``owner: karbon`` and exported.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from murfulu.db.models.people import User
from murfulu.db.models.review import ExpertFeedback, owner_for


class FeedbackRefusedError(PermissionError):
    """Raised when the account may not leave this kind of feedback."""


def record(
    session: Session,
    *,
    author: User,
    category: str,
    target_type: str,
    target_id: str | None = None,
    verdict: str | None = None,
    note: str | None = None,
    context: dict[str, Any] | None = None,
    screenshot_ref: str | None = None,
    corpus_version: str | None = None,
) -> ExpertFeedback:
    """Append one piece of feedback and return the stored row."""
    if category == "linguistic" and target_type == "app":
        # *Is this app good, possible or wrong* is not a question, and
        # docs/REVIEW.md's own table maps the app to a bug report. The widget
        # refuses it too, but the rule belongs here so it holds however a
        # record arrives. Found by running the widget: two such rows exist
        # from before it, and the store is append-only, so they stay.
        raise FeedbackRefusedError(
            "a linguistic verdict is about a word, a rule or a meaning; "
            "feedback about the application itself is a bug report"
        )
    row = ExpertFeedback(
        author_id=author.id,
        category=category,
        target_type=target_type,
        target_id=target_id,
        verdict=verdict,
        note=note,
        context=context or {},
        screenshot_ref=screenshot_ref,
        owner=owner_for(target_type),
        corpus_version=corpus_version,
    )
    session.add(row)
    session.flush()
    return row


def for_target(
    session: Session, target_type: str, target_id: str
) -> list[ExpertFeedback]:
    """Everything ever said about one word, rule or figure, oldest first."""
    statement = (
        select(ExpertFeedback)
        .where(
            ExpertFeedback.target_type == target_type,
            ExpertFeedback.target_id == target_id,
        )
        .order_by(ExpertFeedback.id)
    )
    return list(session.scalars(statement))


def owned_by(session: Session, owner: str) -> list[ExpertFeedback]:
    """Everything belonging to one owner — the karbon export is ``"karbon"``."""
    statement = (
        select(ExpertFeedback)
        .where(ExpertFeedback.owner == owner)
        .order_by(ExpertFeedback.id)
    )
    return list(session.scalars(statement))
