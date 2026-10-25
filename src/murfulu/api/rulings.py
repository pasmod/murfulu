"""The questions waiting on the linguist, and the rulings that settle them.

Thin, like every route: what counts as a ruling and who may give one live in
:mod:`murfulu.db.rulings`.

**This is where the answer is created, so this is the record.** The project
lead's decision, 2026-08-15. `docs/FOR_THE_LINGUIST.md` becomes an export of
this store rather than the place answers are written down — which is the
opposite of `/proposals`, where the YAML in git stays the source of truth. The
difference is what each holds: a proposal is a change to something that already
exists, and a ruling is new information that exists nowhere until it is given.

**Reading is open; ruling is not.** Anyone signed in can see what is being
asked, because the questions are the project's own record of what it does not
know. Only an expert can answer — the same check that guards a graded verdict,
and the expert is the linguist.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from murfulu.api.auth import Caller, Expert, Store
from murfulu.db import rulings as store
from murfulu.db.models.rulings import STATES, LinguistQuestion

router = APIRouter(tags=["rulings"])


class RulingIn(BaseModel):
    """One answer to one question: an option, free text, or both.

    Refused only when it is neither — see :func:`murfulu.db.rulings.rule_on`.
    """

    ruling_fa: str = Field(
        default="",
        description=(
            "the ruling, in Persian. His words are the record. May be empty "
            "when an option is chosen; the option's Persian is stored instead."
        ),
    )
    choice_id: str | None = Field(
        default=None, description="the id of the option chosen, if any"
    )
    ruling_latin: str | None = Field(
        default=None, description="the same ruling in Behnevis, if given"
    )
    ruling_en: str | None = Field(
        default=None, description="our English rendering, written afterwards"
    )
    affects: Any = Field(
        default=None, description="what changes as a result — rule ids, a decision key"
    )
    supersedes_earlier: bool = Field(
        default=False, description="true when this reverses the previous ruling"
    )


def _question(session: Any, reference: str) -> LinguistQuestion:
    try:
        return store.by_reference(session, reference)
    except store.UnknownQuestionError:
        raise HTTPException(404, f"no question {reference!r}") from None


def _ruling(row: Any) -> dict[str, Any]:
    return {
        "ruling_fa": row.ruling_fa,
        # The option chosen and its Persian as it read then. When he wrote
        # nothing of his own, ruling_fa is that same sentence.
        "choice_id": row.choice_id,
        "choice_fa": row.choice_fa,
        "ruling_latin": row.ruling_latin,
        "ruling_en": row.ruling_en,
        "affects": row.affects,
        "supersedes_earlier": row.supersedes_earlier,
        "ruled_at": row.created_at.isoformat() if row.created_at else None,
    }


def _question_body(session: Any, row: LinguistQuestion) -> dict[str, Any]:
    standing = store.standing(session, row)
    return {
        "reference": row.reference,
        "question_fa": row.question_fa,
        "question_latin": row.question_latin,
        "question_en": row.question_en,
        "context": row.context,
        # The options, lifted out of the context so the form need not know
        # where they are kept. Empty for a question answered in free text.
        "choices": store.choices_of(row),
        "state": row.state,
        "blocks_work": row.blocks_work,
        "origin": row.origin,
        "asked_at": row.created_at.isoformat() if row.created_at else None,
        # The ruling that stands, and how many there have been. A second ruling
        # means the answer changed, which is worth seeing without asking again.
        "ruling": _ruling(standing) if standing else None,
        "rulings": len(store.rulings_on(session, row)),
        # The evidence as files, so a question that names a document can be
        # answered without going to find it.
        "files": [
            {
                "filename": one.filename,
                "description_fa": one.description_fa,
                "byte_size": one.byte_size,
                "href": f"/questions/{row.reference}/files/{one.filename}",
            }
            for one in store.files_for(session, row)
        ],
    }


@router.get("/questions")
def questions(
    session: Store,
    who: Caller,
    state: str | None = Query(
        None, description=f"narrow to one of {', '.join(sorted(STATES))}"
    ),
    blocking: bool = Query(False, description="only the questions stopping work"),
) -> dict[str, Any]:
    """Everything waiting on the linguist, blocking questions first.

    Open to anyone signed in: what the project does not yet know is not a
    secret, and a reviewer who can see the open questions is a reviewer who
    will not report one of them as a bug. ``answering_as`` names the caller
    when the caller is the one who can answer.
    """
    if state and state not in STATES:
        raise HTTPException(400, f"state must be one of {', '.join(sorted(STATES))}")

    found = store.questions(session, state=state, blocking_only=blocking)
    return {
        "count": len(found),
        # Everyone behind the wall may answer, so this is never null now.
        "answering_as": who.username,
        "questions": [_question_body(session, row) for row in found],
    }


@router.get("/questions/{reference}")
def question(reference: str, session: Store, who: Caller) -> dict[str, Any]:
    """One question, with every ruling ever given on it.

    Every one, not only the one that stands: a reversal is a fact about the
    grammar, and a reader who cannot see it cannot tell a settled answer from a
    changed mind.
    """
    row = _question(session, reference)
    body = _question_body(session, row)
    body["history"] = [_ruling(one) for one in store.rulings_on(session, row)]
    return body


@router.post("/questions/{reference}/ruling", status_code=201)
def rule(
    reference: str, given: RulingIn, session: Store, who: Expert
) -> dict[str, Any]:
    """Settle a question. Expert only."""
    row = _question(session, reference)
    try:
        made = store.rule_on(
            session,
            author=who,
            question=row,
            ruling_fa=given.ruling_fa,
            choice_id=given.choice_id,
            ruling_latin=given.ruling_latin,
            ruling_en=given.ruling_en,
            affects=given.affects,
            supersedes_earlier=given.supersedes_earlier,
        )
    except store.RulingRefusedError as refused:
        raise HTTPException(400, str(refused)) from None

    session.commit()
    return {"reference": row.reference, "state": row.state, "ruling": _ruling(made)}


@router.get("/questions/{reference}/files/{filename}")
def attachment(reference: str, filename: str, session: Store, who: Caller) -> Response:
    """Download one of a question's attachments.

    Signed in, like the question itself. **Scoped to the question and looked up
    by name**, so there is no path here and nothing to walk out of.
    """
    row = _question(session, reference)
    try:
        found = store.file_named(session, row, filename)
    except store.UnknownQuestionError as absent:
        raise HTTPException(404, str(absent)) from None

    # **The filename is Persian and an HTTP header is latin-1.** Putting it in
    # raw is a 500 at download time, which is the worst place to find it — so
    # the name goes in percent-encoded under RFC 5987's `filename*`, with an
    # ASCII `filename` beside it for anything that does not read that.
    ascii_name = found.filename.encode("ascii", "ignore").decode() or "attachment"
    encoded = quote(found.filename, safe="")
    return Response(
        content=found.content,
        media_type=found.media_type,
        headers={
            # attachment, so a .docx downloads rather than being handed to a
            # plugin, and the name is the one written when it was attached.
            "content-disposition": (
                f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}"
            ),
        },
    )
