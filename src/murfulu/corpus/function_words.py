"""Spellings that are almost always a function word, and so attest nothing else.

A corpus count is a count of letters. که occurs 609,699 times, and nearly every
one of them is the conjunction — so when the lexicon reads the same letters as
the adjective *keh*, the count says nothing about whether *keh* was ever
written. Crediting it anyway made the adjective one of the best-attested words
in classical Persian (data/compare-v12-v13.md).

The list is authored, versioned and small: ``rules/function_words.yaml`` says
how each entry was chosen and ``tools/check_function_words.py`` checks it
against the corpus. This module only reads it. What a listed spelling does to
attestation is decided in :mod:`murfulu.scoring.attestation`, in one place, so
the batch job and a live request cannot disagree about the same word.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from murfulu.corpus.wordtypes import normalise

FILENAME = "function_words.yaml"

#: The closed set of classes an entry may carry. A typo here would otherwise
#: become a new class nobody asked for.
CLASSES = (
    "conjunction",
    "preposition",
    "postposition",
    "contraction",
    "pronoun",
    "demonstrative",
    "particle",
)


class FunctionWordError(ValueError):
    """Raised when the list does not make sense."""


@dataclass(frozen=True)
class FunctionWord:
    """One spelling the corpus uses, overwhelmingly, as a function word."""

    spelling: str
    word_class: str
    #: Where the spelling stood by frequency, and its count, on the corpus
    #: version the list was checked against. Evidence for the entry, not a
    #: setting: the check tool recomputes both.
    rank: int
    count: int
    note: str = ""


@dataclass(frozen=True)
class FunctionWords:
    """The whole list, keyed on the normalised spelling."""

    version: str = ""
    corpus_version: str = ""
    max_rank: int = 0
    by_spelling: dict[str, FunctionWord] = field(default_factory=dict)

    def __len__(self) -> int:
        """How many spellings are listed."""
        return len(self.by_spelling)

    def __contains__(self, spelling: object) -> bool:
        """True when these letters, normalised, are on the list."""
        return isinstance(spelling, str) and normalise(spelling) in self.by_spelling

    def get(self, spelling: str) -> FunctionWord | None:
        """The entry for these letters, or None."""
        return self.by_spelling.get(normalise(spelling))


def default_directory() -> Path:
    """Where the rule data lives. Configuration, never a literal."""
    configured = os.environ.get("MURFULU_RULES_PATH")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / "rules"


def _entry(raw: dict[str, Any], path: Path) -> FunctionWord:
    spelling = str(raw.get("spelling") or "")
    if not spelling:
        raise FunctionWordError(f"{path}: an entry has no spelling")
    if normalise(spelling) != spelling:
        # Stored as the corpus counts it, or the lookup silently misses.
        raise FunctionWordError(f"{path}: {spelling!r} is not normalised")
    word_class = str(raw.get("class") or "")
    if word_class not in CLASSES:
        raise FunctionWordError(
            f"{path}: {spelling!r} has class {word_class!r}, not one of {CLASSES}"
        )
    return FunctionWord(
        spelling=spelling,
        word_class=word_class,
        rank=int(raw.get("rank") or 0),
        count=int(raw.get("count") or 0),
        note=str(raw.get("note") or ""),
    )


def load(directory: Path | None = None) -> FunctionWords:
    """Read the list, refusing duplicates and unknown classes."""
    path = (directory or default_directory()) / FILENAME
    document: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    entries: dict[str, FunctionWord] = {}
    for raw in document.get("entries") or ():
        entry = _entry(raw, path)
        if entry.spelling in entries:
            raise FunctionWordError(f"{path}: {entry.spelling!r} is listed twice")
        entries[entry.spelling] = entry
    if not entries:
        raise FunctionWordError(f"{path}: the list is empty")
    return FunctionWords(
        version=str(document.get("version") or ""),
        corpus_version=str(document.get("corpus_version") or ""),
        max_rank=int(document.get("max_rank") or 0),
        by_spelling=entries,
    )


@lru_cache(maxsize=1)
def loaded() -> FunctionWords:
    """The list, read once per process."""
    return load()
