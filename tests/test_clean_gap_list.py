"""Cleaning the karbon gap list: what may be dropped, and on what evidence.

UPSTREAM B2b. A gap list sent raw asks a headword dictionary to add tens of
thousands of conjugated verbs and plurals. The clean takes those out — but only
where the pattern that recognises them has been shown, on karbon's own
headwords, to be right often enough to act on.

The Analyser and Held here are the real ones, on a handful of made-up words, so
the test asserts the tool's *policy* rather than re-testing the instrument.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from murfulu.corpus.inflection import Analyser, Held

ROOT = Path(__file__).resolve().parent.parent


def _tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "clean_gap_list", ROOT / "tools" / "clean_gap_list.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Registered before it runs: a dataclass reads its own module out of
    # sys.modules while it is being built, and finds nothing if this is left
    # until afterwards.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TOOL = _tool()


@pytest.fixture
def held() -> Held:
    """A tiny lexicon: two headwords and one verb's two stems."""
    return Held.of(headwords=["کتاب", "مرد"], past_stems=["رفت"], present_stems=["رو"])


@pytest.fixture
def analyser(held: Held) -> Analyser:
    return Analyser(held=held)


def _rows(*pairs: tuple[str, int]) -> list:
    return [TOOL.Row(spelling=s, total_count=n, doc_count=1) for s, n in pairs]


def test_an_inflection_of_a_held_word_comes_off_the_list(
    analyser: Analyser, held: Held
) -> None:
    """کتاب‌ها is not a missing headword; کتاب is already there."""
    result = TOOL.clean(_rows(("کتاب‌ها", 40)), analyser, held, ceiling=1.0)

    assert [row.spelling for row in result.dropped] == ["کتاب‌ها"]
    assert result.kept == []
    assert result.dropped[0].base == "کتاب"


def test_a_word_nothing_explains_stays_on_the_list(
    analyser: Analyser, held: Held
) -> None:
    """The whole point of the list is the words that are really missing."""
    result = TOOL.clean(_rows(("گفتار", 4813)), analyser, held, ceiling=1.0)

    assert [row.spelling for row in result.kept] == ["گفتار"]
    assert result.dropped == []


def test_a_pattern_that_misreads_known_words_may_not_drop_anything(
    analyser: Analyser, held: Held
) -> None:
    """A ceiling of zero lets only the patterns that never err take a row off.

    This is the guard that matters: a word held back by a bad pattern is a word
    karbon never hears about, and nothing downstream would ever notice.
    """
    rows = _rows(("کتاب‌ها", 40))
    permissive = TOOL.clean(rows, analyser, held, ceiling=1.0)
    assert permissive.dropped, "it is droppable when any error rate is allowed"

    strict = TOOL.clean(_rows(("کتاب‌ها", 40)), analyser, held, ceiling=-1.0)
    assert strict.dropped == [], "no pattern clears an impossible ceiling"
    assert len(strict.kept) == 1
    assert strict.kept_despite_a_pattern, "and the cost of the ceiling is counted"


def test_the_error_rate_is_measured_on_words_that_are_words(
    analyser: Analyser, held: Held
) -> None:
    """Every headword is a word, so one read as an inflection is a mistake."""
    rates, size = TOOL.error_rates(analyser, held)

    assert size == len(held.headwords)
    assert all(0.0 <= rate <= 1.0 for rate in rates.values())


def test_the_before_and_after_counts_add_up(analyser: Analyser, held: Held) -> None:
    """The number quoted in a pull request has to be the number in the file."""
    result = TOOL.clean(
        _rows(("کتاب‌ها", 40), ("گفتار", 4813), ("رفتار", 1206)),
        analyser,
        held,
        ceiling=1.0,
    )

    assert result.before == 3
    assert len(result.kept) + len(result.dropped) == result.before


def test_the_buildable_filter_keeps_only_what_our_rules_explain(
    tmp_path: Path,
) -> None:
    """Chosen over filtering function words, 2026-08-15.

    و ("and") is not built from anything, so it never qualifies — the filter
    removes the function words as a side effect rather than needing a list of
    them written by hand.
    """
    import json

    affix_map = tmp_path / "affix-map.json"
    affix_map.write_text(
        json.dumps(
            {
                "proposed": {
                    "گفتار:r1": {"rule_ids": ["V-010"], "affixes": ["-ār"]},
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    can_build = TOOL.buildable(affix_map)
    assert can_build["گفتار"]["rule_ids"] == ["V-010"]
    assert "و" not in can_build


def test_a_word_carries_the_rules_that_would_build_it(tmp_path: Path) -> None:
    """The point of option B: every row explains itself.

    Not *please add گفتار* but *گفتار occurs 4,813 times and is goft + -ār by
    rule V-010*.
    """
    import json

    affix_map = tmp_path / "affix-map.json"
    affix_map.write_text(
        json.dumps(
            {"proposed": {"گفتار:": {"rule_ids": ["V-010"], "affixes": ["-ār"]}}}
        ),
        encoding="utf-8",
    )
    found = TOOL.buildable(affix_map)["گفتار"]
    assert found["rule_ids"] and found["affixes"], "a row with no rule is not a request"
