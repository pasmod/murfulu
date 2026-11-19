r"""What a new rule pack builds that the old one did not, and the reverse.

    git archive public/main rules | tar -x -C /tmp/before
    python tools/measure_pack_change.py --before /tmp/before/rules \\
        --lexicon data/lexicon-20261111.sqlite --out build/pack-change-1119.json

Written for the linguist's corrected rules of 2026-11-19, which replaced the
August tables: ~30 new affix forms, merged and split rows, renamed classes. A
change of that size has to be put to the project lead as numbers — how many
words the engine builds before and after, and which words it gains and loses,
each with the rule responsible — not as an impression.

Two measurements, the same two ``tools/measure_karnam_switch.py`` makes:

* **one step**, over every reading in word formation: the forms each pack
  builds in a single step. Every gained or lost form here has exactly one
  rule behind it, so this is where the examples come from.
* **the build's own pool and depth** (``precompute.input_readings``, depth
  2): the forms a corpus build would store under each pack.

A word is its Latin spelling, compared across all readings at once: one that
one reading stops building and another still builds is neither gained nor
lost, and one that only changes class (*Porxerad*, نام → برنام) is counted
apart. The rule named for a word is the
last rule of its shortest path, and for one step the only one.

Read-only; needs the real lexicon. Prints a summary and writes JSON.
"""

from __future__ import annotations

import argparse
import json
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
from murfulu.rules.pack import RulePack, load
from murfulu.scoring.precompute import input_readings

#: How many gained and lost words the summary names.
EXAMPLES = 15


def _classes(reading: Reading) -> tuple[str, ...]:
    try:
        return word_classes_of(reading)
    except UnmappableCategoryError:
        return ()


#: A word → (Persian, word class, rule responsible, base).
Built = dict[str, tuple[str, str, str, str]]

#: (latin, word class) → (Persian, word class, rule responsible, base) for one
#: reading. Keyed on both, so a spelling built in two classes keeps both.
Forms = dict[tuple[str, str], tuple[str, str, str, str]]


def _built(pack: RulePack, reading: Reading, depth: int) -> Forms:
    """Every form one reading builds, one entry per spelling and class."""
    out: Forms = {}
    for form in from_reading(pack, reading, depth=depth).forms:
        path = form.shortest_path
        out[(form.latin, form.word_class)] = (
            form.fa,
            form.word_class,
            path[-1].rule_id,
            form.base_latin,
        )
    return out


def _spellings(forms: Forms) -> int:
    """How many spellings, as tools/measure_karnam_switch.py counts them."""
    return len({latin for latin, _ in forms})


#: Everyday bases the examples are drawn from, so the words they name are
#: readable: a draw over the whole dictionary names mostly bases nobody knows
#: (*xā*, *azd*). Compared without capitals, since a noun's is written.
FAMILIAR = (
    "del",
    "dast",
    "sar",
    "kār",
    "gol",
    "sang",
    "āb",
    "šab",
    "ruz",
    "šāh",
    "mard",
    "zan",
    "xāne",
    "kuh",
    "ketāb",
    "rang",
    "dard",
    "ranj",
    "mehr",
    "dāneš",
    "huš",
    "omid",
    "honar",
    "soxan",
    "āhan",
    "čub",
    "xub",
    "bozorg",
    "rāst",
    "sabz",
    "sorx",
    "zard",
    "šir",
    "do",
    "se",
    "panj",
    "goft",
    "gu",
    "raft",
    "rav",
    "did",
    "bin",
    "xord",
    "xor",
    "sāxt",
    "sāz",
    "šenās",
    "dān",
)


def _examples(forms: Built) -> list[dict[str, str]]:
    """Words for the rules that moved most, each from an everyday base.

    One per rule in order of how much the rule moved, then round again while
    fewer than :data:`EXAMPLES` are named; a base already shown is passed over
    while another will do, so the list shows rules rather than one base.
    """
    by_rule: dict[str, list[tuple[str, tuple[str, str, str, str]]]] = {}
    for latin, entry in forms.items():
        if entry[3].lower() in FAMILIAR:
            by_rule.setdefault(entry[2], []).append((latin, entry))
    ranked = sorted(by_rule, key=lambda rule: (-len(by_rule[rule]), rule))
    rank = {base: i for i, base in enumerate(FAMILIAR)}
    picked: list[dict[str, str]] = []
    shown: set[str] = set()
    used: set[str] = set()
    while len(picked) < EXAMPLES:
        before = len(picked)
        for rule in ranked:
            left = [c for c in by_rule[rule] if c[0] not in shown]
            if not left:
                continue
            latin, (fa, word_class, _, base) = min(
                left,
                key=lambda c: (c[1][3].lower() in used, rank[c[1][3].lower()], c[0]),
            )
            shown.add(latin)
            used.add(base.lower())
            picked.append(
                {
                    "latin": latin,
                    "fa": fa,
                    "class": word_class,
                    "rule": rule,
                    "base": base,
                }
            )
            if len(picked) == EXAMPLES:
                break
        if len(picked) == before:
            break
    return picked


