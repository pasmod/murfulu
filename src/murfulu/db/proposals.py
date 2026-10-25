"""Writing and reading proposed rule changes.

The rules that make a proposal worth having live here rather than in the route
that calls it, so they hold however one arrives — from the API, a script or a
test.

**Anyone behind the password wall may do this**, as of 2026-08-17. It used
to need the expert role, and there are no roles now — the site password is
the whole of the authentication. See :mod:`murfulu.db.site` for what that
gives up.

**A proposal is refused unless it changes something.** A row saying the affix
should stay exactly as it is produces no diff and no work, and a review queue
full of them is a review queue nobody reads.

**A proposal records what the rule said at the time.** Two experts proposing
different values for the same field is a disagreement worth seeing; a proposal
applied on top of a rule that has since changed is a silent revert. The export
can tell the two apart only if the old value was written down.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from murfulu.db.models.people import User
from murfulu.db.models.proposals import RuleProposal, RuleProposalDecision
from murfulu.rules.proposals import PROPOSABLE_FIELDS


class ProposalRefusedError(PermissionError):
    """Raised when the account may not propose, or the proposal is empty."""


class UnknownFieldError(KeyError):
    """Raised for a field that is not the linguist's to change."""


def record(
    session: Session,
    *,
    author: User,
    rule_id: str,
    field: str,
    proposed: Any,
    was: Any,
    reason: str,
    rule_pack_version: str,
) -> RuleProposal:
    """Append one proposed change and return the stored row."""
    if field not in PROPOSABLE_FIELDS:
        raise UnknownFieldError(
            f"{field!r} is not one of {', '.join(sorted(PROPOSABLE_FIELDS))}"
        )
    if not reason.strip():
        raise ProposalRefusedError("a proposal has to say why")
    if proposed == was:
        raise ProposalRefusedError(
            f"the proposed value for {field} is what {rule_id} already says"
        )

    row = RuleProposal(
        rule_id=rule_id,
        author_id=author.id,
        field=field,
        proposed=proposed,
        was=was,
        reason=reason.strip(),
        rule_pack_version=rule_pack_version,
    )
    session.add(row)
    session.flush()
    return row


def all_proposals(session: Session, rule_id: str | None = None) -> list[RuleProposal]:
    """Every proposal, oldest first, or every one about a single rule."""
    statement = select(RuleProposal).order_by(RuleProposal.id)
    if rule_id is not None:
        statement = statement.where(RuleProposal.rule_id == rule_id)
    return list(session.scalars(statement))


def as_dict(row: RuleProposal) -> dict[str, Any]:
    """One proposal, in the shape the export and the API both use."""
    return {
        "id": row.id,
        "rule_id": row.rule_id,
        "author_id": row.author_id,
        "field": row.field,
        "proposed": row.proposed,
        "was": row.was,
        "reason": row.reason,
        "rule_pack_version": row.rule_pack_version,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def decide(
    session: Session,
    *,
    proposal_id: int,
    decided_by: int,
    decision: str,
    reason: str,
    rule_pack_version: str,
) -> RuleProposalDecision:
    """Record what a reviewer did with one proposal.

    Appended, never stamped on the proposal — see
    :class:`murfulu.db.models.proposals.RuleProposalDecision`. Deciding twice
    is allowed: the rows say how the answer changed, and the latest is the one
    that counts.
    """
    row = RuleProposalDecision(
        proposal_id=proposal_id,
        decided_by=decided_by,
        decision=decision,
        reason=reason,
        rule_pack_version=rule_pack_version,
    )
    session.add(row)
    session.flush()
    return row


def latest_decisions(session: Session) -> dict[int, RuleProposalDecision]:
    """The decision that stands for each proposal, by proposal id.

    The **latest** row wins, so a proposal refused and later accepted is
    accepted. Proposals nobody has decided on are simply absent.
    """
    found: dict[int, RuleProposalDecision] = {}
    for row in session.scalars(
        select(RuleProposalDecision).order_by(RuleProposalDecision.id)
    ):
        found[row.proposal_id] = row
    return found


def undecided(session: Session, rule_id: str | None = None) -> list[RuleProposal]:
    """Proposals no reviewer has accepted or refused yet.

    **This is what the export applies.** Applying everything meant a refused
    proposal came back in the next export, was refused again, and the loop
    never converged — S5. A proposal that has been decided either way is
    already reflected in the pack, or was deliberately not, and applying it
    again would overrule the reviewer.
    """
    settled = latest_decisions(session)
    return [one for one in all_proposals(session, rule_id) if one.id not in settled]
