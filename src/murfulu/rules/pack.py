"""Load the rule pack and refuse to load a broken one.

The pack is data a linguist edits, so a mistake in it is expected and must be
caught at load time with a message naming the rule. A rule that silently loads
half-formed is worse than one that fails: the engine will apply it and produce
words nobody can explain.

Every check here names the id and says what is wrong.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from murfulu.rules.types import is_word_class

#: Where the authored rule files live. Configuration, never a literal.
PATH_VARIABLE = "MURFULU_RULES_PATH"

#: One file per source table, so a rule traces back to the table it came from.
RULE_FILES = ("verb_stems", "nominals", "glides", "stem_rules")

#: Stem spellings, kept apart from the rules because they carry no rule id.
STEM_FORMS_FILE = "stem_forms.yaml"

#: The closed semantic tag set, with the gloss template each carries.
SEMANTIC_TAGS_FILE = "semantic_tags.yaml"

#: The shapes a rule can take. Anything else is a mistake.
KINDS = {"suffix", "prefix", "infix", "template", "none", "slot", "stem"}

#: What the source states about how reliably a rule applies.
STRENGTHS = {"obligatory", "typical", "occasional", None}

#: Slot constraints the source grammar uses in its compounding rows.
CONSTRAINTS = {"same_verb", "different_verb", "same_stem", "different_stem"}


class RulePackError(ValueError):
    """Raised when the pack does not load. The message names the rule."""


@dataclass(frozen=True)
class Rule:
    """One word-formation rule, loaded and checked."""

    id: str
    kind: str
    source: dict[str, Any]
    input_types: tuple[str, ...]
    output_types: tuple[str, ...]
    affix: str | None = None
    affix_fa: str | None = None
    affix_variants: tuple[str, ...] = ()
    semantic_tags: tuple[str, ...] = ()
    strength: str | None = None
    examples: tuple[str, ...] = ()
    label_fa: str | None = None
    explanation_fa: str | None = None
    pattern: str | None = None
    pattern_fa: str | None = None
    slots: tuple[dict[str, Any], ...] = ()
    exceptions: tuple[dict[str, Any], ...] = ()
    needs_expert_check: bool = False
    notes: tuple[str, ...] = ()
    active: bool = True
    #: Why a retired rule was retired. Required when ``active`` is false, so a
    #: rule can never quietly stop applying — the same guarantee :class:`Glide`
    #: has had since G-01, and which this class was missing. Ids are permanent
    #: and a retired rule is still served, so the reason is what tells a reader
    #: whether it was ruled on or merely switched off.
    retired_reason: str = ""
    #: The same reason in Persian. Empty where nobody has written it — the
    #: interface may not invent it, so an empty string means the screen shows
    #: the badge alone rather than a sentence somebody guessed. See S14.
    retired_reason_fa: str = ""

    @property
    def family(self) -> str:
        """The letter before the number: V, N, G or S."""
        return self.id.split("-")[0]


@dataclass(frozen=True)
class Glide:
    """One vowel-meeting rule, applied at every join."""

    id: str
    left: str
    right: str
    result: str
    examples: tuple[str, ...] = ()
    explanation_fa: str | None = None
    active: bool = True
    #: Why a retired rule was retired. Required when ``active`` is false, so a
    #: rule can never quietly stop applying.
    retired_reason: str = ""
    #: The same reason in Persian. Empty where nobody has written it — the
    #: interface may not invent it, so an empty string means the screen shows
    #: the badge alone rather than a sentence somebody guessed. See S14.
    retired_reason_fa: str = ""


@dataclass(frozen=True)
class StemForm:
    """How a stem is written alone versus how it behaves with anything after it.

    Not a joining rule. A stem written *row* is *rav* the moment something
    follows, vowel or consonant — see rules/decisions.yaml for the evidence.
    """

    written: str
    working: str
    reason: str = ""


@dataclass(frozen=True)
class SemanticTag:
    """One meaning tag, and the sentence a word carrying it is given.

    ``gloss_template_fa`` is None for all but one tag: writing them states what
    a generated word *means*, which is the linguist's to author, not the
    engine's to invent.
    """

    tag: str
    labels: tuple[str, ...]
    gloss_fa: str
    gloss_en: str
    gloss_template_fa: str | None = None
    gloss_template_en: str | None = None


@dataclass
class RulePack:
    """Everything the engine needs, loaded once."""

    rules: list[Rule] = field(default_factory=list)
    glides: list[Glide] = field(default_factory=list)
    stem_forms: list[StemForm] = field(default_factory=list)
    tags: dict[str, SemanticTag] = field(default_factory=dict)
    version: str = "0.0.0"

    def tag_for(self, label: str) -> SemanticTag | None:
        """The tag a rule's label refers to, or None if it is not declared."""
        return self.tags.get(label)

    def by_id(self, rule_id: str) -> Rule | Glide:
        """One rule by its permanent id."""
        items: list[Rule | Glide] = [*self.rules, *self.glides]
        for item in items:
            if item.id == rule_id:
                return item
        raise KeyError(f"no rule {rule_id!r} in the pack")

    def taking(self, word_class: str) -> list[Rule]:
        """Every active rule whose input side accepts this word class."""
        return [r for r in self.rules if r.active and word_class in r.input_types]

    @property
    def needing_expert_check(self) -> list[Rule]:
        """The rules the transcription could not fully resolve."""
        return [r for r in self.rules if r.needs_expert_check]


