"""The document model: where a text sits and what it is made of."""

import pytest

from murfulu.corpus.documents import (
    Document,
    InvalidDocumentError,
    Line,
    Unit,
    counted_text,
    unit_from_dict,
)

COUPLET = Unit("couplet", (Line("سطر نخست", "first"), Line("سطر دوم", "second")))
NOTE = Unit("note", (Line("یادداشت", "note"),))
PROSE = Unit("prose", (Line("بندی از نثر.", "prose"),))


def test_the_counted_text_is_the_units_lines_without_the_notes():
    assert counted_text([COUPLET, NOTE, PROSE]) == "سطر نخست\nسطر دوم\nبندی از نثر."


def test_a_document_made_from_units_carries_them():
    document = Document.from_units(
        source_id="fixture",
        document_id="fixture:a:1",
        units=[PROSE, NOTE],
        work="کتاب",
        section=("باب",),
    )
    assert document.text_fa == "بندی از نثر."
    assert document.units == (PROSE, NOTE)


def test_text_and_units_cannot_disagree():
    """The count reads text_fa, the reading screen the units."""
    with pytest.raises(InvalidDocumentError, match="counted units"):
        Document(
            source_id="fixture",
            document_id="fixture:a:1",
            text_fa="چیز دیگری",
            units=(PROSE,),
        )


def test_a_couplet_has_two_lines_and_everything_else_one():
    with pytest.raises(InvalidDocumentError, match="2 line"):
        Unit("couplet", (Line("تنها", "first"),))
    with pytest.raises(InvalidDocumentError, match="1 line"):
        Unit("prose", (Line("یک", "prose"), Line("دو", "prose")))


def test_only_known_kinds_and_positions():
    with pytest.raises(InvalidDocumentError, match="kind"):
        Unit("stanza", (Line("سطر", "first"),))
    with pytest.raises(InvalidDocumentError, match="position"):
        Line("سطر", "centre")


def test_a_unit_survives_being_stored():
    assert unit_from_dict(COUPLET.as_dict()) == COUPLET


def test_a_document_without_units_is_still_a_document():
    """A source that says nothing about its structure keeps working."""
    document = Document(source_id="fixture", document_id="fixture:a:2", text_fa="متن")
    assert document.units == () and document.work is None
