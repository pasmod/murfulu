"""One test case per example in the rule pack.

The cases are **generated from the YAML**, not written here. Add a rule with an
example and its test appears; change an example and the test changes with it.
That is what makes the rule pack its own test suite.

Two forms of example appear in the source:

``goft + ār = Goftār``  a worked derivation — base, affix, result
``ravande``             a result only

Until the engine exists (PLAN 2.1) these check the *shape* of every example:
that it parses, that a worked derivation's parts agree with the rule that
carries it, and that the result is a plausible Behnevis form. When the engine
lands, ``expected`` becomes what it must produce.
"""

import json
import os
import re
from pathlib import Path

import pytest

from murfulu.rules.pack import Glide, Rule, load

PACK = load()

#: "goft + ār = Goftār" and "dānā + i = Dānāyi".
WORKED = re.compile(
    r"^(?P<base>[^+=]+?)\s*\+\s*(?P<affix>[^+=]+?)\s*=\s*(?P<result>.+)$"
)

#: The Behnevis letters. Anything outside this is not a Latin form.
BEHNEVIS = re.compile(r"^[A-Za-zāĀšŠžŽčČīĪūŪéÉíÍˈ'-]+$")


class Example:
    """One example, with the rule it came from."""

    def __init__(self, rule: Rule | Glide, text: str) -> None:
        self.rule = rule
        self.text = text
        match = WORKED.match(text)
        self.base = match.group("base").strip() if match else None
        self.affix = match.group("affix").strip() if match else None
        self.expected = (match.group("result") if match else text).strip()

    @property
    def is_worked(self) -> bool:
        return self.base is not None

    def __repr__(self) -> str:
        return f"{self.rule.id}:{self.text}"


def _collect() -> list[Example]:
    found = []
    for rule in [*PACK.rules, *PACK.glides]:
        for text in rule.examples:
            found.append(Example(rule, text))
    return found


EXAMPLES = _collect()
WORKED_EXAMPLES = [e for e in EXAMPLES if e.is_worked]


def test_the_examples_were_generated_not_hand_written():
    """If this file ever stops tracking the pack, the count gives it away."""
    from_pack = sum(len(r.examples) for r in [*PACK.rules, *PACK.glides])
    assert len(EXAMPLES) == from_pack
    assert len(EXAMPLES) > 200, "the pack should carry a few hundred examples"


@pytest.mark.parametrize("example", EXAMPLES, ids=repr)
def test_every_example_is_a_usable_latin_form(example: Example):
    assert example.expected, f"{example.rule.id}: empty example"
    assert BEHNEVIS.match(example.expected), (
        f"{example.rule.id}: {example.expected!r} is not a Behnevis form"
    )


@pytest.mark.parametrize("example", WORKED_EXAMPLES, ids=repr)
def test_a_worked_example_agrees_with_its_own_rule(example: Example):
    """An example like goft + ār = Goftār must sit on a rule whose affix is -ār."""
    rule = example.rule
    if isinstance(rule, Glide):
        assert example.affix, f"{rule.id}: worked example with no right-hand side"
        return
    affixes = {
        a.lstrip("-").rstrip("-") for a in (rule.affix, *rule.affix_variants) if a
    }
    assert example.affix
    assert example.affix.lstrip("-").rstrip("-") in affixes, (
        f"{rule.id}: example uses {example.affix!r}, rule declares {sorted(affixes)}"
    )


@pytest.mark.parametrize("example", WORKED_EXAMPLES, ids=repr)
def test_a_worked_example_ends_with_what_it_starts_with(example: Example):
    """The result must contain the base. Catches a mistyped example."""
    if isinstance(example.rule, Glide):
        return
    assert example.base
    head = example.base[:2].lower()
    assert head in example.expected.lower(), (
        f"{example.rule.id}: {example.expected!r} does not look built from "
        f"{example.base!r}"
    )


@pytest.mark.parametrize(
    "rule", [r for r in PACK.rules if r.active], ids=lambda r: r.id
)
def test_every_active_rule_carries_at_least_one_example(rule: Rule):
    """A rule with no example cannot be checked by anyone, ever."""
    if rule.kind == "stem":
        # Stem rules state a transformation in prose and carry exception lists
        # instead of worked examples.
        assert rule.explanation_fa
        return
    assert rule.examples, f"{rule.id} has no example"


# -- the cases the plan names by hand ---------------------------------------


