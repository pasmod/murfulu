"""Load the YAML rule pack into the authored store.

    docker compose run --rm api python tools/sync_rules.py

The YAML in git stays the source of truth. This copies it in so the app can
join a rule to the feedback left on it, and so a proposed change has something
to be a change *to*.

**This was missing.** :mod:`murfulu.db.rulesync` was written with task 6.0 and
nothing outside the tests ever called it, so the live ``rules`` table was
empty — and the first real proposal (task 8.1) failed on the foreign key that
points at it. Found by running it against the containers rather than by
reading the code.

It never deletes. A rule id is permanent, so an id in the database the pack no
longer mentions is a fault to look at, not a row to tidy away; it is reported
and left alone.
"""

from __future__ import annotations

import argparse
import sys

from murfulu.db.rulesync import sync
from murfulu.db.session import session_scope


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="say what would be written and write nothing",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Load the pack and print what was written."""
    arguments = _parse(argv)
    with session_scope() as session:
        report = sync(session)
        if arguments.check:
            session.rollback()
            print(f"would load      {report}")
            return 0
    print(f"loaded          {report}")
    for unknown in report.unknown_ids:
        print(f"  in the database but not in the pack: {unknown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
