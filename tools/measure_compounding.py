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

**Per second half (`--heads`, 2026-11-21).** One rate per rule gives every row
of the compound page the same build value: a noun's page is built by V-078,
V-079 and V-016 alone. What separates دلبر from دلدوز is the second half, so
`--heads` writes, per slot rule and per second half, how many fronts the rule
joins it to and how many of those words the corpus has — «‑بر» joined to
every noun, against the corpus. The half works like a suffix here, and its
rate goes on the build screen's scale (`murfulu.scoring.compound_heads`).
**Not by spelling, as above**: a pair counts only where the dictionary holds
the joined word as a compound (صفت مرکب، اسم مرکب) under exactly the joined
reading and the corpus has its letters (`_heads` says why — by letters alone
«ر» and «ده» came out on top). That also
keeps out دلم and سرم, *my heart* and *my head*, which by letters would make
the one-letter stem م a most productive half. `--index word_types-v22` reads
the corpus's spellings from that index instead of rebuilding them from the
Ganjoor dump.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from murfulu.compounding import own_readings
from murfulu.corpus import wordtypes
from murfulu.corpus.ganjoor import GanjoorCorpus
from murfulu.engine.affix import CannotApplyError, Word
from murfulu.engine.compound import Verb, fill, fill_slot
from murfulu.engine.compound import front_classes as slot_front_classes
from murfulu.lexicon.bank import is_excluded, word_classes_of
from murfulu.lexicon.categories import UnmappableCategoryError
from murfulu.lexicon.entries import Reading
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import Rule, RulePack, loaded

#: A slot's behind-word comes from a verb stem. Any other input class names
#: something the engine derives rather than something the lexicon holds, so
#: there is no pool to enumerate.
STEM_CLASSES = {"karbon_yek": "past", "karbon_do": "present"}

#: What the dictionary writes after a compound's class: صفت مرکب، اسم مرکب.
#: 21,129 of karbon 1.3.2's 57,944 readings carry it.
COMPOUND_LABEL = "مرکب"

#: A second half of one letter is not counted: ر، ش، م end too many words.
#: With the compound label and the reading both required, دربار still came out
#: as دربا + *r*, باهوش as باهو + *š*, دوتار as دوتا + *r* (the review of
#: 2026-11-21). Seven verbs have such a stem (میدن's م among them, UPSTREAM A8).
SHORTEST_HALF = 2

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
        if is_excluded(reading):
            # Out of word formation (a وام‌واژه): neither a verb nor a front.
            continue
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
            classes = word_classes_of(reading)
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


def _corpus_from_index(index: str) -> tuple[set[str], set[str]]:
    """Every spelling the corpus has, and the corpus versions the index holds."""
    from elasticsearch.helpers import scan

    from murfulu.search.indices import connect

    found: set[str] = set()
    versions: set[str] = set()
    for hit in scan(
        connect(),
        index=index,
        query={"query": {"term": {"population": "corpus"}}},
        _source=["spelling_fa", "corpus_version"],
        size=5000,
    ):
        source = hit["_source"]
        versions.add(str(source.get("corpus_version") or ""))
        spelling = source.get("spelling_fa")
        if spelling:
            found.add(wordtypes.normalise(spelling))
    return found, versions


def same_version(asked: str, held: set[str]) -> None:
    """Stop unless the index holds exactly the corpus version the file will say.

    ``--index word_types-v22`` with the default ``--corpus-version`` wrote v22's
    figures under the name v8 (the review of 2026-11-21).
    """
    if held != {asked}:
        raise SystemExit(
            f"the index holds corpus {sorted(held)}, asked to write {asked!r}: "
            "a figure never moves to another version's name"
        )


