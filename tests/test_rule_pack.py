"""The YAML rule pack: every source row transcribed, nothing invented."""

import json
from pathlib import Path

import pytest
import yaml

from murfulu.rules.types import is_word_class

ROOT = Path(__file__).resolve().parents[1] / "rules"
REGISTER = json.loads((ROOT / "rule_ids.json").read_text(encoding="utf-8"))
TAGS = yaml.safe_load((ROOT / "semantic_tags.yaml").read_text(encoding="utf-8"))

FILES = ["verb_stems", "nominals", "glides", "stem_rules"]
PACK = {
    name: yaml.safe_load((ROOT / f"{name}.yaml").read_text(encoding="utf-8"))
    for name in FILES
}
AFFIX_RULES = PACK["verb_stems"]["rules"] + PACK["nominals"]["rules"]
ALL_RULES = [rule for file in FILES for rule in PACK[file]["rules"]]


@pytest.mark.parametrize("name", FILES)
def test_every_source_row_became_a_rule(name: str):
    """The pack has exactly one rule per id in the register, minus reserved."""
    expected = [e["id"] for e in REGISTER["families"][name] if "reason" not in e]
    assert sorted(r["id"] for r in PACK[name]["rules"]) == sorted(expected)


def test_no_id_appears_twice_across_the_pack():
    ids = [r["id"] for r in ALL_RULES]
    assert len(ids) == len(set(ids))


def test_the_counts_match_the_source_documents():
    assert len(PACK["verb_stems"]["rules"]) == 81
    assert len(PACK["nominals"]["rules"]) == 105
    assert len(PACK["glides"]["rules"]) == 17
    assert len(PACK["stem_rules"]["rules"]) == 9


@pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r["id"])
def test_every_rule_traces_back_to_its_source_row(rule: dict):
    assert rule["source"]["table"]
    assert "row" in rule["source"]


@pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r["id"])
def test_every_word_class_named_is_in_the_closed_set(rule: dict):
    for side in ("input", "output"):
        for name in rule.get(side, {}).get("types", []):
            assert is_word_class(name), f"{rule['id']}: {name}"


@pytest.mark.parametrize("rule", AFFIX_RULES, ids=lambda r: r["id"])
def test_every_rule_says_what_it_takes_and_what_it_makes(rule: dict):
    assert rule["input"]["types"], rule["id"]
    assert rule["output"]["types"], rule["id"]


@pytest.mark.parametrize("rule", AFFIX_RULES, ids=lambda r: r["id"])
def test_every_rule_carries_its_farsi_text(rule: dict):
    """The interface is in Farsi and the engine cannot invent it."""
    assert rule["label_fa"], rule["id"]
    assert rule["explanation_fa"], rule["id"]


@pytest.mark.parametrize("rule", AFFIX_RULES, ids=lambda r: r["id"])
def test_an_affix_rule_has_a_persian_spelling_for_its_affix(rule: dict):
    if rule["kind"] in {"suffix", "prefix", "infix"}:
        assert rule["affix_fa"], rule["id"]


@pytest.mark.parametrize("rule", AFFIX_RULES, ids=lambda r: r["id"])
def test_every_semantic_tag_used_is_declared(rule: dict):
    declared = {label for tag in TAGS["tags"] for label in tag["label_source"]}
    for tag in rule["semantic_tags"]:
        assert tag in declared, f"{rule['id']}: {tag}"


@pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r["id"])
def test_anything_uncertain_says_what_is_uncertain(rule: dict):
    """A flagged rule without a reason is worse than no flag at all."""
    if rule.get("needs_expert_check"):
        assert rule.get("notes"), rule["id"]
        assert all(note.strip() for note in rule["notes"])


def test_only_one_affix_spelling_is_still_in_doubt():
    """V-055: is it باژ or واژ? Everything else was ruled on 2026-08-11."""
    flagged = {r["id"] for r in AFFIX_RULES if r.get("needs_expert_check")}
    assert flagged == {"V-055"}


@pytest.mark.parametrize(
    ("rule_id", "kind", "affix", "source_affix", "affix_fa"),
    [
        # The source writes -mānd; its own example dānešmand says -mand.
        ("N-071", "suffix", "-mand", "-mānd", "مند"),
        # The source writes -bāž as a suffix; its example bāžgunidan puts it
        # at the front, so the dash was on the wrong side.
        ("V-055", "prefix", "bāž-", "-bāž", "باژ"),
        ("V-067", "prefix", "pa-", "pa-", "پ"),
    ],
)
def test_the_corrected_affixes_keep_the_source_spelling_beside_them(
    rule_id: str, kind: str, affix: str, source_affix: str, affix_fa: str
):
    rule = _rule(rule_id)
    assert rule["kind"] == kind
    assert rule["affix"] == affix
    assert rule["affix_source"] == source_affix
    assert rule["affix_fa"] == affix_fa


