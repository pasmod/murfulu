"""Map the lexicon's own categories to the word classes the rules match on.

The lexicon is lexicographic: it says اسم ذات، صفت مرکب، وام‌واژه. The rules are
grammatical: they match on ``nam``, ``barnam``, ``nabesudkarvaze``. The two do
not line up one to one, so the mapping is data — ``rules/lexicon_categories.yaml``
— and a linguist can edit it without touching code.

A category that cannot be mapped is listed with an empty ``word_classes`` and a
reason. Unmapped is a stated position, not an oversight, and asking for the
classes of such a category raises rather than returning a silent default.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from murfulu.rules.types import is_word_class

#: Environment variable pointing at the authored rule data.
PATH_VARIABLE = "MURFULU_RULES_PATH"

_FILENAME = "lexicon_categories.yaml"


class UnmappableCategoryError(LookupError):
    """Raised when a category is deliberately not mapped to any word class."""


class UnknownCategoryError(LookupError):
    """Raised when a category is not in the mapping file at all."""


@dataclass(frozen=True)
class CategoryMapping:
    """One lexicon category and what the rules should see it as."""

    lexicon_category: str | None
    word_classes: tuple[str, ...]
    is_compound: bool
    grounding: str
    note: str
    needs_expert_check: bool = False
    rows: int | None = None

    @property
    def is_mapped(self) -> bool:
        """True when the rules have something to match on."""
        return bool(self.word_classes)


def default_rules_directory() -> Path:
    """Where the authored rule data lives.

    From ``MURFULU_RULES_PATH`` if set, otherwise the ``rules/`` directory next
    to the repository root. Configuration, so a deployment can move it.
    """
    configured = os.environ.get(PATH_VARIABLE)
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / "rules"


def load(directory: Path | None = None) -> dict[str | None, CategoryMapping]:
    """Read the mapping file, checking every target against the closed set."""
    path = (directory or default_rules_directory()) / _FILENAME
    document: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))

    mappings: dict[str | None, CategoryMapping] = {}
    for entry in document["categories"]:
        classes = tuple(entry.get("word_classes") or ())
        unknown = [name for name in classes if not is_word_class(name)]
        if unknown:
            raise ValueError(
                f"{path}: {entry['lexicon_category']!r} maps to unknown "
                f"word class(es): {unknown}"
            )
        category = entry["lexicon_category"]
        if category in mappings:
            raise ValueError(f"{path}: {category!r} is listed twice")
        mappings[category] = CategoryMapping(
            lexicon_category=category,
            word_classes=classes,
            is_compound=bool(entry["is_compound"]),
            grounding=entry["grounding"],
            note=entry["note"],
            needs_expert_check=bool(entry.get("needs_expert_check", False)),
            rows=entry.get("rows"),
        )
    return mappings


@lru_cache(maxsize=1)
def _cached() -> dict[str | None, CategoryMapping]:
    return load()


def mapping_for(category: str | None) -> CategoryMapping:
    """The mapping entry for one lexicon category."""
    try:
        return _cached()[category]
    except KeyError:
        raise UnknownCategoryError(
            f"{category!r} is not in {_FILENAME}. Every category the lexicon "
            f"uses must be listed there, mapped or explicitly unmappable."
        ) from None


def word_classes_for(category: str | None) -> tuple[str, ...]:
    """The word classes the rules should match on for this category.

    Raises rather than returning an empty tuple when the category is
    deliberately unmapped, so a caller cannot mistake "we decided not to" for
    "there happen to be none".
    """
    entry = mapping_for(category)
    if not entry.is_mapped:
        raise UnmappableCategoryError(
            f"{category!r} is not mapped to a word class: {entry.note}"
        )
    return entry.word_classes