@dataclass
class _Readings:
    """Every Latin reading the bank has, by spelling, for the per-half count.

    Lower-cased, variants included, spellings normalised as the corpus's are:
    a capital is a word class showing, not another word.
    """

    #: Every headword the dictionary labels a compound (صفت مرکب، اسم مرکب):
    #: spelling → the readings so labelled.
    words: dict[str, set[str]]
    #: Fronts, by the class a slot rule asks for: class → spelling → readings.
    fronts: dict[str, dict[str, set[str]]]
    #: Verb stems, by slot class (``karbon_do``…): class → spelling → readings.
    stems: dict[str, dict[str, set[str]]]
    #: Stems too short to count: see :data:`SHORTEST_HALF`.
    set_aside: set[str]


def _readings(lexicon: Lexicon) -> _Readings:
    """One pass over the bank, keeping every reading rather than the first.

    Each spelling's entries go through :func:`compounding.own_readings` first,
    as on the compound page: دم's *Dom* (a noun) lists *Dam*, which is another
    entry's reading, and without the cleanup it confirmed دمساز and دمدار as
    a noun's compounds.
    """
    words: dict[str, set[str]] = {}
    fronts: dict[str, dict[str, set[str]]] = {}
    stems: dict[str, dict[str, set[str]]] = {c: {} for c in STEM_CLASSES}
    set_aside: set[str] = set()
    grouped: dict[str, list[Reading]] = {}
    for reading in lexicon.all_readings():
        grouped.setdefault(reading.spelling_fa, []).append(reading)
    for reading in (one for group in grouped.values() for one in own_readings(group)):
        spelling = wordtypes.normalise(reading.spelling_fa)
        latins = {one.lower() for one in reading.all_latin if one}
        if any(COMPOUND_LABEL in (one or "") for one in reading.lexicon_categories):
            words.setdefault(spelling, set()).update(latins)
        if is_excluded(reading):
            continue
        if reading.is_infinitive and reading.has_both_stems:
            for name, fa, latin in (
                ("karbon_yek", reading.past_stem_fa, reading.past_stem_latin),
                ("karbon_do", reading.present_stem_fa, reading.present_stem_latin),
            ):
                if not (fa and latin):
                    continue
                stem = wordtypes.normalise(fa)
                if len(stem) < SHORTEST_HALF:
                    set_aside.add(stem)
                    continue
                stems[name].setdefault(stem, set()).add(latin.lower())
        try:
            classes = word_classes_of(reading)
        except UnmappableCategoryError:
            continue
        for name in classes:
            fronts.setdefault(name, {}).setdefault(spelling, set()).update(latins)
    return _Readings(words=words, fronts=fronts, stems=stems, set_aside=set_aside)


def _heads(rule: Rule, bank: _Readings, corpus: set[str]) -> dict[str, object] | None:
    """Per second half of one slot rule: fronts it joins, and those confirmed.

    A pair counts only where **the dictionary holds the joined word as a
    compound (صفت مرکب، اسم مرکب) under exactly the joined reading, and the
    corpus has its letters**: دلبر is *delbar*, a صفت مرکب, and *del* + *bar*
    is *delbar*. Each condition was added because the run without it was
    wrong. By letters alone the shortest stems won: «ر» and «ده» end countless
    ordinary words (دختر cut as دخت + ر). With the reading but without the
    label, the stems with no vowel still did: ابر is *abr*, اب + ریدن's *r*;
    and دنیدن's *dan* ends every infinitive.

    Walks the bank's headwords the corpus has, cut at every point, rather than
    the 38 million pairs.
    """
    if rule.kind != "slot":
        return None
    fronts: dict[str, set[str]] = {}
    for name in slot_front_classes(rule):
        for spelling, latins in bank.fronts.get(name, {}).items():
            fronts.setdefault(spelling, set()).update(latins)
    behinds: dict[str, set[str]] = {}
    for name in rule.input_types:
        for spelling, latins in bank.stems.get(name, {}).items():
            behinds.setdefault(spelling, set()).update(latins)
    if not fronts or not behinds:
        return None
    # Keyed by the half's letters **and** reading: کش is *keš* (کشیدن) and
    # *koš* (کشتن), and دلکش confirms the first only.
    confirmed: dict[tuple[str, str], set[str]] = {
        (behind, latin): set() for behind, latins in behinds.items() for latin in latins
    }
    for spelling, readings in bank.words.items():
        if spelling not in corpus:
            continue
        for cut in range(1, len(spelling)):
            front, behind = spelling[:cut], spelling[cut:]
            if front not in fronts or behind not in behinds:
                continue
            for latin in behinds[behind]:
                if any(f + latin in readings for f in fronts[front]):
                    confirmed[(behind, latin)].add(front)
    # Only the halves with a confirmed word: most stems never head one. Which
    # halves were measured at all is the file's ``halves``, so an absent one is
    # a measured zero there and unmeasured anywhere else.
    by_behind: dict[str, dict[str, int]] = {}
    for (behind, latin), found in sorted(confirmed.items()):
        if found:
            by_behind.setdefault(behind, {})[latin] = len(found)
    return {
        "fronts": len(fronts),
        "stem_classes": [name for name in rule.input_types if name in STEM_CLASSES],
        "behinds": len(confirmed),
        "by_behind": by_behind,
    }


