"""How much of the corpus is inflection of a word we already hold.

    python tools/measure_inflection.py --corpus-version v4 \
        --out build/inflection-v4.json

Open question S8's remaining half: where the lexicon knows no reading for a
spelling, nothing separates رفتی — "you went" — from گفتار, which is exactly
the kind of word Murfulu builds. Both come back `unlinked` and both rank on a
document count. **This measures the size of that before anything is designed.**

Every spelling in ``word_types`` lands in exactly one bucket:

``held``          the lexicon has a reading for it — a word, not an inflection
``stem``          not a headword, but a verb stem the lexicon carries
``inflection``    strips to a held word by an inflectional pattern
``unaccounted``   none of the above

and the inflections are split again by whether a **derivational** rule in the
pack writes the same letters, because those cannot be told apart by spelling.

Reads the lexicon read-only through :mod:`murfulu.lexicon`; never opens the
snapshot with a plain connection.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

from murfulu.corpus.inflection import (
    Analyser,
    Analysis,
    Held,
    held_from,
    pack_suffixes,
)
from murfulu.corpus.wordtypes import normalise
from murfulu.lexicon.store import Lexicon
from murfulu.search.indices import connect, index_name

#: How many analysed spellings to print for eyeballing. A number nobody has
#: read a sample of is a number nobody has checked.
SAMPLE = 30


@dataclass
class Tally:
    """One bucket: how many spellings, and how much writing they account for."""

    spellings: int = 0
    occurrences: int = 0
    documents: int = 0

    def add(self, total_count: int, doc_count: int) -> None:
        """Count one spelling into the bucket."""
        self.spellings += 1
        self.occurrences += total_count
        self.documents += doc_count

    def as_row(self) -> dict[str, int]:
        """The bucket as it is written out."""
        return {
            "spellings": self.spellings,
            "occurrences": self.occurrences,
            "documents": self.documents,
        }


@dataclass
class Measurement:
    """Every bucket, and what fell into each."""

    held: Tally = field(default_factory=Tally)
    stem: Tally = field(default_factory=Tally)
    clear: Tally = field(default_factory=Tally)
    shared: Tally = field(default_factory=Tally)
    unaccounted: Tally = field(default_factory=Tally)
    by_pattern: Counter[str] = field(default_factory=Counter)
    #: The control: known words each pattern read as an inflection anyway.
    claimed: Counter[str] = field(default_factory=Counter)
    examples: list[tuple[str, str, str, bool]] = field(default_factory=list)

    @property
    def total(self) -> Tally:
        """Every spelling seen, however it was read."""
        whole = Tally()
        for one in (self.held, self.stem, self.clear, self.shared, self.unaccounted):
            whole.spellings += one.spellings
            whole.occurrences += one.occurrences
            whole.documents += one.documents
        return whole

    def as_document(self) -> dict[str, object]:
        """The measurement as JSON, for the docs to quote."""
        return {
            "total": self.total.as_row(),
            "held": self.held.as_row(),
            "stem": self.stem.as_row(),
            "inflection_clear": self.clear.as_row(),
            "inflection_shared": self.shared.as_row(),
            "unaccounted": self.unaccounted.as_row(),
            "by_pattern": dict(self.by_pattern.most_common()),
            "control_known_words_claimed": dict(self.claimed.most_common()),
        }


def _spellings(client: Elasticsearch, index: str) -> dict[str, tuple[int, int]]:
    """Every distinct spelling in the index, with its counts.

    ``word_types`` holds one document per spelling *and reading*, so بتا is in
    it three times. The counts are the spelling's and are identical across its
    readings, which is exactly the confusion S8 is about; they are counted once.
    """
    seen: dict[str, tuple[int, int]] = {}
    fields = ["spelling_fa", "total_count", "doc_count"]
    for hit in scan(client, index=index, query={"_source": fields}, size=2000):
        source = hit["_source"]
        seen[source["spelling_fa"]] = (
            source.get("total_count") or 0,
            source.get("doc_count") or 0,
        )
    return seen


def _count(
    measurement: Measurement, analysis: Analysis, counts: tuple[int, int]
) -> None:
    """Put one analysed spelling into its bucket."""
    bucket = measurement.shared if analysis.is_shared else measurement.clear
    bucket.add(*counts)
    measurement.by_pattern[analysis.pattern.id] += 1
    measurement.examples.append(
        (
            analysis.spelling,
            analysis.base,
            analysis.pattern.label_fa,
            analysis.is_shared,
        )
    )


def measure(
    client: Elasticsearch, index: str, analyser: Analyser, held: Held
) -> Measurement:
    """Read every corpus spelling into a bucket."""
    measurement = Measurement()
    for spelling, counts in _spellings(client, index).items():
        normalised = normalise(spelling)
        if normalised in held.headwords:
            measurement.held.add(*counts)
        elif held.holds(normalised):
            measurement.stem.add(*counts)
        elif (analysis := analyser.best(normalised)) is not None:
            _count(measurement, analysis, counts)
        else:
            measurement.unaccounted.add(*counts)
    return measurement


def control(analyser: Analyser, held: Held) -> Counter[str]:
    """How often the instrument reads a known word as an inflection.

    Every lexicon headword **is a word**. So each one the analyser can strip
    down to another headword is either a mistake or a genuine ambiguity, and
    either way it is not something a ranking could act on. Run per pattern,
    this says which patterns are safe and which are guessing — measured, with
    no judgement about Persian in it.
    """
    claimed: Counter[str] = Counter()
    for spelling in held.headwords:
        if (analysis := analyser.control(spelling)) is not None:
            claimed[analysis.pattern.id] += 1
    return claimed


def _percent(part: int, whole: int) -> str:
    """A share, written the way the docs quote it."""
    return f"{100 * part / whole:.1f}%" if whole else "—"


def _report(measurement: Measurement, seed: int) -> None:
    """Print the buckets, then a sample of the analyses to be read by eye."""
    total = measurement.total
    print(
        f"\n{total.spellings:,} distinct spellings, {total.occurrences:,} occurrences\n"
    )
    rows = (
        ("held — the lexicon has a reading", measurement.held),
        ("a verb stem we hold", measurement.stem),
        ("inflection, no rule writes it", measurement.clear),
        ("inflection, a rule writes it too", measurement.shared),
        ("unaccounted for", measurement.unaccounted),
    )
    print(f"{'':38} {'spellings':>12} {'share':>7} {'occurrences':>14} {'share':>7}")
    for label, tally in rows:
        print(
            f"{label:38} {tally.spellings:>12,} "
            f"{_percent(tally.spellings, total.spellings):>7} "
            f"{tally.occurrences:>14,} "
            f"{_percent(tally.occurrences, total.occurrences):>7}"
        )

    print("\nthe patterns that account for most of it, against the control")
    print(f"  {'pattern':<28} {'corpus':>9} {'known words claimed':>20} {'rate':>7}")
    for pattern_id, count in measurement.by_pattern.most_common(18):
        wrong = measurement.claimed[pattern_id]
        print(
            f"  {pattern_id:<28} {count:>9,} {wrong:>20,} "
            f"{_percent(wrong, wrong + count):>7}"
        )

    print(f"\n{SAMPLE} analyses, sampled — read them")
    for spelling, base, label, shared in random.Random(seed).sample(
        measurement.examples, min(SAMPLE, len(measurement.examples))
    ):
        mark = "shared" if shared else "clear "
        print(f"  {mark}  {spelling:<20} ← {base:<16} {label}")


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-version", default="v4", help="which word_types index")
    parser.add_argument("--out", type=Path, help="where to write the measurement")
    parser.add_argument(
        "--lexicon", type=Path, help="a snapshot other than the default"
    )
    parser.add_argument("--seed", type=int, default=9, help="which sample to print")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Measure one corpus version against one lexicon snapshot."""
    arguments = _parse(argv)
    with Lexicon.open(arguments.lexicon) as lexicon:
        held = held_from(lexicon)
        snapshot = lexicon.snapshot_id
    suffixes = pack_suffixes()
    print(
        f"lexicon {snapshot}: {len(held.headwords):,} headwords, "
        f"{len(held.past_stems):,} past stems, "
        f"{len(held.present_stems):,} present stems"
    )
    print(f"{len(suffixes):,} distinct suffix spellings in the pack")

    index = index_name("word_types", arguments.corpus_version)
    analyser = Analyser(held=held, pack_suffixes=suffixes)
    measurement = measure(connect(), index, analyser, held)
    measurement.claimed = control(analyser, held)
    claimed = sum(measurement.claimed.values())
    print(
        f"control: {claimed:,} of {len(held.headwords):,} known words "
        f"({_percent(claimed, len(held.headwords))}) read as an inflection anyway"
    )
    _report(measurement, arguments.seed)

    if arguments.out:
        document = measurement.as_document()
        document["corpus_version"] = arguments.corpus_version
        document["lexicon_snapshot_id"] = snapshot
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(json.dumps(document, ensure_ascii=False, indent=2))
        print(f"\nwritten to {arguments.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
