"""How much of the corpus the word bank cannot read, and why.

    python tools/measure_bank_gaps.py v17 --top 1000 \
        --text ganjoor:hafez:2132 --text ganjoor:saadi:41293

The reading screen (2026-11-13) shows every word of a text over its Behnevis,
and the drafts for it found about half the words of a ghazal and of a page of
prose with no reading in karbon 1.3.2's word bank. This says how large that
is and what it is made of, so UPSTREAM can quote a number:

``one reading``        the bank reads the spelling one way
``several readings``   the bank reads it more than one way — دل is *Dal*,
                       *Del*, *Dol* and *dall*; the reading screen shows all
``function word``      no reading, and on ``rules/function_words.yaml`` — و
``inflected``          no reading, but strips to a bank word or a verb stem by
                       an inflectional pattern (``corpus/inflection.py``) —
                       بخشم, می‌رود. The patterns over-read: they also take
                       نور and دولت apart. The instrument of open question S8,
                       not a ruling
``uninflected``        no reading and no pattern takes it to one — a word the
                       bank does not have as written (صبر، نعمت، عشق), or an
                       inflection the patterns miss (آید)

for the corpus's most frequent spellings, for all of them weighted by running
words, and for each ``--text`` given, word by word as the reading screen
shows it. Read-only; needs Elasticsearch and the lexicon snapshot.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from typing import Any

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

from murfulu.corpus.function_words import loaded as function_words
from murfulu.corpus.inflection import Analyser, held_from, pack_suffixes
from murfulu.corpus.wordtypes import tokenise
from murfulu.lexicon.store import Lexicon
from murfulu.search.indices import connect

KINDS = (
    "one reading",
    "several readings",
    "function word",
    "inflected",
    "uninflected",
)


def _spellings(client: Elasticsearch, version: str) -> dict[str, tuple[int, int]]:
    """Spelling → (running words, readings the bank gives it)."""
    count: dict[str, int] = {}
    readings: Counter[str] = Counter()
    for hit in scan(
        client,
        index=f"word_types-{version}",
        query={"_source": ["spelling_fa", "total_count", "latin"]},
        size=5000,
    ):
        source = hit["_source"]
        spelling = source["spelling_fa"]
        if source.get("total_count") is not None:
            count[spelling] = source["total_count"]
        if source.get("latin"):
            readings[spelling] += 1
    return {spelling: (n, readings[spelling]) for spelling, n in count.items()}


class Sorter:
    """Puts one spelling into one of :data:`KINDS`."""

    def __init__(self, spellings: dict[str, tuple[int, int]]) -> None:
        self.spellings = spellings
        self.listed = function_words()
        with Lexicon.open() as lexicon:
            self.analyser = Analyser(held_from(lexicon), pack_suffixes())

    def kind(self, spelling: str) -> str:
        """Which of :data:`KINDS` this spelling is."""
        readings = self.spellings.get(spelling, (0, 0))[1]
        if readings:
            return "one reading" if readings == 1 else "several readings"
        if spelling in self.listed:
            return "function word"
        if self.analyser.held.holds(spelling) or self.analyser.best(spelling):
            return "inflected"
        return "uninflected"


def _share(part: int, whole: int) -> str:
    return f"{part / whole:.1%}" if whole else "—"


def _top(sorter: Sorter, top: int) -> list[str]:
    ranked = sorted(sorter.spellings.items(), key=lambda item: -item[1][0])[:top]
    kinds: dict[str, list[str]] = {kind: [] for kind in KINDS}
    for spelling, _ in ranked:
        kinds[sorter.kind(spelling)].append(spelling)
    out = [f"### The {top:,} most frequent spellings", ""]
    for kind in KINDS:
        named = "، ".join(kinds[kind][:20])
        out.append(f"- **{kind}**: {len(kinds[kind]):,} — {named}")
    return out + [""]


def _weighted(sorter: Sorter) -> list[str]:
    words: Counter[str] = Counter()
    types: Counter[str] = Counter()
    for spelling, (n, _) in sorter.spellings.items():
        kind = sorter.kind(spelling)
        words[kind] += n
        types[kind] += 1
    total_words, total_types = sum(words.values()), sum(types.values())
    out = ["### Every spelling", "", "| | spellings | running words |", "|---|---|---|"]
    for kind in KINDS:
        out.append(
            f"| {kind} | {types[kind]:,} ({_share(types[kind], total_types)}) "
            f"| {words[kind]:,} ({_share(words[kind], total_words)}) |"
        )
    return out + [""]


def _text(client: Elasticsearch, sorter: Sorter, version: str, doc: str) -> list[str]:
    source: dict[str, Any] = client.get(index=f"documents-{version}", id=doc)["_source"]
    tokens = tokenise(source["text_fa"])
    kinds = Counter(sorter.kind(one) for one in tokens)
    heading = " · ".join(
        part
        for part in (source.get("author"), source.get("work"), source.get("title"))
        if part
    )
    return [
        f"- `{doc}` ({heading}): {len(tokens):,} words — "
        + ", ".join(f"{kind} {kinds[kind]:,}" for kind in KINDS)
    ]


def main(argv: list[str] | None = None) -> int:
    """Print the measurement as Markdown."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("version", help="the corpus version, e.g. v17")
    parser.add_argument("--top", type=int, default=1000)
    parser.add_argument("--text", action="append", default=[], help="a document id")
    arguments = parser.parse_args(argv)

    client = connect()
    sorter = Sorter(_spellings(client, arguments.version))
    out = [f"## The word bank's gaps, corpus {arguments.version}", ""]
    out += _top(sorter, arguments.top)
    out += _weighted(sorter)
    if arguments.text:
        out += ["### Texts, word by word", ""]
        for doc in arguments.text:
            out += _text(client, sorter, arguments.version, doc)
        out.append("")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
