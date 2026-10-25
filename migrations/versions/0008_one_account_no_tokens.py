"""One account, no tokens, no roles.

A reader needed two credentials to be useful: the site password to see anything
and an expert API token to answer anything. The project lead's call is that
this is one too many for a research app with one reviewer, so the password wall
in front of the whole site is now the whole of the authentication and everyone
behind it is the single account.

**`users` stays, with one row.** Feedback, rulings and proposals all point at
an author and are append-only precisely so a judgement keeps whoever made it.
Dropping the column would have discarded the authorship on records already
stored — nine feedback rows at the time of writing — and made a change of mind
unrecoverable.

**What it costs is not nothing.** `docs/REVIEW.md` treats the feedback set as a
research artefact whose export carries a per-author pseudonym so two reviewers'
verdicts on one word can be compared. With one identity there is only ever one
rater, so inter-rater agreement cannot be measured on anything recorded from
now on. Records made before this migration keep their own authors.

**Downgrade restores the shape and not the tokens.** The column comes back with
every account a `user`, and the table comes back empty. A revoked secret is
gone for good, which is the correct direction for a credential — nothing here
can hand anybody a working token, and that was true before the drop too, since
only hashes were ever stored.

Revision: 0008
Revises: 0007
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop the tokens, drop the role, keep the accounts."""
    op.drop_table("api_tokens")
    # The check constraint has to go first: it names the column. The bare name
    # here, not the expanded one — the metadata naming convention turns "role"
    # into "ck_users_role", and passing the expanded name asks for
    # "ck_users_ck_users_role", which does not exist.
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("role", type_="check")
        batch.drop_column("role")


def downgrade() -> None:
    """Put the shape back. Every account becomes a plain user."""
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column(
                "role",
                sa.String(length=16),
                nullable=False,
                server_default="user",
            )
        )
        batch.create_check_constraint("role", "role IN ('user', 'expert')")

    op.create_table(
        "api_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        # Only ever the hash. The database could not hand anybody a working
        # token before this migration either.
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
