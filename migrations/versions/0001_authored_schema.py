"""The authored schema: rules, people, feedback, corpus versions.

The allowed values are written out as literals rather than imported from the
models. A migration is a snapshot of the schema as it was, and importing the
current models would let a later edit silently rewrite what this migration
did.

Revision: 0001
Revises:
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: JSONB where the database has it, JSON everywhere else. Lists and captured
#: context are variable-shaped; see murfulu/db/base.py.
JSON = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")

#: Feedback is append-only, and on Postgres that is enforced rather than
#: promised. It is the only human work in the system that no job can recreate.
_APPEND_ONLY_FUNCTION = """
CREATE FUNCTION expert_feedback_refuse_change() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'expert_feedback is append-only; % is refused', TG_OP;
END;
$$
"""

_APPEND_ONLY_TRIGGER = """
CREATE TRIGGER expert_feedback_append_only
BEFORE UPDATE OR DELETE ON expert_feedback
FOR EACH ROW EXECUTE FUNCTION expert_feedback_refuse_change()
"""


def _timestamp(name: str) -> sa.Column[datetime]:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def _create_rules() -> None:
    op.create_table(
        "rules",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("family", sa.String(length=4), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("source", JSON, nullable=False),
        sa.Column("input_types", JSON, nullable=False),
        sa.Column("output_types", JSON, nullable=False),
        sa.Column("affix", sa.Text(), nullable=True),
        sa.Column("affix_fa", sa.Text(), nullable=True),
        sa.Column("affix_variants", JSON, nullable=False),
        sa.Column("semantic_tags", JSON, nullable=False),
        sa.Column("strength", sa.String(length=16), nullable=True),
        sa.Column("examples", JSON, nullable=False),
        sa.Column("label_fa", sa.Text(), nullable=True),
        sa.Column("explanation_fa", sa.Text(), nullable=True),
        sa.Column("pattern", sa.Text(), nullable=True),
        sa.Column("pattern_fa", sa.Text(), nullable=True),
        sa.Column("slots", JSON, nullable=False),
        sa.Column("exceptions", JSON, nullable=False),
        sa.Column("needs_expert_check", sa.Boolean(), nullable=False),
        sa.Column("notes", JSON, nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("rule_pack_version", sa.String(length=32), nullable=False),
        _timestamp("loaded_at"),
        sa.CheckConstraint(
            "kind IN ('infix', 'none', 'prefix', 'slot', 'stem', 'suffix', 'template')",
            name=op.f("ck_rules_kind"),
        ),
        sa.CheckConstraint(
            "strength IS NULL OR strength IN ('obligatory', 'occasional', 'typical')",
            name=op.f("ck_rules_strength"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rules")),
    )
    op.create_index(op.f("ix_rules_family"), "rules", ["family"], unique=False)

    op.create_table(
        "glide_rules",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("left_vowel", sa.String(length=8), nullable=False),
        sa.Column("right_vowel", sa.String(length=8), nullable=False),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.Column("examples", JSON, nullable=False),
        sa.Column("explanation_fa", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("retired_reason", sa.Text(), nullable=False),
        sa.Column("rule_pack_version", sa.String(length=32), nullable=False),
        _timestamp("loaded_at"),
        sa.CheckConstraint(
            "active OR retired_reason <> ''",
            name=op.f("ck_glide_rules_retired_glides_say_why"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_glide_rules")),
    )


def _create_corpus() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("licence", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        _timestamp("registered_at"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sources")),
    )
    op.create_table(
        "corpus_versions",
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("document_count", sa.Integer(), nullable=True),
        sa.Column("word_type_count", sa.Integer(), nullable=True),
        sa.Column("lexicon_snapshot_id", sa.Text(), nullable=True),
        sa.Column("rule_pack_version", sa.String(length=32), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        _timestamp("built_at"),
        sa.PrimaryKeyConstraint("version", name=op.f("pk_corpus_versions")),
    )
    op.create_table(
        "corpus_version_sources",
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("document_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_corpus_version_sources_source_id_sources"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["version"],
            ["corpus_versions.version"],
            name=op.f("fk_corpus_version_sources_version_corpus_versions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "version", "source_id", name=op.f("pk_corpus_version_sources")
        ),
    )


def _create_people_and_feedback() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        _timestamp("created_at"),
        sa.CheckConstraint("role IN ('expert', 'user')", name=op.f("ck_users_role")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )
    op.create_table(
        "expert_feedback",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=True),
        sa.Column("verdict", sa.String(length=16), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("context", JSON, nullable=False),
        sa.Column("screenshot_ref", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(length=16), nullable=False),
        sa.Column("corpus_version", sa.String(length=64), nullable=True),
        _timestamp("created_at"),
        sa.CheckConstraint(
            "(category = 'linguistic') = (verdict IS NOT NULL)",
            name=op.f("ck_expert_feedback_linguistic_feedback_is_graded"),
        ),
        sa.CheckConstraint(
            "category IN ('bug', 'data', 'linguistic')",
            name=op.f("ck_expert_feedback_category"),
        ),
        sa.CheckConstraint(
            "owner IN ('karbon', 'murfulu')",
            name=op.f("ck_expert_feedback_owner"),
        ),
        sa.CheckConstraint(
            "target_type IN ('app', 'derivation', 'lexicon_entry', 'meaning', "
            "'rule', 'statistic', 'stem_derivation')",
            name=op.f("ck_expert_feedback_target_type"),
        ),
        sa.CheckConstraint(
            "verdict IS NULL OR verdict IN ('good', 'possible', 'unsure', 'wrong')",
            name=op.f("ck_expert_feedback_verdict"),
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name=op.f("fk_expert_feedback_author_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expert_feedback")),
    )
    for column in ("owner", "target_id", "target_type"):
        op.create_index(
            op.f(f"ix_expert_feedback_{column}"),
            "expert_feedback",
            [column],
            unique=False,
        )


def upgrade() -> None:
    """Build the schema."""
    _create_rules()
    _create_corpus()
    _create_people_and_feedback()
    if op.get_bind().dialect.name == "postgresql":
        op.execute(_APPEND_ONLY_FUNCTION)
        op.execute(_APPEND_ONLY_TRIGGER)


def downgrade() -> None:
    """Take it down again, feedback last so nothing orphans its author."""
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS expert_feedback_append_only ON expert_feedback"
        )
        op.execute("DROP FUNCTION IF EXISTS expert_feedback_refuse_change()")
    for column in ("owner", "target_id", "target_type"):
        op.drop_index(op.f(f"ix_expert_feedback_{column}"), "expert_feedback")
    op.drop_table("expert_feedback")
    op.drop_table("users")
    op.drop_table("corpus_version_sources")
    op.drop_table("corpus_versions")
    op.drop_table("sources")
    op.drop_table("glide_rules")
    op.drop_index(op.f("ix_rules_family"), "rules")
    op.drop_table("rules")
