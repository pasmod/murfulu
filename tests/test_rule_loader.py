"""The rule-pack loader, and what it refuses to load.

Every failure test breaks one rule deliberately and checks the loader says so.
"""

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from murfulu.rules.pack import Glide, Rule, RulePackError, load

PACK = load()

VALID_RULE: dict[str, Any] = {
    "id": "V-999",
    "kind": "suffix",
    "source": {"table": "verb_stems", "row": "999"},
    "affix": "-ār",
    "affix_fa": "ار",
    "input": {"types": ["karbon_yek"]},
    "output": {"types": ["karnam"]},
    "strength": "typical",
    "examples": ["goft + ār = Goftār"],
    "label_fa": "کاربن یک + -ār",
    "explanation_fa": "از کاربن یک با پسوند -ār کارنام ساخته می‌شود",
    "active": True,
}


def _write_pack(directory: Path, rule: dict[str, Any]) -> Path:
    """A minimal but complete pack containing one rule."""
    real = Path(__file__).resolve().parents[1] / "rules"
    for name in ("nominals", "glides", "stem_rules"):
        (directory / f"{name}.yaml").write_text(
            (real / f"{name}.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )
    (directory / "verb_stems.yaml").write_text(
        yaml.safe_dump({"version": "0.1.0", "rules": [rule]}, allow_unicode=True),
        encoding="utf-8",
    )
    return directory


# -- the real pack -----------------------------------------------------------


def test_the_whole_pack_loads():
    assert len(PACK.rules) == 81 + 105 + 9
    assert len(PACK.glides) == 17


def test_rules_are_grouped_into_the_four_families():
    families = {rule.family for rule in PACK.rules}
    assert families == {"V", "N", "S"}
    assert {glide.id.split("-")[0] for glide in PACK.glides} == {"G"}


def test_a_rule_can_be_fetched_by_its_permanent_id():
    rule = PACK.by_id("V-010")
    assert isinstance(rule, Rule)
    assert rule.affix == "-ār"
    assert isinstance(PACK.by_id("G-01"), Glide)


def test_an_unknown_id_raises():
    with pytest.raises(KeyError):
        PACK.by_id("V-999")


def test_the_rules_that_apply_to_a_word_class_can_be_found():
    """The lookup the engine does on every generation step."""
    from_past_stem = PACK.taking("karbon_yek")
    assert PACK.by_id("V-010") in from_past_stem
    assert all("karbon_yek" in rule.input_types for rule in from_past_stem)
    assert PACK.taking("nam"), "the nominal rules must be reachable too"


def test_the_flagged_rules_are_the_ones_we_know_about():
    """Two left of the original six: one affix spelling, one missing stem."""
    flagged = {rule.id for rule in PACK.needing_expert_check}
    assert flagged == {"V-055", "S-09"}
    for rule in PACK.needing_expert_check:
        assert rule.notes


def test_a_retired_rule_keeps_its_id_and_stays_out_of_matching():
    """G-01 is retired. Still addressable, never applied."""
    assert PACK.by_id("G-01").active is False


def test_a_missing_rule_file_is_an_error(tmp_path: Path):
    with pytest.raises(RulePackError, match="missing rule file"):
        load(tmp_path)


# -- deliberately broken rules -----------------------------------------------


@pytest.mark.parametrize(
    ("change", "complaint"),
    [
        ({"kind": "sufix"}, "unknown kind"),
        ({"strength": "quite strong"}, "unknown strength"),
        ({"input": {"types": ["karnamm"]}}, "unknown word class"),
        ({"output": {"types": []}}, "names no word class"),
        ({"affix_fa": None}, "no Persian spelling"),
        ({"explanation_fa": ""}, "no Farsi explanation"),
        ({"label_fa": ""}, "no Farsi label"),
        ({"source": {}}, "does not name its source table"),
        ({"needs_expert_check": True}, "says nothing about why"),
        # A rule could be switched off in the YAML and quietly stop building
        # words. The glide loader has refused that since G-01; this one did
        # not, and it was found when N-090 and N-099 were retired and the
        # reasons written beside them were dropped on load.
        ({"active": False}, "retired but does not say why"),
    ],
)
def test_a_broken_rule_fails_loudly(
    tmp_path: Path, change: dict[str, Any], complaint: str
):
    broken = {**copy.deepcopy(VALID_RULE), **change}
    with pytest.raises(RulePackError, match=complaint) as raised:
        load(_write_pack(tmp_path, broken))
    assert "V-999" in str(raised.value), "the message must name the rule"


def test_a_valid_rule_still_loads(tmp_path: Path):
    """The control: the broken-rule tests would pass vacuously without it."""
    pack = load(_write_pack(tmp_path, copy.deepcopy(VALID_RULE)))
    assert pack.by_id("V-999").affix == "-ār"


@pytest.mark.parametrize(
    ("change", "complaint"),
    [
        ({"pattern": None}, "no pattern"),
        ({"slots": [{"name": "a", "type": "karbon_yek"}]}, "fewer than two slots"),
        (
            {"slots": [{"name": "a", "type": "kārbon"}, {"name": "b", "type": "nam"}]},
            "unknown type",
        ),
        (
            {
                "slots": [
                    {"name": "a", "type": "nam"},
                    {"name": "b", "type": "nam", "constraint": "rhymes"},
                ]
            },
            "unknown constraint",
        ),
    ],
)
def test_a_broken_template_fails_loudly(
    tmp_path: Path, change: dict[str, Any], complaint: str
):
    template = {
        **copy.deepcopy(VALID_RULE),
        "kind": "template",
        "pattern": "{a} + o + {b}",
        "pattern_fa": "{a}و{b}",
        "slots": [
            {"name": "a", "type": "karbon_yek"},
            {"name": "b", "type": "karbon_yek", "constraint": "different_verb"},
        ],
        **change,
    }
    with pytest.raises(RulePackError, match=complaint):
        load(_write_pack(tmp_path, template))


def test_a_duplicate_id_fails_loudly(tmp_path: Path):
    """An id addresses exactly one rule, or every stored derivation is ambiguous."""
    _write_pack(tmp_path, copy.deepcopy(VALID_RULE))
    (tmp_path / "verb_stems.yaml").write_text(
        yaml.safe_dump(
            {"version": "0.1.0", "rules": [VALID_RULE, VALID_RULE]}, allow_unicode=True
        ),
        encoding="utf-8",
    )
    with pytest.raises(RulePackError, match="appears twice"):
        load(tmp_path)


def test_a_broken_glide_fails_loudly(tmp_path: Path):
    _write_pack(tmp_path, copy.deepcopy(VALID_RULE))
    (tmp_path / "glides.yaml").write_text(
        yaml.safe_dump(
            {
                "version": "0.1.0",
                "rules": [{"id": "G-99", "left": "ā", "right": "i", "result": ""}],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    with pytest.raises(RulePackError, match="no result vowel"):
        load(tmp_path)
