"""The lines of one text that hold a spelling, split around the word.

:mod:`murfulu.search.evidence` finds the texts; this finds, in one stored
text, every line holding the spelling and marks the word in it.

**A line shown is a line counted.** The lines are found with the counting's
own tokeniser (``wordtypes.tokenise``), not the search index's analyser, so a
line is listed exactly when the counting would have counted the word in it. A
line is one line of the source — a verse half, a prose paragraph — and a line
the source stored with a line break inside is taken as the lines it holds, as
the counted text (``text_fa``) takes it. A source's note is never quoted.

**A near spelling is said, not hidden.** The search index folds a few letters
the counting keeps apart (:data:`_LOOSE`), so it can find a text that holds
the word only as امد where آمد was asked for, or as خانۀ for خانه. Such a
text has no line the counting would credit; its lines in the near spelling
are given instead, and the text says so. A text with neither — the index
splits a few words differently from the counting — comes with no lines.

**The word is marked where it stands, every time.** Each line comes as its
parts: text, word, text, word, …, text, the word as written, harakat and the
hamza of an ezafe with it, found by the reading screen's own split
(``texts.spans``) so the two screens mark the same letters.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any, Literal

from murfulu.corpus.wordtypes import normalise, tokenise
from murfulu.search.citations import excerpt, lines
from murfulu.search.texts import spans

#: What the search index folds and the counting does not: the stock Arabic and
#: Persian normalisation turns آ into ا, ى into ی, ۀ and its kin into ه.
_LOOSE = str.maketrans(
    {"آ": "ا", "ى": "ی", "ۀ": "ه", "ہ": "ه", "ۂ": "ه", "ۃ": "ه", "ے": "ی"}
)

#: How a text holds the word: as counted, only in a near spelling, or in no
#: line the counting's split can find.
Held = Literal["counted", "near", "none"]


def loosen(spelling: str) -> str:
    """A counted spelling folded the way the search index folds it."""
    return spelling.translate(_LOOSE)


def _as_counted(spelling: str) -> str:
    return spelling


def _fold(near: bool) -> Callable[[str], str]:
    """How a word is compared: as counted, or folded as the index folds it."""
    return loosen if near else _as_counted


@dataclass(frozen=True)
class Line:
    """One line holding the word, and where it stands in its text."""

    unit: int | None
    kind: str | None
    #: The line cut as a citation is, split around the word: text, word,
    #: text, word, …, text. The odd places are the word, as written.
    parts: tuple[str, ...]
    #: The spelling the marked word was counted under, where it is not the one
    #: asked for — امد in a line found for آمد. None otherwise.
    word: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """The shape the API returns; ``word`` only where there is one."""
        shown: dict[str, Any] = {
            "unit": self.unit,
            "kind": self.kind,
            "parts": list(self.parts),
        }
        if self.word is not None:
            shown["word"] = self.word
        return shown


@dataclass(frozen=True)
class Text:
    """One text holding the word, and every line in it that does."""

    document_id: str
    author: str | None
    title: str | None
    century: int | None
    work: str | None
    section: tuple[str, ...]
    lines: tuple[Line, ...]
    held: Held = "counted"

    def as_dict(self) -> dict[str, Any]:
        """The shape the API returns."""
        return {
            "document_id": self.document_id,
            "author": self.author,
            "title": self.title,
            "century": self.century,
            "work": self.work,
            "section": list(self.section),
            "lines": [one.as_dict() for one in self.lines],
            "held": self.held,
        }


def _each_line(source: dict[str, Any]) -> Iterator[tuple[int | None, str | None, str]]:
    """Every counted line of a text, a stored line break making two."""
    for unit, kind, stored in lines(source):
        for line in stored.splitlines():
            if line.strip():
                yield unit, kind, line.strip()


def found(
    source: dict[str, Any], spelling: str
) -> tuple[list[tuple[int | None, str | None, str]], Held]:
    """The lines holding the word as counted, or else in a near spelling."""
    wanted = normalise(spelling)
    every = list(_each_line(source))
    held = [one for one in every if wanted in tokenise(one[2])]
    if held:
        return held, "counted"
    near = loosen(wanted)
    held = [
        one for one in every if any(loosen(word) == near for word in tokenise(one[2]))
    ]
    return held, "near" if held else "none"


def parts(line: str, spelling: str, *, near: bool = False) -> tuple[str, ...]:
    """A line split around every occurrence of the word: text, word, …, text."""
    fold = _fold(near)
    wanted = fold(normalise(spelling))
    text, words = spans(line)
    split: list[str] = []
    written_to = 0
    for start, end, counted in words:
        if fold(counted) == wanted:
            split.extend([text[written_to:start], text[start:end]])
            written_to = end
    split.append(text[written_to:])
    return tuple(split)


def _near_word(line: str, spelling: str) -> str | None:
    """The spelling a near line holds the word under, as the counting wrote it."""
    wanted = loosen(normalise(spelling))
    return next((one for one in tokenise(line) if loosen(one) == wanted), None)


def _line(
    unit: int | None, kind: str | None, line: str, spelling: str, near: bool
) -> Line:
    quoted = excerpt(line, spelling, fold=_fold(near))
    return Line(
        unit,
        kind,
        parts(quoted, spelling, near=near),
        _near_word(quoted, spelling) if near else None,
    )


def text_of(source: dict[str, Any], spelling: str) -> Text:
    """One stored text as an entry of the list."""
    held, how = found(source, spelling)
    near = how == "near"
    return Text(
        document_id=source.get("document_id", ""),
        author=source.get("author") or None,
        title=source.get("title"),
        century=source.get("century"),
        work=source.get("work"),
        section=tuple(source.get("section") or ()),
        lines=tuple(
            _line(unit, kind, line, spelling, near) for unit, kind, line in held
        ),
        held=how,
    )
