r"""Export the expert feedback as a dataset.

    docker compose run --rm api python tools/export_feedback.py --into build/feedback
    docker compose run --rm api python tools/export_feedback.py \
        --into build/karbon --owner karbon

Two files come out: ``feedback.jsonl``, one record per line, and ``README.md``
describing what the records are, what is in them and what is deliberately not.

**This set is the gold standard** (``docs/REVIEW.md``). karbon's reviewed
entries validate the transcription of words that already exist and contain no
generated word at all, so there is nothing else to fit the scoring weights
against — and the NGI application promises open outputs.

``--owner karbon`` gives the share that belongs upstream: feedback about the
lexicon and about stem derivations, which we mount read-only and cannot fix.

**No account names leave.** The author is a stable pseudonym, which is all
inter-rater agreement needs. And **the code's licence stops here**: Murfulu is
Apache-2.0, these records are not, and the manifest names the licence only to
say where it ends. They are judgements experts made about the language, not
anything this project wrote.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from murfulu.db.dataset import build
from murfulu.db.models.review import OWNERS, ExpertFeedback
from murfulu.db.session import session_scope

DATA_FILE = "feedback.jsonl"
MANIFEST_FILE = "README.md"


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--into", type=Path, required=True, help="where to write")
    parser.add_argument(
        "--owner",
        choices=sorted(OWNERS),
        help="only what one side can act on; karbon's share goes upstream",
    )
    parser.add_argument("--category", help="linguistic, data or bug", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Write the dataset and say what it holds."""
    arguments = _parse(argv)

    statement = select(ExpertFeedback).order_by(ExpertFeedback.id)
    if arguments.owner:
        statement = statement.where(ExpertFeedback.owner == arguments.owner)
    if arguments.category:
        statement = statement.where(ExpertFeedback.category == arguments.category)

    with session_scope() as session:
        rows = list(session.scalars(statement))
        # One query for the roles rather than one per record: the role is a
        # fact about the record's weight, not about the person.
        dataset = build(rows, exported_on=datetime.now(UTC).date().isoformat())

    print(f"records        {len(dataset)}")
    if not len(dataset):
        # Not an error. An empty evaluation set is the state this project is
        # in until the reviewers have used the app, and saying so beats
        # writing an empty file that looks like a finished one.
        print("nothing        no feedback has been left yet; wrote nothing")
        return 0

    arguments.into.mkdir(parents=True, exist_ok=True)
    data = arguments.into / DATA_FILE
    data.write_text("\n".join(dataset.lines()) + "\n", encoding="utf-8")
    manifest = arguments.into / MANIFEST_FILE
    manifest.write_text(dataset.manifest(), encoding="utf-8")

    print(f"wrote          {data}")
    print(f"wrote          {manifest}")
    for name in ("category", "owner", "verdict"):
        counted = dataset.counted(name)
        counted.pop("None", None)
        if counted:
            listed = ", ".join(f"{key} {value}" for key, value in counted.items())
            print(f"{name:<14} {listed}")
    print("licence        the code is Apache-2.0; these records are not")
    return 0


if __name__ == "__main__":
    sys.exit(main())
