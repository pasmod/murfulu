"""Trace every path two corpus versions disagree on to a change in the lexicon.

    python tools/attribute_lexicon_change.py \
        data/lexicon-20260808.sqlite data/lexicon-20261012.sqlite \
        build/derivations-v12.jsonl build/derivations-v13.jsonl

**Why this exists.** ``compare_versions.py`` says how many records and paths a
rebuild gained or lost, per rule. When the rebuild exists because the lexicon
moved (v13, karbon 1.2.0), that is not enough: a loss nobody can trace to the
lexicon is a loss in the engine. This matches the two derivation files path by
path and asks, for each path that differs, what happened to the lexicon
reading it was built from (``source_spelling_fa`` + ``source_latin``):

``reading changed``  the row is still there, read differently (*rošan* → *rowšan*)
``row added/removed``  the row is new, or gone
``stems changed``  same reading, other stems
``variants changed``  the list of second readings moved
``source unchanged``  **nothing** about the source moved — the line that must
                      be zero for the difference to be the lexicon's alone

Readings are taken through :class:`~murfulu.lexicon.store.Lexicon`, so the
overrides and the look-alike repair are applied exactly as the build saw them.
Prints Markdown, so the output can go straight into ``data/compare-*.md``.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from murfulu.lexicon.store import Lexicon
from murfulu.scoring.precompute import REVIEWED_CATEGORIES

Key = tuple[str, str]
PathKey = tuple[str, str, str, tuple[str, ...], tuple[str, ...]]


@dataclass(frozen=True)
class Source:
    """What a build could have taken from one reading."""

    primary: str
    ids: frozenset[int]
    category: str | None
    stems: tuple[str | None, ...]
    variants: tuple[str, ...]
    review: bool


@dataclass
class Side:
    """One snapshot: readings by (spelling, Latin), and spellings by row id."""

    readings: dict[Key, Source]
    rows: dict[int, tuple[str, tuple[str, ...]]]


def _side(path: Path) -> Side:
    readings: dict[Key, Source] = {}
    rows: dict[int, tuple[str, tuple[str, ...]]] = {}
    with Lexicon.open(path) as lexicon:
        print(f"- `{lexicon.snapshot_id}`: overrides {lexicon.describe_overrides()}")
        for one in lexicon.all_readings():
            source = Source(
                primary=one.latin,
                ids=frozenset(one.source_entry_ids),
                category=one.lexicon_category,
                stems=(
                    one.past_stem_latin,
                    one.present_stem_latin,
                    one.past_stem_fa,
                    one.present_stem_fa,
                ),
                variants=one.latin_variants,
                review=one.needs_review,
            )
            for latin in one.all_latin:
                readings.setdefault((one.spelling_fa, latin), source)
            for row in one.source_entry_ids:
                rows[row] = (one.spelling_fa, one.all_latin)
    return Side(readings, rows)


def classify(key: Key, old: Side, new: Side) -> str:
    """What happened to the reading a path was built from."""
    before, after = old.readings.get(key), new.readings.get(key)
    if before and after:
        moved = [
            label
            for label, differs in (
                ("stems changed", before.stems != after.stems),
                ("category changed", before.category != after.category),
                ("variants changed", before.variants != after.variants),
                ("needs_review changed", before.review != after.review),
                ("primary/variant swapped", before.primary != after.primary),
            )
            if differs
        ]
        return " + ".join(moved) or "source unchanged"
    present = before or after
    if present is None:
        return "source in neither snapshot"
    other = new if before else old
    kept = [other.rows[row] for row in present.ids if row in other.rows]
    if kept:
        spelling, latin = kept[0]
        if spelling == key[0] and key[1] not in latin:
            return f"reading changed ({present.category})"
        return f"row changed otherwise ({present.category})"
    return f"row {'removed' if before else 'added'} ({present.category})"


def _paths(path: Path) -> dict[str, set[PathKey]]:
    found: dict[str, set[PathKey]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            found[record["id"]] = {
                (
                    one.get("source_spelling_fa") or "",
                    one.get("source_latin") or "",
                    one.get("base_form") or "",
                    tuple(one.get("rule_ids") or ()),
                    tuple(one.get("glide_ids") or ()),
                )
                for one in record.get("paths") or ()
            }
    return found


def _table(title: str, counts: Counter[str]) -> None:
    print(f"\n### {title}\n")
    for label, count in counts.most_common():
        print(f"- {label}: {count:,}")
    if not counts:
        print("- none")


def main(argv: list[str] | None = None) -> int:
    """Attribute the difference between two derivation files to the lexicon."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old_lexicon", type=Path)
    parser.add_argument("new_lexicon", type=Path)
    parser.add_argument("old_derivations", type=Path)
    parser.add_argument("new_derivations", type=Path)
    arguments = parser.parse_args(argv)

    print("## Lexicon\n")
    old, new = _side(arguments.old_lexicon), _side(arguments.new_lexicon)
    pool = set(REVIEWED_CATEGORIES)
    differs: Counter[str] = Counter()
    for key in set(old.readings) | set(new.readings):
        categories = {
            side.readings[key].category for side in (old, new) if key in side.readings
        }
        if categories & pool:
            label = classify(key, old, new)
            if label != "source unchanged":
                differs[label] += 1
    _table("Input-pool readings that differ", differs)

    was, now = _paths(arguments.old_derivations), _paths(arguments.new_derivations)
    lost: Counter[str] = Counter()
    gained: Counter[str] = Counter()
    gone: Counter[str] = Counter()
    appeared: Counter[str] = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    cache: dict[Key, str] = {}

    def cause(path: PathKey) -> str:
        key = (path[0], path[1])
        if key not in cache:
            cache[key] = classify(key, old, new)
        return cache[key]

    for record in set(was) | set(now):
        before, after = was.get(record, set()), now.get(record, set())
        if before == after:
            continue
        for tally, side, paths in (
            ("lost", lost, before - after),
            ("gained", gained, after - before),
        ):  # noqa: E501
            for path in paths:
                label = cause(path)
                side[label] += 1
                shown = examples[f"{tally}: {label}"]
                if len(shown) < 4:
                    shown.append(
                        f"`{record}` ← {path[0]} *{path[1]}* {'/'.join(path[3])}"
                    )  # noqa: E501
        if not after:
            gone[cause(next(iter(before)))] += 1
        if not before:
            appeared[cause(next(iter(after)))] += 1

    print("\n## Derivations\n")
    print(f"- records {len(was):,} → {len(now):,} ({len(now) - len(was):+,})")
    print(f"- records gone {sum(gone.values()):,}, new {sum(appeared.values()):,}")
    print(f"- paths lost {sum(lost.values()):,}, gained {sum(gained.values()):,}")
    print(
        f"- **paths whose source did not change: lost "
        f"{lost['source unchanged']:,}, gained {gained['source unchanged']:,}** "
        f"(must be 0 for the difference to be the lexicon's alone)"
    )
    _table("Records gone, by what happened to their source", gone)
    _table("Records new, by what happened to their source", appeared)
    _table("Paths lost, by cause", lost)
    _table("Paths gained, by cause", gained)
    print("\n### Examples\n")
    for label in sorted(examples):
        print(f"- {label}")
        for line in examples[label]:
            print(f"  - {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
