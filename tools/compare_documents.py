"""Put two corpus versions' texts side by side: documents, lines and counts.

    python tools/compare_documents.py v16 v17 > build/compare-documents-v16-v17.md

``compare_versions.py`` compares what an ingest measured and what a build
produced. It cannot say **which lines** a new version gained or lost, and v17
exists to change exactly that: Ganjoor's position values were read from its
own source code on 2026-11-13, so band second halves came in and the source's
notes went out of the counted text (FINDINGS 2026-11-13).

This reads both ``documents-<version>`` indices and both
``word_types-<version>`` indices from the stack and prints, as Markdown:

* documents in one version and not the other;
* counted lines gained and lost, matched text against text within each
  document, and — where the newer version stored its units — what kind of line
  each one is there (a lost line that the newer version keeps as a note is
  named as one);
* the spellings whose corpus count moved most, and the spellings that appear
  or disappear.

Read-only: it creates, changes and releases nothing. Needs Elasticsearch,
through ``MURFULU_ELASTICSEARCH_URL`` (on the Mac, the forwarder of
``tools/es_forward.py``).
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

from murfulu.search.indices import connect

#: How many spellings each list of movers names.
TOP = 25


@dataclass
class Texts:
    """One version's documents: counted lines, and each line's kind if known."""

    lines: dict[str, Counter[str]] = field(default_factory=dict)
    #: (document, line text) → every position the line has there, from the
    #: stored units. A line written twice in one text can sit in two places.
    kinds: dict[tuple[str, str], set[str]] = field(default_factory=dict)
    #: (document, line text) of every note the version stores and does not count.
    notes: set[tuple[str, str]] = field(default_factory=set)


def _texts(client: Elasticsearch, version: str) -> Texts:
    read = Texts()
    for hit in scan(
        client,
        index=f"documents-{version}",
        query={"query": {"match_all": {}}},
        _source=["document_id", "text_fa", "units"],
        size=2000,
    ):
        source = hit["_source"]
        document = source["document_id"]
        read.lines[document] = Counter(
            line.strip() for line in source.get("text_fa", "").splitlines()
        )
        for unit in source.get("units") or []:
            for line in unit.get("lines") or []:
                # A source line can hold a line break, and text_fa then holds
                # it as two lines; key each piece as text_fa has it.
                for piece in line["text"].splitlines():
                    key = (document, piece.strip())
                    if unit["kind"] == "note":
                        read.notes.add(key)
                    else:
                        read.kinds.setdefault(key, set()).add(line["position"])
    return read


def _counts(client: Elasticsearch, version: str) -> dict[str, tuple[int, int]]:
    """Each spelling's corpus count and document count, once per spelling."""
    counted: dict[str, tuple[int, int]] = {}
    for hit in scan(
        client,
        index=f"word_types-{version}",
        query={"query": {"match_all": {}}},
        _source=["spelling_fa", "total_count", "doc_count"],
        size=5000,
    ):
        source = hit["_source"]
        total = source.get("total_count")
        if total is None:
            # A function word's reading carries no count; its spelling's own
            # document does.
            continue
        counted[source["spelling_fa"]] = (total, source.get("doc_count") or 0)
    return counted


def _label(positions: set[str]) -> str:
    """One name for a gained line: a band second half if it is one anywhere.

    The line came in because one of its places is newly counted; when the same
    words also stand elsewhere in the text (a refrain), that is the place.
    """
    if "band_second" in positions:
        return "band_second"
    return " or ".join(sorted(positions)) or "unknown"


def _moved(
    before: dict[str, Counter[str]], after: dict[str, Counter[str]]
) -> Iterator[tuple[str, str, int]]:
    """(document, line, ±n) for every counted line gained or lost."""
    for document in before.keys() | after.keys():
        old = before.get(document, Counter())
        new = after.get(document, Counter())
        for line, n in (new - old).items():
            yield document, line, n
        for line, n in (old - new).items():
            yield document, line, -n


def _table(rows: Sequence[tuple[str, ...]], header: tuple[str, ...]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(row) + " |" for row in rows]
    return out


