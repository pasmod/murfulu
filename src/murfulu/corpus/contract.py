"""The shared test every source adapter must pass.

Lives in the package rather than in ``tests/`` on purpose: a new adapter proves
itself by calling :func:`check_adapter`, so the bar is the same for the second
corpus as for the first, and nobody has to remember what it was.

Raises :class:`AdapterContractError` with a plain description of what is wrong.
"""

from __future__ import annotations

from itertools import islice

from murfulu.corpus.adapter import SourceAdapter, check_source_id
from murfulu.corpus.documents import Document

#: How many documents the contract check reads. Enough to catch a broken
#: adapter, few enough to run against a corpus of any size.
SAMPLE_SIZE = 50


class AdapterContractError(AssertionError):
    """Raised when an adapter does not behave as the interface requires."""


def check_adapter(adapter: SourceAdapter, sample_size: int = SAMPLE_SIZE) -> int:
    """Run every shared requirement against ``adapter``. Returns docs checked."""
    _check_identity(adapter)

    seen: set[str] = set()
    first_pass: list[str] = []
    for document in islice(adapter.documents(), sample_size):
        _check_document(adapter, document, seen)
        first_pass.append(document.document_id)

    if not first_pass:
        raise AdapterContractError(f"{adapter.source_id} yielded no documents")
    _check_repeatable(adapter, first_pass)
    return len(first_pass)


def _check_identity(adapter: SourceAdapter) -> None:
    try:
        check_source_id(adapter.source_id)
    except ValueError as error:
        raise AdapterContractError(str(error)) from error
    if not adapter.licence.strip():
        raise AdapterContractError(
            f"{adapter.source_id} states no licence. Every source must say "
            f"under what terms its material may be held."
        )


def _check_document(adapter: SourceAdapter, document: Document, seen: set[str]) -> None:
    if not isinstance(document, Document):
        raise AdapterContractError(
            f"{adapter.source_id} yielded {type(document).__name__}, not a Document"
        )
    if document.source_id != adapter.source_id:
        raise AdapterContractError(
            f"{document.document_id} claims source {document.source_id!r} but "
            f"came from {adapter.source_id!r}"
        )
    if document.document_id in seen:
        raise AdapterContractError(
            f"{adapter.source_id} yielded {document.document_id} twice. "
            f"Document ids are the index key and must be unique."
        )
    seen.add(document.document_id)


def _check_repeatable(adapter: SourceAdapter, first_pass: list[str]) -> None:
    """Iterating twice must give the same documents in the same order.

    Ingest is re-run whenever a corpus version is rebuilt. An adapter that
    yields a different order each time makes two builds incomparable.

    Compared against the *first* pass, not against a third one: an adapter that
    is wrong from the second pass onwards but self-consistent after that would
    otherwise slip through.
    """
    second = [d.document_id for d in islice(adapter.documents(), len(first_pass))]
    if first_pass != second:
        raise AdapterContractError(
            f"{adapter.source_id} is not repeatable: two passes gave different "
            f"documents. Ingest must be able to run twice."
        )
