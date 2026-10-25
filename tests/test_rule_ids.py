"""The permanent rule-id register.

The three unbreakable rules from docs/RULE_PACK.md, as tests: an id is
permanent, ids are appended never inserted, and no id is ever reused.
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTER = json.loads((ROOT / "rules" / "rule_ids.json").read_text(encoding="utf-8"))
SOURCE = json.loads((ROOT / "rules" / "source_rows.json").read_text(encoding="utf-8"))

ALL_ENTRIES = [e for entries in REGISTER["families"].values() for e in entries]


def test_no_id_is_used_twice():
    ids = [e["id"] for e in ALL_ENTRIES]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("table", ["verb_stems", "nominals", "glides"])
def test_every_content_row_has_exactly_one_id(table: str):
    content = [r for r in SOURCE["tables"][table] if not r["blank"]]
    used = [e for e in REGISTER["families"][table] if "reason" not in e]
    assert len(used) == len(content)
    positions = sorted(e["docx_row_position"] for e in used)
    assert positions == sorted(r["docx_row_position"] for r in content)


@pytest.mark.parametrize(
    ("id_", "table", "row"),
    [
        # The worked examples in docs/RULE_PACK.md. If these ever move, every
        # stored derivation and every message quoting a rule id goes stale.
        ("V-010", "verb_stems", "10"),
        ("V-017", "verb_stems", "17"),
        ("V-053", "verb_stems", "53"),
    ],
)
def test_documented_ids_still_point_at_their_source_row(id_: str, table: str, row: str):
    entry = next(e for e in REGISTER["families"][table] if e["id"] == id_)
    assert entry["source"]["row"] == row


def test_the_empty_verb_row_keeps_a_reserved_id():
    """Source row 77 is blank. V-077 is reserved so it can never be reused."""
    entry = next(e for e in REGISTER["families"]["verb_stems"] if e["id"] == "V-077")
    assert "reason" in entry


@pytest.mark.parametrize(
    ("table", "id_", "follows"),
    [("verb_stems", "V-082", "8"), ("nominals", "N-105", "84")],
)
def test_unnumbered_rows_are_appended_not_inserted(table: str, id_: str, follows: str):
    entry = next(e for e in REGISTER["families"][table] if e["id"] == id_)
    assert entry["source"]["row"] is None
    assert entry["source"]["follows_row"] == follows
    highest = max(int(e["id"].split("-")[1]) for e in REGISTER["families"][table])
    assert int(id_.split("-")[1]) <= highest


def test_glide_ids_cover_the_documented_range():
    ids = sorted(e["id"] for e in REGISTER["families"]["glides"])
    assert ids == [f"G-{n:02d}" for n in range(1, 18)]


def test_all_five_families_carry_ids():
    assert set(REGISTER["families"]) == {
        "verb_stems",
        "nominals",
        "glides",
        "stem_rules",
    }


def test_the_stem_rules_cover_the_documented_range():
    ids = sorted(e["id"] for e in REGISTER["families"]["stem_rules"])
    assert ids == [f"S-{n:02d}" for n in range(1, 10)]


def test_the_stem_sub_rules_hang_off_rule_four():
    """The document divides stem 2 into eight groups, so 4-1 and 4-2 are parts."""
    by_id = {e["id"]: e for e in REGISTER["families"]["stem_rules"]}
    assert by_id["S-04"]["sub_rules"] == ["4-1", "4-2"]
    assert all(not by_id[i]["sub_rules"] for i in by_id if i != "S-04")


def test_every_stem_rule_but_the_first_has_exceptions():
    """Rule 1 strips -an from every infinitive; only 2-9 have exception lists."""
    by_id = {e["id"]: e["exception_count"] for e in REGISTER["families"]["stem_rules"]}
    assert by_id["S-01"] == 0
    assert all(count > 0 for name, count in by_id.items() if name != "S-01")


def test_the_dropped_family_is_recorded_with_its_reason():
    """D was planned and never issued. That has to stay written down."""
    assert set(REGISTER["retired_families"]) == {"D"}
    assert "V-003" in REGISTER["retired_families"]["D"]


def test_no_d_id_exists_anywhere():
    assert not [e for e in ALL_ENTRIES if e["id"].startswith("D-")]


def test_the_two_denominal_verb_rules_are_v_003_and_v_004():
    """The concept document names exactly these two. Verb table rows 3 and 4."""
    by_id = {e["id"]: e for e in REGISTER["families"]["verb_stems"]}
    assert by_id["V-003"]["source"]["row"] == "3"
    assert by_id["V-004"]["source"]["row"] == "4"
