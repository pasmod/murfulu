"""Proposed changes to the rule pack.

An expert cannot write to the repository from a browser and should not be able
to. A change is proposed here, exported into the YAML by a command, and
reviewed as a git diff.

The allowed field names are written out rather than imported: a migration is a
snapshot of the schema as it was, and importing the model would let a later
edit rewrite what this migration did.

Revision: 0003
Revises: 0002
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_FIELDS = (
    "active",
    "affix",
    "affix_fa",
    "examples",
    "explanation_fa",
    "label_fa",
    "needs_expert_check",
    "notes",
    "semantic_tags",
    "strength",
)


def upgrade() -> None:
    """Add the proposals table."""
    allowed = ", ".join(f"'{name}'" for name in _FIELDS)
    op.create_table(
        "rule_proposals",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("rule_id", sa.String(length=16), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("field", sa.String(length=32), nullable=False),
        sa.Column("proposed", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("was", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("rule_pack_version", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"field IN ({allowed})", name=op.f("ck_rule_proposals_field")
        ),
        sa.CheckConstraint(
            "length(trim(reason)) > 0",
            name=op.f("ck_rule_proposals_a_proposal_says_why"),
        ),
        sa.ForeignKeyConstraint(
            ["rule_id"],
            ["rules.id"],
            name=op.f("fk_rule_proposals_rule_id_rules"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name=op.f("fk_rule_proposals_author_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rule_proposals")),
    )
    op.create_index(
        op.f("ix_rule_proposals_rule_id"), "rule_proposals", ["rule_id"], unique=False
    )


def downgrade() -> None:
    """Take it away again."""
    op.drop_index(op.f("ix_rule_proposals_rule_id"), table_name="rule_proposals")
    op.drop_table("rule_proposals")
