"""Copy the rule pack into karbon, so the two do not drift.

    python tools/mirror_to_karbon.py --check --into ~/Code/karbon/data/murfulu-rules
    python tools/mirror_to_karbon.py --into ~/Code/karbon/data/murfulu-rules

``docs/DECISIONS.md``: **one master, one mirror.** The YAML in this repository
is the master; karbon carries a copy, updated by pull request. Two editable
copies would be two rule sets within a month.

**The mirror is byte-identical, plus a manifest.** Nothing is transformed, so
"is the copy current?" is a comparison anyone can run in either repository
without loading anything. ``--check`` is that comparison and is what a job in
either repository would run; it exits 1 when the copy is stale.

**It does not open a pull request, and it never will from here.** Sending a
change to somebody else's repository is the project lead's to do — PLAN and
CLAUDE.md both say never unasked. What this prints instead is what the pull
request would say.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from murfulu.rules import mirror
from murfulu.rules.pack import load as load_pack


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-d", "--directory", type=Path, default=Path("rules"))
    parser.add_argument(
        "--into",
        type=Path,
        required=True,
        help="the mirror directory inside the karbon checkout",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare only; exit 1 if the copy is stale",
    )
    return parser.parse_args(argv)


def source_commit(directory: Path) -> str:
    """The commit the pack is being copied from, if this is a checkout."""
    found = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=directory,
        capture_output=True,
        text=True,
        check=False,
    )
    return found.stdout.strip() if found.returncode == 0 else ""


def main(argv: list[str] | None = None) -> int:
    """Compare or write the mirror, and say what a pull request would carry."""
    arguments = _parse(argv)
    pack = load_pack(arguments.directory)
    built = mirror.build(
        arguments.directory, pack.version, source_commit(arguments.directory)
    )
    print(f"rule pack      {built.rule_pack_version}, {len(built.files)} files")
    print(f"mirror         {arguments.into}")

    differences = mirror.compare(built, arguments.into)
    if not differences:
        print("state          current — nothing to send")
        return 0

    for difference in differences:
        print(f"  {difference}")

    if arguments.check:
        print(f"state          stale: {len(differences)} files differ")
        return 1

    arguments.into.mkdir(parents=True, exist_ok=True)
    for name, text in built.as_written().items():
        (arguments.into / name).write_text(text, encoding="utf-8")
    print(f"wrote          {len(built.files) + 1} files")
    print(
        "next           this opens no pull request. Review the diff in the "
        "karbon checkout and send it on the project lead's word."
    )
    print(f"               title: mirror murfulu rule pack {built.rule_pack_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
