"""Measure whether the poem's metre makes the automatic Behnevis surer.

    python tools/extract_metre_lines.py v22 --ganjoor CACHE_DIR   # once
    python tools/evaluate_behnevis_metre.py v22 > data/behnevis-metre-eval-v22.md

Needs what ``tools/evaluate_behnevis.py`` needs (the model files of
``tools/build_behnevis.py`` and the lexicon) and the poems with a known metre
that ``tools/extract_metre_lines.py`` writes. No Elasticsearch. An experiment:
nothing here changes the served model (:mod:`murfulu.behnevis.metre`).

Two measurements, each **before** (the model as it is) **and after** (the same
words weighed by the metre, :class:`murfulu.behnevis.metre.Metre`):

1. **Marked words, poets held out.** The same method as the evaluation's
   section 1: the model learns without one poet in five
   (:func:`murfulu.behnevis.folds.fold_model`); here it reads every verse half of those
   poets' poems that has a known metre and a vowel sign on some word, **with
   every sign of the line hidden**, and a marked word's reading counts as
   right when its signs fit it. Each wrong reading is put in one of three
   kinds, so the limit of the metre is measured rather than assumed:

   - *presence or length*: some reading the model offered fits the signs and
     behaves differently from the wrong one in a line — the metre can prefer
     it;
   - *vowel quality*: every reading offered that fits the signs behaves as
     the wrong one does in any line (*kenār*, *kanār*) — the metre cannot;
   - *not offered*: no reading the model offered fits the signs.

2. **What is left to a person.** Every running word of one poem in
   ``--sample`` (by a stable hash of the poem's id), read as the reading screen
   reads it — the full model, the text's own signs used, و by the verse rule —
   then weighed by the metre. The share at or above each threshold.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import zlib
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from murfulu.behnevis.choice import Answered
from murfulu.behnevis.folds import MAX_SIGNED_SHARE, fold_model, held_out
from murfulu.behnevis.inflect import Inflector
from murfulu.behnevis.metre import Licences, Metre, behaviour, patterns
from murfulu.behnevis.stats import cluster_lower_bound
from murfulu.behnevis.transcribe import Transcriber, Word, bank_from, key
from murfulu.corpus.inflection import Analyser, held_from
from murfulu.lexicon.store import Lexicon
from murfulu.search import harakat
from murfulu.search.texts import tokens

DATA = Path(__file__).resolve().parents[1] / "data"
THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9, 0.95)
#: The reading screen's levels (``behnevis.serve``): below MID a word is red.
MID, SURE = 0.7, 0.9
KINDS = ("presence or length", "vowel quality", "not offered")


@dataclass(frozen=True)
class Marked:
    """One marked word of a held-out poet, read before and after the metre."""

    poet: str
    source: str
    before: float
    right_before: bool
    kind_before: str | None
    after: float
    right_after: bool
    kind_after: str | None
    scanned: bool


def kind(word: Word, written: str) -> str | None:
    """Why a reading is wrong (one of :data:`KINDS`), or None when it is right."""
    if word.latin is not None and harakat.fits(written, word.latin) is True:
        return None
    fitting = [c for c, _ in word.candidates if harakat.fits(written, c) is True]
    if not fitting:
        return "not offered"
    # The same behaviour fits the same lines at the same costs (*Del*, *Dal*;
    # metre.behaviour): when every reading that fits the signs behaves as the
    # wrong one does, no metre can prefer any of them to it.
    chosen = behaviour(word.latin, word.spelling) if word.latin else None
    if chosen is not None and all(
        behaviour(c, word.spelling) == chosen for c in fitting
    ):
        return "vowel quality"
    return "presence or length"


def poems(path: Path) -> Iterator[dict[str, Any]]:
    """The poems with a known metre, one at a time."""
    with path.open(encoding="utf-8") as lines:
        for line in lines:
            yield json.loads(line)


def counted(line: str) -> list[tuple[str, str]]:
    """A verse half's words as written, each with its key."""
    return [(t.fa, key(t.spelling)) for t in tokens(line) if t.spelling]


