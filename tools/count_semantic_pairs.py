"""Count what each rule gives a semantic model to learn from.

    python tools/count_semantic_pairs.py < build/derivations-v1.jsonl

PLAN 5.6 asks for semantic plausibility, and the method in
[RESEARCH_SCORING.md](../docs/RESEARCH_SCORING.md) — FRACSS — trains one
matrix per affix on attested **base → derived** pairs. Whether that is
possible here is not a question about which embedding model to choose. It is a
question about how many pairs the data holds, and this counts them.

Two things decide it, and they are counted separately.

**How many pairs a rule has.** A matrix fitted on eight pairs is not a
measurement of anything.

**What the base is.** This grammar builds most words on a *kārbon* — a verb
stem — which is a bound form. A distributional vector exists only for
something that occurs in text, so the base type is not a detail here: it is
the difference between a method that has an input and one that does not.

Only single-step derivations count. A two-step chain is evidence about the
chain, not about either affix alone.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from typing import Any

#: Levels at which the corpus has the word. A form nobody ever wrote teaches a
#: semantic model nothing — it is the thing being judged.
ATTESTED = frozenset({"reading", "spelling"})

#: Base types that are bound stems rather than free words.
STEM_TYPES = frozenset({"karbon_yek", "karbon_do"})

#: The thresholds worth reporting. The lowest is where a fitted matrix stops
#: being a measurement; the highest is where one is comfortable.
THRESHOLDS = (200, 100, 50, 20, 10, 5, 1)


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=20, help="how many rules to list")
    return parser.parse_args(argv)


class Counted:
    """Pairs per rule, and what the bases of those pairs are."""

    def __init__(self) -> None:
        self.pairs: dict[str, set[tuple[str, str]]] = defaultdict(set)
        self.confirmed: dict[str, set[tuple[str, str]]] = defaultdict(set)
        self.base_types: dict[str, Counter[str]] = defaultdict(Counter)
        self.records = 0

    def add(self, record: dict[str, Any]) -> None:
        """Take one derivation record into the count."""
        self.records += 1
        level = record.get("attestation")
        if level not in ATTESTED:
            return
        derived = record.get("form_latin") or ""
        for path in record.get("paths", []):
            rules = path.get("rule_ids") or []
            base = path.get("base_form") or ""
            if len(rules) != 1 or not base or not derived:
                continue
            rule = rules[0]
            self.pairs[rule].add((base, derived))
            self.base_types[rule][path.get("base_type") or "unknown"] += 1
            if level == "reading":
                self.confirmed[rule].add((base, derived))

    def ranked(self) -> list[tuple[str, int, int]]:
        """Rules by how much material they give, most first."""
        return sorted(
            (
                (rule, len(found), len(self.confirmed[rule]))
                for rule, found in self.pairs.items()
            ),
            key=lambda row: -row[1],
        )

    def bases(self) -> Counter[str]:
        """What the bases are, across every pair of every rule."""
        overall: Counter[str] = Counter()
        for kinds in self.base_types.values():
            overall.update(kinds)
        return overall


def main(argv: list[str] | None = None) -> int:
    """Read the derivation dump on standard input and report."""
    arguments = _parse(argv)
    counted = Counted()
    for line in sys.stdin:
        counted.add(json.loads(line))

    rows = counted.ranked()
    print(f"records read       {counted.records:,}")
    print(f"rules with a pair  {len(rows)}")
    for threshold in THRESHOLDS:
        any_level = sum(1 for _, pairs, _ in rows if pairs >= threshold)
        sure = sum(1 for _, _, ok in rows if ok >= threshold)
        print(
            f"  >= {threshold:>3} pairs    {any_level:>4} rules"
            f"   ({sure} of them on confirmed readings alone)"
        )

    print(f"\nthe {arguments.top} rules with the most material")
    print(f"{'rule':<8}{'pairs':>8}{'confirmed':>11}  bases")
    for rule, pairs, sure in rows[: arguments.top]:
        kinds = ", ".join(
            f"{kind} {number}"
            for kind, number in counted.base_types[rule].most_common(3)
        )
        print(f"{rule:<8}{pairs:>8}{sure:>11}  {kinds}")

    bases = counted.bases()
    total = sum(bases.values())
    bound = sum(number for kind, number in bases.items() if kind in STEM_TYPES)
    print("\nwhat the bases are")
    for kind, number in bases.most_common():
        print(f"  {kind:<16} {number:,}")
    if total:
        # The number that decides whether a base→derived model has an input.
        print(f"\nbound stems        {bound:,} of {total:,} ({bound / total:.1%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
