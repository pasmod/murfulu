r"""What the open ruling L26 (with L18) costs, measured both ways.

    python tools/measure_karnam_switch.py --lexicon data/lexicon-20261111.sqlite \\
        --out build/karnam-switch-20261111.json

L26 asks whether «نام» in the rule table takes a کارنام too. The answer is the
linguist's, and he is revising his rules, so ``rules/bank_groups.yaml`` keeps
today's behaviour behind the switch ``karnam_counts_as_nam`` (off). This
counts what each setting builds, so the question can be put with its numbers:

* **readings**: how many lexicon readings are in word formation, how many feed
  a کارنام, and how many feed a کارنام and no نام — the words the switch opens;
* **one step**, over every reading in word formation: forms built off and on;
* **the build's own pool and depth** (``precompute.input_readings``, depth 2):
  forms off and on, by the dictionary category that put a reading in the pool —
  what a corpus build would store under each setting;
* **the rule examples L26 names**, and the هوش family of L35: whether each is
  built from its base under each setting.

Read-only; needs the real lexicon. Prints a summary and writes JSON.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from murfulu.generation import from_reading
from murfulu.lexicon.bank import is_excluded, word_classes_of
from murfulu.lexicon.categories import UnmappableCategoryError
from murfulu.lexicon.entries import Reading
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import RulePack, load, widen_nam_to_karnam
from murfulu.scoring.precompute import REVIEWED_CATEGORIES, input_readings

#: (base spelling, the form a rule's own example says it builds). The first
#: four are L26's; the rest are the هوش family the هوشواره run measured (L35).
EXAMPLES = (
    ("دانش", "dānešmand", "N-071"),
    ("امید", "omidvār", "N-074"),
    ("دانش", "dānešgāh", "N-068"),
    ("دانش", "dānešvar", "N-080"),
    ("هوش", "hušvāre", "N-078 / N-079"),
    ("هوش", "hušmand", "N-071"),
    ("هوش", "bihuš", "N-008"),
    ("هوش", "bāhuš", "N-002"),
)


def _classes(reading: Reading) -> tuple[str, ...]:
    try:
        return word_classes_of(reading)
    except UnmappableCategoryError:
        return ()


def _forms(pack: RulePack, reading: Reading, depth: int) -> set[str]:
    return {form.latin for form in from_reading(pack, reading, depth=depth).forms}


def measure(lexicon: Lexicon, depth: int) -> dict[str, Any]:
    """Every figure in the module docstring, for this lexicon."""
    off = load()
    if off.version.endswith("+karnam-as-nam"):
        raise SystemExit("the shipped switch is on; this measures from off")
    on = widen_nam_to_karnam(off)

    readings = list(lexicon.all_readings())
    in_formation = [one for one in readings if not is_excluded(one) and _classes(one)]
    karnam = [one for one in in_formation if "karnam" in _classes(one)]
    opened = [one for one in karnam if "nam" not in _classes(one)]
    opened_ids = {id(one) for one in opened}

    one_step_off = one_step_on = 0
    changed_one_step = 0
    per_opened: list[int] = []
    for reading in in_formation:
        a = len(_forms(off, reading, 1))
        b = len(_forms(on, reading, 1))
        one_step_off += a
        one_step_on += b
        changed_one_step += a != b
        if id(reading) in opened_ids:
            per_opened.append(b)

    pool: Counter[str] = Counter()
    built: dict[str, Counter[str]] = {"off": Counter(), "on": Counter()}
    changed_pool = 0
    for reading in input_readings(lexicon):
        category = reading.lexicon_category or ""
        pool[category] += 1
        a = len(_forms(off, reading, depth))
        b = len(_forms(on, reading, depth))
        built["off"][category] += a
        built["on"][category] += b
        changed_pool += a != b

    examples = []
    for spelling, expected, rule in EXAMPLES:
        bases = lexicon.by_spelling(spelling)
        row: dict[str, Any] = {"base": spelling, "expected": expected, "rule": rule}
        for name, pack in (("off", off), ("on", on)):
            row[name] = any(
                expected in {form.lower() for form in _forms(pack, one, 1)}
                for one in bases
            )
        examples.append(row)

    return {
        "lexicon": lexicon.snapshot_id,
        "rule_pack": {"off": off.version, "on": on.version},
        "readings": {
            "all": len(readings),
            "in_word_formation": len(in_formation),
            "excluded_loanwords": sum(1 for one in readings if is_excluded(one)),
            "feeding_karnam": len(karnam),
            "karnam_without_nam": len(opened),
        },
        "one_step_all_readings": {
            "off": one_step_off,
            "on": one_step_on,
            "readings_changed": changed_one_step,
            "opened_median_on": statistics.median(per_opened) if per_opened else 0,
        },
        "build_pool": {
            "categories": list(REVIEWED_CATEGORIES),
            "depth": depth,
            "readings": dict(pool),
            "forms_off": dict(built["off"]),
            "forms_on": dict(built["on"]),
            "total_off": sum(built["off"].values()),
            "total_on": sum(built["on"].values()),
            "readings_changed": changed_pool,
        },
        "examples": examples,
    }


def main(argv: list[str] | None = None) -> int:
    """Measure, print the summary, write the JSON."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--lexicon", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--depth", type=int, default=2)
    args = parser.parse_args(argv)

    started = time.monotonic()
    with Lexicon.open(args.lexicon) as lexicon:
        result = measure(lexicon, args.depth)
    result["seconds"] = round(time.monotonic() - started)

    r, one, pool = (
        result["readings"],
        result["one_step_all_readings"],
        result["build_pool"],
    )
    print(
        f"lexicon {result['lexicon']}   off {result['rule_pack']['off']}  "
        f"on {result['rule_pack']['on']}"
    )
    print(
        f"readings {r['all']:,}  in word formation {r['in_word_formation']:,}  "
        f"loanwords out {r['excluded_loanwords']:,}"
    )
    print(
        f"  feed a کارنام {r['feeding_karnam']:,}, "
        f"of them no نام {r['karnam_without_nam']:,}"
    )
    print(
        f"one step, every reading: off {one['off']:,}  on {one['on']:,}  "
        f"({one['readings_changed']:,} readings change; median of the opened, on: "
        f"{one['opened_median_on']})"
    )
    print(
        f"build pool at depth {pool['depth']}: off {pool['total_off']:,}  "
        f"on {pool['total_on']:,}  ({pool['readings_changed']:,} readings change)"
    )
    for category, count in pool["readings"].items():
        print(
            f"  {category:12} {count:6,} readings  "
            f"off {pool['forms_off'][category]:>10,}"
            f"  on {pool['forms_on'][category]:>10,}"
        )
    for row in result["examples"]:
        print(
            f"  {row['expected']:12} {row['rule']:14} "
            f"off {row['off']!s:5}  on {row['on']}"
        )
    print(f"{result['seconds']} s")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
