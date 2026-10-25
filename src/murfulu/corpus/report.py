"""What one ingest measured about one corpus version.

The ingest already counts everything the corpus screen needs — documents,
running words, distinct spellings, how many of them the lexicon can read — and
until now it **printed those numbers and threw them away**. This module makes
them an artefact, the same way ``rule_productivity-<version>.json`` is one.

**The figures are written by the batch job, never recomputed on request.**
That is not only about speed. Counting them from the search index gives the
wrong answer twice over, and both ways look right:

``word_types`` holds one document per *reading*, so summing ``total_count``
counts a spelling with two readings twice — 29,288,852 instead of the
25,497,189 words the corpus actually has. And Elasticsearch's ``cardinality``
aggregation is an estimate, so "how many distinct spellings" comes back
409,500 against a true 409,916: close enough to pass for exact, and it is not.

Both numbers are exact here because the pass that produced them held the whole
corpus in memory and counted it.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from murfulu.corpus import ganjoor
from murfulu.corpus.adapter import SourceAdapter
from murfulu.corpus.link import LinkResult
from murfulu.corpus.wordtypes import Corpus

#: Where the ingest's measurements live. Never a literal in the code.
PATH_VARIABLE = "MURFULU_CORPUS_REPORT_PATH"

#: How many unlinked spellings the report carries. The whole list is a
#: separate export — 393,202 of them — and no screen shows that many.
TOP_GAPS = 200


@dataclass(frozen=True)
class Gap:
    """One corpus spelling the lexicon has no entry for.

    Not an error and not a rare word: the biggest ones are و, ز and بر —
    grammar words a dictionary of headwords was never going to list. The pile
    is a deliverable in its own right (docs/FRONTEND.md §7), so it is named
    rather than summarised away.
    """

    spelling_fa: str
    total_count: int
    doc_count: int
    author_count: int


@dataclass(frozen=True)
class CorpusReport:
    """One ingest run, as the app reads it back."""

    corpus_version: str = ""
    #: What to type: the identifier `source:ganjoor` is written with.
    source_id: str = ""
    #: What to read: the source's name in Persian. Empty on a report written
    #: before 2026-08-18, and the screen falls back to `source_id` when it is.
    source_name_fa: str = ""
    #: English, for the log and for NOTICE.
    licence: str = ""
    #: The same statement for the reader. Empty on a report written before
    #: 2026-08-17, and the screen falls back to `licence` when it is.
    licence_fa: str = ""
    #: When the ingest ran. A count is only true for the corpus that produced
    #: it, and only as of the day it was counted.
    built_at: str = ""
    lexicon_snapshot_id: str = ""

    documents: int = 0
    #: Words of running text, counted once per occurrence.
    tokens: int = 0
    #: Distinct spellings. The corpus has no vowels, so this is spellings and
    #: not words.
    spellings: int = 0
    #: One per *reading*, so a spelling the lexicon reads two ways is two.
    word_types: int = 0

    documents_without_author: int = 0
    documents_without_century: int = 0

    spellings_linked: int = 0
    tokens_linked: int = 0
    #: Spellings the lexicon reads more than one way. The corpus cannot tell
    #: مرد the man from مرد the dead, so both readings are kept.
    ambiguous_spellings: int = 0

    #: Poet slugs the century table does not cover.
    poets_without_a_century: list[str] = field(default_factory=list)
    #: Century-table keys naming a poet this corpus does not have. They date
    #: nothing and look exactly like entries that work.
    centuries_without_a_poet: list[str] = field(default_factory=list)

    biggest_gaps: list[Gap] = field(default_factory=list)

    @property
    def measured(self) -> bool:
        """False when no ingest has been reported here."""
        return bool(self.corpus_version)

    @property
    def type_share(self) -> float:
        """Share of distinct spellings the lexicon can read."""
        return self.spellings_linked / self.spellings if self.spellings else 0.0

    @property
    def token_share(self) -> float:
        """Share of running text the lexicon can read.

        Far higher than the type share, and the two answer different
        questions: type coverage is how much of the vocabulary we can read,
        token coverage is how much of the **text** we can read.
        """
        return self.tokens_linked / self.tokens if self.tokens else 0.0

    def as_dict(self) -> dict[str, Any]:
        """The stored shape, with the two shares computed rather than kept."""
        return {
            **asdict(self),
            "spellings_unlinked": self.spellings - self.spellings_linked,
            "type_share": self.type_share,
            "token_share": self.token_share,
        }


def build(
    adapter: SourceAdapter,
    corpus: Corpus,
    linked: LinkResult,
    corpus_version: str,
    top_gaps: int = TOP_GAPS,
    now: datetime | None = None,
) -> CorpusReport:
    """Turn what the ingest already holds in memory into a report."""
    poets_missing = getattr(adapter, "poets_without_a_century", None)
    centuries_stale = getattr(adapter, "centuries_without_a_poet", None)
    return CorpusReport(
        corpus_version=corpus_version,
        source_id=adapter.source_id,
        licence=adapter.licence,
        licence_fa=adapter.licence_fa,
        built_at=(now or datetime.now(UTC)).isoformat(timespec="seconds"),
        lexicon_snapshot_id=linked.lexicon_snapshot_id,
        documents=corpus.document_count,
        tokens=corpus.token_count,
        spellings=len(corpus),
        word_types=len(linked.linked),
        documents_without_author=corpus.documents_without_author,
        documents_without_century=corpus.documents_without_century,
        spellings_linked=linked.coverage.types_linked,
        tokens_linked=linked.coverage.tokens_linked,
        ambiguous_spellings=linked.coverage.ambiguous_types,
        poets_without_a_century=list(poets_missing()) if poets_missing else [],
        centuries_without_a_poet=list(centuries_stale()) if centuries_stale else [],
        biggest_gaps=[
            Gap(
                spelling_fa=item.spelling_fa,
                total_count=item.word.total_count,
                doc_count=item.word.doc_count,
                author_count=item.word.author_count,
            )
            for item in linked.biggest_gaps(top_gaps)
        ],
    )


def write(report: CorpusReport, destination: Path) -> Path:
    """Store one report as JSON, next to the productivity file."""
    destination.write_text(
        json.dumps(report.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


#: The reader's licence sentence by source, for reports written before the
#: field existed. A licence is a fact about the source and not something an
#: ingest measured, so filling it in from here is reading it rather than
#: inventing it — and without this the corpus screen shows the English to every
#: reader until the next ingest, which is hours of work for one sentence.
LICENCE_FA_BY_SOURCE = {ganjoor.SOURCE_ID: ganjoor.LICENCE_FA}

#: The source's Persian name, on the same terms and for the same reason.
NAME_FA_BY_SOURCE = {ganjoor.SOURCE_ID: ganjoor.NAME_FA}


def from_document(document: dict[str, Any]) -> CorpusReport:
    """Read a stored report back, ignoring the fields it computes."""
    known = {f for f in CorpusReport.__dataclass_fields__}
    fields = {key: value for key, value in document.items() if key in known}
    if not fields.get("licence_fa"):
        fields["licence_fa"] = LICENCE_FA_BY_SOURCE.get(fields.get("source_id", ""), "")
    if not fields.get("source_name_fa"):
        fields["source_name_fa"] = NAME_FA_BY_SOURCE.get(
            fields.get("source_id", ""), ""
        )
    fields["biggest_gaps"] = [
        Gap(
            spelling_fa=row["spelling_fa"],
            total_count=row.get("total_count", 0),
            doc_count=row.get("doc_count", 0),
            author_count=row.get("author_count", 0),
        )
        for row in document.get("biggest_gaps", [])
    ]
    return CorpusReport(**fields)


def path() -> Path | None:
    """The configured file, if there is one and it exists."""
    configured = os.environ.get(PATH_VARIABLE)
    if not configured:
        return None
    found = Path(configured).expanduser()
    return found if found.is_file() else None


@lru_cache(maxsize=1)
def loaded() -> CorpusReport:
    """The stored report, read once.

    An empty report is a legitimate answer: a machine that has never run an
    ingest has nothing to report, and the screen says so rather than showing
    zeros that look like measurements.
    """
    found = path()
    if found is None:
        return CorpusReport()
    return from_document(json.loads(found.read_text(encoding="utf-8")))
