"""Files attached to a question, so it can be answered without leaving it.

A question that names the grammar document, or a list of twenty-one words, is
not answerable until the reader has that document and that list in front of
them. Sending them to a shared drive to find it is the thing this store was
built to stop.

**The bytes are held here rather than a path on disk.** A path is a promise
about a machine: it breaks when the file moves, when the container is rebuilt,
or when the drive is not mounted — and it breaks silently, at the moment
somebody is trying to answer. The files are small; the largest attached today
is under a megabyte.

Revision: 0006
Revises: 0005
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the attachments table."""
    op.create_table(
        "linguist_question_files",
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
        # What it is called when it lands in his downloads folder.
        sa.Column("filename", sa.String(length=200), nullable=False),
        sa.Column("media_type", sa.String(length=100), nullable=False),
        # **In Persian**, because it is read beside the question and the
        # question is in Persian. A file nobody can tell the purpose of is a
        # file nobody opens.
        sa.Column("description_fa", sa.Text(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("length(trim(filename)) > 0", name="a_file_is_named"),
        sa.CheckConstraint(
            "length(trim(description_fa)) > 0", name="a_file_says_what_it_is"
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["linguist_questions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id", "filename", name="one_name_per_question"),
    )
    op.create_index(
        "ix_linguist_question_files_question_id",
        "linguist_question_files",
        ["question_id"],
    )


def downgrade() -> None:
    """Drop it."""
    op.drop_index(
        "ix_linguist_question_files_question_id", table_name="linguist_question_files"
    )
    op.drop_table("linguist_question_files")
