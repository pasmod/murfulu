"""Check the function-word list against the corpus, and show what it shadows.

    env MURFULU_GANJOOR_PATH=… MURFULU_LEXICON_PATH=… \
        python tools/check_function_words.py --top 200

``rules/function_words.yaml`` is authored, and an authored list drifts. This
recounts the corpus and, for every entry, prints its rank and count beside the
ones the file records, and the lexicon readings it takes the count away from.
**It fails if an entry is not among the ``max_rank`` most frequent spellings**,
which is the list's own measurable criterion; the other two — closed class,
and the function use plainly dominating — are judgements and stay in the file.

``--top N`` also prints the N most frequent spellings that are **not** on the
list, so a reviewer sees what was left out and can argue with it.

Reads the lexicon read-only through :mod:`murfulu.lexicon`.
"""

from __future__ import annotations

import argparse
import sys

from murfulu.corpus import wordtypes
from murfulu.corpus.function_words import loaded
from murfulu.corpus.ganjoor import GanjoorCorpus
from murfulu.corpus.wordtypes import normalise
from murfulu.lexicon.store import Lexicon


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="also print this many frequent spellings that are not listed",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Recount, compare, and say whether every entry still qualifies."""
    arguments = _parse(argv)
    listed = loaded()
    corpus = wordtypes.build(GanjoorCorpus())
    ranked = corpus.most_common(len(corpus))
    rank_of = {word.spelling_fa: n for n, word in enumerate(ranked, start=1)}
    with Lexicon.open() as lexicon:
        readings: dict[str, list[str]] = {}
        for reading in lexicon.all_readings():
            spelling = normalise(reading.spelling_fa)
            readings.setdefault(spelling, []).append(
                f"{reading.latin} ({reading.lexicon_category})"
            )
        snapshot = lexicon.snapshot_id

    print(
        f"list {listed.version}, {len(listed)} spellings, checked on "
        f"{listed.corpus_version}; corpus now {corpus.token_count:,} tokens; "
        f"lexicon {snapshot}"
    )
    failures = []
    covered = 0
    for entry in sorted(listed.by_spelling.values(), key=lambda e: e.rank):
        word = corpus.word_types.get(entry.spelling)
        count = word.total_count if word else 0
        rank = rank_of.get(entry.spelling, 0)
        covered += count
        moved = "" if (rank, count) == (entry.rank, entry.count) else "  (file differs)"
        shadows = ", ".join(readings.get(entry.spelling, [])) or "—"
        print(
            f"  {rank:>5} {entry.spelling:<6} {count:>10,}  {entry.word_class:<13} "
            f"shadows {shadows}{moved}"
        )
        if not rank or rank > listed.max_rank:
            failures.append(entry.spelling)
    share = covered / corpus.token_count if corpus.token_count else 0.0
    print(f"listed spellings hold {covered:,} tokens, {share:.1%} of the text")

    if arguments.top:
        print(f"\nthe {arguments.top} most frequent spellings, unlisted ones shown:")
        for n, word in enumerate(ranked[: arguments.top], start=1):
            if word.spelling_fa in listed:
                continue
            shadows = ", ".join(readings.get(word.spelling_fa, [])) or "—"
            print(f"  {n:>5} {word.spelling_fa:<8} {word.total_count:>10,}  {shadows}")

    if failures:
        print(
            f"FAILED: not among the {listed.max_rank} most frequent: "
            f"{', '.join(failures)}"
        )
        return 1
    print(f"all {len(listed)} among the {listed.max_rank} most frequent spellings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
