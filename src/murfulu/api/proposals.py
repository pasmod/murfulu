"""Proposing a change to the rule pack, and reading what has been proposed.

Thin, like every route: the rules about who may propose and what counts as a
proposal live in :mod:`murfulu.db.proposals`.

**Nothing here writes to the repository.** A proposal is stored, exported into
the YAML by `tools/export_proposals.py`, and reviewed as a git diff. A browser
with a write path into the rule pack would be a browser that can change the
grammar without anyone reading the change.

**The proposal carries what the rule says now**, taken from the loaded pack
rather than from the request: a caller that reported the wrong current value
could otherwise make a stale proposal look fresh.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from murfulu.api.auth import Expert, Store
from murfulu.db import proposals as store
from murfulu.rules.pack import Rule, RulePack
from murfulu.rules.pack import loaded as loaded_pack
from murfulu.rules.proposals import PROPOSABLE_FIELDS

router = APIRouter(tags=["proposals"])


class ProposalIn(BaseModel):
    """One proposed change to one field of one rule."""

    field: str = Field(description=f"one of {', '.join(sorted(PROPOSABLE_FIELDS))}")
    proposed: Any = Field(default=None, description="the new value, in its own shape")
    reason: str = Field(description="why, in Persian")


def _pack() -> RulePack:
    return loaded_pack()


def _rule(pack: RulePack, rule_id: str) -> Rule:
    try:
        found = pack.by_id(rule_id)
    except KeyError:
        raise HTTPException(404, f"no rule {rule_id!r} in the pack") from None
    if not isinstance(found, Rule):
        raise HTTPException(
            400, f"{rule_id!r} is a glide rule; those are not proposed against"
        )
    return found


def _held(rule: Rule, name: str) -> Any:
    """What the rule says now, in the shape the YAML stores it."""
    value = getattr(rule, name, None)
    return list(value) if isinstance(value, tuple) else value


@router.post("/rules/{rule_id}/proposals", status_code=201)
def propose(
    rule_id: str, given: ProposalIn, author: Expert, session: Store
) -> dict[str, Any]:
    """Propose one change. Expert only, and it has to change something."""
    if given.field not in PROPOSABLE_FIELDS:
        raise HTTPException(
            400,
            f"{given.field!r} is not one of {', '.join(sorted(PROPOSABLE_FIELDS))}",
        )
    pack = _pack()
    rule = _rule(pack, rule_id)
    try:
        row = store.record(
            session,
            author=author,
            rule_id=rule_id,
            field=given.field,
            proposed=given.proposed,
            was=_held(rule, given.field),
            reason=given.reason,
            rule_pack_version=pack.version,
        )
    except store.ProposalRefusedError as refused:
        raise HTTPException(403, str(refused)) from None
    except IntegrityError:
        # The rule is in the pack — it was just looked up — so the only way
        # the foreign key fails is that nothing has loaded the pack into the
        # store. That is an operational state and it should say so, not
        # answer with a page of SQL.
        session.rollback()
        raise HTTPException(
            503,
            "the rule pack has not been loaded into the authored store; run "
            "tools/sync_rules.py",
        ) from None
    return store.as_dict(row)


@router.get("/proposals")
def read_proposals(
    _who: Expert,
    session: Store,
    rule_id: str | None = Query(None, description="narrow to one rule"),
) -> dict[str, Any]:
    """Everything proposed, oldest first.

    Expert only: a proposal is unreviewed linguistic opinion, and showing it
    beside the pack to a reader who cannot tell them apart would make the
    grammar look less settled than it is.
    """
    rows = [store.as_dict(row) for row in store.all_proposals(session, rule_id)]
    return {"rule_id": rule_id, "returned": len(rows), "proposals": rows}