def default_directory() -> Path:
    """Where the rule files live: the environment, or ``rules/`` in the repo."""
    configured = os.environ.get(PATH_VARIABLE)
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / "rules"


def _require(condition: bool, rule_id: str, complaint: str) -> None:
    if not condition:
        raise RulePackError(f"{rule_id}: {complaint}")


def _check_word_classes(rule_id: str, side: str, names: list[str]) -> None:
    _require(bool(names), rule_id, f"{side} names no word class")
    for name in names:
        _require(
            is_word_class(name), rule_id, f"{side} names unknown word class {name!r}"
        )


def _load_rule(raw: dict[str, Any]) -> Rule:
    rule_id = raw.get("id") or "<rule with no id>"
    _require("id" in raw, rule_id, "has no id")
    _require(raw.get("kind") in KINDS, rule_id, f"unknown kind {raw.get('kind')!r}")
    _require(
        raw.get("strength") in STRENGTHS,
        rule_id,
        f"unknown strength {raw.get('strength')!r}",
    )
    _require(
        bool(raw.get("source", {}).get("table")),
        rule_id,
        "does not name its source table",
    )

    input_types = list(raw.get("input", {}).get("types", []))
    output_types = list(raw.get("output", {}).get("types", []))
    _check_word_classes(rule_id, "input", input_types)
    _check_word_classes(rule_id, "output", output_types)

    kind = raw["kind"]
    if kind in {"suffix", "prefix", "infix"}:
        _require(
            bool(raw.get("affix_fa")), rule_id, "has no Persian spelling for its affix"
        )
    if kind == "template":
        _require(bool(raw.get("pattern")), rule_id, "is a template with no pattern")
        _require(
            bool(raw.get("pattern_fa")),
            rule_id,
            "is a template with no Persian pattern",
        )
        slots = raw.get("slots") or []
        _require(len(slots) >= 2, rule_id, "is a template with fewer than two slots")
        for slot in slots:
            _require(
                is_word_class(slot.get("type", "")),
                rule_id,
                f"slot {slot.get('name')!r} has unknown type {slot.get('type')!r}",
            )
            constraint = slot.get("constraint")
            _require(
                constraint is None or constraint in CONSTRAINTS,
                rule_id,
                f"slot {slot.get('name')!r} has unknown constraint {constraint!r}",
            )

    # Farsi text is not decoration: the interface is in Farsi and the engine
    # cannot invent it. A rule without it cannot be shown to anyone.
    _require(bool(raw.get("explanation_fa")), rule_id, "has no Farsi explanation")
    if kind != "none" or raw.get("label_fa"):
        _require(bool(raw.get("label_fa")), rule_id, "has no Farsi label")

    if raw.get("needs_expert_check"):
        _require(
            bool(raw.get("notes")),
            rule_id,
            "is flagged for review but says nothing about why",
        )

    # The same guarantee the glide loader has always had. Without it a rule
    # could be switched off in the YAML and stop building words with nothing
    # anywhere saying so — and since ids are permanent and a retired rule is
    # still served, the reason is the only thing that distinguishes a ruling
    # from a rule somebody disabled.
    active = bool(raw.get("active", True))
    _require(
        active or bool(raw.get("retired_reason")),
        rule_id,
        "is retired but does not say why",
    )

    return Rule(
        id=raw["id"],
        kind=kind,
        source=raw["source"],
        input_types=tuple(input_types),
        output_types=tuple(output_types),
        affix=raw.get("affix"),
        affix_fa=raw.get("affix_fa"),
        affix_variants=tuple(raw.get("affix_variants") or ()),
        semantic_tags=tuple(raw.get("semantic_tags") or ()),
        strength=raw.get("strength"),
        examples=tuple(raw.get("examples") or ()),
        label_fa=raw.get("label_fa"),
        explanation_fa=raw.get("explanation_fa"),
        pattern=raw.get("pattern"),
        pattern_fa=raw.get("pattern_fa"),
        slots=tuple(raw.get("slots") or ()),
        exceptions=tuple(raw.get("exceptions") or ()),
        needs_expert_check=bool(raw.get("needs_expert_check")),
        notes=tuple(raw.get("notes") or ()),
        active=active,
        retired_reason=" ".join((raw.get("retired_reason") or "").split()),
        retired_reason_fa=" ".join((raw.get("retired_reason_fa") or "").split()),
    )


