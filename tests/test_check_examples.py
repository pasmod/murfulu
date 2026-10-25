"""Sorting a failed example into the right pile.

PLAN 9.3. The tool ran for a session reporting *75 examples do not rebuild*
and nothing more, so every one of them read as though the engine might be at
fault. What separates them is running the rule forward from the same base and
looking at what came out — and the assertions here are about that judgement,
not about Persian.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent


def _tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "check_examples", ROOT / "tools" / "check_examples.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TOOL = _tool()


def _checked(**fields: object) -> object:
    base = {
        "rule_id": "N-001",
        "example": "x",
        "expected": "x",
        "explained_by_its_own_rule": False,
    }
    return TOOL.Checked(**{**base, **fields})


def test_a_rebuilt_example_is_not_a_failure() -> None:
    assert _checked(explained_by_its_own_rule=True).why == "rebuilt"


def test_a_vowel_difference_is_not_an_engine_fault() -> None:
    """Bexrad against bexerad: the same word, spelled two ways."""
    one = _checked(
        expected="bexrad",
        base="xrad",
        base_held=True,
        base_in_class=True,
        base_matched="vowels",
        built=("bexerad",),
    )
    assert one.why == "the two spell the same word differently"


def test_a_missing_base_is_not_blamed_on_the_engine() -> None:
    """کتاب is absent, so Ketābí can never rebuild. UPSTREAM B2."""
    one = _checked(expected="Ketābí", base="Ketāb", base_held=False)
    assert one.why == "the base is not in the lexicon"


def test_a_base_held_in_the_wrong_class_is_its_own_answer() -> None:
    """Ruz is in the lexicon; the rule still cannot take it. PLAN 3.2."""
    one = _checked(
        expected="Ruze",
        base="Ruz",
        base_held=True,
        base_in_class=False,
        base_matched="exact",
    )
    assert one.why == "the lexicon has the base in another word class"


def test_a_real_engine_fault_is_still_named_as_one() -> None:
    """The pile that matters must not be explained away by the others."""
    one = _checked(
        expected="vāgoftan",
        base="goft",
        base_held=True,
        base_in_class=True,
        base_matched="exact",
        built=("vāgoft",),
    )
    assert one.why == "the engine builds a different word"


def test_a_weak_skeleton_match_does_not_become_a_spelling_question() -> None:
    """*div* finds *Dāv*, which is a different word, not another spelling."""
    one = _checked(
        expected="divāne",
        base="div",
        base_held=True,
        base_in_class=True,
        base_matched="vowels",
        built=("adviyāne", "dāvegāne"),
    )
    assert one.why == "the base is not in the lexicon"


def test_the_vowels_come_out_of_a_skeleton() -> None:
    assert TOOL._skeleton("bexrad") == TOOL._skeleton("bexerad")
    assert TOOL._skeleton("Goftār") != TOOL._skeleton("Gofte")


def test_the_base_is_read_off_a_worked_example() -> None:
    from murfulu.rules.pack import load

    rule = load().by_id("V-010")
    assert TOOL._implied_base(rule, "goft + ār = Goftār", "Goftār") == "goft"


def test_the_base_is_read_through_an_affix_variant() -> None:
    """V-004 declares -ānidan; its own example tarsāndan uses -āndan."""
    from murfulu.rules.pack import load

    rule = load().by_id("V-004")
    assert "-āndan" in {rule.affix, *rule.affix_variants}
    assert TOOL._implied_base(rule, "tarsāndan", "tarsāndan") == "tars"