def marked_words(
    fold: Transcriber, metres: Sequence[Metre], found: Iterable[dict[str, Any]]
) -> tuple[list[list[Marked]], Counter[str]]:
    """Section 1: the held-out poets' marked words, signs hidden, before and after.

    One list of rows for each metre setting, the words read once for all;
    the tally counts lines as the first setting scans them.
    """
    rows: list[list[Marked]] = [[] for _ in metres]
    tally: Counter[str] = Counter()
    for poem in found:
        if not held_out(poem["author"], 5):
            continue
        allowed = patterns(poem["metre"])
        if not allowed:
            tally["poems whose label gives no pattern"] += 1
            continue
        tally["poems"] += 1
        for line in poem["lines"]:
            words = counted(line)
            signed = sum(harakat.has_signs(w) for w, _ in words)
            if not signed:
                continue
            if signed > MAX_SIGNED_SHARE * len(words):
                tally["lines left out as quotations"] += 1
                continue
            tally["lines"] += 1
            read = [
                fold.word(
                    written,
                    spelling,
                    words[i - 1][1] if i else None,
                    words[i + 1][1] if i + 1 < len(words) else None,
                    use_signs=False,
                )
                for i, (written, spelling) in enumerate(words)
            ]
            was = [
                kind(before, written)
                for (written, _), before in zip(words, read, strict=True)
            ]
            for setting, metre in enumerate(metres):
                weighed = metre.weigh(read, allowed)
                if not setting:
                    tally["lines that scan"] += weighed[0].scanned
                for (written, _), before, after, wrong in zip(
                    words, read, weighed, was, strict=True
                ):
                    if not harakat.has_signs(written):
                        continue
                    now = kind(after.word, written)
                    rows[setting].append(
                        Marked(
                            poem["author"],
                            before.source,
                            before.confidence,
                            wrong is None,
                            wrong,
                            after.word.confidence,
                            now is None,
                            now,
                            after.scanned,
                        )
                    )
    return rows, tally


def running_words(
    model: Transcriber, metre: Metre, found: Iterable[dict[str, Any]], sample: int
) -> tuple[list[tuple[str, float, float, bool]], Counter[str]]:
    """Section 2: (source, before, after, the line scans) for each sampled word."""
    rows: list[tuple[str, float, float, bool]] = []
    tally: Counter[str] = Counter()
    for poem in found:
        if zlib.crc32(str(poem["poem"]).encode()) % sample:
            continue
        allowed = patterns(poem["metre"])
        if not allowed:
            continue
        tally["poems"] += 1
        for line in poem["lines"]:
            read = model.line(line, verse=True)
            if not read:
                continue
            tally["lines"] += 1
            weighed = metre.weigh(read, allowed)
            tally["lines that scan"] += weighed[0].scanned
            rows += [
                (b.source, b.confidence, a.word.confidence, a.scanned)
                for b, a in zip(read, weighed, strict=True)
                if b.latin is not None
            ]
    return rows, tally


def share(n: int, of: int) -> str:
    """A share as the report prints it."""
    return f"{n / of:.1%}" if of else "—"


def accuracy_table(rows: list[Marked]) -> list[str]:
    """Section 1's table: each threshold, before and after."""
    lines = [
        "| threshold | words at or above, before | right, before "
        "| words at or above, after | right, after |",
        "|---:|---:|---:|---:|---:|",
    ]
    for t in (0.0, *THRESHOLDS):
        before = [r.right_before for r in rows if r.before >= t]
        after = [r.right_after for r in rows if r.after >= t]
        lines.append(
            f"| {t:.2f} | {share(len(before), len(rows))} "
            f"| {share(sum(before), len(before))} "
            f"| {share(len(after), len(rows))} | {share(sum(after), len(after))} |"
        )
    return lines


def bound(rows: list[Marked], t: float, after: bool) -> tuple[int, float, float]:
    """Places at or above, accuracy, and its 95 % lower bound drawing poets again."""
    groups: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in rows:
        confidence, right = (
            (r.after, r.right_after) if after else (r.before, r.right_before)
        )
        if confidence >= t:
            groups[r.poet][0] += right
            groups[r.poet][1] += 1
    pairs = [(k, n) for k, n in groups.values()]
    n = sum(n for _, n in pairs)
    if not n:
        return 0, math.nan, math.nan
    k = sum(k for k, _ in pairs)
    return n, k / n, cluster_lower_bound(pairs, 0.05, draws=20_000)


