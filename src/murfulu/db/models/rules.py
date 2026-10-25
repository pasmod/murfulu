"""The rule pack, as loaded from YAML.

YAML in git is the source of truth; these tables are its loaded form, so the
app can join a rule to the feedback left on it and so a proposed change has
something to be a change *to*. The loader is
:mod:`murfulu.db.rulesync`.

The columns mirror :class:`murfulu.rules.pack.Rule` and
:class:`murfulu.rules.pack.Glide` field for field. ``docs/ARCHITECTURE.md``
sketched a shorter list — singular ``input_type``, ``semantic_tag``,
``example`` — but a rule takes several input types, carries several tags and
gives several examples, and flattening them here would lose what the pack
already holds. The difference is recorded in that document.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from murfulu.db.base import Base, Json, created_at_column, one_of
from murfulu.rules.pack import KINDS, STRENGTHS

#: The strengths a rule may state. ``None`` is a value in the loader's set —
#: the source states a strength for 3 of 195 rules — and is the NULL case here.
NAMED_STRENGTHS = tuple(sorted(s for s in STRENGTHS if s is not None))

#: A rule id is short and permanent: ``V-010``, ``G-04``, ``S-01``.
_ID_LENGTH = 16


class RuleRow(Base):
    """One word-formation rule."""

    __tablename__ = "rules"
    __table_args__ = (
        CheckConstraint(one_of("kind", tuple(sorted(KINDS))), name="kind"),
        CheckConstraint(
            f"strength IS NULL OR {one_of('strength', NAMED_STRENGTHS)}",
            name="strength",
        ),
    )

    #: The permanent id. Appended, never inserted, never reused, so it is the
    #: natural key and no surrogate is wanted.
    id: Mapped[str] = mapped_column(String(_ID_LENGTH), primary_key=True)

    #: The letter before the number. Derivable from the id and stored anyway,
    #: so "every V rule" is one query rather than a scan with string work.
    family: Mapped[str] = mapped_column(String(4), nullable=False, index=True)

    kind: Mapped[str] = mapped_column(String(16), nullable=False)

    #: Which table and which row of the source grammar this came from.
    source: Mapped[dict[str, Any]] = mapped_column(Json, nullable=False)

    input_types: Mapped[list[str]] = mapped_column(Json, nullable=False)
    output_types: Mapped[list[str]] = mapped_column(Json, nullable=False)

    affix: Mapped[str | None] = mapped_column(Text)
    affix_fa: Mapped[str | None] = mapped_column(Text)
    affix_variants: Mapped[list[str]] = mapped_column(Json, nullable=False)

    semantic_tags: Mapped[list[str]] = mapped_column(Json, nullable=False)
    strength: Mapped[str | None] = mapped_column(String(16))
    examples: Mapped[list[str]] = mapped_column(Json, nullable=False)

    label_fa: Mapped[str | None] = mapped_column(Text)
    explanation_fa: Mapped[str | None] = mapped_column(Text)

    pattern: Mapped[str | None] = mapped_column(Text)
    pattern_fa: Mapped[str | None] = mapped_column(Text)
    slots: Mapped[list[dict[str, Any]]] = mapped_column(Json, nullable=False)
    exceptions: Mapped[list[dict[str, Any]]] = mapped_column(Json, nullable=False)

    needs_expert_check: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[list[str] | None] = mapped_column(Json)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    #: Which version of the pack this row was loaded from. A rule read back
    #: without it cannot be compared with the derivation that used it.
    rule_pack_version: Mapped[str] = mapped_column(String(32), nullable=False)
    loaded_at: Mapped[datetime] = created_at_column()


class GlideRuleRow(Base):
    """One vowel-meeting rule, applied wherever two parts join."""

    __tablename__ = "glide_rules"
    __table_args__ = (
        CheckConstraint(
            "active OR retired_reason <> ''",
            name="retired_glides_say_why",
        ),
    )

    id: Mapped[str] = mapped_column(String(_ID_LENGTH), primary_key=True)
    left_vowel: Mapped[str] = mapped_column(String(8), nullable=False)
    right_vowel: Mapped[str] = mapped_column(String(8), nullable=False)
    result: Mapped[str] = mapped_column(String(16), nullable=False)
    examples: Mapped[list[str]] = mapped_column(Json, nullable=False)
    explanation_fa: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    #: Required when the rule is not active, so a rule can never quietly stop
    #: applying — the same guarantee the YAML loader makes.
    retired_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")

    rule_pack_version: Mapped[str] = mapped_column(String(32), nullable=False)
    loaded_at: Mapped[datetime] = created_at_column()