@pytest.mark.parametrize(
    ("rule_id", "expected"),
    [
        ("V-022", "ravande"),
        ("V-023", "Ravandegi"),
        ("V-017", "Zadoxord"),
        ("V-018", "Goftogu"),
        ("V-024", "dānā"),
        ("V-025", "Dānāyi"),
    ],
)
def test_the_examples_the_build_plan_names(rule_id: str, expected: str):
    """PLAN tasks 2.2, 2.3 and 2.4 name these. They must be in the pack."""
    rule = PACK.by_id(rule_id)
    assert expected in rule.examples, f"{rule_id}: {expected} missing"


def test_the_glide_rules_the_engine_must_pass():
    """PLAN 2.2: row + eš → Raveš, and dānā + i → Dānāyi."""
    texts = {g.id: " ".join(g.examples) for g in PACK.glides}
    assert any("Raveš" in t for t in texts.values())
    assert any("Dānāyi" in t for t in texts.values())


# -- the half the docstring above promised and never delivered ---------------
#
# The engine landed in session 2 and `expected` never became what the engine
# must produce, so ~200 examples have been checked for spelling alone ever
# since. Measured 2026-08-14 against the real snapshot at depth 3: of 163
# active prefix and suffix rules carrying an example, **88 rebuild by the rule
# that lists them**, 14 rebuild by some other rule, and 61 do not rebuild at
# all — and a good part of the last two piles is a vowel convention rather
# than a fault. N-004's example is `bexrad`; the engine builds `bexerad` from
# the lexicon's `Xerad`, and which spelling is right is the linguist's.
#
# **100 as of 2026-08-15**, in two steps. Correcting V-052 to a prefix and
# V-063 to V-066 to the stem they attach to took it to 93: exactly those five
# moved, and N-022 improved with them. The examples were not consulted in
# making either ruling, so that was the pack checking the rulings rather than
# agreeing with them. Then PLAN 9.3 ran every failing rule *forward* from its
# own base, which separated the piles for the first time and left one real
# engine fault — V-070 to V-076 dropped the infinitive ending — worth another
# seven.
#
# **The 52 that remain are not ours.** 35 name a base the lexicon does not
# hold (UPSTREAM B2) and 22 spell the base differently from karbon (the
# linguist's, FOR_THE_LINGUIST L11). Neither is fixable by changing code here.
#
# So the 100 are pinned and the rest are recorded with a number. **The list may
# grow and must never shrink**: that makes every future engine change show its
# effect on the grammar's own examples, without anyone having to settle 75
# linguistic questions first. See S20.

BASELINE = json.loads(
    (Path(__file__).parent / "example_baseline.json").read_text(encoding="utf-8")
)


def _real_lexicon() -> Path | None:
    """The configured snapshot, if it is the real one and not a fixture.

    An example names a real Persian word — *Goftār*, *Nāšenās* — and the
    fixture holds eleven entries, so this can only run where the snapshot is.
    """
    configured = os.environ.get("MURFULU_LEXICON_PATH")
    if not configured:
        return None
    found = Path(configured).expanduser()
    return found if found.is_file() else None


@pytest.mark.skipif(_real_lexicon() is None, reason="needs the real lexicon snapshot")
@pytest.mark.parametrize("rule_id", BASELINE["explained_by_its_own_rule"])
def test_the_example_this_rule_carries_still_rebuilds(rule_id: str) -> None:
    """A rule that could explain its own example must go on doing so."""
    from murfulu import analysis
    from murfulu.lexicon.store import Lexicon

    rule = PACK.by_id(rule_id)
    assert isinstance(rule, Rule)
    example = rule.examples[0]
    expected = example.split("=")[-1].strip() if "=" in example else example.strip()

    with Lexicon.open() as lexicon:
        found = analysis.explain(lexicon, PACK, expected, depth=3)

    rebuilt = {step.rule_id for account in found.analyses for step in account.steps}
    assert rule_id in rebuilt, f"{rule_id}: {expected} no longer rebuilds"


def test_the_baseline_says_how_much_of_the_pack_is_not_yet_asserted() -> None:
    """The gap is carried as a number, not left to be rediscovered.

    This is the test that makes the shortfall visible in the suite itself. It
    does not enforce the shortfall — moving an example out of these two piles
    is progress and only requires updating the file.
    """
    pinned = len(BASELINE["explained_by_its_own_rule"])
    unresolved = len(BASELINE["rebuilt_by_another_rule"]) + len(
        BASELINE["not_rebuilt_at_all"]
    )

    assert pinned + unresolved == BASELINE["checked"]
    assert pinned >= 100, "an example that used to rebuild must not stop rebuilding"
