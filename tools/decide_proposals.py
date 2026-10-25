"""Record what a reviewer did with a proposal, so a refusal stops coming back.

    python tools/decide_proposals.py --list
    python tools/decide_proposals.py --accept 12 --by 1 --reason "..."
    python tools/decide_proposals.py --refuse 13 --by 1 --reason "..."

**Why this exists.** `tools/export_proposals.py` writes the proposals into the
YAML and the review is ``git diff rules/``. Accepting is committing; refusing
is ``git checkout rules/`` — and that leaves no trace at all. So the proposal
was still in the table, the next export applied it again, and the reviewer
refused it again. The loop did not converge. That is S5.

**The decision is a row, never a stamp on the proposal.** The feedback table
records a verdict as a row and `linguist_rulings` records a reversal as a row
saying it reverses; this is the same shape, and it is the only one of the three
candidates that keeps the history whole. The table is append-only behind a
trigger for the same reason those are.

**Deciding twice is allowed.** A proposal refused under one pack version may
deserve a different answer under another, and the latest row is the one the
export reads — so a later `--accept` genuinely reopens it.
"""

from __future__ import annotations

import argparse
import sys

from murfulu.db import proposals as store
from murfulu.db.session import session_scope
from murfulu.rules.pack import loaded


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="show every proposal")
    parser.add_argument("--accept", type=int, metavar="ID")
    parser.add_argument("--refuse", type=int, metavar="ID")
    parser.add_argument("--by", type=int, help="the reviewer's account id")
    parser.add_argument("--reason", help="why, in Persian")
    return parser.parse_args(argv)


def _show() -> int:
    """Every proposal with the decision that stands, if any."""
    with session_scope() as session:
        settled = store.latest_decisions(session)
        rows = store.all_proposals(session)
        if not rows:
            print("no proposals")
            return 0
        for row in rows:
            found = settled.get(row.id)
            mark = f"{found.decision:<9}" if found else "open     "
            print(f"  {row.id:>5}  {mark}  {row.rule_id:<8} {row.field}")
        print(f"\n{len(rows)} proposals, {len(rows) - len(settled)} still open")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Record one decision, or list what is outstanding."""
    arguments = _parse(argv)
    if arguments.list or not (arguments.accept or arguments.refuse):
        return _show()

    if arguments.accept and arguments.refuse:
        print("give --accept or --refuse, not both")
        return 1
    # A refusal nobody explained teaches the proposer nothing, and the next
    # reviewer cannot tell a considered no from a lost one. The database
    # refuses it too; failing here says so in a sentence instead of a
    # constraint name.
    if not (arguments.reason or "").strip():
        print("--reason is required: a decision nobody explained cannot be read")
        return 1
    if not arguments.by:
        print("--by is required: a decision without an author has no weight")
        return 1

    decision = "accepted" if arguments.accept else "refused"
    proposal_id = arguments.accept or arguments.refuse
    with session_scope() as session:
        store.decide(
            session,
            proposal_id=proposal_id,
            decided_by=arguments.by,
            decision=decision,
            reason=arguments.reason,
            rule_pack_version=loaded().version,
        )
    print(f"recorded       proposal {proposal_id} {decision}")
    print("               the next export will skip it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
