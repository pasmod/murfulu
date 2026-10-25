"""The committed transcription of the stem rules.

Runs against ``rules/stem_source_rows.json``, never against the .docx.
"""

import json
from pathlib import Path

DUMP = json.loads(
    (Path(__file__).resolve().parents[1] / "rules" / "stem_source_rows.json").read_text(
        encoding="utf-8"
    )
)


def test_there_are_nine_rules():
    assert [r["rule"] for r in DUMP["rules"]] == list(range(1, 10))


def test_the_two_sub_rules_belong_to_rule_four():
    assert [(s["parent_rule"], s["part"]) for s in DUMP["sub_rules"]] == [
        (4, 1),
        (4, 2),
    ]


def test_every_rule_carries_its_persian_text():
    for rule in DUMP["rules"] + DUMP["sub_rules"]:
        assert rule["text_fa"].strip()


def test_the_exception_lists_are_complete():
    """39 verbs, spread over rules 2 to 9."""
    assert len(DUMP["exceptions"]) == 39
    assert {e["rule"] for e in DUMP["exceptions"]} == set(range(2, 10))


def test_the_known_stem_pairs_are_transcribed_correctly():
    by_infinitive = {e["infinitive_fa"]: e["stems_fa"] for e in DUMP["exceptions"]}
    assert by_infinitive["رفتن"] == ["رفت", "رو"]
    assert by_infinitive["گفتن"] == ["گفت", "گو"]
    assert by_infinitive["کردن"] == ["کرد", "کن"]
    assert by_infinitive["دیدن"] == ["دید", "بین"]
    assert by_infinitive["پختن"] == ["پخت", "پز"]


def test_the_rows_that_cannot_be_read_are_flagged_not_repaired():
    """Three rows the document leaves unresolved. None of them was guessed."""
    flagged = {
        e["infinitive_fa"]: e["note"]
        for e in DUMP["exceptions"]
        if e.get("needs_expert_check")
    }
    assert set(flagged) == {"گشادن", "افراشتن", "نهفتن"}
    assert all(note.strip() for note in flagged.values())


def test_everything_else_has_exactly_two_stems():
    for entry in DUMP["exceptions"]:
        if not entry.get("needs_expert_check"):
            assert len(entry["stems_fa"]) == 2, entry["raw"]


def test_the_source_document_is_identified():
    assert DUMP["source_document"].endswith(".docx")
    assert len(DUMP["source_sha256"]) == 64
