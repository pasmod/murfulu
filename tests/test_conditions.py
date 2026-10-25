"""What a rule says about its base, beyond the word class.

The source states a condition for 186 of 195 rules. For 164 it is the word
class again, which `input_types` already enforces. **Twelve say more, and
nothing read them** — the text sat in the YAML and no code looked at it.

What is checked here is mostly restraint: that a condition is recorded and
never used to refuse a word, that a tendency is not reported as a rule, and
that "we could not test this" never comes back looking like "this failed".
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from murfulu.engine.affix import Word, apply
from murfulu.rules import conditions
from murfulu.rules.pack import loaded as loaded_pack

PACK = Path(__file__).resolve().parents[1] / "rules"


@pytest.fixture
def table() -> dict[str, conditions.Condition]:
    return conditions.load(PACK)


# -- the authored table ------------------------------------------------------


def test_every_condition_quotes_the_grammar(table: dict[str, conditions.Condition]):
    """A condition nobody can check against the source is not evidence."""
    for condition in table.values():
        assert condition.source_text.strip()


def test_the_quoted_text_is_really_what_the_rule_says(
    table: dict[str, conditions.Condition],
):
    """The table is authored, so it can drift from the pack. It must not."""
    rows = {}
    for name in ("verb_stems", "nominals", "stem_rules"):
        document = yaml.safe_load((PACK / f"{name}.yaml").read_text(encoding="utf-8"))
        for rule in document["rules"]:
            rows[rule["id"]] = rule

    for rule_id, condition in table.items():
        assert rule_id in rows, f"{rule_id} is not in the pack"
        said = (rows[rule_id].get("input") or {}).get("condition_text") or ""
        assert condition.source_text == said, (
            f"{rule_id}: the table quotes {condition.source_text!r} but the "
            f"pack says {said!r}"
        )


def test_a_condition_with_nothing_to_test_is_refused():
    with pytest.raises(conditions.ConditionError):
        conditions._load(
            {"conditions": [{"rule": "V-010", "test": "ends_with", "values": []}]}
        )


def test_a_condition_with_no_source_text_is_refused():
    with pytest.raises(conditions.ConditionError):
        conditions._load(
            {
                "conditions": [
                    {
                        "rule": "V-010",
                        "test": "ends_with",
                        "values": ["t"],
                        "strictness": "tendency",
                    }
                ]
            }
        )


def test_two_conditions_for_one_rule_are_refused():
    one = {
        "rule": "V-010",
        "test": "ends_with",
        "values": ["t"],
        "strictness": "stated",
        "source_text": "x",
    }
    with pytest.raises(conditions.ConditionError):
        conditions._load({"conditions": [one, dict(one)]})


# -- testing a base ----------------------------------------------------------


def test_the_ending_is_checked_on_the_latin(table: dict[str, conditions.Condition]):
    """Behnevis is phonemic, so a final sound is a final letter here.

    In the Persian script it would not be — which is the whole reason this
    project works in Latin.
    """
    v010 = table["V-010"]
    assert v010.met_by("raft") is True
    assert v010.met_by("goft") is True
    assert v010.met_by("did") is True
    assert v010.met_by("row") is False


def test_a_rule_with_no_condition_answers_nothing_at_all():
    """183 of the 195 rules. The ordinary case, and not a failure."""
    condition, met = conditions.check("V-015", "raft")
    assert condition is None
    assert met is None


def test_a_condition_we_cannot_test_is_not_reported_as_failed(
    table: dict[str, conditions.Condition],
):
    """The difference between *we did not check* and *it did not hold*.

    V-001 turns on which of karbon's stem groups NKZ names, and nobody has
    ruled on that. Guessing would silently mark half the verbs as breaking a
    rule they may well keep.
    """
    v001 = table["V-001"]
    assert v001.needs_expert_check
    assert v001.testable is False
    assert v001.met_by("raft") is None


# -- what it must not do ------------------------------------------------------


def test_a_failing_condition_never_stops_the_rule():
    """The source hedges, and a filter is the linguist's ruling, not ours."""
    pack = loaded_pack()
    rule = pack.by_id("V-010")
    built = apply(pack, rule, Word(latin="row", fa="رو", word_class="karbon_yek"))
    # The word is still built, and it still says the condition was not met.
    assert built.latin == "Ravār"
    assert built.path[0].condition_met is False


def test_a_met_condition_is_recorded_too():
    """Recording only the failures would make a silence ambiguous."""
    pack = loaded_pack()
    built = apply(
        pack, pack.by_id("V-010"), Word(latin="raft", fa="رفت", word_class="karbon_yek")
    )
    assert built.path[0].condition_met is True
    assert "Pāyāne" in built.path[0].condition_text


def test_a_tendency_is_marked_as_a_tendency(table: dict[str, conditions.Condition]):
    """V-010 says *bištar* — mostly. Reporting that as a rule overstates it."""
    assert table["V-010"].strictness == "tendency"
    assert "بیشتر" in table["V-010"].describe_fa()
    assert table["V-023"].strictness == "stated"
    assert "بیشتر" not in table["V-023"].describe_fa()


def test_the_engine_refuses_nothing_it_used_to_build():
    """A word that was generated yesterday is still generated today.

    Recording a condition must not quietly become a filter, which is the one
    way this change could damage the project.
    """
    pack = loaded_pack()
    from murfulu.engine.affix import apply_all

    for base, kind in (("raft", "karbon_yek"), ("row", "karbon_do")):
        built = apply_all(pack, Word(latin=base, fa="", word_class=kind))
        assert built, f"nothing built from {base}"
        # Every rule that could apply still did.
        applied = {form.path[0].rule_id for form in built}
        expected = {
            rule.id
            for rule in pack.rules
            if rule.active
            and rule.kind in {"suffix", "prefix", "infix", "none"}
            and kind in rule.input_types
            and rule.output_types
        }
        assert applied == expected
