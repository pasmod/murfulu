"""Load the YAML rule pack into Postgres.

YAML in git stays the source of truth. This copies it in so the app can join a
rule to the feedback left on it, and so an expert's proposed change has
something to be a change *to* — the round trip in ``docs/ARCHITECTURE.md``.

Two things it deliberately does not do.

**It never deletes.** A rule id is permanent, and a retired rule keeps its row
with ``active`` false. An id in the database that the pack no longer mentions
is therefore a fault, not a tidy-up, so it is reported and left alone.

**It never invents.** The row is the loaded rule, field for field. If the pack
would not load, nothing is written.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from murfulu.db.models.rules import GlideRuleRow, RuleRow
from murfulu.rules.pack import Glide, Rule, RulePack
from murfulu.rules.pack import loaded as loaded_pack


@dataclass
class SyncReport:
    """What one load did."""

    rules_written: int = 0
    glides_written: int = 0
    rule_pack_version: str = ""

    #: Ids the database holds and the pack does not. Never deleted here; a
    #: permanent id that stopped existing is something to look at.
    unknown_ids: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        """One line, for a log or a command's output."""
        line = (
            f"rule pack {self.rule_pack_version}: "
            f"{self.rules_written} rules, {self.glides_written} glide rules"
        )
        if self.unknown_ids:
            line += f", {len(self.unknown_ids)} ids in the database are not in it"
        return line


def _rule_row(rule: Rule, version: str) -> RuleRow:
    return RuleRow(
        id=rule.id,
        family=rule.family,
        kind=rule.kind,
        source=dict(rule.source),
        input_types=list(rule.input_types),
        output_types=list(rule.output_types),
        affix=rule.affix,
        affix_fa=rule.affix_fa,
        affix_variants=list(rule.affix_variants),
        semantic_tags=list(rule.semantic_tags),
        strength=rule.strength,
        examples=list(rule.examples),
        label_fa=rule.label_fa,
        explanation_fa=rule.explanation_fa,
        pattern=rule.pattern,
        pattern_fa=rule.pattern_fa,
        slots=[dict(slot) for slot in rule.slots],
        exceptions=[dict(item) for item in rule.exceptions],
        needs_expert_check=rule.needs_expert_check,
        notes=list(rule.notes),
        active=rule.active,
        rule_pack_version=version,
    )


def _glide_row(glide: Glide, version: str) -> GlideRuleRow:
    return GlideRuleRow(
        id=glide.id,
        left_vowel=glide.left,
        right_vowel=glide.right,
        result=glide.result,
        examples=list(glide.examples),
        explanation_fa=glide.explanation_fa,
        active=glide.active,
        retired_reason=glide.retired_reason,
        rule_pack_version=version,
    )


def sync(session: Session, pack: RulePack | None = None) -> SyncReport:
    """Write the pack into the database and report what happened."""
    pack = pack or loaded_pack()
    report = SyncReport(rule_pack_version=pack.version)

    for rule in pack.rules:
        session.merge(_rule_row(rule, pack.version))
        report.rules_written += 1
    for glide in pack.glides:
        session.merge(_glide_row(glide, pack.version))
        report.glides_written += 1
    session.flush()

    known = {rule.id for rule in pack.rules}
    stored = set(session.scalars(select(RuleRow.id)))
    known_glides = {glide.id for glide in pack.glides}
    stored_glides = set(session.scalars(select(GlideRuleRow.id)))
    report.unknown_ids = sorted((stored - known) | (stored_glides - known_glides))
    return report
