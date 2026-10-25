"""What a reviewer did with a proposal, so a refusal stops coming back.

Accepting a proposal is committing the diff the export wrote; refusing it is
``git checkout rules/``, which leaves no trace anywhere. So the proposal stayed
in the table, the next export applied it again, and the reviewer refused it
again. The loop did not converge. That is open question S5.

**A second appended row, not a marker on the first.** Three ways out were open:
do nothing and read the export's own list, stamp the proposal `settled`, or
append a decision. The third is the shape this schema already uses twice — the
feedback table records a verdict as a row and `linguist_rulings` records a
reversal as a row saying it reverses — and it is the only one that keeps the
history whole. Stamping would have made `rule_proposals` the one authored table
edited in place, in a schema that protects the others with a trigger.

Revision: 0007
Revises: 0006
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the decisions table, append-only on Postgres."""
    op.create_table(
        "rule_proposal_decisions",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "proposal_id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=False,
        ),
        sa.Column("decided_by", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("rule_pack_version", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("decision IN ('accepted', 'refused')", name="decision"),
        # A refusal nobody explained teaches the proposer nothing, and the next
        # export cannot tell a considered no from a lost one.
        sa.CheckConstraint("length(trim(reason)) > 0", name="a_decision_says_why"),
        # RESTRICT on both, as everywhere else: an account is disabled rather
        # than deleted precisely so its judgements keep an author, and a
        # proposal is never deleted out from under its decision.
        sa.ForeignKeyConstraint(
            ["proposal_id"], ["rule_proposals.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rule_proposal_decisions_proposal_id",
        "rule_proposal_decisions",
        ["proposal_id"],
    )

    # Judgement no job can recreate, protected the way the rulings table is.
    # Changing an answer is a new row; the latest one is what the export reads,
    # so a refusal reversed later genuinely reopens the proposal.
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION rule_proposal_decisions_are_append_only()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION
                    'rule_proposal_decisions is append-only: decide again instead';
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER rule_proposal_decisions_append_only
            BEFORE UPDATE OR DELETE ON rule_proposal_decisions
            FOR EACH ROW EXECUTE FUNCTION rule_proposal_decisions_are_append_only();
            """
        )


def downgrade() -> None:
    """Drop the table and its trigger."""
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS rule_proposal_decisions_append_only "
            "ON rule_proposal_decisions"
        )
        op.execute("DROP FUNCTION IF EXISTS rule_proposal_decisions_are_append_only()")
    op.drop_index(
        "ix_rule_proposal_decisions_proposal_id",
        table_name="rule_proposal_decisions",
    )
    op.drop_table("rule_proposal_decisions")
