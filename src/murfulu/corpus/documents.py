"""What every corpus source yields.

One document is a poem, a page or a chapter — **never a line**. Where a line
begins differs from source to source, so a line is not a unit that survives
adding a second corpus.

Nothing here may assume poetry. ``author`` and ``century`` are optional because
a news article has neither in the sense a divan does, and since 2026-11-13 a
document also says **where it sits** — its work and its section — and **what
it is made of**: its units, in order, each a couplet, a verse half or a prose
paragraph. The reading screen draws a text from its units; everything that
counts words still reads ``text_fa``, which is the counted units' lines joined
by newlines, so the two can never disagree.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

#: A document id is ``source:path:to:item`` — the source first, so an id says
#: where it came from without a lookup.
_ID_PATTERN = re.compile(r"^[a-z0-9_]+(:[^\s:]+)+$")

#: What a unit of text can be. A couplet is two halves read as one line of a
#: poem; a half is a verse line standing alone (free verse, an unpaired band
#: line); prose is a paragraph; a note is the source's own explanation or
#: heading, kept for the reader and **never counted** — it is not the text.
UNIT_KINDS = ("couplet", "half", "prose", "note")

#: Where a line sits, in this project's words rather than any source's codes.
#: ``first`` and ``second`` are the halves of an ordinary couplet; ``band_*``
#: the halves of the band couplet that closes a stanza of a tarji'band or
#: tarkib-band, which a printed divan centres; ``free`` a line of free verse.
LINE_POSITIONS = (
    "first",
    "second",
    "band_first",
    "band_second",
    "free",
    "prose",
    "note",
)


class InvalidDocumentError(ValueError):
    """Raised when a source yields a document that cannot be indexed."""


@dataclass(frozen=True)
class Line:
    """One line of a unit as the source writes it, and where it sits."""

    text: str
    position: str

    def __post_init__(self) -> None:
        """Reject a position this project has no word for."""
        if self.position not in LINE_POSITIONS:
            raise InvalidDocumentError(f"unknown line position {self.position!r}")


@dataclass(frozen=True)
class Unit:
    """A couplet, a verse half, a prose paragraph or a note — in order."""

    kind: str
    lines: tuple[Line, ...]

    def __post_init__(self) -> None:
        """A couplet has two lines, every other kind one."""
        if self.kind not in UNIT_KINDS:
            raise InvalidDocumentError(f"unknown unit kind {self.kind!r}")
        wanted = 2 if self.kind == "couplet" else 1
        if len(self.lines) != wanted:
            raise InvalidDocumentError(
                f"a {self.kind} has {wanted} line(s), not {len(self.lines)}"
            )

    @property
    def counted(self) -> bool:
        """Whether its words are the text's words. A note's are not."""
        return self.kind != "note"

    def as_dict(self) -> dict[str, Any]:
        """The stored shape: short keys, because a long text has thousands."""
        return {
            "kind": self.kind,
            "lines": [
                {"text": one.text, "position": one.position} for one in self.lines
            ],
        }


def unit_from_dict(stored: dict[str, Any]) -> Unit:
    """Read a stored unit back."""
    return Unit(
        kind=stored["kind"],
        lines=tuple(
            Line(text=one["text"], position=one["position"]) for one in stored["lines"]
        ),
    )


def counted_text(units: Iterable[Unit]) -> str:
    """The lines whose words are counted, one per line, in order."""
    return "\n".join(line.text for unit in units if unit.counted for line in unit.lines)


@dataclass(frozen=True)
class Document:
    """One indexable unit of a corpus."""

    source_id: str
    document_id: str
    text_fa: str
    title: str | None = None
    author: str | None = None
    century: int | None = None
    #: Anything the source carries that no other source has. Kept out of the
    #: shared fields so adding a corpus never widens this class.
    extra: dict[str, str] = field(default_factory=dict)
    #: The book the text belongs to — a divan's غزلیات, the گلستان — or None
    #: when the source files it directly under its author.
    work: str | None = None
    #: The sections between the work and the text, outermost first.
    section: tuple[str, ...] = ()
    #: The text's units in order. Empty for a source that has not said what
    #: its text is made of; ``text_fa`` is then all there is.
    units: tuple[Unit, ...] = ()
    #: The text's place in its source, so a work's texts can be listed in the
    #: order the source gives them. None when the source has no order.
    order: int | None = None

    def __post_init__(self) -> None:
        """Reject a document the index could not hold."""
        if not _ID_PATTERN.match(self.document_id):
            raise InvalidDocumentError(
                f"document_id {self.document_id!r} must look like 'source:path:to:item'"
            )
        if not self.document_id.startswith(f"{self.source_id}:"):
            raise InvalidDocumentError(
                f"document_id {self.document_id!r} does not start with its "
                f"source id {self.source_id!r}"
            )
        if not self.text_fa.strip():
            raise InvalidDocumentError(f"{self.document_id} has no text")
        if self.century is not None and not 1 <= self.century <= 21:
            raise InvalidDocumentError(
                f"{self.document_id}: century {self.century} is out of range"
            )
        if self.units and counted_text(self.units) != self.text_fa:
            # The count reads text_fa and the reading screen reads the units.
            # If they could differ, a word could be counted that no reader can
            # find, or shown that was never counted.
            raise InvalidDocumentError(
                f"{self.document_id}: text_fa is not its counted units' lines"
            )

    @classmethod
    def from_units(
        cls, *, source_id: str, document_id: str, units: Iterable[Unit], **rest: Any
    ) -> Document:
        """A document whose counted text is made from its units."""
        held = tuple(units)
        return cls(
            source_id=source_id,
            document_id=document_id,
            text_fa=counted_text(held),
            units=held,
            **rest,
        )
