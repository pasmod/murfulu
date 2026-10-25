"""Put every rule's own example back through the engine.

    python tools/check_examples.py --out build/examples-v8.json

**The rule pack was going to be the test suite.** The quality bar says so, and
`tests/test_golden_examples.py` says so in its own docstring: *"Until the
engine exists (PLAN 2.1) these check the shape of every example… When the
engine lands, `expected` becomes what it must produce."* The engine landed in
session 2. **The upgrade never happened**, so ~200 examples are still checked
for spelling and parseability alone.

This is the missing half: it takes each example, asks `analysis.explain` to
take it apart, and asks whether the rule that *lists* the example is among the
rules that rebuild it.

**A failure here is not automatically a bug in the engine**, which is exactly
why this writes a report rather than assertions — and until 2026-08-15 it had
no way of telling the piles apart, so all 75 of them read as though they might
be ours. **PLAN 9.3 is that missing half**: each failing rule is now run
*forward* from the base its own example implies, and what it built is the
evidence that sorts it.

Five answers, and only one of them is ours to fix:

* **the engine builds a different word** — ours. It was seven when this was
  written (V-070 to V-076 dropped the infinitive ending) and is now none.
* **the two spell the same word differently** — N-004's example is `bexrad`
  and the engine builds `bexerad` from karbon's `Xerad`. A vowel convention
  between the source grammar and the phonemizer; the linguist's, not a code
  change. Claimed only when the rule **builds the expected word bar its
  vowels**, because a bare consonant skeleton is a weak match on a short base:
  *div* finds *Dāv*, which is a different word.
* **the base is not in the lexicon** — `Ketābí` cannot rebuild while کتاب is
  absent. Neither an engine fault nor a bad example: UPSTREAM B2.
* **the lexicon has the base in another word class** — *Ruz* is held; N-089
  still cannot take it. That is the category mapping, PLAN 3.2.
* **the example does not use the affix the rule declares** — the rule writes
  `-āk` and its example is *kāvak*. A transcription question.

Needs the real lexicon snapshot: an example names a real Persian word and the
fixture holds eleven.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from murfulu import analysis
from murfulu.engine import CannotApplyError, apply
from murfulu.generation import bases_of
from murfulu.lexicon.entries import Reading
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import Glide, Rule, RulePack, loaded

#: A worked example — ``goft + ār = Goftār`` — states its own result after the
#: equals sign. A bare one is the result already.
WORKED = "="

#: The Behnevis vowels. Two spellings that differ only in these are the same
#: word written two ways — *bexrad* and *bexerad* — and that is a convention
#: between the source grammar and karbon's phonemizer, not a fault in either.
VOWELS = "aeiouāíé"


@dataclass(frozen=True)
class Checked:
    """One example, and what the engine made of it."""

    rule_id: str
    example: str
    expected: str
    #: Rules that rebuilt the word, in any account.
    rebuilt_by: tuple[str, ...] = ()
    #: True when the rule that lists the example is one of them.
    explained_by_its_own_rule: bool = False
    #: The base this example implies, read off a worked example or by taking
    #: the rule's own affix off the front or the end.
    base: str = ""
    #: Whether the lexicon holds that base at all, in any word class.
    base_held: bool = False
    #: Whether it holds it in a class this rule accepts. *Ruz* is in the
    #: lexicon; N-089 still cannot use it, and that is a different answer from
    #: karbon not having the word.
    base_in_class: bool = False
    #: How the base was found: exactly, or only once the vowels were ignored.
    #: The source writes *xrad* and karbon writes *Xerad*, and calling that a
    #: missing word would blame the lexicon for a spelling convention.
    base_matched: str = ""
    #: What the rule actually builds from that base. Empty when the base is
    #: not held, which is a different answer from *the engine built nothing*.
    built: tuple[str, ...] = ()

    @property
    def state(self) -> str:
        """Which pile this one is in."""
        if self.explained_by_its_own_rule:
            return "explained by its own rule"
        if self.rebuilt_by:
            return "rebuilt, but by another rule"
        return "not rebuilt at all"

    @property
    def why(self) -> str:
        """Which of the piles a *failure* belongs to, and on what evidence.

        This is the whole point of running the rule forward. Without it every
        failure reads as *the engine is wrong*, and most of them are not.
        """
        if self.explained_by_its_own_rule:
            return "rebuilt"
        if not self.base:
            return "the example does not use the affix the rule declares"

        # **The evidence is the result, not the base.** A skeleton is a weak
        # match on a short base — *div* finds *Dāv*, which is a different word
        # — so a spelling disagreement is only claimed when the rule then
        # builds something that *is* the expected word bar its vowels.
        if any(_same_skeleton(one, self.expected) for one in self.built):
            return "the two spell the same word differently"
        if self.base_matched == "exact":
            if not self.base_in_class:
                return "the lexicon has the base in another word class"
            if not self.built:
                return "the engine builds nothing from this base"
            return "the engine builds a different word"
        # کتاب is not in the lexicon, so `Ketābí` can never rebuild. Not an
        # engine fault and not a bad example — an upstream gap, B2.
        return "the base is not in the lexicon"


def _skeleton(latin: str) -> str:
    """A form with its vowels taken out, for comparing spellings.

    *bexrad* and *bexerad* have the same skeleton and are the same word; the
    difference is a vowel convention. *Goftār* and *Gofte* do not.
    """
    return "".join(c for c in latin.lower() if c not in VOWELS)


def _same_skeleton(one: str, other: str) -> bool:
    return bool(one) and _skeleton(one) == _skeleton(other)


def _expected(example: str) -> str:
    """The form an example says the rule produces."""
    if WORKED in example:
        return example.split(WORKED)[-1].strip()
    return example.strip()


def _implied_base(rule: Rule, example: str, expected: str) -> str:
    """The base an example was built from.

    A worked example — ``goft + ār = Goftār`` — states it. A bare one does
    not, so the rule's own affix comes off whichever end the rule puts it.
    """
    if WORKED in example:
        left = example.split(WORKED)[0]
        return left.split("+")[0].strip()

    # Every spelling the rule declares, not only the first: the pack carries
    # affix_variants for exactly this, and V-004 writes -ānidan while its own
    # example tarsāndan uses -āndan.
    candidates = [
        one.strip("-")
        for one in (rule.affix, *rule.affix_variants)
        if one and one.strip("-")
    ]
    if not candidates:
        return expected
    for affix in sorted(candidates, key=len, reverse=True):
        if rule.kind == "prefix":
            if expected.lower().startswith(affix.lower()):
                return expected[len(affix) :]
        elif expected.lower().endswith(affix.lower()):
            return expected[: -len(affix)]
    return ""


def skeleton_index(lexicon: Lexicon) -> dict[str, list[Reading]]:
    """Every reading filed under its consonant skeleton.

    So *xrad* can find karbon's *Xerad*. Without this the source's own vowel
    convention reads as a word the lexicon does not have, which blames the
    lexicon for a disagreement about spelling.
    """
    index: dict[str, list[Reading]] = {}
    for reading in lexicon.all_readings():
        for latin in reading.all_latin:
            if latin:
                index.setdefault(_skeleton(latin), []).append(reading)
    return index


def _forward(
    lexicon: Lexicon,
    skeletons: dict[str, list[Reading]],
    pack: RulePack,
    rule: Rule,
    base: str,
) -> tuple[bool, bool, str, tuple[str, ...]]:
    """Run the rule forward from the base, and say what came out.

    Returns whether the lexicon holds the base at all, whether it holds it in a
    class this rule takes, how it was found, and what the rule built from it.
    """
    if not base:
        return False, False, "", ()

    # Case first, and it is not cosmetic. A prefix rule lower-cases the letter
    # it covers — سربلند is Sarbaland — so taking the prefix back off a noun
    # leaves *kenār* where the lexicon holds *Kenār*. Reporting that as a word
    # karbon does not have would be this instrument's error, not karbon's.
    readings = []
    for spelling in (base, base[:1].upper() + base[1:], base.lower()):
        readings = lexicon.by_latin(spelling)
        if readings:
            break
    how = "exact"
    if not readings:
        readings = skeletons.get(_skeleton(base), [])
        how = "vowels"

    held = False
    in_class = False
    built: list[str] = []
    for reading in readings:
        held = True
        for word in bases_of(reading):
            if word.word_class not in rule.input_types or not word.latin:
                continue
            in_class = True
            try:
                built.append(apply(pack, rule, word).latin)
            except CannotApplyError:
                continue
    return held, in_class, (how if held else ""), tuple(sorted(set(built)))


def check(
    lexicon: Lexicon,
    skeletons: dict[str, list[Reading]],
    pack: RulePack,
    rule: Rule,
    example: str,
    depth: int,
) -> Checked:
    """Take one example apart and see which rules put it back together."""
    expected = _expected(example)
    found = analysis.explain(lexicon, pack, expected, depth=depth)
    rebuilt = {step.rule_id for account in found.analyses for step in account.steps}
    base = _implied_base(rule, example, expected)
    held, in_class, how, built = _forward(lexicon, skeletons, pack, rule, base)
    return Checked(
        rule_id=rule.id,
        example=example,
        expected=expected,
        rebuilt_by=tuple(sorted(rebuilt)),
        explained_by_its_own_rule=rule.id in rebuilt,
        base=base,
        base_held=held,
        base_in_class=in_class,
        base_matched=how,
        built=built,
    )


def main(argv: list[str] | None = None) -> int:
    """Check every example and print the three piles."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--out", type=Path, help="write the full report here")
    parser.add_argument(
        "--kinds",
        nargs="*",
        default=["prefix", "suffix"],
        help="rule kinds to check; the rest build nothing through this route",
    )
    arguments = parser.parse_args(argv)

    pack = loaded()
    results: list[Checked] = []
    with Lexicon.open() as lexicon:
        skeletons = skeleton_index(lexicon)
        for rule in pack.rules:
            if isinstance(rule, Glide) or not rule.active:
                continue
            if rule.kind not in arguments.kinds or not rule.examples:
                continue
            results.append(
                check(lexicon, skeletons, pack, rule, rule.examples[0], arguments.depth)
            )

    piles: dict[str, list[Checked]] = {}
    for one in results:
        piles.setdefault(one.state, []).append(one)

    print(f"examples checked   {len(results)} ({', '.join(arguments.kinds)} rules)")
    for state in sorted(piles):
        found = piles[state]
        share = len(found) / len(results) if results else 0
        print(f"  {state:<28} {len(found):>4}  {share:>6.1%}")

    failures = [one for one in results if not one.explained_by_its_own_rule]
    reasons: dict[str, list[Checked]] = {}
    for one in failures:
        reasons.setdefault(one.why, []).append(one)

    print(f"\nwhy the {len(failures)} failures failed, by running the rule forward\n")
    for why in sorted(reasons, key=lambda w: -len(reasons[w])):
        print(f"  {why:<46} {len(reasons[why]):>4}")
    print("\nonly *the engine builds a different word* is ours to fix.\n")
    for why in sorted(reasons, key=lambda w: -len(reasons[w])):
        print(f"  -- {why}")
        for one in sorted(reasons[why], key=lambda o: o.rule_id):
            made = ", ".join(one.built) if one.built else "—"
            print(
                f"     {one.rule_id}  {one.expected:<18} "
                f"base {one.base or '?':<14} built {made}"
            )

    if arguments.out:
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(
            json.dumps(
                {
                    "depth": arguments.depth,
                    "kinds": list(arguments.kinds),
                    "checked": len(results),
                    "examples": [
                        {
                            "rule_id": one.rule_id,
                            "example": one.example,
                            "expected": one.expected,
                            "state": one.state,
                            "rebuilt_by": list(one.rebuilt_by),
                            "why": one.why,
                            "base": one.base,
                            "base_held": one.base_held,
                            "base_in_class": one.base_in_class,
                            "base_matched": one.base_matched,
                            "built": list(one.built),
                        }
                        for one in sorted(results, key=lambda one: one.rule_id)
                    ],
                },
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
        print(f"report             {arguments.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
