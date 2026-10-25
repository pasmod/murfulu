"""Write the experts' proposed changes back into the rule pack YAML.

    docker compose run --rm api python tools/export_proposals.py --dry-run
    docker compose run --rm api python tools/export_proposals.py

**The review is the git diff.** Nothing here accepts anything: it applies the
proposals to the YAML, writes the files, and prints what it did. Then
``git diff rules/`` is the change, read by whoever reviews it, and
``git checkout rules/`` is the rejection.

That works because the pack round-trips byte for byte — measured on all four
tables — so an applied proposal shows up as the one line it changed and
nothing else. The dump settings here must therefore stay exactly the ones
``tools/build_rule_pack.py`` uses.

**A proposal written against a rule that has since changed is skipped**, not
applied. Applying it would silently revert whoever changed it. Those are
printed with what the pack actually says, so the disagreement is visible.

**And a proposal somebody has already decided on is skipped too.** Refusing
used to leave no trace — ``git checkout rules/`` restores the file and says
nothing — so the next export applied the proposal again and the reviewer
refused it again. The loop did not converge. That was S5, and it is closed by
recording the decision as a row: ``tools/decide_proposals.py``. Pass ``--all``
to apply decided ones anyway, which is a deliberate override and not a default.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from murfulu.db import proposals as store
from murfulu.db.session import session_scope
from murfulu.rules.proposals import apply

#: The tables the pack is written across. Glide rules are not proposed
#: against — they are a closed table of seventeen vowel meetings.
TABLES = ("verb_stems", "nominals", "stem_rules")


def _dumped(table: dict[str, Any]) -> str:
    """One table as YAML, with exactly the settings the builder writes with.

    A different width or sort order would reformat every file and bury the one
    changed line in a diff of two thousand — and the whole review method is
    that diff.
    """
    return yaml.safe_dump(table, allow_unicode=True, sort_keys=False, width=100)


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-d", "--directory", type=Path, default=Path("rules"))
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="say what would change and write nothing",
    )
    parser.add_argument("--rule", help="only proposals about this rule id")
    parser.add_argument(
        "--all",
        action="store_true",
        help="apply decided proposals too — normally they are skipped",
    )
    return parser.parse_args(argv)


def read_tables(directory: Path) -> dict[str, dict[str, Any]]:
    """Load every rule table the pack is written across."""
    found: dict[str, dict[str, Any]] = {}
    for name in TABLES:
        path = directory / f"{name}.yaml"
        if path.is_file():
            found[name] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return found


def write_table(directory: Path, name: str, table: dict[str, Any]) -> Path:
    """Write one table back, with the settings that keep the diff minimal."""
    path = directory / f"{name}.yaml"
    path.write_text(_dumped(table), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    """Apply the proposals and print what happened to each."""
    arguments = _parse(argv)
    tables = read_tables(arguments.directory)
    if not tables:
        print(f"no rule tables in {arguments.directory}")
        return 1

    with session_scope() as session:
        every = store.all_proposals(session, arguments.rule)
        open_ones = every if arguments.all else store.undecided(session, arguments.rule)
        rows = [store.as_dict(row) for row in open_ones]
        settled = len(every) - len(open_ones)
    decided = f", {settled} already decided" if settled else ""
    print(f"proposals      {len(rows)} open{decided}")
    if not rows:
        return 0

    result = apply(tables, rows)
    for outcome in result.outcomes:
        print(f"  {outcome}")
    print(f"result         {result.summary()}")

    changed = result.changed_tables
    if not changed:
        print("files          nothing to write")
        return 0
    if arguments.dry_run:
        print(f"files          would rewrite {', '.join(changed)} (dry run)")
        return 0

    for name in changed:
        path = write_table(arguments.directory, name, result.tables[name])
        print(f"wrote          {path}")
    print("review         git diff rules/ — and git checkout rules/ to refuse")
    print("record         then say so, or the next export applies it again:")
    print("               tools/decide_proposals.py --refuse <id> --reason ...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
