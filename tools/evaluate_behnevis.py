"""Measure the automatic Behnevis: what each confidence threshold costs and saves.

    python tools/evaluate_behnevis.py v17 > data/behnevis-eval-v17.md

Needs the files ``tools/build_behnevis.py`` writes and the lexicon snapshot
(``MURFULU_LEXICON_PATH``); no Elasticsearch. Three measurements, each on
data the model did not learn from:

1. **Marked words, poets held out.** The corpus's vowel-marked words in
   Persian lines; the model learns its choices and coverage without one poet
   in five, reads those poets' marked words **with the signs hidden**, and a
   reading counts as right when the signs fit it. Pessimistic twice over:
   editions mark the hard words, and a guess from the letters is right only if
   it fits the signs *and* the rest of the word, of which only the signs are
   checked here — so the letters' figure is the next one.
2. **Unknown words.** The letter model learns from nine bank words in ten and
   guesses the tenth; right means the whole word is the bank's reading.
3. **How much of the text each threshold leaves to a person.** Every spelling
   of the corpus, read without neighbours, weighted by its count.
"""

from __future__ import annotations

import argparse
import json
import zlib
from collections import Counter
from pathlib import Path

from murfulu.behnevis.choice import Answered, ChoiceModel, ranked
from murfulu.behnevis.letters import LetterModel, latin_key
from murfulu.behnevis.transcribe import Transcriber, bank_from, key
from murfulu.lexicon.store import Lexicon
from murfulu.search import harakat

DATA = Path(__file__).resolve().parents[1] / "data"
THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9, 0.95)
#: The example the project lead quotes: Hafez's ghazals in corpus v17.
HAFEZ_WORDS = 62_300
#: Assumed, not measured (the timed sample replaces them): words an expert
#: writes by hand per hour, and proposals a person checks per hour.
BY_HAND, CHECKED = 600, 900


def held_out(name: str, every: int) -> bool:
    """One in ``every`` by a stable hash, so a rerun holds out the same."""
    return zlib.crc32(name.encode()) % every == 0


