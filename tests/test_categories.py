"""The lexicon category → word class mapping."""

import pytest

from murfulu.lexicon.categories import (
    UnknownCategoryError,
    UnmappableCategoryError,
    load,
    mapping_for,
    word_classes_for,
)
from murfulu.rules.types import WORD_CLASSES, describe, is_word_class

# Every category the snapshot uses, counted 2026-08-11.
CATEGORIES_IN_THE_SNAPSHOT = {
    "اسم ذات": 14391,
    "صفت مرکب": 12131,
    "اسم مرکب": 8132,
    "وام‌واژه": 5347,
    "اسم معنی": 1991,
    "مصدر": 1752,
    "صفت": 1528,
    "صفت-اسم": 296,
    None: 11,
}

MAPPINGS = load()


@pytest.mark.parametrize("category", CATEGORIES_IN_THE_SNAPSHOT)
def test_every_category_is_accounted_for(category: str | None):
    """Mapped, or explicitly unmappable. Never simply absent."""
    entry = mapping_for(category)
    assert entry.is_mapped or entry.note


@pytest.mark.parametrize(("category", "rows"), list(CATEGORIES_IN_THE_SNAPSHOT.items()))
def test_the_recorded_row_counts_match_the_snapshot(category: str | None, rows: int):
    assert mapping_for(category).rows == rows


def test_no_category_is_declared_that_the_snapshot_does_not_use():
    assert set(MAPPINGS) == set(CATEGORIES_IN_THE_SNAPSHOT)


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("مصدر", ("nabesudkarvaze",)),
        ("صفت", ("barnam",)),
        ("اسم معنی", ("karnam",)),
        ("اسم ذات", ("nam",)),
        ("اسم مرکب", ("nam",)),
        ("صفت مرکب", ("barnam",)),
    ],
)
def test_the_settled_categories_map_as_the_source_grammar_says(
    category: str, expected: tuple[str, ...]
):
    assert word_classes_for(category) == expected


@pytest.mark.parametrize("category", ["وام‌واژه", "صفت-اسم", None])
def test_asking_for_an_unmapped_category_raises_with_the_reason(category: str | None):
    with pytest.raises(UnmappableCategoryError) as raised:
        word_classes_for(category)
    assert str(raised.value).strip()


def test_an_unknown_category_raises():
    with pytest.raises(UnknownCategoryError):
        mapping_for("اسم خیالی")


def test_everything_unresolved_is_flagged_for_the_expert():
    for entry in MAPPINGS.values():
        if not entry.is_mapped:
            assert entry.needs_expert_check, entry.lexicon_category
            assert entry.note


def test_the_settled_ones_say_what_they_are_grounded_in():
    for entry in MAPPINGS.values():
        if entry.is_mapped:
            assert entry.grounding == "source", entry.lexicon_category


def test_compounds_are_marked_as_such():
    """Not a word class — it decides what may feed the compounding rules."""
    assert mapping_for("اسم مرکب").is_compound
    assert mapping_for("صفت مرکب").is_compound
    assert not mapping_for("مصدر").is_compound


def test_every_target_is_in_the_closed_set():
    for entry in MAPPINGS.values():
        for name in entry.word_classes:
            assert is_word_class(name), name


def test_the_word_classes_all_carry_a_description():
    for name in WORD_CLASSES:
        assert describe(name).strip()


def test_an_unknown_word_class_raises_helpfully():
    with pytest.raises(KeyError, match="not a word class"):
        describe("karnamm")