def _load_glide(raw: dict[str, Any]) -> Glide:
    rule_id = raw.get("id") or "<glide with no id>"
    for side in ("left", "right", "result"):
        _require(bool(raw.get(side)), rule_id, f"has no {side} vowel")
    _require(bool(raw.get("explanation_fa")), rule_id, "has no Farsi explanation")
    active = bool(raw.get("active", True))
    _require(
        active or bool(raw.get("retired_reason")),
        rule_id,
        "is retired but does not say why",
    )
    return Glide(
        id=raw["id"],
        left=raw["left"],
        right=raw["right"],
        result=raw["result"],
        examples=tuple(raw.get("examples") or ()),
        explanation_fa=raw.get("explanation_fa"),
        active=active,
        retired_reason=" ".join((raw.get("retired_reason") or "").split()),
        retired_reason_fa=" ".join((raw.get("retired_reason_fa") or "").split()),
    )


def load(directory: Path | None = None) -> RulePack:
    """Read every rule file, checking each rule as it goes."""
    base = directory or default_directory()
    pack = RulePack()
    seen: set[str] = set()

    for name in RULE_FILES:
        path = base / f"{name}.yaml"
        if not path.exists():
            raise RulePackError(f"missing rule file: {path}")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        pack.version = document.get("version", pack.version)
        for raw in document.get("rules", []):
            item: Rule | Glide = (
                _load_glide(raw) if name == "glides" else _load_rule(raw)
            )
            # An id is permanent and addresses exactly one rule. Two rules
            # answering to one id makes every stored derivation ambiguous.
            if item.id in seen:
                raise RulePackError(f"{item.id}: appears twice in the pack")
            seen.add(item.id)
            if isinstance(item, Glide):
                pack.glides.append(item)
            else:
                pack.rules.append(item)

    tags_path = base / SEMANTIC_TAGS_FILE
    if tags_path.exists():
        document = yaml.safe_load(tags_path.read_text(encoding="utf-8")) or {}
        for raw in document.get("tags") or []:
            tag = SemanticTag(
                tag=raw["tag"],
                labels=tuple(raw["label_source"]),
                gloss_fa=raw["gloss_fa"],
                gloss_en=raw["gloss_en"],
                gloss_template_fa=raw.get("gloss_template_fa"),
                gloss_template_en=raw.get("gloss_template_en"),
            )
            # Keyed on every spelling a rule may use, so a lookup never needs
            # to know which variant the source wrote.
            for label in tag.labels:
                pack.tags[label] = tag

    forms_path = base / STEM_FORMS_FILE
    if forms_path.exists():
        document = yaml.safe_load(forms_path.read_text(encoding="utf-8")) or {}
        for raw in document.get("rules") or []:
            pack.stem_forms.append(
                StemForm(
                    written=raw["written"],
                    working=raw["working"],
                    reason=" ".join(raw.get("reason", "").split()),
                )
            )

    return pack


@lru_cache(maxsize=1)
def loaded() -> RulePack:
    """The pack, loaded once from the configured directory."""
    return load()
