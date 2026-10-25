"""Read the source grammar's own wording.

The rule tables are prose in cells: *"Kārboné yek, bištar bā Pāyāne -t va -d"*,
*"Kārboné yek + o + Kārboné do az Hamānkārvāže"*. This module turns that wording
into structured input, and says plainly when it cannot.

Everything it does not recognise comes back in ``unresolved`` rather than being
dropped. A silently dropped slot is worse than a flagged one: a compounding rule
that loses its second half still looks like a valid rule.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# How the source documents spell each word class. Includes their own slips:
# "Nāmen" for Nām, "Barnam" for Barnām, "Kārboé" for Kārboné.
TYPE_SPELLINGS: dict[str, str] = {
    "kārboné yek": "karbon_yek",
    "kārbon-e yek": "karbon_yek",
    "kārboé yek": "karbon_yek",
    "kārboné do": "karbon_do",
    "kārboé do": "karbon_do",
    "nābesudkārvāže": "nabesudkarvaze",
    "kārnām": "karnam",
    "nām": "nam",
    "nāmen": "nam",
    "barnām": "barnam",
    "barnam": "barnam",
    "kārandekārbahr": "karandekarbahr",
    "kāridekārbahr": "karidekarbahr",
    "čonvāže": "jonvaze",
    "čonvāze": "jonvaze",
    "jānām": "janam",
    "pišvāže": "pisvaze",
    "nedāyi": "nedayi",
}

#: Persian display name per word class, from the grammar's terminology table.
TYPE_FA: dict[str, str] = {
    "karbon_yek": "کاربن یک",
    "karbon_do": "کاربن دو",
    "nabesudkarvaze": "نابسودکارواژه",
    "karnam": "کارنام",
    "nam": "نام",
    "barnam": "برنام",
    "karandekarbahr": "کارنده‌کاربهر",
    "karidekarbahr": "کاریده‌کاربهر",
    "jonvaze": "چون‌واژه",
    "janam": "جانام",
    "pisvaze": "پیش‌واژه",
    "nedayi": "ندایی",
}

#: What a slot qualifier means. "Hamān" is *the same*, "Digar" is *another*.
CONSTRAINTS: dict[str, str] = {
    "az hamānkārvāže": "same_verb",
    "az digarkārvāže": "different_verb",
    "hamānkārbon": "same_stem",
    "digarkārbon": "different_stem",
}

#: Letters that join the two halves of a compound: Zadoxord, Kešākeš.
JOINERS = {"o", "ā", "va"}

#: The negation particle inside a compound: Budonabud.
NEGATOR = "na"

#: "bištar" — *mostly*. A row that says it states a tendency, not a rule that
#: always applies.
_TENDENCY = re.compile(r"[,،]?\s*\bbištar\b.*$", re.IGNORECASE)

_SPLIT = re.compile(r"[\n/,]+")


@dataclass
class Slot:
    """One filled position in a compounding template."""

    name: str
    type: str
    constraint: str | None = None
    negated: bool = False


@dataclass
class ParsedInput:
    """What the "attaches to" cell of a rule row says."""

    types: list[str] = field(default_factory=list)
    slots: list[Slot] = field(default_factory=list)
    pattern: str | None = None
    tendency: str | None = None
    unresolved: list[str] = field(default_factory=list)

    @property
    def is_template(self) -> bool:
        """True when the row joins two parts rather than taking one base."""
        return bool(self.slots)


def clean(text: str) -> str:
    """Collapse the whitespace a Word cell brings with it."""
    return " ".join(text.replace("\n", " ").split())


def word_class(text: str) -> str | None:
    """Resolve one word-class name, ignoring any modifier after it."""
    stripped = clean(text).strip(".,;").lower()
    if stripped in TYPE_SPELLINGS:
        return TYPE_SPELLINGS[stripped]
    # "Nābesudkārvāžeé gozarā" is a type plus a modifier. Longest match first,
    # so "Kārboné do" never loses to "Kārboné yek".
    for spelling in sorted(TYPE_SPELLINGS, key=len, reverse=True):
        if stripped.startswith(spelling):
            return TYPE_SPELLINGS[spelling]
    return None


def word_classes(cell: str) -> tuple[list[str], list[str]]:
    """Every word class a cell names, and the parts that did not resolve."""
    resolved: list[str] = []
    unresolved: list[str] = []
    for part in _SPLIT.split(cell):
        if not part.strip():
            continue
        machine = word_class(part)
        if machine is None:
            unresolved.append(clean(part))
        elif machine not in resolved:
            resolved.append(machine)
    return resolved, unresolved


def _parse_slot(text: str, name: str, negated: bool) -> tuple[Slot | None, str | None]:
    stripped = clean(text)
    lowered = stripped.lower()
    constraint = next(
        (value for key, value in CONSTRAINTS.items() if key in lowered), None
    )
    machine = word_class(re.sub(r"\b(hamān|digar)", "", stripped, flags=re.IGNORECASE))
    if machine is None:
        return None, stripped
    return Slot(name=name, type=machine, constraint=constraint, negated=negated), None


def parse_input(cell: str) -> ParsedInput:
    """Read one "attaches to" cell."""
    parsed = ParsedInput()
    text = clean(cell)

    if match := _TENDENCY.search(text):
        parsed.tendency = match.group(0).lstrip(" ,،")
        text = text[: match.start()]

    parts = [part.strip() for part in text.split("+") if part.strip()]
    if len(parts) <= 1:
        parsed.types, parsed.unresolved = word_classes(text)
        return parsed

    # A compounding row. Slots are named a, b, c… in the order they appear.
    names = iter("abcdefg")
    pattern: list[str] = []
    negate_next = False
    for part in parts:
        lowered = part.lower()
        if lowered == NEGATOR:
            negate_next = True
            pattern.append(NEGATOR)
            continue
        if lowered in JOINERS:
            pattern.append(part)
            continue
        slot, problem = _parse_slot(part, next(names), negate_next)
        negate_next = False
        if slot is None:
            parsed.unresolved.append(problem or part)
            pattern.append("?")
        else:
            parsed.slots.append(slot)
            pattern.append(f"{{{slot.name}}}")

    parsed.pattern = " + ".join(pattern)
    parsed.types = list(dict.fromkeys(slot.type for slot in parsed.slots))
    return parsed
