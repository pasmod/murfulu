"""The project's own name for each word class, loaded from authored data.

:mod:`murfulu.rules.types` holds the **closed set** of machine ids and what
traditional grammar calls each one, because that is what the source document's
terminology column carries. This module holds the other half: the linguist's
coined Persian term, which is the label a reader should actually see.

**Why it is data and not a dict in Python.** The interface may not invent
Persian — every user-facing string comes from an authored file — and a coined
term is authored, not derived. `rules/word_classes.yaml` says for each class
who wrote its Persian and whether the linguist has confirmed it, and four of
the twelve are unconfirmed. See S3.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from murfulu.rules.pack import default_directory
from murfulu.rules.types import WORD_CLASSES

#: Authored beside the rules, and loaded from the same configured directory.
WORD_CLASSES_FILE = "word_classes.yaml"


class WordClassError(ValueError):
    """Raised when the table does not load. The message names the class."""


@dataclass(frozen=True)
class WordClass:
    """One word class under both vocabularies."""

    name: str
    coined_fa: str | None
    traditional_fa: str | None
    behnevis: str | None
    gloss_en: str
    #: One plain Persian line saying what the class is, for the tooltip.
    #: **Authored, and none of the twelve is confirmed** — see L17.
    explanation_fa: str
    #: Whether the linguist has stated this Persian term. **False is a
    #: doubt about the letters, never about the class.**
    confirmed: bool
    source: str

    @property
    def label_fa(self) -> str | None:
        """What to print in Persian: the coined term, or the traditional one.

        A class with no coined term falls back rather than showing nothing —
        but :attr:`label_is_traditional` says it fell back, so a screen can
        avoid presenting the old vocabulary as though it were the new one.
        """
        return self.coined_fa or self.traditional_fa

    @property
    def label_is_traditional(self) -> bool:
        """True when :attr:`label_fa` is the term this project set out to replace."""
        return not self.coined_fa and bool(self.traditional_fa)


def load(directory: Path | None = None) -> dict[str, WordClass]:
    """Read the table, and refuse one that disagrees with the closed set.

    The two must name exactly the same classes. A class in the closed set with
    no row here would be labelled in English on screen; a row here for a class
    that does not exist is a term nothing can ever show. Both are mistakes
    worth failing on rather than discovering in the interface.
    """
    base = directory or default_directory()
    path = base / WORD_CLASSES_FILE
    if not path.exists():
        raise WordClassError(f"missing word class table: {path}")
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    loaded_classes: dict[str, WordClass] = {}
    for raw in document.get("classes") or []:
        name = raw["name"]
        if name in loaded_classes:
            raise WordClassError(f"{name}: appears twice in the word class table")
        loaded_classes[name] = WordClass(
            name=name,
            coined_fa=raw.get("coined_fa"),
            traditional_fa=raw.get("traditional_fa"),
            behnevis=raw.get("behnevis"),
            gloss_en=" ".join((raw.get("gloss_en") or "").split()),
            explanation_fa=" ".join((raw.get("explanation_fa") or "").split()),
            confirmed=bool(raw.get("confirmed")),
            source=raw.get("source", ""),
        )
    missing = sorted(set(WORD_CLASSES) - set(loaded_classes))
    if missing:
        raise WordClassError(f"no Persian term for: {', '.join(missing)}")
    # A screen shows this line; an empty one would render as a blank tooltip,
    # which reads as *nothing to say* rather than *nobody has written it*.
    silent = sorted(
        name for name, one in loaded_classes.items() if not one.explanation_fa
    )
    if silent:
        raise WordClassError(f"no Persian explanation for: {', '.join(silent)}")
    unknown = sorted(set(loaded_classes) - set(WORD_CLASSES))
    if unknown:
        raise WordClassError(f"not a word class: {', '.join(unknown)}")
    # In the closed set's order, so the API's list is the grammar's own order
    # rather than the order somebody happened to type the file in.
    return {name: loaded_classes[name] for name in WORD_CLASSES}


@lru_cache(maxsize=1)
def loaded() -> dict[str, WordClass]:
    """The table, read once from the configured directory."""
    return load()