def report(client: Elasticsearch, old: str, new: str) -> list[str]:
    """The comparison, as Markdown lines."""
    before, after = _texts(client, old), _texts(client, new)
    out = [f"## Texts, {old} → {new}", ""]

    gone = sorted(before.lines.keys() - after.lines.keys())
    came = sorted(after.lines.keys() - before.lines.keys())
    out += [
        f"Documents: {len(before.lines):,} → {len(after.lines):,}; "
        f"**{len(came):,} added, {len(gone):,} removed**.",
        "",
    ]
    if came:
        out.append("Added: " + ", ".join(f"`{one}`" for one in came[:TOP]))
    if gone:
        # A removed document left no units to say why; the dump does. On
        # v16 → v17 every one is a page whose only lines are notes.
        out.append("Removed: " + ", ".join(f"`{one}`" for one in gone[:TOP]))
    out.append("")

    gained: Counter[str] = Counter()
    lost: Counter[str] = Counter()
    touched: set[str] = set()
    for document, line, n in _moved(before.lines, after.lines):
        touched.add(document)
        if n > 0:
            gained[_label(after.kinds.get((document, line), set()))] += n
        else:
            lost[
                "a note in " + new
                if (document, line) in after.notes
                else "not in " + new
            ] -= n
    total_old = sum(sum(c.values()) for c in before.lines.values())
    total_new = sum(sum(c.values()) for c in after.lines.values())
    out += [
        f"Counted lines: {total_old:,} → {total_new:,} "
        f"({total_new - total_old:+,}), in {len(touched):,} documents.",
        "",
        *_table(
            [(kind, f"+{n:,}") for kind, n in gained.most_common()]
            + [(why, f"−{n:,}") for why, n in lost.most_common()],
            ("line", "lines"),
        ),
        "",
    ]

    old_counts, new_counts = _counts(client, old), _counts(client, new)
    deltas = {
        spelling: new_counts.get(spelling, (0, 0))[0]
        - old_counts.get(spelling, (0, 0))[0]
        for spelling in old_counts.keys() | new_counts.keys()
    }
    moved = [s for s, d in deltas.items() if d]
    appeared = sorted(
        new_counts.keys() - old_counts.keys(), key=lambda s: -new_counts[s][0]
    )
    vanished = sorted(
        old_counts.keys() - new_counts.keys(), key=lambda s: -old_counts[s][0]
    )
    out += [
        f"## Word counts, {old} → {new}",
        "",
        f"Spellings whose corpus count moved: **{len(moved):,}** of "
        f"{len(new_counts):,}; {len(appeared):,} appear, {len(vanished):,} "
        f"disappear. Running words: "
        f"{sum(c for c, _ in old_counts.values()):,} → "
        f"{sum(c for c, _ in new_counts.values()):,}.",
        "",
        "Largest gains:",
        "",
        *_table(
            [
                (
                    s,
                    f"{old_counts.get(s, (0, 0))[0]:,}",
                    f"{new_counts.get(s, (0, 0))[0]:,}",
                    f"{deltas[s]:+,}",
                )
                for s in sorted(moved, key=lambda s: -deltas[s])[:TOP]
            ],
            ("spelling", old, new, "change"),
        ),
        "",
        "Largest losses:",
        "",
        *_table(
            [
                (
                    s,
                    f"{old_counts.get(s, (0, 0))[0]:,}",
                    f"{new_counts.get(s, (0, 0))[0]:,}",
                    f"{deltas[s]:+,}",
                )
                for s in sorted(moved, key=lambda s: deltas[s])[:TOP]
                if deltas[s] < 0
            ],
            ("spelling", old, new, "change"),
        ),
        "",
        "Appear, most frequent first: "
        + "، ".join(f"{s} ({new_counts[s][0]:,})" for s in appeared[:TOP]),
        "",
        "Disappear, most frequent first: "
        + "، ".join(f"{s} ({old_counts[s][0]:,})" for s in vanished[:TOP]),
        "",
    ]
    return out


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("old", help="the version being replaced, e.g. v16")
    parser.add_argument("new", help="the version replacing it, e.g. v17")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Print the comparison; exit 0 whatever it says — it measures, never decides."""
    arguments = _parse(argv)
    print("\n".join(report(connect(), arguments.old, arguments.new)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
