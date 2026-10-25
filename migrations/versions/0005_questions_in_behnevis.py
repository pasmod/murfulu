"""A question and a ruling in Behnevis, beside the Persian.

**Murfulu operates on Behnevis, never on raw Arabic script**, and the linguist
is the authority on that script. A question about *šāhvār* against *šāhevār*
that can only be read in Persian is a question written in the one form the
project does not work in — and every example inside it is already Behnevis.

So three renderings, and each has a different job: the Persian is what he
reads, the Behnevis is the form the project actually holds, and the English is
our gloss for the repository. Nullable, all of them but the Persian: a question
is complete without a translation and marking one absent is better than
inventing it.

Revision: 0005
Revises: 0004
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the Behnevis rendering to a question and to a ruling."""
    op.add_column(
        "linguist_questions", sa.Column("question_latin", sa.Text(), nullable=True)
    )
    op.add_column(
        "linguist_rulings", sa.Column("ruling_latin", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Drop both columns."""
    op.drop_column("linguist_rulings", "ruling_latin")
    op.drop_column("linguist_questions", "question_latin")
