"""Which corpora exist, and which build of them a figure came from.

Every count in this system is true for one corpus version only. The counts
themselves live in Elasticsearch and are rebuilt on every run; what is
recorded here is the authored half — a source's licence, and what went into
each version — because that is what nobody can recover by re-running a job.

The sources of a version are a table of their own rather than a list of names,
so a version cannot claim a source that was never registered.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from murfulu.db.base import Base, created_at_column

#: A source id is the prefix on every document it yields: ``ganjoor:…``.
_ID_LENGTH = 64


class Source(Base):
    """One corpus source, with the terms it may be used under."""

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(_ID_LENGTH), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    #: Spelled the way the rest of the project spells it. An adapter that has
    #: not settled its terms says so in words rather than leaving the field
    #: empty, which would read as "no restrictions" — and one whose source
    #: declines to warrant anything says *that*, which is Ganjoor's case.
    licence: Mapped[str] = mapped_column(Text, nullable=False)

    url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    registered_at: Mapped[datetime] = created_at_column()


class CorpusVersion(Base):
    """One build of the corpus: what was ingested, and how much of it."""

    __tablename__ = "corpus_versions"

    #: The suffix on the concrete indices — ``word_types-v3`` is version
    #: ``v3``. Same token, so a figure can be traced from the app to the index.
    version: Mapped[str] = mapped_column(String(_ID_LENGTH), primary_key=True)

    document_count: Mapped[int | None] = mapped_column(Integer)
    word_type_count: Mapped[int | None] = mapped_column(Integer)

    #: The lexicon and the rule pack that produced it. A derivation count
    #: means nothing without both.
    lexicon_snapshot_id: Mapped[str | None] = mapped_column(Text)
    rule_pack_version: Mapped[str | None] = mapped_column(String(32))

    notes: Mapped[str | None] = mapped_column(Text)
    built_at: Mapped[datetime] = created_at_column()


class CorpusVersionSource(Base):
    """Which sources went into which version."""

    __tablename__ = "corpus_version_sources"

    version: Mapped[str] = mapped_column(
        String(_ID_LENGTH),
        ForeignKey("corpus_versions.version", ondelete="CASCADE"),
        primary_key=True,
    )
    source_id: Mapped[str] = mapped_column(
        String(_ID_LENGTH),
        ForeignKey("sources.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    document_count: Mapped[int | None] = mapped_column(Integer)
