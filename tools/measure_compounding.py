"""Measure the compounding rules, which the main productivity pass cannot.

    python tools/measure_compounding.py --corpus-version v8 \
        --into data/rule_productivity-v8.json

**Why this is a second pass and not part of the first.** `run_productivity.py`
counts what the precompute built, and the precompute does affixation: it walks
one base at a time and applies rules to it. Compounding is not that shape. A
slot rule joins a word to *another word*, so its output is a **product** —
21,833 nouns against 1,741 verbs is 38 million forms for one rule — and the
precompute would have to hold them all to count them. It does not, deliberately,
and it should not start.

So the rules reported `types_built: 0` with a reason saying nothing called
them. That was true until `/compound` was written and is false now, and a
figure of zero beside a rule that builds millions of forms is worse than no
figure at all.

**What is measured, and what a reader has to know about it.** For each rule the
two pools are deduplicated **by Persian spelling** and joined pairwise; the
result is checked against the corpus. So:

* `types_built` is the number of distinct **pairs**, not of distinct strings.
  Two different pairs can spell the same word — دل+بر and دلب+ر — and this
  counts them twice. Measured on the pack it is a small effect and it is
  stated rather than corrected, because correcting it means holding 38 million
  strings in memory to save a rounding error.
* `types_attested` **is** distinct: it is a set of the forms found.
* There is no `band`. The bands in the main file are cut from the distribution
  of *affixation* realisation rates, and a compounding rate has a different
  denominator entirely — putting one on that scale would compare a product
  with a sum.

Rules whose pools cannot be enumerated say so instead of guessing: N-104 joins
two free nouns, which is 21,833 against itself.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Iterator
from pathlib import Path

from murfulu.corpus import wordtypes
from murfulu.corpus.ganjoor import GanjoorCorpus
from murfulu.engine.affix import CannotApplyError, Word
from murfulu.engine.compound import Verb, fill, fill_slot
from murfulu.engine.compound import front_classes as slot_front_classes
from murfulu.lexicon.categories import UnmappableCategoryError, word_classes_for
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import Rule, RulePack, loaded

#: A slot's behind-word comes from a verb stem. Any other input class names
#: something the engine derives rather than something the lexicon holds, so
#: there is no pool to enumerate.
STEM_CLASSES = {"karbon_yek": "past", "karbon_do": "present"}

#: Said instead of a number, never beside one.
NO_POOL = "one side is a derived class, not a word the lexicon holds"
TOO_MANY = "both sides are free nouns: {a:,} against itself is {n:,} pairs"


def _pools(lexicon: Lexicon) -> tuple[dict[str, list[Word]], list[Verb]]:
    """Every word by class and every verb, each deduplicated by spelling.

    Deduplicating by the **Persian** spelling is what makes the pair count
    meaningful: one spelling with three Latin readings is one word to join,
    and counting it three times would treble every figure below.
    """
    by_class: dict[str, dict[str, Word]] = {}
    verbs: dict[str, Verb] = {}
    for reading in lexicon.all_readings():
        if reading.is_infinitive and reading.has_both_stems:
            verbs.setdefault(
                reading.spelling_fa,
                Verb(
                    past_stem=Word(
                        reading.past_stem_latin or "",
                        reading.past_stem_fa or "",
                        "karbon_yek",
                    ),
                    present_stem=Word(
                        reading.present_stem_latin or "",
                        reading.present_stem_fa or "",
                        "karbon_do",
                    ),
                ),
            )
        try:
            classes = word_classes_for(reading.lexicon_category)
        except UnmappableCategoryError:
            continue
        for name in classes:
            by_class.setdefault(name, {}).setdefault(
                reading.spelling_fa,
                Word(reading.latin, reading.spelling_fa, name),
            )
    return (
        {name: list(words.values()) for name, words in by_class.items()},
        list(verbs.values()),
    )


def _stems(verbs: list[Verb], word_class: str) -> list[Word]:
    """One stem per verb, deduplicated by spelling."""
    found: dict[str, Word] = {}
    for verb in verbs:
        stem = verb.stem(word_class)
        if stem.fa:
            found.setdefault(stem.fa, stem)
    return list(found.values())


def _slot_forms(rule: Rule, fronts: list[Word], behinds: list[Word]) -> Iterator[str]:
    """Every Persian form this slot rule makes from the two pools."""
    for front in fronts:
        for behind in behinds:
            try:
                yield fill_slot(rule, front, behind).fa
            except (CannotApplyError, ValueError, KeyError):
                continue


def _template_forms(rule: Rule, verbs: list[Verb]) -> Iterator[str]:
    """Every Persian form this template makes, from one verb or from two."""
    two = any(
        slot.get("constraint") in {"different_verb", "different_stem"}
        for slot in rule.slots
    )
    if not two:
        for verb in verbs:
            try:
                yield fill(rule, verb).fa
            except (CannotApplyError, ValueError, KeyError):
                continue
        return
    for first in verbs:
        for second in verbs:
            if first is second:
                continue
            try:
                yield fill(rule, first, second).fa
            except (CannotApplyError, ValueError, KeyError):
                continue


def _count(forms: Iterator[str], corpus: set[str]) -> tuple[int, set[str]]:
    """How many were built, and which of them the corpus has."""
    built = 0
    found: set[str] = set()
    for form in forms:
        built += 1
        if form in corpus:
            found.add(form)
    return built, found


def _measure_rule(
    rule: Rule,
    by_class: dict[str, list[Word]],
    verbs: list[Verb],
    corpus: set[str],
) -> dict[str, object]:
    """One rule's row, measured or refused with a reason."""
    if rule.kind == "slot":
        fronts = [
            word for name in slot_front_classes(rule) for word in by_class.get(name, ())
        ]
        wanted = [c for c in rule.input_types if c in STEM_CLASSES]
        if not fronts or not wanted:
            return {"unmeasurable_reason": NO_POOL}
        behinds = [stem for c in wanted for stem in _stems(verbs, c)]
        built, found = _count(_slot_forms(rule, fronts, behinds), corpus)
        pools = {"front": len(fronts), "behind": len(behinds)}
    else:
        free_nouns = [
            slot for slot in rule.slots if slot.get("type") not in STEM_CLASSES
        ]
        if free_nouns:
            side = len(by_class.get("nam", ()))
            return {"unmeasurable_reason": TOO_MANY.format(a=side, n=side * side)}
        built, found = _count(_template_forms(rule, verbs), corpus)
        pools = {"front": len(verbs), "behind": len(verbs)}

    return {
        "types_built": built,
        "types_attested": len(found),
        "realisation_rate": (len(found) / built) if built else None,
        "pool": pools,
        "unmeasurable_reason": "",
    }


