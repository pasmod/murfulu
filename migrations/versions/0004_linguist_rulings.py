"""Questions for the linguist, and the rulings that answer them.

The questions lived in ``docs/FOR_THE_LINGUIST.md`` and were answered in one
conversation at the end of a session. The store becomes the record and the
document becomes an export of it — the project lead's decision, 2026-08-15 —
because the file is English Markdown in a repository and he works in Persian.

**No new role.** A third one was tried on 2026-08-15, splitting *ruling* from
*grading* on the argument that a verdict is evidence and a ruling is authority.
True, and not worth a concept: in practice the expert is the linguist, so
settling a question is an expert's right like the other two. Taken out again on
2026-08-16 before anything was committed, which is why this migration does not
touch ``users``.

The allowed values are written out rather than imported: a migration is a
snapshot of the schema as it was, and importing the model would let a later
edit rewrite what this migration did.

Revision: 0004
Revises: 0003
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ORIGINS = ("app", "document")
_STATES = ("answered", "blocked", "open", "withdrawn")


def _one_of(column: str, allowed: tuple[str, ...]) -> str:
    listed = ", ".join(f"'{value}'" for value in sorted(allowed))
    return f"{column} IN ({listed})"


def upgrade() -> None:
    """Add the two tables."""
    op.create_table(
        "linguist_questions",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            autoincrement=True,
            nullable=False,
        ),
        # L13, S11, Q2 — the handle the documents and the git history already
        # use. Unique, or every past reference to it becomes ambiguous.
        sa.Column("reference", sa.String(length=16), nullable=False),
        # What he reads. He works in Persian.
        sa.Column("question_fa", sa.Text(), nullable=False),
        sa.Column("question_en", sa.Text(), nullable=True),
        sa.Column(
            "context",
            sa.JSON().with_variant(sa.dialects.postgresql.JSONB, "postgresql"),
            nullable=True,
        ),
        sa.Column("origin", sa.String(length=16), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("blocks_work", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(_one_of("origin", _ORIGINS), name="origin"),
        sa.CheckConstraint(_one_of("state", _STATES), name="state"),
        sa.CheckConstraint("length(trim(question_fa)) > 0", name="a_question_is_asked"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference"),
    )

    op.create_table(
        "linguist_rulings",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.BigInteger().with_variant(sa.Integer, "sqlite"),
            nullable=False,
        ),
        sa.Column("author_id", sa.Integer(), nullable=False),
        # His own words, in his own language. Never translated on the way in.
        sa.Column("ruling_fa", sa.Text(), nullable=False),
        sa.Column("ruling_en", sa.Text(), nullable=True),
        sa.Column(
            "affects",
            sa.JSON().with_variant(sa.dialects.postgresql.JSONB, "postgresql"),
            nullable=True,
        ),
        sa.Column("supersedes_earlier", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(ruling_fa)) > 0", name="a_ruling_says_something"
        ),
        # RESTRICT on both: an account is disabled rather than deleted so that
        # a ruling keeps pointing at whoever gave it, and a question with a
        # ruling on it cannot vanish underneath it.
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["question_id"], ["linguist_questions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_linguist_rulings_question_id", "linguist_rulings", ["question_id"]
    )

    # A ruling is work no job can recreate — the same argument the expert
    # feedback table makes, and the same protection. A later ruling that
    # reverses an earlier one is a new row saying so, never an edit.
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION linguist_rulings_are_append_only()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION
                    'linguist_rulings is append-only: rule again instead';
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER linguist_rulings_append_only
            BEFORE UPDATE OR DELETE ON linguist_rulings
            FOR EACH ROW EXECUTE FUNCTION linguist_rulings_are_append_only();
            """
        )


def downgrade() -> None:
    """Drop both tables."""
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS linguist_rulings_append_only ON linguist_rulings"
        )
        op.execute("DROP FUNCTION IF EXISTS linguist_rulings_are_append_only()")

    op.drop_index("ix_linguist_rulings_question_id", table_name="linguist_rulings")
    op.drop_table("linguist_rulings")
    op.drop_table("linguist_questions")
