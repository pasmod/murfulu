"""One row per word, keeping every way of reaching it.

Different chains can arrive at the same string. That is not noise to be thrown
away — two derivations for one form often means the word carries two senses —
so the paths are kept and shown under the form, shortest first.

The grouping key is **the Latin form plus the output word class**:

- not the Persian spelling, which collapses distinctions the Latin keeps
- not case-folded, because *Gofte* (a noun) and *gofte* (an adjective) are two
  different words in Behnevis
- the class is part of the key because the same string in two classes is two
  words
"""

from __future__ import annotations

from dataclasses import dataclass, field

from murfulu.engine.affix import DerivedForm, Step


@dataclass(frozen=True)
class GroupedForm:
    """One word, with every derivation that produces it."""

    latin: str
    fa: str
    word_class: str
    #: Shortest first. A tie keeps the order the paths were found in, so the
    #: same input always gives the same output.
    paths: tuple[tuple[Step, ...], ...] = ()
    semantic_tags: tuple[str, ...] = field(default_factory=tuple)
    base_latin: str = ""
    base_fa: str = ""

    @property
    def key(self) -> tuple[str, str]:
        """What two results must share to be the same word."""
        return (self.latin, self.word_class)

    @property
    def depth(self) -> int:
        """How many steps the shortest derivation took."""
        return len(self.paths[0]) if self.paths else 0

    @property
    def shortest_path(self) -> tuple[Step, ...]:
        """The path to show first, and to score the form by."""
        return self.paths[0] if self.paths else ()


def deduplicate(forms: list[DerivedForm]) -> list[GroupedForm]:
    """Group forms by Latin plus word class, keeping every path."""
    order: list[tuple[str, str]] = []
    grouped: dict[tuple[str, str], list[DerivedForm]] = {}

    for form in forms:
        key = (form.latin, form.word_class)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(form)

    result = []
    for key in order:
        members = grouped[key]
        first = members[0]
        # Stable: sorted() keeps the discovery order among equal lengths.
        paths = tuple(sorted((m.path for m in members), key=len))
        tags: list[str] = []
        for member in members:
            for tag in member.semantic_tags:
                if tag not in tags:
                    tags.append(tag)
        result.append(
            GroupedForm(
                latin=first.latin,
                fa=first.fa,
                word_class=first.word_class,
                paths=paths,
                semantic_tags=tuple(tags),
                base_latin=first.base_latin,
                base_fa=first.base_fa,
            )
        )
    return result