def _merge(
    into: Path,
    rows: dict[str, dict[str, object]],
    version: str,
    pack_version: str = "",
) -> int:
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
    held = document.get("rule_pack_version", "")
    if pack_version and held and held != pack_version:
        raise SystemExit(
            f"{into} was measured with rule pack {held!r}, this run has "
            f"{pack_version!r} (L26's switch?). A figure never moves between packs."
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
    parser.add_argument(
        "--heads", type=Path, help="write the per-second-half figures here and stop"
    )
    parser.add_argument(
        "--index", help="read the corpus's spellings from this word_types index"
    )
    arguments = parser.parse_args(argv)

    pack: RulePack = loaded()
    started = time.monotonic()
    if arguments.index:
        corpus, held = _corpus_from_index(arguments.index)
        same_version(arguments.corpus_version, held)
    else:
        counted = wordtypes.build(GanjoorCorpus())
        corpus = set(counted.word_types)
    spent = time.monotonic() - started
    print(f"corpus         {len(corpus):,} spellings ({spent:,.0f}s)")

    with Lexicon.open() as lexicon:
        by_class, verbs = _pools(lexicon)
        snapshot = lexicon.snapshot_id
        bank = _readings(lexicon) if arguments.heads else None

    if arguments.heads and bank is not None:
        heads: dict[str, object] = {}
        for rule in pack.rules:
            if not rule.active:
                continue
            row = _heads(rule, bank, corpus)
            if row is None:
                continue
            heads[rule.id] = row
            counts = row["by_behind"]
            assert isinstance(counts, dict)
            pairs = sum(n for latins in counts.values() for n in latins.values())
            print(
                f"{rule.id:<8} {row['fronts']:>6,} fronts  "
                f"{row['behinds']:>5,} halves  "
                f"{pairs:>6,} confirmed pairs"
            )
        arguments.heads.write_text(
            json.dumps(
                {
                    "corpus_version": arguments.corpus_version,
                    "rule_pack_version": pack.version,
                    "lexicon_snapshot_id": snapshot,
                    "measured_by": "tools/measure_compounding.py --heads",
                    "counted": "a pair counts where the dictionary holds the "
                    "joined word as a compound under the joined reading and the "
                    "corpus has its letters",
                    # Every half measured, by stem class: a half listed here
                    # and absent from a rule's ``by_behind`` found nothing; a
                    # half not listed was not measured (a stem added since).
                    "halves": {
                        name: {
                            fa: sorted(latins) for fa, latins in sorted(found.items())
                        }
                        for name, found in bank.stems.items()
                    },
                    "set_aside": {
                        "halves": sorted(bank.set_aside),
                        "reason": "a one-letter second half ends too many words "
                        "to be told from a compound",
                    },
                    "rules": heads,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        print(f"wrote          {arguments.heads}")
        return 0
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
        changed = _merge(arguments.into, rows, arguments.corpus_version, pack.version)
        print(f"merged         {changed} rules into {arguments.into}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
