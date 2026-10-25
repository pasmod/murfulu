"""Measure how productive each rule is, from a finished precompute.

    python tools/run_productivity.py --from build/derivations.jsonl \
        --out build/rule_productivity-v1.json

Reads the records the precompute wrote and rolls them up into one row per
rule: how many words the rule built, how many of them the corpus has, the
hapax counts and Baayen's P, and the share of built forms anyone ever wrote.

The output file name carries the corpus version, because none of these
numbers means anything without it.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from pathlib import Path

from murfulu.rules.pack import loaded
from murfulu.scoring.productivity import RuleStatistics, measure
from murfulu.scoring.reload import read_jsonl


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from",
        dest="source",
        type=Path,
        required=True,
        help="the JSON-lines file tools/run_precompute.py wrote",
    )
    parser.add_argument("--out", type=Path, help="where to write the rule rows")
    parser.add_argument("--top", type=int, default=15, help="how many rules to show")
    return parser.parse_args(argv)


def _rows(statistics: RuleStatistics) -> Iterator[dict[str, object]]:
    """One row per rule, with the band and the disagreement written in.

    The band is a tercile of the measured distribution, so it can only be
    worked out where the whole distribution is — here. Leaving the app to
    recompute it would be a second implementation of the same judgement.
    """
    bands = statistics.bands()
    disagreeing = {one.rule_id: one for one in statistics.disagreements()}
    for rule_id in sorted(statistics.by_rule):
        row = statistics.by_rule[rule_id].as_document()
        row["band"] = bands.get(rule_id)
        found = disagreeing.get(rule_id)
        row["disagrees_with_strength"] = found is not None
        row["expected_band"] = found.expected_band if found else None
        yield row


def main(argv: list[str] | None = None) -> int:
    """Roll the precompute up and print the report."""
    arguments = _parse(argv)
    pack = loaded()
    statistics = measure(pack, read_jsonl(arguments.source))

    if arguments.out:
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(
            json.dumps(
                {
                    "corpus_version": statistics.corpus_version,
                    "rules": list(_rows(statistics)),
                },
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )

    print(statistics.summary())
    print()
    print(f"{'rule':8} {'built':>9} {'attested':>9} {'P':>8} {'rate':>8} {'echo':>7}")
    for row in statistics.most_productive(arguments.top):
        measured_p = row.potential_p
        printed = f"{measured_p:.4f}" if measured_p is not None else "—"
        print(
            f"{row.rule_id:8} {row.types_built:9,} {row.types_attested:9,} "
            f"{printed:>8} {row.realisation_rate or 0:8.4f} "
            f"{row.echo_share or 0:7.2f}"
        )

    print()
    for disagreement in statistics.disagreements():
        print(
            f"{disagreement.rule_id}: authored {disagreement.authored_strength} "
            f"expects the {disagreement.expected_band} band, measured "
            f"{disagreement.measured_band} ({disagreement.realisation_rate:.4f})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