def report(  # noqa: PLR0913 (one report, many parts)
    version: str,
    lines_path: Path,
    total_words: int,
    held: list[Marked],
    held_tally: Counter[str],
    running: list[tuple[str, float, float, bool]],
    running_tally: Counter[str],
    sample: int,
    sensitivity: list[tuple[str, list[Marked]]],
) -> list[str]:
    """The report, as Markdown lines."""
    known_poems = known_words = unreadable = 0
    for poem in poems(lines_path):
        known_poems += 1
        n = sum(len(counted(line)) for line in poem["lines"])
        if patterns(poem["metre"]):
            known_words += n
        else:
            unreadable += 1
    out = [
        f"# The poem's metre as a signal for the automatic Behnevis, corpus {version}",
        "",
        "Made by `tools/evaluate_behnevis_metre.py` (the metre step:",
        "`src/murfulu/behnevis/metre.py`; the poems with a metre:",
        "`tools/extract_metre_lines.py`). **A first, rough measurement on poetry,",
        "not a result**: each number carries its limits beside it.",
        "",
        "## 0. How much of the corpus has a known metre",
        "",
        f"- Running words of corpus {version}: {total_words:,}.",
        f"- Poems joined to a Ganjoor metre label: {known_poems:,}; of them "
        f"{unreadable:,} have a label this step cannot read into a pattern.",
        f"- Running words in poems with a readable label: {known_words:,} "
        f"({share(known_words, total_words)} of all running words).",
        "",
        "Limits: the label is Ganjoor's, joined by poem id and kept only where the",
        "first verse half agrees (`tools/extract_metre_lines.py` prints what was",
        "dropped); Sokhan's metre study found Ganjoor's labels right for about 99",
        "poems in 100 of those it could scan. A poem of several metres is left out.",
        "",
        "## 1. Marked words, poets held out, signs hidden",
        "",
        f"Poems of the held-out poets with a known metre: {held_tally['poems']:,}; "
        f"verse halves with a marked word: {held_tally['lines']:,} "
        f"(left out as quotations, over {MAX_SIGNED_SHARE:.0%} of words marked: "
        f"{held_tally['lines left out as quotations']:,}); marked words: "
        f"{len(held):,}, by {len({r.poet for r in held}):,} poets. Verse halves "
        f"that scan with the readings offered: "
        f"{share(held_tally['lines that scan'], held_tally['lines'])}.",
        "",
        "Limits: editions mark the hard words, so these are pessimistic; a reading",
        "counts as right when the word's signs fit it, which checks only the",
        "marked letters; the whole line's signs are hidden, so the model reads the",
        "neighbours unaided too. The before column differs from",
        f"`data/behnevis-eval-{version}.md`'s section 1 because only poems with a",
        "known metre are read here, each word between its neighbours in the line.",
        "",
    ]
    out += accuracy_table(held)
    out += [
        "",
        "### By where the reading came from (before the metre), all confidences",
        "",
        "| source | words | right, before | right, after | below 0.7, before "
        "| below 0.7, after |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for source in sorted({r.source for r in held}):
        mine = [r for r in held if r.source == source]
        out.append(
            f"| {source} | {len(mine):,} "
            f"| {share(sum(r.right_before for r in mine), len(mine))} "
            f"| {share(sum(r.right_after for r in mine), len(mine))} "
            f"| {share(sum(r.before < MID for r in mine), len(mine))} "
            f"| {share(sum(r.after < MID for r in mine), len(mine))} |"
        )
    wrong_before = Counter(r.kind_before for r in held if r.kind_before)
    wrong_after = Counter(r.kind_after for r in held if r.kind_after)
    fixed = Counter(r.kind_before for r in held if r.kind_before and r.right_after)
    broken = Counter(r.kind_after for r in held if r.right_before and r.kind_after)
    out += [
        "",
        "### What kind of error, and what the metre did to it",
        "",
        "| kind of error | before | share of errors | made right | after "
        "| share of errors | newly wrong |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for one in KINDS:
        out.append(
            f"| {one} | {wrong_before[one]:,} "
            f"| {share(wrong_before[one], sum(wrong_before.values()))} "
            f"| {fixed[one]:,} | {wrong_after[one]:,} "
            f"| {share(wrong_after[one], sum(wrong_after.values()))} "
            f"| {broken[one]:,} |"
        )
    out += [
        "",
        "*Presence or length*: some reading the model offered fits the signs",
        "and behaves differently in a line — the metre can prefer it. *Vowel",
        "quality*: every reading offered that fits behaves as the wrong one",
        "does in every line (*kenār*, *kanār*) — no metre can. *Not",
        "offered*: none fits; the metre can only lower the confidence. *Made right*",
        "counts the errors of that kind before that the metre turned right; *newly",
        "wrong* the right readings it turned into errors of that kind.",
        "",
        "### With what certainty (95 %, drawing poets again)",
        "",
        "| threshold | places, before | right | at least | places, after | right "
        "| at least |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for t in (MID, SURE):
        nb, ab, lb = bound(held, t, after=False)
        na, aa, la = bound(held, t, after=True)
        out.append(
            f"| {t:.2f} | {nb:,} | {ab:.1%} | {lb:.1%} | {na:,} | {aa:.1%} | {la:.1%} |"
        )
    out += [
        "",
        "One threshold each, read off, not searched; the lower bound holds for",
        "these poets' marked words, not for a single word.",
        "",
        "### Sensitivity: the licences' costs, set beforehand",
        "",
        "The numbers above use the costs in `Licences()`, set before measuring.",
        "Other settings, on the same words, to show how much they matter (not to",
        "choose one by the test):",
        "",
        "| setting | right at 0.70 or more | words at 0.70 or more "
        "| right at 0.90 or more | words at 0.90 or more |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, rows in sensitivity:
        cells = []
        for t in (MID, SURE):
            kept = [r.right_after for r in rows if r.after >= t]
            cells += [share(sum(kept), len(kept)), share(len(kept), len(rows))]
        out.append(f"| {name} | {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} |")
    out += [
        "",
        "## 2. What is left to a person, before and after",
        "",
        f"One poem in {sample} with a known metre (a stable hash of its id): "
        f"{running_tally['poems']:,} poems, {running_tally['lines']:,} verse "
        f"halves, {len(running):,} running words, read as the reading screen "
        f"reads them (the full model, the text's own signs, و by the verse rule). "
        f"Verse halves that scan with the readings offered: "
        f"{share(running_tally['lines that scan'], running_tally['lines'])}.",
        "",
        "Limits: whether the words taken as read are right is section 1's",
        "question, measured there on the hard marked words only; here only how",
        "many cross each threshold. Each word between its neighbours in the line,",
        "so the before column differs from the context-free section 3 of",
        f"`data/behnevis-eval-{version}.md`.",
        "",
        "| threshold | taken as read, before | after | left to a person, before "
        "| after |",
        "|---:|---:|---:|---:|---:|",
    ]
    for t in THRESHOLDS:
        b = sum(r[1] >= t for r in running)
        a = sum(r[2] >= t for r in running)
        out.append(
            f"| {t:.2f} | {share(b, len(running))} | {share(a, len(running))} "
            f"| {share(len(running) - b, len(running))} "
            f"| {share(len(running) - a, len(running))} |"
        )
    out += [
        "",
        "### By source: below 0.7 (red on the reading screen), before and after",
        "",
        "| source | share of words | below 0.7, before | after |",
        "|---|---:|---:|---:|",
    ]
    for source in sorted({r[0] for r in running}):
        read = [r for r in running if r[0] == source]
        out.append(
            f"| {source} | {share(len(read), len(running))} "
            f"| {share(sum(r[1] < MID for r in read), len(read))} "
            f"| {share(sum(r[2] < MID for r in read), len(read))} |"
        )
    return out


def main(argv: list[str] | None = None) -> int:
    """Run both measurements and print the report."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("version", help="corpus version, e.g. v22")
    parser.add_argument(
        "--sample",
        type=int,
        default=50,
        help="section 2 reads one poem in this many (default 50)",
    )
    args = parser.parse_args(argv)
    version = args.version
    lines_path = DATA / f"behnevis-metre-lines-{version}.jsonl"

    with Lexicon.open() as lexicon:
        inflection = Analyser(held_from(lexicon))
        readings = list(lexicon.all_readings())
        inflector = Inflector.from_readings(readings, inflection)
        pairs = [
            (r.spelling_fa, latin) for r in readings for latin in r.all_latin if latin
        ]
    bank = bank_from(pairs)
    model = Transcriber.load(DATA / f"behnevis-{version}.json", bank, inflection)
    model.inflector = inflector
    marked = [
        json.loads(line)
        for line in (DATA / f"behnevis-marked-{version}.jsonl").open(encoding="utf-8")
    ]
    answered = [
        Answered(**json.loads(line))
        for line in (DATA / f"behnevis-answered-{version}.jsonl").open(encoding="utf-8")
    ]
    counts: dict[str, int] = json.loads(
        (DATA / f"behnevis-counts-{version}.json").read_text(encoding="utf-8")
    )
    fold = fold_model(model, bank, inflection, inflector, marked, answered)
    functions = frozenset(model.functions)

    metre = Metre(functions=functions)
    settings = [
        ("as set (the tables above)", Licences()),
        ("another reading cheaper (2)", Licences(other=2.0)),
        ("another reading dearer (5)", Licences(other=5.0)),
        ("ezafe and lengthening free", Licences(ezafe=0.0, lengthen=0.0)),
    ]
    every, held_tally = marked_words(
        fold,
        [Metre(licences, functions) for _, licences in settings],
        poems(lines_path),
    )
    held = every[0]
    sensitivity = [
        (name, rows) for (name, _), rows in zip(settings, every, strict=True)
    ]
    print(f"section 1: {len(held):,} marked words", file=sys.stderr)
    running, running_tally = running_words(model, metre, poems(lines_path), args.sample)
    print(f"section 2: {len(running):,} running words", file=sys.stderr)
    print(
        "\n".join(
            report(
                version,
                lines_path,
                sum(counts.values()),
                held,
                held_tally,
                running,
                running_tally,
                args.sample,
                sensitivity,
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
