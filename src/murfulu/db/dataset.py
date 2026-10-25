"""The feedback set, shaped for release.

``docs/REVIEW.md``: this store is the gold standard. karbon's reviewed entries
validate the transcription of words that already **exist** and contain no
generated word at all, so there is nothing else to fit the scoring weights
against, and the NGI application promises open outputs. It has to leave the
system as a dataset.

Three decisions about what leaves with it:

**The author is a stable pseudonym, never the account.** Usernames are handles
by policy, but an export is a different act from a database row: inter-rater
agreement needs to know two verdicts came from different people and needs
nothing else. So ``author-2``, plus the role, because *only an expert may
grade a word* is a fact about the record's weight.

**The record says which corpus version and which rule pack it judged.** A
verdict stays valid across a rebuild — it judged the form, not the count — but
what was on screen beside it is true for one version only, and a dataset that
lost that would be a dataset of unfalsifiable opinions.

**The code's licence does not reach it, and the manifest says so.** Murfulu is
Apache-2.0 as of 2026-08-17; these records are not. They are judgements experts
made about the language rather than anything this project wrote, Apache is a
licence for software, and they were not given to us to hand on. Saying "the
repository is Apache" and letting a reader draw the obvious conclusion would be
the same fault as guessing a licence, one step further along.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any

from murfulu.db.models.review import ExpertFeedback

#: What one exported record holds, in order. Written down because it is the
#: dataset's schema and a reader outside this repository needs it.
FIELDS = (
    "id",
    "created_at",
    "author",
    "category",
    "target_type",
    "target_id",
    "verdict",
    "note",
    "context",
    "owner",
    "corpus_version",
)

#: What each field means, for the manifest. In English: a dataset is read by
#: people who do not read this repository.
MEANINGS = {
    "id": "stable identifier of the record",
    "created_at": "when it was left, UTC",
    "author": "stable pseudonym; never an account name. **Records made from "
    "2026-08-17 all carry one author**: the site moved to a single account "
    "with no roles, so inter-rater agreement cannot be measured across them. "
    "Earlier records carry the author who made them and remain comparable",
    "category": "linguistic, data or bug",
    "target_type": "what was judged: a derivation, a rule, a meaning, a "
    "statistic, a lexicon entry, a stem derivation, or the app",
    "target_id": "the word, rule or figure. Null only for the app itself",
    "verdict": "good, possible, wrong or unsure. Set for linguistic records "
    "and for no others",
    "note": "free text, in Persian",
    "context": "what was on screen, as data: the form, the rule chain, the "
    "evidence, the screen and the query",
    "owner": "murfulu, or karbon where the record is about karbon's data",
    "corpus_version": "which corpus the figures beside it came from",
}


def pseudonym(author_id: int) -> str:
    """A stable label for one author, carrying nothing about who they are."""
    return f"author-{author_id}"


def as_record(row: ExpertFeedback) -> dict[str, Any]:
    """One feedback row as the dataset holds it.

    **The role went with the roles.** The set used to carry `author_role`
    beside the pseudonym, because only an expert could leave a verdict and a
    reader of the dataset needed to know which records those were. There is one
    account and no roles as of 2026-08-17, so the column would have been a
    constant — and a constant in a research dataset reads as a distinction that
    was measured.
    """
    return {
        "id": row.id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "author": pseudonym(row.author_id),
        "category": row.category,
        "target_type": row.target_type,
        "target_id": row.target_id,
        "verdict": row.verdict,
        "note": row.note,
        "context": row.context,
        "owner": row.owner,
        "corpus_version": row.corpus_version,
    }


@dataclass
class Dataset:
    """The exported records, and what they add up to."""

    records: list[dict[str, Any]] = field(default_factory=list)
    #: The date the export ran, as the caller supplies it. Not taken from the
    #: clock here, so the same rows always produce the same file.
    exported_on: str = ""

    def __len__(self) -> int:
        """How many records the dataset holds."""
        return len(self.records)

    def counted(self, name: str) -> dict[str, int]:
        """How many records fall under each value of one field."""
        found: dict[str, int] = {}
        for record in self.records:
            key = str(record.get(name))
            found[key] = found.get(key, 0) + 1
        return dict(sorted(found.items()))

    def lines(self) -> Iterator[str]:
        """The dataset as JSON Lines: one record per line, streamable."""
        for record in self.records:
            yield json.dumps(record, ensure_ascii=False, sort_keys=False)

    def manifest(self) -> str:
        """What the dataset is, what is in it, and what it does not claim."""
        graded = self.counted("verdict")
        graded.pop("None", None)
        lines = [
            "# murfulu expert feedback",
            "",
            "Judgements left on generated words, rules, composed meanings and "
            "corpus figures by the reviewers using the application. It is the "
            "evaluation set the scoring weights are fitted against: there is "
            "no other set of *generated* words anyone has graded.",
            "",
            f"- records: {len(self)}",
            f"- exported: {self.exported_on or 'unknown'}",
            "- format: JSON Lines, one record per line, UTF-8",
            "",
            "## Licence",
            "",
            "**The code's licence does not reach this file.** Murfulu is "
            "Apache-2.0 as of 2026-08-17; these records are not. They are "
            "judgements experts made about the language, they are not code, "
            "and they were not given to this project to hand on. Ask before "
            "redistributing.",
            "",
            "## What is in it",
            "",
            "| by | counts |",
            "|---|---|",
            f"| category | {_counted(self.counted('category'))} |",
            f"| target | {_counted(self.counted('target_type'))} |",
            f"| verdict | {_counted(graded) or 'none graded'} |",
            f"| owner | {_counted(self.counted('owner'))} |",
            f"| author | {_counted(self.counted('author'))} |",
            "",
            "## Fields",
            "",
            "| field | meaning |",
            "|---|---|",
        ]
        lines += [f"| `{name}` | {MEANINGS[name]} |" for name in FIELDS]
        lines += [
            "",
            "## What is not in it",
            "",
            "**No account names.** The author is a stable pseudonym, so two "
            "records can be told apart without naming anybody.",
            "",
            "**No screenshots.** The application captures none — see "
            "docs/OPEN_QUESTIONS S4. The structured context is the reusable "
            "half and it is here in full.",
            "",
            "**Records marked `owner: karbon`** are about the lexicon, which "
            "this project mounts read-only and cannot change. They are "
            "recorded here and sent upstream, not fixed here.",
            "",
        ]
        return "\n".join(lines)


def _counted(counts: dict[str, int]) -> str:
    """A counts dictionary as one readable cell."""
    return ", ".join(f"{name} {number}" for name, number in counts.items())


def build(
    rows: Iterable[ExpertFeedback],
    exported_on: str = "",
) -> Dataset:
    """Shape feedback rows into the dataset, oldest first."""
    return Dataset(
        records=[as_record(row) for row in sorted(rows, key=lambda one: one.id)],
        exported_on=exported_on,
    )
