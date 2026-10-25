"""How many *built* words rank on a count that belongs to an inflection.

    python tools/measure_built_inflection.py --corpus-version v5 \
        --out build/inflection-built-v5.json

The companion to ``tools/measure_inflection.py``, which measures the corpus.
This measures what the reader actually sees. Only an **attested** form carries
a number, and only an attested form is ranked on one, so the corpus-wide share
is the wrong denominator for a decision about ranking — this is the right one.

Open question S8's remaining half, stated as a population: of the forms
Murfulu built and then found in the corpus, how many were found because the
corpus writes an **inflection** with those letters rather than the word we
built? رفتی is "you went"; گفتار is the word we built; both come back
``unlinked`` and both rank on their document count.

``attestation_unlinked`` marks the ones where the lexicon has no reading for
the spelling at all, which is exactly the half no condition over the fields we
hold can close. They are reported apart.

Nothing here decides anything. A form whose pattern shares its letters with a
derivational rule is counted apart, because آبادانی is both the indefinite of
آبادان and the noun "prosperity", and that is the linguist's to rule on.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

from murfulu.corpus.inflection import Analyser, Analysis, held_from, pack_suffixes
from murfulu.lexicon.store import Lexicon
from murfulu.search.indices import connect, index_name

#: How many analysed forms to print. A number nobody has read a sample of is
#: a number nobody has checked.
SAMPLE = 25

#: The two levels that carry a count. ``none`` forms are not ranked on one.
ATTESTED = ("spelling", "reading")

#: One built form read as an inflection: spelling, base, label, shared, docs.
Example = tuple[str, str, str, bool, int]


@dataclass
class Built:
    """One population of built forms, and how much of it reads as inflection."""

    forms: int = 0
    documents: int = 0
    inflection: int = 0
    inflection_documents: int = 0
    shared: int = 0
    by_pattern: Counter[str] = field(default_factory=Counter)

    def add(self, documents: int, analysis: Analysis | None) -> None:
        """Count one built form, with its reading if it has one."""
        self.forms += 1
        self.documents += documents
        if analysis is None:
            return
        self.inflection += 1
        self.inflection_documents += documents
        self.shared += 1 if analysis.is_shared else 0
        self.by_pattern[analysis.pattern.id] += 1

    def as_row(self) -> dict[str, object]:
        """The population as it is written out."""
        return {
            "forms": self.forms,
            "documents": self.documents,
            "inflection": self.inflection,
            "inflection_documents": self.inflection_documents,
            "inflection_shared": self.shared,
            "by_pattern": dict(self.by_pattern.most_common(20)),
        }


def _attested(client: Elasticsearch, index: str) -> Iterator[dict[str, Any]]:
    """Every attested built form, with the fields the ranking uses."""
    query = {
        "query": {"terms": {"attestation": list(ATTESTED)}},
        "_source": [
            "form_fa",
            "form_latin",
            "attestation",
            "attestation_unlinked",
            "attested_docs",
        ],
    }
    for hit in scan(client, index=index, query=query, size=2000):
        yield hit["_source"]


def measure(
    client: Elasticsearch, index: str, analyser: Analyser
) -> tuple[Built, Built, Built, list[Example]]:
    """Split the attested forms into unlinked and linked, and read each."""
    whole, unlinked, linked = Built(), Built(), Built()
    examples: list[Example] = []
    for source in _attested(client, index):
        spelling = source.get("form_fa")
        documents = source.get("attested_docs") or 0
        if not spelling:
            continue
        analysis = analyser.best(spelling)
        whole.add(documents, analysis)
        bucket = unlinked if source.get("attestation_unlinked") else linked
        bucket.add(documents, analysis)
        if analysis is not None:
            examples.append(
                (
                    spelling,
                    analysis.base,
                    analysis.pattern.label_fa,
                    analysis.is_shared,
                    documents,
                )
            )
    return whole, unlinked, linked, examples


def _percent(part: int, whole: int) -> str:
    """A share, written the way the docs quote it."""
    return f"{100 * part / whole:.1f}%" if whole else "—"


def _report(
    rows: tuple[tuple[str, Built], ...], examples: list[Example], seed: int
) -> None:
    """Print the populations, then a sample to be read by eye."""
    header = f"{'':34} {'forms':>9} {'inflection':>11} {'share':>7}"
    print(f"\n{header} {'of which shared':>16}")
    for label, population in rows:
        print(
            f"{label:34} {population.forms:>9,} {population.inflection:>11,} "
            f"{_percent(population.inflection, population.forms):>7} "
            f"{population.shared:>16,}"
        )

    print(f"\n{'':34} {'documents claimed':>18} {'by an inflection':>18} {'share':>7}")
    for label, population in rows:
        print(
            f"{label:34} {population.documents:>18,} "
            f"{population.inflection_documents:>18,} "
            f"{_percent(population.inflection_documents, population.documents):>7}"
        )

    whole = rows[0][1]
    print("\nthe patterns that account for most of it")
    for pattern_id, count in whole.by_pattern.most_common(12):
        print(f"  {count:>7,}  {pattern_id}")

    print(f"\n{SAMPLE} built forms that read as an inflection — read them")
    chosen = random.Random(seed).sample(examples, min(SAMPLE, len(examples)))
    for spelling, base, label, shared, documents in sorted(chosen, key=lambda x: -x[4]):
        mark = "shared" if shared else "clear "
        print(f"  {mark}  {documents:>7,} docs  {spelling:<20} ← {base:<16} {label}")


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus-version", default="v5", help="which derivations index"
    )
    parser.add_argument("--out", type=Path, help="where to write the measurement")
    parser.add_argument(
        "--lexicon", type=Path, help="a snapshot other than the default"
    )
    parser.add_argument("--seed", type=int, default=9, help="which sample to print")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Measure one derivations version against one lexicon snapshot."""
    arguments = _parse(argv)
    with Lexicon.open(arguments.lexicon) as lexicon:
        held = held_from(lexicon)
        snapshot = lexicon.snapshot_id
    analyser = Analyser(held=held, pack_suffixes=pack_suffixes())

    index = index_name("derivations", arguments.corpus_version)
    whole, unlinked, linked, examples = measure(connect(), index, analyser)
    rows = (
        ("every attested built form", whole),
        ("  of them, unlinked", unlinked),
        ("  of them, the lexicon knows it", linked),
    )
    _report(rows, examples, arguments.seed)

    if arguments.out:
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(
            json.dumps(
                {
                    "corpus_version": arguments.corpus_version,
                    "lexicon_snapshot_id": snapshot,
                    "attested": whole.as_row(),
                    "unlinked": unlinked.as_row(),
                    "linked": linked.as_row(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        print(f"\nwritten to {arguments.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
