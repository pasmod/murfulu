"""A ruling can choose one of the question's options.

**The questions screen became a multiple-choice form on 2026-10-18**, at the
project lead's request: each question offers a few options as full Persian
sentences, and a free-text box is always there beside them. The options live
in the question's ``context`` (see ``CHOICES_KEY`` in
``murfulu.db.models.rulings``); a ruling records which one was chosen.

Two columns rather than one, because the question's wording may still be
revised while it waits and the answer must not move with it: ``choice_id``
says which option, ``choice_fa`` keeps the sentence as it read when it was
chosen. Both nullable — a ruling in free text alone is still a ruling, and
every ruling before today has neither.

Adding columns is not an UPDATE, so the append-only trigger from 0004 is
untouched and still refuses every edit to a row once written.

Revision: 0009
Revises: 0008
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the chosen option, and its Persian as it read, to a ruling."""
    op.add_column(
        "linguist_rulings", sa.Column("choice_id", sa.String(32), nullable=True)
    )
    op.add_column("linguist_rulings", sa.Column("choice_fa", sa.Text(), nullable=True))


def downgrade() -> None:
    """Drop both columns."""
    op.drop_column("linguist_rulings", "choice_fa")
    op.drop_column("linguist_rulings", "choice_id")
