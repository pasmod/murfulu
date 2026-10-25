"""Ingest a corpus into Elasticsearch: documents, then word types.

    python tools/run_ingest.py --corpus-version v1
    python tools/run_ingest.py --corpus-version v1 --no-release
    python tools/run_ingest.py --corpus-version v1 --report-only \
        --report-out data/corpus_report-v1.json

Three steps, in order. Read the corpus into ``documents``. Count every
spelling. Link the spellings to the lexicon and write them into
``word_types``.

**The alias only moves when both writes are complete.** A half-filled index
that the app is already serving would give wrong counts with nothing to show
that anything went wrong, so ``--no-release`` exists for building a version
without putting it into service.

``--report-only`` runs the counting and the linking and writes what they
measured, without creating an index or moving an alias. It is how a version
that is already in service gets described without being rebuilt.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from murfulu.corpus import link, report, wordtypes
from murfulu.corpus.function_words import loaded as function_words
from murfulu.corpus.ganjoor import CENTURIES_VARIABLE, GanjoorCorpus
from murfulu.lexicon.store import Lexicon
from murfulu.search import ingest
from murfulu.search.backfill import AffixMap
from murfulu.search.indices import IndexAdmin, connect


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-version", default="v1")
    parser.add_argument(
        "--no-release",
        action="store_true",
        help="build the indices but leave the aliases where they are",
    )
    parser.add_argument(
        "--affix-map",
        type=Path,
        help="what tools/run_precompute.py --affix-map-out wrote",
    )
    parser.add_argument(
        "--skip-documents",
        action="store_true",
        help="only rebuild word types; the poems are the slow half",
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        help="where to write what this run measured, for the corpus screen",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="count and link, write the report, touch no index",
    )
    parser.add_argument(
        "--unlinked-out",
        type=Path,
        help="every spelling the lexicon has no entry for, as TSV",
    )
    return parser.parse_args(argv)


def _write_unlinked(linked: link.LinkResult, destination: Path) -> int:
    """Write the whole unmatched pile, biggest first.

    It is a deliverable in its own right — words in classical Persian the
    dictionary does not cover — and it is far too long for any screen, so it
    leaves the system as a file rather than through the API.
    """
    rows = sorted(linked.unlinked, key=lambda item: -item.word.total_count)
    with destination.open("w", encoding="utf-8") as handle:
        handle.write("spelling_fa\ttotal_count\tdoc_count\tauthor_count\n")
        for item in rows:
            word = item.word
            handle.write(
                f"{word.spelling_fa}\t{word.total_count}\t"
                f"{word.doc_count}\t{word.author_count}\n"
            )
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    """Run the ingest and print what each step did."""
    arguments = _parse(argv)
    version = arguments.corpus_version
    # A report-only run measures the corpus and writes nothing to the cluster,
    # so a version that is already being served can be described without any
    # risk of rebuilding it.
    report_only = arguments.report_only
    client = None if report_only else connect()
    admin = None if client is None else IndexAdmin(client)

    corpus_source = GanjoorCorpus()
    written = []

    # Without the poet→century table every document is undated, every word
    # gets a null first and last century, and the dispersion chart — the thing
    # that separates a real word from one poet's rhyme — has nothing to draw.
    # Nothing fails, which is exactly why it has to be said out loud.
    if not corpus_source.centuries:
        print(
            f"centuries      none loaded. Set {CENTURIES_VARIABLE} or every "
            f"word will be undated."
        )
    else:
        print(f"centuries      {len(corpus_source.centuries):,} poets dated")

    if not arguments.skip_documents and admin is not None and client is not None:
        started = time.monotonic()
        admin.create(ingest.DOCUMENTS, version)
        result = ingest.write_documents(client, version, corpus_source)
        print(f"documents      {result.summary()} ({time.monotonic() - started:,.0f}s)")
        # A table entry naming a slug the corpus does not use dates nothing
        # and looks exactly like one that works. That is how فردوسی — the
        # largest poet in the corpus — came to be undated.
        stale = corpus_source.centuries_without_a_poet()
        if stale:
            print(
                f"centuries      {len(stale)} table entries match no poet here: "
                f"{', '.join(stale[:6])}" + ("…" if len(stale) > 6 else "")
            )
        if not result.complete:
            print(f"first failure  {result.failures[0]}")
            return 1
        written.append(ingest.DOCUMENTS)

    started = time.monotonic()
    corpus = wordtypes.build(corpus_source)
    print(
        f"counted        {corpus.document_count:,} documents, "
        f"{corpus.token_count:,} words, {len(corpus):,} spellings "
        f"({time.monotonic() - started:,.0f}s)"
    )

    with Lexicon.open() as lexicon:
        print(f"overrides      {lexicon.describe_overrides()}")
        linked = link.link(corpus, lexicon)
    print(f"link           {linked.coverage.summary()}")

    if arguments.unlinked_out:
        count = _write_unlinked(linked, arguments.unlinked_out)
        print(f"unlinked       {count:,} spellings → {arguments.unlinked_out}")

    if arguments.report_out:
        measured = report.build(corpus_source, corpus, linked, version)
        report.write(measured, arguments.report_out)
        print(
            f"report         {measured.type_share:.1%} of spellings, "
            f"{measured.token_share:.1%} of text → {arguments.report_out}"
        )

    if report_only or admin is None or client is None:
        print("report only    no index was created and no alias moved")
        return 0

    formed = None
    if arguments.affix_map:
        formed = AffixMap.from_document(
            json.loads(arguments.affix_map.read_text(encoding="utf-8"))
        )
        print(f"affix map      {len(formed):,} word types traced to a rule")
    else:
        # Leaving it out does not fail. It builds a `word_types` index where no
        # corpus word was formed by any rule, so every `rule:` search answers
        # nothing and looks exactly like a rule that formed nothing. v6 and v7
        # were both built this way and both were released; the same shape of
        # silence as the missing century table above.
        print(
            "affix map      none given. Every corpus word will say no rule "
            "formed it. Pass --affix-map."
        )

    listed = function_words()
    print(
        f"function words {len(listed)} spellings: their readings carry no count "
        f"(rules/function_words.yaml {listed.version})"
    )
    started = time.monotonic()
    admin.create(ingest.WORD_TYPES, version)
    result = ingest.write_word_types(client, version, linked, formed, listed=listed)
    print(f"word types     {result.summary()} ({time.monotonic() - started:,.0f}s)")
    if not result.complete:
        print(f"first failure  {result.failures[0]}")
        return 1
    written.append(ingest.WORD_TYPES)

    if arguments.no_release:
        print(f"built          {', '.join(written)}-{version}, aliases unchanged")
        return 0
    for alias in written:
        admin.release(alias, version)
    print(f"released       {', '.join(written)} now serving {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
