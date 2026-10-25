"""Expert feedback: append-only, and the evaluation set.

This table is the only place in the system holding work a human did that no
job can recreate. It is therefore append-only, and on Postgres that is a
trigger rather than a promise — the migration installs one that refuses every
UPDATE and DELETE. See ``docs/REVIEW.md``.

It doubles as the gold standard. There is nothing else to fit the scoring
weights against: karbon's reviewed entries validate the transcription of words
that already exist, and contain no generated word at all.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from murfulu.db.base import Base, Json, created_at_column, one_of

#: The form adapts to the category, because a graded verdict does not fit
#: "this button does nothing".
CATEGORIES = ("linguistic", "data", "bug")

#: What the feedback is about. The first four are ours; the last three are
#: karbon's data and the app itself.
TARGET_TYPES = (
    "derivation",
    "rule",
    "meaning",
    "statistic",
    "lexicon_entry",
    "stem_derivation",
    "app",
)

#: A graded verdict, so notes can be aggregated. Free text alone cannot be.
VERDICTS = ("good", "possible", "wrong", "unsure")

#: Who can act on it. Two target types are karbon's; we mount its lexicon
#: read-only and cannot fix them, so they are recorded and exported instead of
#: dropped.
OWNERS = ("murfulu", "karbon")

#: Which target types belong to karbon rather than to us.
KARBON_TARGETS = frozenset({"lexicon_entry", "stem_derivation"})


class ExpertFeedback(Base):
    """One piece of feedback. Never updated, never deleted."""

    __tablename__ = "expert_feedback"
    __table_args__ = (
        CheckConstraint(one_of("category", CATEGORIES), name="category"),
        CheckConstraint(one_of("target_type", TARGET_TYPES), name="target_type"),
        CheckConstraint(one_of("owner", OWNERS), name="owner"),
        CheckConstraint(
            f"verdict IS NULL OR {one_of('verdict', VERDICTS)}", name="verdict"
        ),
        # A verdict is what makes a linguistic judgement countable, and it
        # means nothing on a bug report. The two go together or neither does.
        CheckConstraint(
            "(category = 'linguistic') = (verdict IS NOT NULL)",
            name="linguistic_feedback_is_graded",
        ),
    )

    # SQLite only auto-numbers a column declared INTEGER, so the offline tests
    # would not exercise the insert at all if this stayed BIGINT everywhere.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    category: Mapped[str] = mapped_column(String(16), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    #: What was being judged: ``Raftorow:karnam``, ``V-010``. Null only for
    #: feedback on the app itself, which points at no record.
    target_id: Mapped[str | None] = mapped_column(Text, index=True)

    verdict: Mapped[str | None] = mapped_column(String(16))
    note: Mapped[str | None] = mapped_column(Text)

    #: Everything that was on screen, as data. This is the reusable half; the
    #: screenshot is a convenience.
    context: Mapped[dict[str, Any]] = mapped_column(Json, nullable=False)

    #: A path in a screenshots volume. **Always null, deliberately.**
    #:
    #: Settled 2026-08-17 as S4: no screenshot is captured and none will be.
    #: The structured `context` above is the reusable half and is captured in
    #: full; an image is not machine-readable, and it captures whatever else
    #: was on the reviewer's screen — which nobody consented to, no field of
    #: ours describes, and the deliberately unlicensed feedback export could
    #: not honestly carry.
    #:
    #: The column stays rather than being dropped, because dropping it is a
    #: migration that buys nothing and because a caller may one day supply a
    #: reference to an image it holds elsewhere. Nothing in this repository
    #: writes it, and `tools/export_feedback.py` says so in the manifest.
    screenshot_ref: Mapped[str | None] = mapped_column(Text)

    #: Derived from the target type, and stored so the karbon export is one
    #: query rather than a rule repeated at every call site.
    owner: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    #: Which corpus version the figures on screen came from. The verdict
    #: stays valid across rebuilds — it judged the form, not the count — but
    #: what was shown alongside it is only true for one version.
    corpus_version: Mapped[str | None] = mapped_column(String(64))

    created_at: Mapped[datetime] = created_at_column()


def owner_for(target_type: str) -> str:
    """Who can act on feedback about this kind of target."""
    return "karbon" if target_type in KARBON_TARGETS else "murfulu"
