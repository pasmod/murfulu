"""Measure how the semantic scores are spread, so one of them can be placed.

    python tools/measure_typicality_spread.py --from build/derivations-v7.jsonl \
        --out data/typicality-v7.json

**Why.** The score is a cosine and on this corpus it never leaves the middle:
every scored form falls between 0.554 and 0.914 and the middle half between
0.800 and 0.852. Shown as a bare percentage, 84% reads as a good mark out of
a hundred and is actually the median. The project lead read one off the screen
and asked what it meant, which is the answer: on its own, very little.

So the app shows a band instead — the same remedy `tools/run_productivity.py`
applies to rule productivity, and for the same reason. **The band can only be
worked out where the whole distribution is**, which is here and never a page
load.

The output carries the corpus version, because a spread measured on one
version says nothing about another.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from murfulu.scoring.reload import read_jsonl
from murfulu.scoring.spread import BANDS, CUTS

#: The field the precompute writes the score into.
FIELD = "semantic_typicality"


def scores(source: Path) -> list[float]:
    """Every semantic score the run wrote, in no particular order."""
    found = []
    for record in read_jsonl(source):
        value = getattr(record, FIELD, None)
        if isinstance(value, int | float):
            found.append(float(value))
    return found


def percentile(sorted_scores: list[float], percent: float) -> float:
    """The value at one percentile, by nearest rank.

    Nearest rank rather than interpolation: the answer is a real score some
    word actually has, which is the honest thing to put a boundary on.
    """
    if not sorted_scores:
        raise ValueError("no scores to take a percentile of")
    rank = max(1, min(len(sorted_scores), round(percent / 100 * len(sorted_scores))))
    return sorted_scores[rank - 1]


@dataclass
class Measured:
    """One run's spread, as the tool writes it."""

    counted: int
    lowest: float
    highest: float
    median: float
    boundaries: list[float]

    def as_document(self) -> dict[str, object]:
        """The spread as JSON, for the app to read back."""
        return {
            "counted": self.counted,
            "lowest": self.lowest,
            "highest": self.highest,
            "median": self.median,
            "boundaries": list(self.boundaries),
        }


def measure(found: list[float]) -> Measured:
    """The spread, as the tool writes it."""
    ordered = sorted(found)
    return Measured(
        counted=len(ordered),
        lowest=ordered[0],
        highest=ordered[-1],
        median=percentile(ordered, 50),
        boundaries=[percentile(ordered, cut) for cut in CUTS],
    )


def _report(measured: Measured) -> None:
    """Print what was measured, and what each band will hold."""
    print(f"{measured.counted:,} scored forms")
    print(
        f"  lowest {measured.lowest:.3f}  "
        f"median {measured.median:.3f}  "
        f"highest {measured.highest:.3f}"
    )
    edges = [measured.lowest, *measured.boundaries, measured.highest]
    print("\n  band       from     to     percentile")
    for index, name in enumerate(BANDS):
        low, high = edges[index], edges[index + 1]
        span = f"{100 * low:.1f}%  {100 * high:.1f}%"
        first = 0.0 if index == 0 else CUTS[index - 1]
        last = 100.0 if index == len(BANDS) - 1 else CUTS[index]
        print(f"  {name:10} {span:16} {first:.0f}–{last:.0f}")


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from",
        dest="source",
        type=Path,
        required=True,
        help="the JSON-lines file tools/run_precompute.py wrote",
    )
    parser.add_argument("--out", type=Path, help="where to write the spread")
    parser.add_argument(
        "--corpus-version",
        default="",
        help="stamped on the output; taken from the records when not given",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Measure one precompute's spread."""
    arguments = _parse(argv)
    found = scores(arguments.source)
    if not found:
        print(f"no {FIELD} in {arguments.source} — nothing to measure")
        return 1
    measured = measure(found)
    _report(measured)

    if arguments.out:
        version = arguments.corpus_version or _version_of(arguments.source)
        document = measured.as_document()
        document["corpus_version"] = version
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(json.dumps(document, indent=2))
        print(f"\nwritten to {arguments.out} (corpus {version or 'unstamped'})")
    return 0


def _version_of(source: Path) -> str:
    """The corpus version from the first record, so it is never guessed."""
    for record in read_jsonl(source):
        return str(getattr(record, "corpus_version", "") or "")
    return ""


if __name__ == "__main__":
    sys.exit(main())
