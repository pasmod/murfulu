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
``word classes changed``  the word classes the build fed it moved — since
                      karbon 1.3.0 they come from the linguist's word-bank
                      groups (``rules/bank_groups.yaml``), several per word
``now out of word formation``  the reading is a وام‌واژه, which builds nothing
``merged into another row``  karbon 1.3.0 merged the row (``merge_map``)
``source unchanged``  **nothing** about the source moved
``metadata only``  only ``needs_review`` or the dictionary's label moved, and
                      neither reaches what the build makes — so it cannot
                      explain a path, and counts with ``source unchanged`` in
                      the line that must be zero for the difference to be the
                      lexicon's alone

Row ids are followed through the newer snapshot's ``merge_map``, so a merged
row is not mistaken for a removed one. ``--old-overrides`` reads the older side
with the overrides table as it stood when that build ran (``git show
REV:rules/lexicon_overrides.yaml``), so a later correction to the table is not
mistaken for an unchanged source.

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

from murfulu.generation import bases_of
from murfulu.lexicon import overrides as held_overrides
from murfulu.lexicon.bank import is_excluded
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
    #: The word classes the build entered it as (stems for a verb).
    classes: tuple[str, ...] = ()
    excluded: bool = False
    #: Whether the build's input pool takes it: the pool is chosen by the
    #: dictionary's label (``precompute.REVIEWED_CATEGORIES``), so a label
    #: change can move a reading in or out of what is built at all.
    in_pool: bool = False


@dataclass
class Side:
    """One snapshot: readings by (spelling, Latin), and spellings by row id."""

    readings: dict[Key, Source]
    rows: dict[int, tuple[str, tuple[str, ...]]]
    #: Old row id → the row it was merged into. Empty before karbon 1.3.0.
    merged: dict[int, int]


def _side(path: Path, overrides_file: Path | None = None) -> Side:
    readings: dict[Key, Source] = {}
    primaries: set[Key] = set()
    rows: dict[int, tuple[str, tuple[str, ...]]] = {}
    held = None
    if overrides_file is not None:
        if not overrides_file.is_file():
            raise SystemExit(f"--old-overrides: no such file {overrides_file}")
        held = held_overrides.load_file(overrides_file)
    with Lexicon.open(path, overrides=held) as lexicon:
        if held is not None and not held.applies_to(lexicon.snapshot_id):
            raise SystemExit(
                f"--old-overrides: {overrides_file} was not checked against "
                f"{lexicon.snapshot_id}; it is the wrong table for this build"
            )
        print(f"- `{lexicon.snapshot_id}`: overrides {lexicon.describe_overrides()}")
        merged = lexicon.merge_map()
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
                classes=tuple(sorted({base.word_class for base in bases_of(one)})),
                excluded=is_excluded(one),
                in_pool=one.lexicon_category in REVIEWED_CATEGORIES,
            )
            # A word's own reading wins over another row's second reading:
            # 1.3.2 added کشنی *Košni* as a row of its own, which 1.2.0 had
            # only as a variant of *Kešni*, and the build took it from the new
            # row. First come, first kept among variants alone.
            key = (one.spelling_fa, one.latin)
            if key not in primaries:
                readings[key] = source
                primaries.add(key)
            for latin in one.latin_variants:
                readings.setdefault((one.spelling_fa, latin), source)
            for row in one.source_entry_ids:
                rows[row] = (one.spelling_fa, one.all_latin)
    return Side(readings, rows, merged)


#: Changes that do not reach what a build makes: the review flag, and the
#: dictionary's label once the word classes it fed are compared directly.
_METADATA = frozenset({"needs_review changed", "category changed"})

#: Labels that explain nothing, and must count to zero in the check line.
UNEXPLAINED = ("source unchanged", "metadata only", "source in neither snapshot")


def unexplained(label: str) -> bool:
    """True when a cause label does not account for a moved path."""
    return label.startswith(UNEXPLAINED)


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
                ("word classes changed", before.classes != after.classes),
                ("left the input pool", before.in_pool and not after.in_pool),
                ("entered the input pool", after.in_pool and not before.in_pool),
                (
                    "now out of word formation",
                    after.excluded and not before.excluded,
                ),
            )
            if differs
        ]
        if not moved:
            return "source unchanged"
        explaining = [label for label in moved if label not in _METADATA]
        if not explaining:
            return "metadata only (" + " + ".join(moved) + ")"
        return " + ".join(moved)
    present = before or after
    if present is None:
        return "source in neither snapshot"
    other = new if before else old
    if before:
        # Old ids into the new snapshot, through its merge map.
        across = [new.merged.get(row, row) for row in present.ids]
    else:
        # New ids back into the old one: the row itself, or what merged into it.
        across = list(present.ids) + [
            old_id for old_id, new_id in new.merged.items() if new_id in present.ids
        ]
    kept = [other.rows[row] for row in across if row in other.rows]
    if before and any(row in new.merged for row in present.ids) and kept:
        spelling, latin = kept[0]
        if (spelling, key[1]) != key or key[1] not in latin:
            return f"merged into another row ({present.category})"
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
    parser.add_argument(
        "--old-overrides",
        type=Path,
        help="the overrides table as it stood when the older build ran",
    )
    arguments = parser.parse_args(argv)

    print("## Lexicon\n")
    old = _side(arguments.old_lexicon, arguments.old_overrides)
    new = _side(arguments.new_lexicon)
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
    not_lost = sum(count for label, count in lost.items() if unexplained(label))
    not_gained = sum(count for label, count in gained.items() if unexplained(label))
    print(
        f"- **paths no change in their source explains: lost {not_lost:,}, "
        f"gained {not_gained:,}** (source unchanged, metadata only, or in "
        f"neither snapshot; must be 0 for the difference to be the lexicon's alone)"
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
    # Non-zero when the check fails, so a script cannot read past it.
    return 1 if not_lost or not_gained else 0


if __name__ == "__main__":
    raise SystemExit(main())
