"""Leaving feedback, and reading back what was left.

The store is :mod:`murfulu.db.feedback`; this turns it into HTTP and nothing
more. Who may say what is decided there, so the rule holds whether a record
arrives over HTTP, from a script or from a test.

**The caller proves who they are with an API token**, and the record is
written in that account's name. Nothing takes an author from the request body:
a feedback record naming the wrong author is worse than no record, because the
set is the evaluation set. See :mod:`murfulu.api.auth`.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from murfulu.api.auth import Caller, Store
from murfulu.db import feedback as store
from murfulu.db.models.review import (
    CATEGORIES,
    OWNERS,
    TARGET_TYPES,
    VERDICTS,
    ExpertFeedback,
)

router = APIRouter(tags=["feedback"])

#: How many records one read returns.
DEFAULT_SIZE = 50
MAX_SIZE = 500


class FeedbackIn(BaseModel):
    """One piece of feedback, as it arrives.

    There is no author field. Who left it comes from the token, never from
    the body.
    """

    category: str = Field(description=f"one of {', '.join(CATEGORIES)}")
    target_type: str = Field(description=f"one of {', '.join(TARGET_TYPES)}")
    target_id: str | None = Field(
        default=None, description="the word, rule or figure being judged"
    )
    verdict: str | None = Field(
        default=None, description=f"linguistic only: {', '.join(VERDICTS)}"
    )
    note: str | None = Field(default=None, description="free text, in Persian")
    context: dict[str, Any] = Field(
        default_factory=dict, description="what was on screen, as data"
    )
    screenshot_ref: str | None = None
    corpus_version: str | None = None


def _said(row: ExpertFeedback) -> dict[str, Any]:
    return {
        "id": row.id,
        "author_id": row.author_id,
        "category": row.category,
        "target_type": row.target_type,
        "target_id": row.target_id,
        "verdict": row.verdict,
        "note": row.note,
        "context": row.context,
        "screenshot_ref": row.screenshot_ref,
        "owner": row.owner,
        "corpus_version": row.corpus_version,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _one_of(value: str, allowed: tuple[str, ...], field: str) -> None:
    if value not in allowed:
        raise HTTPException(
            400, f"{field} {value!r} is not one of {', '.join(sorted(allowed))}"
        )


@router.post("/feedback", status_code=201)
def leave_feedback(given: FeedbackIn, author: Caller, session: Store) -> dict[str, Any]:
    """Append one piece of feedback.

    Append is the only operation. The record cannot be edited or withdrawn
    afterwards — the database refuses both — because this set is what the
    scoring weights will be fitted against.
    """
    _one_of(given.category, CATEGORIES, "category")
    _one_of(given.target_type, TARGET_TYPES, "target type")
    if given.verdict is not None:
        _one_of(given.verdict, VERDICTS, "verdict")
    if (given.category == "linguistic") != (given.verdict is not None):
        raise HTTPException(
            400,
            "a linguistic judgement carries a verdict and nothing else does; "
            f"got category {given.category!r} and verdict {given.verdict!r}",
        )

    try:
        row = store.record(
            session,
            author=author,
            category=given.category,
            target_type=given.target_type,
            target_id=given.target_id,
            verdict=given.verdict,
            note=given.note,
            context=given.context,
            screenshot_ref=given.screenshot_ref,
            corpus_version=given.corpus_version,
        )
    except store.FeedbackRefusedError as refused:
        raise HTTPException(403, str(refused)) from None
    return _said(row)


@router.get("/feedback")
def read_feedback(
    _who: Caller,
    session: Store,
    target_type: str | None = Query(None, description="narrow to one kind"),
    target_id: str | None = Query(None, description="narrow to one word or rule"),
    owner: str | None = Query(None, description=f"one of {', '.join(OWNERS)}"),
    size: int = Query(DEFAULT_SIZE, ge=1, le=MAX_SIZE),
) -> dict[str, Any]:
    """Everything said about a target, or everything one owner has to act on.

    The ``owner`` filter is how karbon's share is found: we mount its lexicon
    read-only, so a wrong reading is recorded here and exported, never fixed
    here.
    """
    if owner is not None:
        _one_of(owner, OWNERS, "owner")
    if target_type is not None:
        _one_of(target_type, TARGET_TYPES, "target type")

    statement = select(ExpertFeedback).order_by(ExpertFeedback.id)
    if target_type is not None:
        statement = statement.where(ExpertFeedback.target_type == target_type)
    if target_id is not None:
        statement = statement.where(ExpertFeedback.target_id == target_id)
    if owner is not None:
        statement = statement.where(ExpertFeedback.owner == owner)

    rows = [_said(row) for row in session.scalars(statement.limit(size))]
    return {
        "target_type": target_type,
        "target_id": target_id,
        "owner": owner,
        "returned": len(rows),
        "feedback": rows,
    }
