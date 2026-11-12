"""A question can be set aside: deferred, not asked now, not withdrawn.

**L26 waits for the linguist's corrected rules** (2026-11-12): he is revising
them, and the answer depends on the new ones. Withdrawn would say we stopped
caring, and it is the most consequential question there is; left waiting, it
would sit at the top of his list as though we needed it this week. So a fifth
state, ``deferred``: shown under its own heading with the reason, never as
waiting, and back to waiting the moment its wording is loaded without a
deferral (``db.rulings.reword``).

Only the check constraint changes; the reason lives in the question's
``context`` as ``deferred_because``, like ``withdrawn_because``.

Revision: 0010
Revises: 0009
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BEFORE = ("answered", "blocked", "open", "withdrawn")
_AFTER = ("answered", "blocked", "deferred", "open", "withdrawn")


def _one_of(column: str, allowed: tuple[str, ...]) -> str:
    listed = ", ".join(f"'{value}'" for value in sorted(allowed))
    return f"{column} IN ({listed})"


def upgrade() -> None:
    """Allow ``deferred`` as a question's state."""
    with op.batch_alter_table("linguist_questions") as batch:
        batch.drop_constraint(op.f("ck_linguist_questions_state"), type_="check")
        batch.create_check_constraint("state", _one_of("state", _AFTER))


def downgrade() -> None:
    """Back to four states. Refused while any question is deferred."""
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM linguist_questions WHERE state = "
        "'deferred') THEN RAISE EXCEPTION 'a question is deferred; ask or "
        "withdraw it first'; END IF; END $$"
    )
    with op.batch_alter_table("linguist_questions") as batch:
        batch.drop_constraint(op.f("ck_linguist_questions_state"), type_="check")
        batch.create_check_constraint("state", _one_of("state", _BEFORE))
