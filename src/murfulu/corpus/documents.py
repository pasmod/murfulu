"""What every corpus source yields.

One document is a poem, a page or a chapter — **never a line**. Where a line
begins differs from source to source, so a line is not a unit that survives
adding a second corpus.

Nothing here may assume poetry. ``author`` and ``century`` are optional because
a news article has neither in the sense a divan does.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: A document id is ``source:path:to:item`` — the source first, so an id says
#: where it came from without a lookup.
_ID_PATTERN = re.compile(r"^[a-z0-9_]+(:[^\s:]+)+$")


class InvalidDocumentError(ValueError):
    """Raised when a source yields a document that cannot be indexed."""


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
