"""The one interface every corpus source implements.

Ganjoor is the first source, not the only one. Books, prose and journalism
follow, and each arrives as another adapter behind this interface — nothing
outside ``murfulu.corpus`` changes when one is added.

An adapter is responsible for exactly three things: saying what source it is,
saying under what licence, and yielding documents. It does no indexing, no
tokenising and no counting; those are pipelines that consume any adapter.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Iterator

from murfulu.corpus.documents import Document

#: Source ids are lower-case and stable: they appear in every document id and
#: in stored derivation evidence, so renaming one invalidates stored results.
_SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")


class SourceAdapter(ABC):
    """A corpus this project can ingest."""

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Stable lower-case identifier, e.g. ``ganjoor``."""

    @property
    @abstractmethod
    def licence(self) -> str:
        """Under what terms the material may be held and quoted.

        Required, not optional. A corpus whose licence nobody wrote down is a
        corpus that cannot be shipped, and finding that out at release time is
        too late.

        **English, and it stays English.** This is what the ingest log carries
        and what NOTICE quotes. What the *reader* sees is
        :attr:`licence_fa`.
        """

    @property
    def licence_fa(self) -> str:
        """The same statement, for the reader, in Persian.

        The corpus screen printed :attr:`licence` — an English sentence — under
        a Persian heading, which is the thing FRONTEND.md says never happens.
        A source that has not written its Persian yet falls back to the
        English, because a missing sentence about copyright is worse than one
        in the wrong language.
        """
        return self.licence

    @abstractmethod
    def documents(self) -> Iterator[Document]:
        """Yield the corpus, one indexable unit at a time.

        A generator, not a list: some sources are far larger than memory.
        """

    def describe(self) -> str:
        """One line naming the source and its licence, for the ingest log."""
        return f"{self.source_id} ({self.licence})"


def check_source_id(source_id: str) -> None:
    """Raise unless ``source_id`` follows the convention."""
    if not _SOURCE_ID_PATTERN.match(source_id):
        raise ValueError(
            f"source_id {source_id!r} must be lower-case letters, digits and "
            f"underscores"
        )