def measure(
    lexicon: Lexicon, before: RulePack, after: RulePack, depth: int
) -> dict[str, Any]:
    """Every figure in the module docstring, for this lexicon."""
    readings = [
        one for one in lexicon.all_readings() if not is_excluded(one) and _classes(one)
    ]

    pool = {"before": 0, "after": 0}
    pool_readings = 0
    for reading in input_readings(lexicon):
        pool_readings += 1
        pool["before"] += _spellings(_built(before, reading, depth))
        pool["after"] += _spellings(_built(after, reading, depth))

    # Every word each pack builds in one step, over all readings at once: a
    # word one reading stops building and another still builds is neither
    # gained nor lost. A capital is the word class showing (a noun's is
    # written), so words are matched without it and a class change counted
    # apart.
    words: dict[str, Built] = {"before": {}, "after": {}}
    classes: dict[str, dict[str, set[str]]] = {"before": {}, "after": {}}
    one_step = {"before": 0, "after": 0}
    for reading in readings:
        for name, pack in (("before", before), ("after", after)):
            built = _built(pack, reading, 1)
            one_step[name] += _spellings(built)
            for (latin, _), entry in built.items():
                words[name].setdefault(latin.lower(), entry)
                classes[name].setdefault(latin.lower(), set()).add(entry[1])

    really_gained = {
        k: v for k, v in words["after"].items() if k not in words["before"]
    }
    really_lost = {k: v for k, v in words["before"].items() if k not in words["after"]}
    reclassified = sum(
        1
        for k in words["before"].keys() & words["after"].keys()
        if classes["before"][k] != classes["after"][k]
    )

    def per_rule(forms: Built) -> dict[str, int]:
        return dict(Counter(entry[2] for entry in forms.values()).most_common())

    return {
        "lexicon": lexicon.snapshot_id,
        "rule_pack": {"before": before.version, "after": after.version},
        "rules_active": {
            "before": sum(1 for r in before.rules if r.active),
            "after": sum(1 for r in after.rules if r.active),
        },
        "readings_in_word_formation": len(readings),
        "one_step": {
            **one_step,
            "words_gained": len(really_gained),
            "words_lost": len(really_lost),
            "words_reclassified": reclassified,
            "gained_by_rule": per_rule(really_gained),
            "lost_by_rule": per_rule(really_lost),
            "gained_examples": _examples(really_gained),
            "lost_examples": _examples(really_lost),
        },
        "build_pool": {"depth": depth, "readings": pool_readings, **pool},
    }


def main(argv: list[str] | None = None) -> int:
    """Measure, print the summary, write the JSON."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--before", type=Path, required=True, help="old rules/ dir")
    parser.add_argument("--after", type=Path, help="new rules/ dir (default: ours)")
    parser.add_argument("--lexicon", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--depth", type=int, default=2)
    args = parser.parse_args(argv)

    started = time.monotonic()
    before, after = load(args.before), load(args.after)
    with Lexicon.open(args.lexicon) as lexicon:
        result = measure(lexicon, before, after, args.depth)
    result["seconds"] = round(time.monotonic() - started)

    one, pool = result["one_step"], result["build_pool"]
    print(f"lexicon {result['lexicon']}")
    print(
        f"active rules {result['rules_active']['before']} → "
        f"{result['rules_active']['after']}"
    )
    print(
        f"one step, {result['readings_in_word_formation']:,} readings: "
        f"{one['before']:,} → {one['after']:,}  (words +{one['words_gained']:,}, "
        f"−{one['words_lost']:,}; {one['words_reclassified']:,} change class)"
    )
    print(
        f"build pool at depth {pool['depth']}, {pool['readings']:,} readings: "
        f"{pool['before']:,} → {pool['after']:,}"
    )
    for name in ("gained", "lost"):
        print(f"{name}, by rule: {list(one[f'{name}_by_rule'].items())[:12]}")
        for row in one[f"{name}_examples"]:
            print(
                f"  {row['latin']:22} {row['fa']:16} {row['class']:15} "
                f"{row['rule']}  ← {row['base']}"
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
