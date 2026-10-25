"""Proposed changes to the rule pack.

The YAML in git is the source of truth and stays that way. An expert working
in the app cannot edit it — there is no write path from the browser to the
repository, and there should not be — so a change is **proposed**, stored
here, exported back into the YAML by a command, and reviewed as a git diff.
That is the round trip ``docs/ARCHITECTURE.md`` describes.

**Only what a linguist can judge may be proposed.** The closed set is
:data:`murfulu.rules.proposals.PROPOSABLE_FIELDS`, defined there because the
pack owns what its own fields are, and enforced here by a check constraint.

**A proposal records what the rule said when it was made.** A proposal written
against a rule that has since changed is a proposal about something else, and
the export has to be able to see that rather than apply it blindly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from murfulu.db.base import Base, Json, created_at_column, one_of
from murfulu.rules.proposals import PROPOSABLE_FIELDS

_ID_LENGTH = 16


class RuleProposal(Base):
    """One proposed change to one field of one rule."""

    __tablename__ = "rule_proposals"
    __table_args__ = (
        CheckConstraint(one_of("field", PROPOSABLE_FIELDS), name="field"),
        # A change nobody explained cannot be reviewed. The reason is the
        # whole content of the review, so it is required rather than nullable.
        CheckConstraint("length(trim(reason)) > 0", name="a_proposal_says_why"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    #: The permanent id of the rule. A proposal against a rule the pack does
    #: not have is refused, so this always points at something.
    rule_id: Mapped[str] = mapped_column(
        String(_ID_LENGTH), ForeignKey("rules.id", ondelete="RESTRICT"), index=True
    )

    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    field: Mapped[str] = mapped_column(String(32), nullable=False)

    #: The proposed value, in the shape the field has: a string, a list, a
    #: boolean, or null. Stored as JSON so the shape survives the round trip.
    proposed: Mapped[Any] = mapped_column(Json, nullable=True)

    #: What the field held when the proposal was made. The export compares
    #: this with the pack: if they differ, the rule moved underneath the
    #: proposal and applying it would silently undo somebody else's work.
    was: Mapped[Any] = mapped_column(Json, nullable=True)

    #: In Persian, like every other authored text. Required.
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    #: Which version of the pack the proposal was written against.
    rule_pack_version: Mapped[str] = mapped_column(String(32), nullable=False)

    created_at: Mapped[datetime] = created_at_column()


#: What a reviewer did with a proposal. **Refusing is as much a decision as
#: accepting** and has to be recorded as one — that is the whole of S5.
DECISIONS = ("accepted", "refused")


class RuleProposalDecision(Base):
    """What a reviewer did with one proposal, appended rather than stamped.

    **The problem this closes.** Accepting a proposal is committing the diff
    the export wrote and refusing it is ``git checkout rules/`` — which leaves
    no trace anywhere. So the proposal was still in the table, the next export
    applied it again, and the reviewer refused it again. The loop did not
    converge. S5.

    **A second row, not a marker on the first.** Three ways out were open: do
    nothing and read the export's list, stamp the proposal `settled`, or append
    a decision. The third is the shape this codebase already uses twice — the
    feedback table records a verdict as a row, and `linguist_rulings` records a
    reversal as a row saying it reverses — and it is the only one that keeps
    the history whole. Stamping would have made this the one authored table
    that is edited in place, in a project that protects the others with a
    trigger.

    **Refusing twice is allowed and is not a mistake.** A proposal refused
    under one pack version can be made again under another, and the reviewer
    may reach a different answer; the rows say so in order. What the export
    reads is the *latest* decision, so a later accept genuinely reopens one.

    **Append-only**, like the rulings table and for the same reason: this is
    judgement nobody can recreate, and a review that quietly changed would make
    the record worth less than no record.
    """

    __tablename__ = "rule_proposal_decisions"
    __table_args__ = (
        CheckConstraint(one_of("decision", DECISIONS), name="decision"),
        # A refusal nobody explained teaches the proposer nothing, and the next
        # export cannot tell a considered no from a lost one.
        CheckConstraint("length(trim(reason)) > 0", name="a_decision_says_why"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    proposal_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("rule_proposals.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    #: Who decided. RESTRICT for the same reason every other authored row uses
    #: it: an account is disabled rather than deleted so its work keeps an
    #: author.
    decided_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    decision: Mapped[str] = mapped_column(String(16), nullable=False)

    #: Why, in Persian like every other authored text here.
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    #: Which pack version the decision was taken against. A refusal is about
    #: the pack as it stood, and the same proposal may deserve a different
    #: answer later.
    rule_pack_version: Mapped[str] = mapped_column(String(32), nullable=False)

    created_at: Mapped[datetime] = created_at_column()
