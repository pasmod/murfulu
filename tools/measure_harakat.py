"""Where a word's own harakat rule out the word bank's readings, over the corpus.

    python tools/measure_harakat.py v17 --top 150 > data/harakat-v17.md

The reading screen shows a reading paler when the text's own vowel signs rule
it out (2026-11-14, the project lead's choice; ``search/harakat.py``). This
counts how often that happens and lists, for the linguist, the words whose
signs fit **none** of the bank's readings: «تُرکان» where the bank has only
*Tarkān*. Such a word is one of three things, and only the linguist can say
which — a reading the bank lacks (*Torkān*), an edition's wrong sign, or a
word that is not Persian at all (the Arabic «مِنْ» is not the pronoun *man*).

Every word here is counted as the reading screen splits it, and only in units
that are counted (not the source's notes). Read-only; needs Elasticsearch.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from typing import Any

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

from murfulu.search import harakat
from murfulu.search.indices import connect
from murfulu.search.texts import _source_line, _units, tokens

Reading = tuple[str, tuple[str, ...]]


def _readings(client: Elasticsearch, version: str) -> dict[str, list[Reading]]:
    """Spelling → the bank's readings of it, each with its variants."""
    found: dict[str, list[Reading]] = defaultdict(list)
    for hit in scan(
        client,
        index=f"word_types-{version}",
        query={"query": {"exists": {"field": "latin"}}},
        _source=["spelling_fa", "latin", "latin_variants"],
    ):
        source = hit["_source"]
        found[source["spelling_fa"]].append(
            (source["latin"], tuple(source.get("latin_variants") or ()))
        )
    return found


def _signed(written: str) -> str:
    """The word as written, without what its last letter carries: the ezafe's kasra."""
    shape = harakat.letters(written)
    order = (harakat.SHADDA, harakat.FATHA, harakat.DAMMA, harakat.KASRA, harakat.SUKUN)
    return "".join(
        letter
        + ("" if at == len(shape) - 1 else "".join(s for s in order if s in signs))
        for at, (letter, signs) in enumerate(shape)
    )


def measure(client: Elasticsearch, version: str) -> dict[str, Any]:
    """Count every word of the corpus against its signs and the bank's readings."""
    bank = _readings(client, version)
    counts: Counter[str] = Counter()
    none_fits: Counter[tuple[str, str]] = Counter()
    pale: Counter[tuple[str, str, tuple[str, ...]]] = Counter()
    texts_of: dict[tuple[str, str], set[str]] = defaultdict(set)
    for hit in scan(
        client,
        index=f"documents-{version}",
        query={"query": {"match_all": {}}},
        _source=["document_id", "units", "text_fa"],
    ):
        source = hit["_source"]
        for unit in _units(source):
            if unit.get("kind") == "note":
                continue
            for line in unit.get("lines") or []:
                for piece in _source_line(line):
                    for token in tokens(piece):
                        if not token.spelling:
                            continue
                        counts["words"] += 1
                        if not harakat.has_signs(token.fa):
                            continue
                        counts["with signs"] += 1
                        readings = bank.get(token.spelling)
                        if not readings:
                            continue
                        counts["with signs and a reading"] += 1
                        ruled = [
                            latin
                            for latin, variants in readings
                            if harakat.against(token.fa, latin, variants)
                        ]
                        if not ruled:
                            continue
                        key = (token.spelling, _signed(token.fa))
                        if len(ruled) < len(readings):
                            counts["some readings pale"] += 1
                            pale[(*key, tuple(sorted(ruled)))] += 1
                        else:
                            counts["no reading fits"] += 1
                            none_fits[key] += 1
                            texts_of[key].add(source.get("document_id", hit["_id"]))
    return {
        "counts": counts,
        "none_fits": none_fits,
        "pale": pale,
        "texts_of": texts_of,
        "bank": bank,
    }


def report(found: dict[str, Any], version: str, top: int) -> str:
    """The counts and both lists, as Markdown."""
    counts: Counter[str] = found["counts"]
    bank: dict[str, list[Reading]] = found["bank"]
    words = counts["words"] or 1
    lines = [
        f"# Harakat against the word bank's readings, corpus {version}",
        "",
        "Made by `tools/measure_harakat.py`. A reading is *against* a word when the",
        "word's own vowel signs rule it out (`search/harakat.py`); the reading screen",
        "shows it paler. The last letter's signs are not read (the ezafe).",
        "",
        "| | words | of all |",
        "|---|---:|---:|",
    ]
    for name in (
        "words",
        "with signs",
        "with signs and a reading",
        "some readings pale",
        "no reading fits",
    ):
        lines.append(f"| {name} | {counts[name]:,} | {counts[name] / words:.2%} |")
    lines += [
        "",
        f"## No reading fits: the {top} most frequent",
        "",
        "Each is a reading the bank lacks, a wrong sign in the edition, or a word",
        "that is not Persian (Arabic quotations). For the linguist.",
        "",
        "| written | times | texts | the bank's readings | one text |",
        "|---|---:|---:|---|---|",
    ]
    for (spelling, signed), times in found["none_fits"].most_common(top):
        texts = sorted(found["texts_of"][(spelling, signed)])
        readings = ", ".join(latin for latin, _ in sorted(bank[spelling]))
        lines.append(
            f"| {signed} | {times:,} | {len(texts):,} | {readings} | {texts[0]} |"
        )
    lines += [
        "",
        "## Readings shown pale: the 40 most frequent",
        "",
        "| written | times | pale | still alike |",
        "|---|---:|---|---|",
    ]
    for (spelling, signed, ruled), times in found["pale"].most_common(40):
        kept = ", ".join(
            sorted(latin for latin, _ in bank[spelling] if latin not in ruled)
        )
        lines.append(f"| {signed} | {times:,} | {', '.join(ruled)} | {kept} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Measure one corpus version and print the report."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("version", help="corpus version, e.g. v17")
    parser.add_argument("--top", type=int, default=150)
    args = parser.parse_args(argv)
    found = measure(connect(), args.version)
    sys.stdout.write(report(found, args.version, args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