def main(argv: list[str] | None = None) -> int:
    """Run the three measurements and print the report."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("version", help="corpus version, e.g. v17")
    version = parser.parse_args(argv).version

    with Lexicon.open() as lexicon:
        pairs = [
            (r.spelling_fa, latin)
            for r in lexicon.all_readings()
            for latin in r.all_latin
            if latin
        ]
    bank = bank_from(pairs)
    model = Transcriber.load(DATA / f"behnevis-{version}.json", bank)
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

    # 1. marked words, one poet in five held out --------------------------------
    test = [m for m in marked if held_out(m["author"], 5)]
    train_answered = [a for a in answered if not held_out(a.author, 5)]
    covered: dict[str, list[int]] = {}
    for m in marked:
        if held_out(m["author"], 5):
            continue
        candidates = list(
            dict.fromkeys(
                (*model.functions.get(m["spelling"], ()), *bank.get(m["spelling"], ()))
            )
        )
        if not candidates:
            continue
        verdicts = [harakat.fits(m["written"], c) for c in candidates]
        if not any(verdicts) and not all(v is False for v in verdicts):
            continue  # the signs cannot judge these readings
        fits = any(verdicts)
        covered.setdefault(m["spelling"], [0, 0])[0 if fits else 1] += 1
    fold = Transcriber(
        bank=bank,
        letters=model.letters,
        choice=ChoiceModel.train(train_answered),
        covered={k: (v[0], v[1]) for k, v in covered.items()},
    )
    results = []
    for m in test:
        word = fold.word(
            m["written"], m["spelling"], m["before"], m["after"], use_signs=False
        )
        right = (
            word.latin is not None and harakat.fits(m["written"], word.latin) is True
        )
        results.append((word.source, word.confidence, right))

    # 1b. the choice alone: answered places of held-out poets -----------------
    choice_only = []
    for a in answered:
        if not held_out(a.author, 5):
            continue
        candidates = list(
            dict.fromkeys(
                (*model.functions.get(a.spelling, ()), *bank.get(a.spelling, ()))
            )
        )
        function = model.functions.get(a.spelling, ())
        probs = fold.choice.probabilities(
            a.spelling, candidates, a.before, a.after, function[0] if function else None
        )
        best = ranked(probs)[0]
        choice_only.append((best[1], best[0] == a.reading))

    # 2. unknown words: letters, one bank word in ten held out ------------------
    seen_pairs = [(s, r) for s, r in pairs if not held_out(key(s), 10)]
    test_pairs: dict[str, set[str]] = {}
    for s, r in pairs:
        if held_out(key(s), 10):
            test_pairs.setdefault(key(s), set()).add(latin_key(r))
    letters = LetterModel.train(seen_pairs)
    guessed = []
    for spelling, readings in test_pairs.items():
        g = letters.guess(spelling)
        if g:
            guessed.append((g[1], latin_key(g[0]) in readings))

    # 3. the corpus: how much each threshold leaves to a person -----------------
    total = sum(counts.values())
    confidence_of: dict[str, float] = {}
    for spelling in counts:
        confidence_of[spelling] = model.word(spelling, spelling, None, None).confidence
    source_share: Counter[str] = Counter()
    for spelling, n in counts.items():
        source_share[model.word(spelling, spelling, None, None).source] += n

    def curve(rows: list[tuple[float, bool]], t: float) -> tuple[float, float]:
        kept = [right for confidence, right in rows if confidence >= t]
        return len(kept) / max(1, len(rows)), sum(kept) / max(1, len(kept))

    lines = [f"# Automatic Behnevis, corpus {version}: what each threshold costs", ""]
    lines += [
        "Made by `tools/evaluate_behnevis.py`; the model by `tools/build_behnevis.py`.",
        "",
        "## Where the text's words get their reading (context-free, by running words)",
        "",
        "| source | share of running words |",
        "|---|---:|",
    ]
    for source, n in source_share.most_common():
        lines.append(f"| {source} | {n / total:.1%} |")
    lines += [
        "",
        f"## 1. Marked words, poets held out ({len(test):,} words, signs hidden)",
        "",
        "| threshold | words at or above | of those right |",
        "|---:|---:|---:|",
    ]
    rows = [(c, r) for _, c, r in results]
    for t in (0.0, *THRESHOLDS):
        share, rate = curve(rows, t)
        lines.append(f"| {t:.2f} | {share:.0%} | {rate:.1%} |")
    lines += [
        "",
        "By source, all confidences:",
        "",
        "| source | words | right |",
        "|---|---:|---:|",
    ]
    for source in sorted({s for s, _, _ in results}):
        mine = [r for s, _, r in results if s == source]
        lines.append(f"| {source} | {len(mine):,} | {sum(mine) / len(mine):.1%} |")
    lines += [
        "",
        "## 1b. Several readings: the choice alone, poets held out "
        f"({len(choice_only):,})",
        "",
        "Places where the text's signs leave one of the bank's readings; the model",
        "chooses without the signs. Right means it chose that one.",
        "",
        "| threshold | places at or above | of those right |",
        "|---:|---:|---:|",
    ]
    for t in (0.0, *THRESHOLDS):
        share, rate = curve(choice_only, t)
        lines.append(f"| {t:.2f} | {share:.0%} | {rate:.1%} |")
    lines += [
        "",
        "## 2. Unknown words: the letter model on held-out bank words "
        f"({len(guessed):,})",
        "",
        "| threshold | words at or above | of those right |",
        "|---:|---:|---:|",
    ]
    for t in (0.0, *THRESHOLDS):
        share, rate = curve(guessed, t)
        lines.append(f"| {t:.2f} | {share:.0%} | {rate:.1%} |")
    lines += [
        "",
        "## 3. What a threshold leaves to a person",
        "",
        f"Running words of corpus {version}: {total:,}. Each spelling read without",
        "neighbours, so a word the context would settle counts as unsure here.",
        f"Hours for Hafez's ghazals ({HAFEZ_WORDS:,} words) assume {BY_HAND} words",
        f"an hour by hand and {CHECKED} checked proposals an hour — assumptions,",
        "not measurements;",
        f"by hand they take {HAFEZ_WORDS / BY_HAND:.0f} hours.",
        "",
        "| threshold | taken as read | checked by a person | hours for Hafez |",
        "|---:|---:|---:|---:|",
    ]
    for t in THRESHOLDS:
        auto = sum(n for s, n in counts.items() if confidence_of[s] >= t) / total
        lines.append(
            f"| {t:.2f} | {auto:.0%} | {1 - auto:.0%} | "
            f"{(1 - auto) * HAFEZ_WORDS / CHECKED:.0f} |"
        )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
