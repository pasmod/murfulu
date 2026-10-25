"""The semantic tag set must cover every bracketed tag in the source grammar."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TAGS = yaml.safe_load(
    (ROOT / "rules" / "semantic_tags.yaml").read_text(encoding="utf-8")
)
SOURCE = json.loads((ROOT / "rules" / "source_rows.json").read_text(encoding="utf-8"))


def _labels_in_the_source() -> set[str]:
    """Every bracketed label the two rule tables use, verbatim."""
    found: set[str] = set()
    for table in ("verb_stems", "nominals"):
        for row in SOURCE["tables"][table]:
            if row["blank"]:
                continue
            for bracket in re.findall(r"\((.*?)\)", row["affix"] or ""):
                found.update(p.strip() for p in bracket.split(",") if p.strip())
    return found


def test_every_tag_used_by_a_rule_exists_in_the_file():
    declared = {label for tag in TAGS["tags"] for label in tag["label_source"]}
    assert _labels_in_the_source() - declared == set()


def test_no_tag_is_declared_that_no_rule_uses():
    declared = {label for tag in TAGS["tags"] for label in tag["label_source"]}
    assert declared - _labels_in_the_source() == set()


def test_every_tag_carries_both_glosses():
    for tag in TAGS["tags"]:
        assert tag["gloss_fa"], tag["tag"]
        assert tag["gloss_en"], tag["tag"]


def test_machine_ids_are_unique_and_ascii():
    ids = [tag["tag"] for tag in TAGS["tags"]]
    assert len(ids) == len(set(ids))
    for tag_id in ids:
        assert re.fullmatch(r"[a-z]+", tag_id), tag_id


def test_every_usage_points_at_a_real_source_row():
    rows = {
        f"{table}:{row['row']}"
        for table in ("verb_stems", "nominals")
        for row in SOURCE["tables"][table]
        if row["row"] and not row["blank"]
    }
    for tag in TAGS["tags"]:
        assert set(tag["used_by"]) <= rows, tag["tag"]


def test_uncertain_tags_carry_a_note():
    """Anything flagged for the linguist must say what the question is."""
    for tag in TAGS["tags"]:
        if tag.get("needs_expert_check"):
            assert tag.get("note"), tag["tag"]