def test_the_duplicate_glide_rule_is_retired_not_deleted():
    """G-01 duplicates G-03. Retired, keeps its id, and says why."""
    glide = next(g for g in PACK["glides"]["rules"] if g["id"] == "G-01")
    assert glide["active"] is False
    assert "duplicate" in glide["retired_reason"].lower()
    assert glide["examples"] == [], "its example was filed under the wrong rule"


def test_the_two_clitic_rows_are_retired_not_deleted():
    """N-090 is the ezāfe and N-099 the indefinite -i. Neither makes a word.

    Both are rows of the source's nominal table, so both keep their id and
    their transcription — the rules screen still shows what row 90 and row 99
    said. What changes is that the generator stops running them.

    Their own examples are the argument: N-090's is ``Ketābé u`` — کتابِ او,
    *his book*, which is two words joined — and N-099's is ``Ketābí``, کتابی,
    *a book*, which is the same word with an article on it.
    """
    for rule_id, why in (("N-090", "ezāfe"), ("N-099", "indefinite")):
        rule = _rule(rule_id)
        assert rule["active"] is False, f"{rule_id} still generates"
        assert why in rule["retired_reason"].lower()
        # The transcription itself is untouched: the row is still readable.
        assert rule["examples"], f"{rule_id} lost the source's example"


def test_the_misfiled_glide_example_moved_to_the_right_rule():
    """ā + ande = Āyande joins ā with a, so it belongs to the ā + a rule."""
    g04 = next(g for g in PACK["glides"]["rules"] if g["id"] == "G-04")
    assert (g04["left"], g04["right"], g04["result"]) == ("ā", "a", "āya")
    assert "ā + ande = Āyande" in g04["examples"]


def test_the_surviving_a_plus_e_rule_keeps_its_own_example():
    g03 = next(g for g in PACK["glides"]["rules"] if g["id"] == "G-03")
    assert g03["active"] is True
    assert g03["examples"] == ["Pā + e = Pāye"]


# -- the worked examples in docs/RULE_PACK.md --------------------------------


def _rule(rule_id: str) -> dict:
    return next(r for r in ALL_RULES if r["id"] == rule_id)


def test_the_documented_suffix_rule_is_as_the_design_record_says():
    rule = _rule("V-010")
    assert rule["kind"] == "suffix"
    assert rule["affix"] == "-ār"
    assert rule["input"]["types"] == ["karbon_yek"]
    assert rule["output"]["types"] == ["karnam"]
    # "bištar" — mostly. A tendency, so not full weight.
    assert rule["strength"] == "typical"
    assert rule["label_fa"] == "کاربن یک + -ār"


def test_the_documented_prefix_rule_is_as_the_design_record_says():
    rule = _rule("V-053")
    assert rule["kind"] == "prefix"
    assert rule["affix"] == "bar-"
    assert rule["semantic_tags"] == ["bālā"]
    assert rule["input"]["types"] == ["nabesudkarvaze"]
    assert rule["output"]["types"] == ["nabesudkarvaze"]


@pytest.mark.parametrize(
    ("rule_id", "pattern", "constraint", "example"),
    [
        ("V-017", "{a} + o + {b}", "different_verb", "Zadoxord"),
        ("V-018", "{a} + o + {b}", "same_verb", "Goftogu"),
        ("V-044", "{a} + ā + {b}", "same_stem", "Kešākeš"),
    ],
)
def test_the_compounding_templates_keep_both_slots(
    rule_id: str, pattern: str, constraint: str, example: str
):
    """A template that loses its second slot still looks like a valid rule."""
    rule = _rule(rule_id)
    assert rule["kind"] == "template"
    assert rule["pattern"] == pattern
    assert len(rule["slots"]) == 2
    assert rule["slots"][1]["constraint"] == constraint
    assert example in rule["examples"]


def test_the_negated_template_is_marked_negated():
    rule = _rule("V-021")
    assert rule["pattern"] == "{a} + o + na + {b}"
    assert rule["slots"][1]["negated"] is True
    assert "Budonabud" in rule["examples"]


