"""The words karbon does not hold, with the inflections taken out.

    python tools/clean_gap_list.py --corpus-version v9 \
        --out build/gap-list-v9.tsv

UPSTREAM B2 proposes sending karbon the unlinked corpus spellings ranked by
frequency, and it is the single most useful thing we can send. **B2b is why it
cannot go raw:** 11.7% of corpus spellings are not missing headwords at all but
inflections of something karbon already holds — رفتی on رفت, کتاب‌ها on کتاب.
Sent unfiltered, the list asks a headword dictionary to add tens of thousands
of conjugated verbs and plurals.

**Which inflections are dropped is decided by measurement, not by opinion.**
Every karbon headword *is* a word, so any headword the analyser strips down to
another headword is a false positive. Run per pattern that gives each pattern
an error rate — 0.0% for the ‌های plural, 20.2% for the Arabic -ون — and only
patterns at or under ``--max-error`` are allowed to remove anything. A word
held out by a pattern that is wrong one time in five is a word karbon never
hears about, and the whole value of the list is that every entry is real.

**A dropped spelling is written to ``--dropped``, never discarded silently.**
The point is a pull request that can be argued with.

Reads the lexicon read-only through :mod:`murfulu.lexicon`; never opens the
snapshot with a plain connection.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

from murfulu.corpus.inflection import Analyser, Held, held_from, pack_suffixes
from murfulu.corpus.wordtypes import normalise
from murfulu.lexicon.store import Lexicon
from murfulu.search.indices import connect

#: The default ceiling on a pattern's measured error rate. **5% is a choice and
#: is written here so it can be argued with**: at 0% only the patterns that
#: never misread a headword may drop anything, and at 20% every pattern the
#: instrument has may. The tool prints the effect of several ceilings so the
#: number is picked from the measurement rather than from this line.
MAX_ERROR = 0.05


@dataclass
class Row:
    """One spelling the corpus writes and the lexicon has no reading for."""

    spelling: str
    total_count: int
    doc_count: int
    #: Set when an inflectional pattern explains it away.
    pattern_id: str = ""
    base: str = ""
    pattern_label: str = ""
    #: The measured error rate of the pattern that explains it.
    error_rate: float = 0.0
    #: True when a derivational rule in the pack writes the same letters, so
    #: the two cannot be told apart by spelling alone.
    shared: bool = False
    #: The rules that would build this word, where our own rules can build it.
    #: This is what turns a bare list into a request somebody can act on.
    built_by: tuple[str, ...] = ()
    #: The affixes those rules add.
    affixes: tuple[str, ...] = ()


@dataclass
class Cleaned:
    """The list before and after, and why each row went where it did."""

    kept: list[Row] = field(default_factory=list)
    dropped: list[Row] = field(default_factory=list)
    #: Rows an unsafe pattern explained. Kept, and counted separately, because
    #: they are the cost of the ceiling and a reader should see it.
    kept_despite_a_pattern: list[Row] = field(default_factory=list)
    error_rates: dict[str, float] = field(default_factory=dict)
    control_size: int = 0

    @property
    def before(self) -> int:
        """How long the list was before any inflection was taken out."""
        return len(self.kept) + len(self.dropped)


def _unlinked(client: Elasticsearch, index: str, held: Held) -> list[Row]:
    """Every corpus spelling the lexicon has no reading for, counted once.

    ``word_types`` holds one document per spelling *and* reading, and the
    counts are the spelling's, so a spelling read three ways would otherwise be
    counted three times.
    """
    seen: dict[str, Row] = {}
    fields = ["spelling_fa", "total_count", "doc_count"]
    for hit in scan(client, index=index, query={"_source": fields}, size=2000):
        source = hit["_source"]
        spelling = source["spelling_fa"]
        if spelling in seen:
            continue
        normalised = normalise(spelling)
        # A headword karbon holds is not a gap. A verb stem is not one either:
        # karbon carries it, just not as a headword.
        if normalised in held.headwords or held.holds(normalised):
            continue
        seen[spelling] = Row(
            spelling=spelling,
            total_count=source.get("total_count") or 0,
            doc_count=source.get("doc_count") or 0,
        )
    return sorted(seen.values(), key=lambda row: -row.total_count)


def error_rates(analyser: Analyser, held: Held) -> tuple[dict[str, float], int]:
    """Each pattern's error rate, measured on words that are words.

    Every karbon headword is a word by definition, so a headword this pattern
    strips to another headword is a false positive. No judgement about Persian
    is made here.
    """
    claimed: Counter[str] = Counter()
    for spelling in held.headwords:
        if (analysis := analyser.control(spelling)) is not None:
            claimed[analysis.pattern.id] += 1
    size = len(held.headwords)
    return ({p: n / size for p, n in claimed.items()}, size)


def buildable(affix_map: Path) -> dict[str, dict[str, list[str]]]:
    """Corpus spellings our own rules can build, from the precompute's map.

    The precompute keeps a `proposed` list: spellings the corpus writes, that a
    rule in the pack can form, and that no lexicon entry confirms. Each carries
    the rule and the affix, so the request upstream is not *please add گفتار*
    but **گفتار occurs 4,813 times and is goft + -ār by rule V-010**.

    Keyed by ``spelling:reading_id``; the spelling alone is what a gap list
    knows about.
    """
    raw = json.loads(affix_map.read_text(encoding="utf-8")).get("proposed") or {}
    found: dict[str, dict[str, list[str]]] = {}
    for key, value in raw.items():
        found.setdefault(key.split(":")[0], value)
    return found


def clean(rows: list[Row], analyser: Analyser, held: Held, ceiling: float) -> Cleaned:
    """Split the gap list into what to send and what to hold back."""
    rates, size = error_rates(analyser, held)
    result = Cleaned(error_rates=rates, control_size=size)

    for row in rows:
        analysis = analyser.best(normalise(row.spelling))
        if analysis is None:
            result.kept.append(row)
            continue
        row.pattern_id = analysis.pattern.id
        row.base = analysis.base
        row.pattern_label = analysis.pattern.label_fa
        row.shared = analysis.is_shared
        row.error_rate = rates.get(analysis.pattern.id, 0.0)
        if row.error_rate <= ceiling:
            result.dropped.append(row)
        else:
            result.kept.append(row)
            result.kept_despite_a_pattern.append(row)
    return result


def _write(path: Path, rows: list[Row], *, with_reason: bool) -> None:
    """One file, tab separated, ready to attach to an issue."""
    header = ["spelling_fa", "occurrences", "documents"]
    if with_reason:
        header += ["pattern", "base", "pattern_fa", "error_rate", "shares_a_rule"]
    else:
        header += ["built_by_rules", "affixes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        out = csv.writer(handle, delimiter="\t")
        out.writerow(header)
        for row in rows:
            line = [row.spelling, row.total_count, row.doc_count]
            if not with_reason:
                line += [" ".join(row.built_by), " ".join(row.affixes)]
            if with_reason:
                line += [
                    row.pattern_id,
                    row.base,
                    row.pattern_label,
                    f"{row.error_rate:.3f}",
                    "yes" if row.shared else "no",
                ]
            out.writerow(line)


def _report(result: Cleaned, ceiling: float) -> None:
    before, after = result.before, len(result.kept)
    removed = len(result.dropped)
    print(f"\ngap list at a {ceiling:.0%} ceiling on a pattern's error rate\n")
    print(f"  before          {before:>9,} spellings")
    print(f"  inflections out {removed:>9,}  ({100 * removed / before:.1f}%)")
    print(f"  after           {after:>9,} spellings")
    print(
        f"  occurrences     {sum(r.total_count for r in result.kept):>9,} "
        f"kept, {sum(r.total_count for r in result.dropped):,} held back"
    )
    print(
        f"\ncontrol: {result.control_size:,} karbon headwords, "
        "each pattern's error rate measured on them\n"
    )
    by_use = Counter(row.pattern_id for row in result.dropped)
    unsafe = Counter(row.pattern_id for row in result.kept_despite_a_pattern)
    print(f"  {'pattern':<22}{'error':>8}{'dropped':>10}{'kept':>8}")
    for pattern_id, rate in sorted(result.error_rates.items(), key=lambda p: p[1]):
        if not by_use[pattern_id] and not unsafe[pattern_id]:
            continue
        mark = "" if rate <= ceiling else "  ← over the ceiling, kept"
        print(
            f"  {pattern_id:<22}{rate:>7.1%}{by_use[pattern_id]:>10,}"
            f"{unsafe[pattern_id]:>8,}{mark}"
        )
    if result.kept_despite_a_pattern:
        print(
            f"\n  {len(result.kept_despite_a_pattern):,} rows an unsafe pattern "
            "explained are kept, because the pattern is wrong too often to act on"
        )


def _ceilings(rows: list[Row], analyser: Analyser, held: Held) -> None:
    """What other ceilings would have done, so the default is a choice."""
    print("\nwhat the ceiling costs, so it is picked from the measurement\n")
    print(f"  {'ceiling':>9}{'dropped':>10}{'kept':>10}")
    for ceiling in (0.0, 0.01, 0.05, 0.10, 0.25):
        trial = clean(
            [Row(r.spelling, r.total_count, r.doc_count) for r in rows],
            analyser,
            held,
            ceiling,
        )
        print(f"  {ceiling:>8.0%}{len(trial.dropped):>10,}{len(trial.kept):>10,}")


def main() -> int:
    """Read the gap list, clean it, and write both halves out."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-version", default="v9", help="which word_types index")
    parser.add_argument("--out", type=Path, help="where to write the cleaned list")
    parser.add_argument(
        "--dropped",
        type=Path,
        help="where to write what was held back, with its reason",
    )
    parser.add_argument("--json", type=Path, help="the counts, for a write-up")
    parser.add_argument(
        "--max-error",
        type=float,
        default=MAX_ERROR,
        help="a pattern may only drop rows if it misreads at most this share "
        f"of known words (default {MAX_ERROR:.0%})",
    )
    parser.add_argument(
        "--top", type=int, default=25, help="how many of the biggest gaps to print"
    )
    parser.add_argument(
        "--buildable",
        type=Path,
        help="an affix map from the precompute. Given one, the list is cut to "
        "the words our own rules can build, each carrying the rules that build "
        "it. Chosen by the project lead 2026-08-15 over filtering function "
        "words: 'and' is not built from anything, so it never qualifies.",
    )
    args = parser.parse_args()

    index = f"word_types-{args.corpus_version}"
    client = connect()
    if not client.indices.exists(index=index):
        print(f"no index {index}", file=sys.stderr)
        return 1

    with Lexicon.open() as lexicon:
        snapshot = lexicon.snapshot_id
        held = held_from(lexicon)
    analyser = Analyser(held=held, pack_suffixes=pack_suffixes())

    print(f"lexicon {snapshot}: {len(held.headwords):,} headwords")
    rows = _unlinked(client, index, held)
    print(f"{index}: {len(rows):,} spellings with no reading")

    result = clean(rows, analyser, held, args.max_error)
    _report(result, args.max_error)
    _ceilings(rows, analyser, held)

    if args.buildable:
        can_build = buildable(args.buildable)
        before = len(result.kept)
        keeping = []
        for row in result.kept:
            found = can_build.get(row.spelling)
            if not found:
                continue
            row.built_by = tuple(found.get("rule_ids") or ())
            row.affixes = tuple(found.get("affixes") or ())
            keeping.append(row)
        result.kept = keeping
        print(
            f"\nour rules can build {len(keeping):,} of those {before:,}. "
            "The rest are sent as a separate ask, or not at all:\n"
        )
        short = sum(1 for row in keeping if len(row.spelling) <= 3)
        print(f"  three characters or fewer, still in  {short:,}")
        print(
            f"  occurrences covered                  "
            f"{sum(r.total_count for r in keeping):,}"
        )

    print(f"\nthe {args.top} biggest gaps that survive the clean\n")
    for row in result.kept[: args.top]:
        print(f"  {row.spelling:<16} {row.total_count:>8,} occurrences")

    if args.out:
        _write(args.out, result.kept, with_reason=False)
        print(f"\nwrote {len(result.kept):,} rows to {args.out}")
    if args.dropped:
        _write(args.dropped, result.dropped, with_reason=True)
        print(f"wrote {len(result.dropped):,} held-back rows to {args.dropped}")
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "corpus_version": args.corpus_version,
                    "lexicon_snapshot_id": snapshot,
                    "max_error": args.max_error,
                    "before": result.before,
                    "after": len(result.kept),
                    "dropped": len(result.dropped),
                    "kept_despite_a_pattern": len(result.kept_despite_a_pattern),
                    "control_headwords": result.control_size,
                    "error_rates": result.error_rates,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"wrote the counts to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
