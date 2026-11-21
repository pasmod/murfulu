"""Rank the spellings the reading screen leaves to a person; say what deciding saves.

    python tools/measure_unsure_spellings.py v22 > data/behnevis-unsure-v22.md

Reads every text of the corpus version from Elasticsearch, word by word, as
the reading screen reads it (:func:`murfulu.behnevis.serve.annotate`: the
model, the text's own signs, و by the verse rule, and the poem's metre where
the labels file is beside the model and ``MURFULU_BEHNEVIS_METRE`` is not
``off``, as served since 2026-11-21). Counts, per spelling, the running words
below the red edge (0.7), ranks the spellings by them, and writes:

- ``data/behnevis-unsure-<version>.json``, beside the model (not in git: it
  holds karbon's readings, NOTICE): the ``--top`` spellings with their
  readings, neighbours and three example places, as the API serves them;
- the report, on standard output: how many running words the top 100, 500
  and 2,000 spellings hold, by kind of decision, and how far the share left
  to a person would fall if they were decided;
- ``data/behnevis-unsure-tally-<version>.pickle``, the counts themselves (not
  in git), so ``--from-tally`` can write the list and report again without
  reading the corpus.

Needs ``MURFULU_BEHNEVIS_PATH`` (the model), ``MURFULU_LEXICON_PATH`` and
Elasticsearch (``tools/es_forward.py``); read-only on all three. Reads the
corpus in ``--workers`` slices at once; about ten minutes on 14 cores.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import pickle
import sys
import time
from collections import Counter
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from elasticsearch.helpers import scan

from murfulu.behnevis import serve, unsure
from murfulu.behnevis.transcribe import Transcriber, key
from murfulu.lexicon.store import Lexicon
from murfulu.search.indices import connect
from murfulu.search.texts import lay_out

DATA = Path(__file__).resolve().parents[1] / "data"
TOPS = (100, 500, 1_000, 2_000, 5_000)
#: A spelling keeps its neighbours and examples when the corpus has it this
#: often: the 2,000th spelling of the list leaves far more to a person.
WATCH_FROM = 100

_model: Transcriber | None = None


def _start() -> None:
    """Load the model once per worker."""
    global _model  # noqa: PLW0603 (one model per process)
    _model = serve.loaded()
    if _model is None:
        raise SystemExit("no model: set MURFULU_BEHNEVIS_PATH and MURFULU_LEXICON_PATH")


def _heading(source: dict[str, Any]) -> str:
    """Author, work, sections and title, as the reading screen joins them."""
    parts = [
        source.get("author"),
        source.get("work"),
        *(source.get("section") or []),
        source.get("title"),
    ]
    return " · ".join(p for p in parts if p)


def read_slice(job: tuple[str, int, int, frozenset[str], int | None]) -> unsure.Tally:
    """One slice of the corpus, read and counted (``most`` texts, for a trial)."""
    version, slice_id, slices, watch, most = job
    assert _model is not None
    tally = unsure.Tally(watch=watch)
    query: dict[str, Any] = {"query": {"match_all": {}}}
    if slices > 1:
        query["slice"] = {"id": slice_id, "max": slices}
    for hit in scan(
        connect(),
        index=f"documents-{version}",
        query=query,
        size=100,
        _source=[
            "units",
            "text_fa",
            "document_id",
            "author",
            "work",
            "section",
            "title",
        ],
    ):
        if most is not None and most <= 0:
            break
        most = None if most is None else most - 1
        source = hit["_source"]
        document = source.get("document_id") or hit["_id"]
        units, _, _ = lay_out(source, 0, 10**9)
        serve.annotate(units, _model, serve.metre_of(document))
        heading = _heading(source)
        for unit in units:
            for at, line in enumerate(unit.get("lines") or []):
                words = line.get("words")
                if words:
                    tally.add_line(
                        words,
                        {
                            "document_id": document,
                            "unit": unit["index"],
                            "line": at,
                            "heading": heading,
                        },
                    )
    return tally


def read_corpus(
    version: str, workers: int, watch: frozenset[str], trial: int | None, metre: bool
) -> tuple[unsure.Tally, float]:
    """Every text of the version, read in slices at once, and how long it took."""
    print(
        f"reading {version} in {workers} slices; metre "
        f"{'on' if metre else 'off'}; details kept for {len(watch):,} spellings",
        file=sys.stderr,
    )
    started = time.monotonic()
    tally = unsure.Tally(watch=watch)
    jobs = [(version, i, workers, watch, trial) for i in range(workers)]
    with multiprocessing.get_context("spawn").Pool(workers, initializer=_start) as pool:
        for done, part in enumerate(pool.imap_unordered(read_slice, jobs), start=1):
            tally.merge(part)
            print(
                f"slice {done}/{workers}: {tally.words:,} words so far",
                file=sys.stderr,
            )
    return tally, time.monotonic() - started


def watched(version: str) -> frozenset[str]:
    """Spellings the corpus has at least ``WATCH_FROM`` times, keyed."""
    counts: dict[str, int] = json.loads(
        (DATA / f"behnevis-counts-{version}.json").read_text(encoding="utf-8")
    )
    keyed: Counter[str] = Counter()
    for spelling, n in counts.items():
        keyed[key(spelling)] += n
    return frozenset(s for s, n in keyed.items() if n >= WATCH_FROM)


def share(n: int, of: int) -> str:
    """A share as the report prints it."""
    return f"{n / of:.1%}" if of else "—"


KIND_NAMES = {
    unsure.CHOICE: "a choice among the bank's readings",
    unsure.ONE: "the bank's one reading, doubted",
    unsure.MISSING: "missing from the word bank",
}


def report(  # noqa: PLR0913, PLR0915 (one report, many parts)
    version: str,
    tally: unsure.Tally,
    listed: list[dict[str, Any]],
    covered: list[unsure.Covered],
    fits: dict[str, unsure.Fit],
    metre: bool,
    seconds: float,
) -> list[str]:
    """The report, as Markdown lines."""
    words, red = tally.words, tally.unsure_words
    out = [
        f"# The spellings the reading screen leaves to a person, corpus {version}",
        "",
        "Made by `tools/measure_unsure_spellings.py` (the counting:",
        "`src/murfulu/behnevis/unsure.py`). **A first, rough measurement, not a",
        "result**: each number carries its limits beside it.",
        "",
        "## 0. How it was read",
        "",
        f"Every text of corpus {version}, word by word, as the reading screen reads "
        "it: the model, the text's own signs, و by the verse rule, and the poem's "
        f"metre {'on, as served since 2026-11-21' if metre else 'OFF'}. Each word "
        "between its neighbours in its line. A word is *left to a person* when its "
        f"confidence is below {unsure.RED} (red on the screen) or the model has no "
        f"reading for it. Read in {seconds / 60:.0f} minutes.",
        "",
        f"- Running words read: {words:,}.",
        f"- Left to a person: {red:,} ({share(red, words)}).",
        f"- Spellings with at least one such place: {len(tally.ranked()):,}.",
        "",
        "Limits: the share left to a person says nothing about whether the words",
        "taken as read are right; `data/behnevis-eval-v22.md` and",
        "`data/behnevis-metre-eval-v22.md` measure that, on the hard marked words.",
        "The metre measurement's sample (one poem in 50) left 33.2 % to a person;",
        "this reads every text, prose and poems without a known metre too.",
        "",
        "## 1. How many running words the most frequent unsure spellings hold",
        "",
        "Spellings ranked by the running words they leave to a person. Each kind",
        "is what a decision there means (`unsure.kind_of`): *a choice among the",
        "bank's readings* is learned at the model's next build; *the bank's one",
        "reading, doubted* is learned when a person confirms the bank's reading,",
        "and goes to karbon when they name another; *missing from the word bank*",
        "goes to karbon, and the model learns it only once the bank holds it",
        "(DECISIONS 2026-11-14).",
        "",
        "| top spellings | unsure running words they hold | share of all left to a "
        "person | share of all running words | "
        + " | ".join(KIND_NAMES[k] for k in unsure.KINDS)
        + " |",
        "|---:|---:|---:|---:|" + "---:|" * len(unsure.KINDS),
    ]
    for c in covered:
        out.append(
            f"| {c.top:,} | {c.unsure:,} | {share(c.unsure, red)} | "
            f"{share(c.unsure, words)} | "
            + " | ".join(share(c.by_kind[k], words) for k in unsure.KINDS)
            + " |"
        )
    missing = [one for one in listed if one["kind"] == unsure.MISSING]
    sources: Counter[str] = Counter()
    for one in missing:
        sources.update(one["sources"])
    out += [
        "",
        "The kind columns are shares of all running words. For comparison, all",
        f"{len(tally.ranked()):,} spellings with an unsure place hold {red:,}.",
        f"Of the {len(missing):,} listed spellings *missing from the word bank*,",
        f"{sources['inflected']:,} unsure places are inflected forms the bank's",
        f"stems build readings for (*konam*, *nabāšad*) and {sources['letters']:,}",
        "are guesses from the letters (الله، نور، شمع): words karbon lacks.",
        "",
        "## 2. If they were decided: what would be left to a person",
        "",
        "Upper bounds: every unsure place of a decided spelling counted as taken",
        "from the person, as if one decision (or a few, by neighbour) fitted all",
        "its places. Section 3 says how far one reading per spelling is from",
        "that. Read from the listed spellings, so up to the list's length.",
        "",
        "| top spellings decided | left to a person now | after the next build "
        "| after karbon also takes the readings it lacks |",
        "|---:|---:|---:|---:|",
    ]
    for top in (t for t in TOPS if t <= len(listed)):
        chosen = listed[:top]
        learned = sum(
            one["unsure"]
            for one in chosen
            if one["kind"] == unsure.CHOICE
            or (one["kind"] == unsure.ONE and not unsure.marks_another(one))
        )
        every = sum(one["unsure"] for one in chosen)
        out.append(
            f"| {top:,} | {share(red, words)} | {share(red - learned, words)} | "
            f"{share(red - every, words)} |"
        )
    another = [one for one in listed if unsure.marks_another(one)]
    out += [
        "",
        "*After the next build* counts the choices among the bank's readings and",
        "the spellings with one bank reading that the editions' marks do not",
        f"contradict. The {len(another):,} listed spellings whose marks fit another",
        "reading (section 2b) wait for karbon with the missing ones.",
        "",
        "Limits: a *one* spelling the editions never marked often enough is",
        "counted as learned, though a person may name another reading there too;",
        "and a decided place counts as taken although a decision *everywhere*",
        "can read a place wrong that the model read right (section 3).",
        "",
        "## 2b. Where the bank's one reading is not the one the editions mark",
        "",
        f"Listed spellings with one bank reading and at least {unsure.MIN_MARKED}",
        "marked places, whose marks fit another reading more often than any",
        "the bank holds: mostly verb forms the bank reads as nouns (UPSTREAM B9).",
        f"{len(another):,} spellings, {sum(o['unsure'] for o in another):,} unsure "
        "running words. The first twelve:",
        "",
        "| spelling | unsure | the bank's reading | the editions' marks fit |",
        "|---|---:|---|---|",
    ]
    for one in another[:12]:
        marked = one["marked"]
        out.append(
            f"| {one['written']} | {one['unsure']:,} | {', '.join(one['known'])} | "
            f"{marked['reading']} ({marked['best']:,} of {marked['fitted']:,}) |"
        )
    out += [
        "",
        "## 3. Would one reading per spelling do?",
        "",
        "For each listed spelling the corpus's marked places (`behnevis-marked`,",
        "the editions' vowel signs, quotations left out), read against the",
        "readings the list names for it: the share of places whose signs fit the",
        "one reading that fits most often. Weighted by the spelling's unsure",
        "running words; only spellings with at least 5 marked places that fit a",
        "named reading.",
        "",
        "| top spellings | kind | spellings with 5+ fitting marked places | their "
        "unsure running words | one reading fits |",
        "|---:|---|---:|---:|---:|",
    ]
    for top in (100, 500, 2_000):
        for k in unsure.KINDS:
            chosen = [
                one
                for one in listed[:top]
                if one["kind"] == k
                and fits.get(one["spelling"])
                and fits[one["spelling"]].fitted >= 5
            ]
            weight = sum(one["unsure"] for one in chosen)
            if not weight:
                out.append(f"| {top:,} | {KIND_NAMES[k]} | 0 | 0 | — |")
                continue
            mean = (
                sum(
                    one["unsure"]
                    * fits[one["spelling"]].best
                    / fits[one["spelling"]].fitted
                    for one in chosen
                )
                / weight
            )
            out.append(
                f"| {top:,} | {KIND_NAMES[k]} | {len(chosen):,} | {weight:,} | "
                f"{mean:.0%} |"
            )
    out += [
        "",
        "Limits: editions mark the hard places, so a spelling's marked places",
        "lean to its rarer reading and the share is pessimistic; the signs check",
        "only the letters they mark, so two readings that differ elsewhere both",
        "fit; and a reading none of the named ones (a reading the bank lacks) is",
        "not counted at all. Where the share is low, a decision *by neighbour*",
        "(after or before one word) is the safer scope; the screen offers both.",
        "",
        "## 4. The 100 spellings that leave the most to a person",
        "",
        "*Unsure* counts the running words the screen shows red (below 0.7);",
        "*places* all of the spelling's running words; *read as* the model's most",
        "frequent reading at the unsure places; the last column the reading that",
        "fits most of the spelling's marked places (section 3), and how often.",
        f"The full list (the top {len(listed):,}) is the JSON file beside the model,",
        "served on the reading screen's list of the most frequent unsure words",
        "(`/texts?view=unsure`).",
        "",
        "| # | spelling | unsure | places | kind | bank's readings | read as | "
        "fits most marked places |",
        "|---:|---|---:|---:|---|---:|---|---:|",
    ]
    for one in listed[:100]:
        fit = fits.get(one["spelling"])
        fitted = (
            f"{fit.reading} {fit.best / fit.fitted:.0%} of {fit.fitted:,}"
            if fit and fit.fitted
            else "—"
        )
        read_as = one["read_as"][0][0] if one["read_as"] else "—"
        out.append(
            f"| {one['rank']} | {one['written']} | {one['unsure']:,} | "
            f"{one['places']:,} | {one['kind']} | {len(one['known'])} | "
            f"{read_as} | {fitted} |"
        )
    return out


def main(argv: list[str] | None = None) -> int:
    """Read the corpus, write the list beside the model, print the report."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("version", help="corpus version, e.g. v22")
    parser.add_argument(
        "--top", type=int, default=2_000, help="how many spellings the list keeps"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, (os.cpu_count() or 2) - 4),
        help="slices of the corpus read at once",
    )
    parser.add_argument(
        "--trial",
        type=int,
        default=None,
        help="read only this many texts per slice (a quick trial, not a measurement)",
    )
    parser.add_argument(
        "--from-tally",
        action="store_true",
        help="write the list and report from the counts the last run kept, "
        "without reading the corpus again",
    )
    args = parser.parse_args(argv)
    version = args.version
    kept = DATA / f"behnevis-unsure-tally-{version}.pickle"

    model_path = serve.path()
    if model_path is None:
        raise SystemExit("MURFULU_BEHNEVIS_PATH names no model file")
    metre = serve.metre_path() is not None
    model = serve.loaded()
    if model is None:
        raise SystemExit("the model did not load (is MURFULU_LEXICON_PATH set?)")
    watch = watched(version)
    if args.from_tally:
        # Our own file, written below by the last full run: the counts, read
        # back so the report can change without reading the corpus again.
        with kept.open("rb") as stored:
            tally, seconds = pickle.load(stored)  # noqa: S301 (our own file)
    else:
        tally, seconds = read_corpus(version, args.workers, watch, args.trial, metre)
        if args.trial is None:
            with kept.open("wb") as store:
                pickle.dump((tally, seconds), store)

    listed = unsure.entries(tally, model.bank, model.functions, args.top)
    missing = [one["spelling"] for one in listed if one["spelling"] not in watch]
    if missing:
        print(
            f"warning: {len(missing)} listed spellings kept no details "
            f"(below {WATCH_FROM} in the counts): {missing[:10]}",
            file=sys.stderr,
        )
    tops = [t for t in TOPS if t <= len(tally.ranked())]
    covered = unsure.coverage(tally, model.bank, model.functions, tops)
    with (DATA / f"behnevis-marked-{version}.jsonl").open(encoding="utf-8") as lines:
        fits = unsure.single_reading_fit(listed, (json.loads(line) for line in lines))
    for one in listed:
        fit = fits.get(one["spelling"])
        one["marked"] = asdict(fit) if fit else None
    with Lexicon.open() as lexicon:
        snapshot = lexicon.snapshot_id
    unsure.write(
        unsure.path_beside(model_path),
        {
            "corpus_version": version,
            "lexicon_snapshot_id": snapshot,
            "model": model_path.name,
            "metre": metre,
            "red": unsure.RED,
            "words": tally.words,
            "unsure_words": tally.unsure_words,
            "spellings_unsure": len(tally.ranked()),
            "measured": date.today().isoformat(),
            "covered": [
                {"top": c.top, "unsure": c.unsure, "by_kind": c.by_kind}
                for c in covered
            ],
        },
        listed,
    )
    print(
        f"written: {unsure.path_beside(model_path)} ({len(listed):,} spellings)",
        file=sys.stderr,
    )
    print("\n".join(report(version, tally, listed, covered, fits, metre, seconds)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
