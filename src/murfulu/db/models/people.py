"""Accounts. Since 2026-08-17 there is exactly one, and it has no role.

**There used to be two roles**, because ``docs/REVIEW.md`` needed two: anyone
could report a bug, but a linguistic verdict becomes the evaluation set the
scoring weights are fitted against, so only an expert could leave one. A third
was tried for rulings and taken out again a day later, on the argument that in
practice the expert *is* the linguist.

**And now there are none**, the project lead's call: a reader needed the site
password to see anything and an expert token to answer anything, and that is
one credential too many for a research app with one reviewer. The password wall
in front of the whole site is the authentication; everything behind it is the
single account in :mod:`murfulu.db.site`.

**The table stays, with one row in it.** Feedback, rulings and proposals all
point at an author and are append-only precisely so a judgement keeps whoever
made it. Dropping the column would have discarded the authorship on records
already stored and made a change of mind unrecoverable. What it costs is real
and is written down in :mod:`murfulu.db.site`: with one identity, inter-rater
agreement cannot be measured.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from murfulu.db.base import Base, created_at_column


class User(Base):
    """One account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    #: How the account is addressed. Unique, and a handle rather than a
    #: person's name — the repository is public and ``docs/ENGINEERING.md``
    #: allows no personal names anywhere.
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    display_name: Mapped[str | None] = mapped_column(Text)

    #: An account is disabled, never deleted: its feedback is append-only and
    #: must keep pointing at whoever gave it.
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = created_at_column()