# -- glides ------------------------------------------------------------------


@pytest.mark.parametrize("rule", PACK["glides"]["rules"], ids=lambda r: r["id"])
def test_every_glide_rule_is_complete(rule: dict):
    assert rule["left"] and rule["right"] and rule["result"]
    assert rule["explanation_fa"]


def test_the_glide_rules_the_engine_will_be_tested_on():
    by_id = {r["id"]: r for r in PACK["glides"]["rules"]}
    dana = next(r for r in by_id.values() if r["result"] == "āyi")
    assert "dānā + i = Dānāyi" in " ".join(dana["examples"])
    row = next(r for r in by_id.values() if r["left"] == "ow" and r["right"] == "e")
    assert row["result"] == "av"


# -- stem rules --------------------------------------------------------------


def test_the_first_stem_rule_makes_stem_one_and_the_rest_make_stem_two():
    by_id = {r["id"]: r for r in PACK["stem_rules"]["rules"]}
    assert by_id["S-01"]["output"]["types"] == ["karbon_yek"]
    assert all(
        by_id[i]["output"]["types"] == ["karbon_do"] for i in by_id if i != "S-01"
    )


def test_the_stem_exceptions_are_attached_to_their_rule():
    by_id = {r["id"]: r for r in PACK["stem_rules"]["rules"]}
    pairs = {e["infinitive_fa"]: e["stems_fa"] for e in by_id["S-09"]["exceptions"]}
    assert pairs["رفتن"] == ["رفت", "رو"]
    assert pairs["گفتن"] == ["گفت", "گو"]


def test_the_two_resolved_exceptions_say_who_resolved_them():
    """The karbon library read the same document; its readings are cited."""
    by_id = {r["id"]: r for r in PACK["stem_rules"]["rules"]}
    resolved = {
        e["infinitive_fa"]: e
        for rule in by_id.values()
        for e in rule["exceptions"]
        if e.get("read_by")
    }
    assert set(resolved) == {"گشادن", "افراشتن"}
    for entry in resolved.values():
        assert entry["read_by"] == "karbon"
        assert entry["source_text"], "the original wording must stay visible"
        assert entry["resolution_note"].strip()
        assert not entry.get("needs_expert_check")


def test_the_one_exception_nobody_can_read_is_still_open():
    """The document writes ؟ and karbon leaves the verb out. Not guessed here."""
    by_id = {r["id"]: r for r in PACK["stem_rules"]["rules"]}
    entry = next(
        e for e in by_id["S-09"]["exceptions"] if e["infinitive_fa"] == "نهفتن"
    )
    assert entry["needs_expert_check"]
    assert "؟" in entry["stems_fa"]
    assert by_id["S-09"]["needs_expert_check"]


def test_the_stem_sub_rules_hang_off_rule_four():
    by_id = {r["id"]: r for r in PACK["stem_rules"]["rules"]}
    assert [s["part"] for s in by_id["S-04"]["sub_rules"]] == ["4-1", "4-2"]
    assert all(not by_id[i]["sub_rules"] for i in by_id if i != "S-04")


#: What each Latin joining element is written as in Persian. Only the three
#: the source uses; a fourth would have to be added deliberately.
JOINS = {"o": "و", "ona": "ونا", "ā": "ا"}


def test_a_compounding_pattern_says_the_same_thing_in_both_alphabets():
    """The Latin and the Persian of one rule must join with the same letters.

    V-021 read `{a} + o + na + {b}` in Latin and `{a}ون{b}` in Persian — the
    ا of *na* was missing, so the engine built *Budonabud* correctly and
    بودونبود wrongly, and the rule's own example says which is right. One
    rule of ten, silent, and only visible by building a compound.
    """
    import re

    patterned = [rule for rule in ALL_RULES if rule.get("pattern")]
    assert patterned, "no compounding rule has a pattern; the check is vacuous"
    for rule in patterned:
        latin = re.sub(r"^\{a\}|\{b\}$", "", rule["pattern"])
        latin = latin.replace("+", "").replace(" ", "")
        persian = re.sub(r"^\{a\}|\{b\}$", "", rule.get("pattern_fa") or "")
        assert latin in JOINS, f"{rule['id']} joins with {latin!r}, which is new"
        assert persian == JOINS[latin], (
            f"{rule['id']} joins with {latin!r} in Latin and {persian!r} in Persian"
        )
