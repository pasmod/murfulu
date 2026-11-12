"""The linguist's word-bank groups, and what each one feeds in word formation.

Since karbon 1.3.0 every lexicon entry carries the linguist's own groups
(:attr:`~murfulu.lexicon.entries.Reading.bank_groups`): نام، کارنام، برنام،
وام‌واژه and eight more, several per word. They are the authority on what a
word is, so word formation reads them; ``rules/bank_groups.yaml`` says what
each one feeds, and a linguist can change it without touching code.

Three rules, all in :func:`word_classes_of`:

- a reading's word classes are the **union** of its groups' classes, in the
  file's order;
- a reading in a group that is **out of word formation** (وام‌واژه) builds
  nothing, whatever its other groups say;
- a snapshot from before the bank has no groups, and falls back to
  ``rules/lexicon_categories.yaml`` exactly as before.

The file also holds the one switch an open ruling decides,
``karnam_counts_as_nam`` (L26 with L18). The rule pack reads it
(:func:`murfulu.rules.pack.load`), because it widens what rules accept rather
than what words are.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from murfulu.lexicon.categories import (
    UnmappableCategoryError,
    default_rules_directory,
    word_classes_for,
)
from murfulu.lexicon.entries import Reading
from murfulu.rules.pack import BANK_GROUPS_FILE, KARNAM_AS_NAM
from murfulu.rules.types import is_word_class


class BankGroupError(ValueError):
    """Raised when the mapping file does not load. The message names the group."""


class UnknownBankGroupError(LookupError):
    """Raised when a reading carries a group the mapping file does not list."""


class ExcludedFromWordFormationError(UnmappableCategoryError):
    """The reading is in a group the linguist keeps out of word formation.

    A subclass of :class:`UnmappableCategoryError` on purpose: every caller
    already treats that as "builds nothing, and that is a decision", which is
    exactly what this is.
    """


@dataclass(frozen=True)
class BankGroup:
    """One of the linguist's groups and what it feeds."""

    key: str
    label_fa: str
    word_classes: tuple[str, ...]
    in_word_formation: bool
    grounding: str
    note: str
    rows: int | None = None


@dataclass(frozen=True)
class BankMapping:
    """The whole file: every group, in its order, and the switches."""

    groups: dict[str, BankGroup]
    karnam_counts_as_nam: bool = False
    version: str = ""

    def group(self, key: str) -> BankGroup:
        """One group, or :class:`UnknownBankGroupError` naming it."""
        try:
            return self.groups[key]
        except KeyError:
            raise UnknownBankGroupError(
                f"«{key}» is a word-bank group the snapshot uses and "
                f"{BANK_GROUPS_FILE} does not list; every group must be there, "
                f"mapped or explicitly feeding nothing"
            ) from None


_GROUNDINGS = frozenset({"linguist", "source", "ours"})


def load(directory: Path | None = None) -> BankMapping:
    """Read the mapping file, checking every target against the closed set."""
    path = (directory or default_rules_directory()) / BANK_GROUPS_FILE
    document: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    groups: dict[str, BankGroup] = {}
    for raw in document.get("groups") or []:
        key = raw["key"]
        if key in groups:
            raise BankGroupError(f"{path}: «{key}» is listed twice")
        classes = tuple(raw.get("word_classes") or ())
        unknown = [name for name in classes if not is_word_class(name)]
        if unknown:
            raise BankGroupError(
                f"{path}: «{key}» maps to unknown word class(es) {unknown}"
            )
        if raw.get("grounding") not in _GROUNDINGS:
            raise BankGroupError(
                f"{path}: «{key}» has grounding {raw.get('grounding')!r}, "
                f"not one of {sorted(_GROUNDINGS)}"
            )
        if not raw.get("in_word_formation", True) and classes:
            raise BankGroupError(
                f"{path}: «{key}» is out of word formation and still maps to "
                f"{list(classes)}; say one or the other"
            )
        groups[key] = BankGroup(
            key=key,
            label_fa=raw["label_fa"],
            word_classes=classes,
            in_word_formation=bool(raw.get("in_word_formation", True)),
            grounding=raw["grounding"],
            note=" ".join(str(raw.get("note", "")).split()),
            rows=raw.get("rows"),
        )
    switches = document.get("switches") or {}
    return BankMapping(
        groups=groups,
        karnam_counts_as_nam=bool(switches.get(KARNAM_AS_NAM, False)),
        version=str(document.get("version", "")),
    )


@lru_cache(maxsize=1)
def loaded() -> BankMapping:
    """The mapping, read once."""
    return load()


def is_excluded(reading: Reading, mapping: BankMapping | None = None) -> bool:
    """True when one of the reading's groups is out of word formation."""
    if not reading.bank_groups:
        return False
    held = mapping or loaded()
    return any(not held.group(key).in_word_formation for key in reading.bank_groups)


def word_classes_of(
    reading: Reading, mapping: BankMapping | None = None
) -> tuple[str, ...]:
    """The word classes the rules should see this reading as.

    Raises :class:`UnmappableCategoryError` (or its subclass
    :class:`ExcludedFromWordFormationError`) rather than returning an empty
    tuple, so a caller cannot mistake "we decided not to" for "there happen to
    be none" — the same contract as
    :func:`murfulu.lexicon.categories.word_classes_for`, which a snapshot
    without groups still goes through.
    """
    if not reading.bank_groups:
        return word_classes_for(reading.lexicon_category)
    held = mapping or loaded()
    groups = [held.group(key) for key in reading.bank_groups]
    shut = [group.key for group in groups if not group.in_word_formation]
    if shut:
        raise ExcludedFromWordFormationError(
            f"{reading.latin}: in {', '.join(shut)}, which the linguist keeps out "
            f"of word formation"
        )
    classes: list[str] = []
    for group in groups:
        for name in group.word_classes:
            if name not in classes:
                classes.append(name)
    if not classes:
        raise UnmappableCategoryError(
            f"{reading.latin}: its groups ({', '.join(reading.bank_groups)}) "
            f"feed no rule"
        )
    return tuple(classes)


def group_labels(reading: Reading, mapping: BankMapping | None = None) -> list[str]:
    """The linguist's names for a reading's groups, in order."""
    held = mapping or loaded()
    return [held.group(key).label_fa for key in reading.bank_groups]