def _merge(into: Path, rows: dict[str, dict[str, object]], version: str) -> int:
    """Write the compounding rows into an existing productivity file.

    The rows keep the shape the app already reads, so nothing in the app
    changes. `band` is set to null on purpose — see the module docstring.
    """
    document = json.loads(into.read_text(encoding="utf-8"))
    if document.get("corpus_version") != version:
        raise SystemExit(
            f"{into} is corpus {document.get('corpus_version')!r}, asked for "
            f"{version!r}. A figure never moves to another version's file."
        )
    changed = 0
    for row in document.get("rules", []):
        measured = rows.get(row["rule_id"])
        if measured is None:
            continue
        row.update(measured)
        row["measured"] = not measured.get("unmeasurable_reason")
        row["band"] = None
        row["measured_by"] = "tools/measure_compounding.py"
        changed += 1
    into.write_text(
        json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return changed


def main(argv: list[str] | None = None) -> int:
    """Measure every compounding rule and print what each one did."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-version", default="v8")
    parser.add_argument("--into", type=Path, help="a rule_productivity file to update")
    parser.add_argument("--out", type=Path, help="write the rows on their own")
    arguments = parser.parse_args(argv)

    pack: RulePack = loaded()
    started = time.monotonic()
    counted = wordtypes.build(GanjoorCorpus())
    corpus = set(counted.word_types)
    spent = time.monotonic() - started
    print(f"corpus         {len(corpus):,} spellings ({spent:,.0f}s)")

    with Lexicon.open() as lexicon:
        by_class, verbs = _pools(lexicon)
    print(
        f"pools          {len(verbs):,} verbs, "
        + ", ".join(f"{len(w):,} {n}" for n, w in sorted(by_class.items()))
    )

    rows: dict[str, dict[str, object]] = {}
    for rule in pack.rules:
        if rule.kind not in ("slot", "template") or not rule.active:
            continue
        started = time.monotonic()
        row = _measure_rule(rule, by_class, verbs, corpus)
        rows[rule.id] = row
        spent = time.monotonic() - started
        if row.get("unmeasurable_reason"):
            print(f"{rule.id:<8} not measured: {row['unmeasurable_reason']}")
        else:
            rate = row["realisation_rate"]
            assert isinstance(rate, float)
            print(
                f"{rule.id:<8} {row['types_built']:>12,} built  "
                f"{row['types_attested']:>6,} attested  {rate:>7.4%}  ({spent:,.0f}s)"
            )

    if arguments.out:
        arguments.out.write_text(
            json.dumps(
                {"corpus_version": arguments.corpus_version, "rules": rows},
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
    if arguments.into:
        changed = _merge(arguments.into, rows, arguments.corpus_version)
        print(f"merged         {changed} rules into {arguments.into}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
