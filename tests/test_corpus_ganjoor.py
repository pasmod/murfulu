"""The Ganjoor adapter, against a fixture with the real schema."""

import re
from pathlib import Path

import pytest

from murfulu.corpus.contract import check_adapter
from murfulu.corpus.documents import Document
from murfulu.corpus.ganjoor import GanjoorCorpus, UnknownPositionError, units_of

CENTURIES = {"hafez": 14, "saadi": 13}


def _corpus(snapshot: Path) -> GanjoorCorpus:
    return GanjoorCorpus(snapshot, centuries=CENTURIES)


def test_it_passes_the_shared_adapter_test(ganjoor_snapshot: Path):
    assert check_adapter(_corpus(ganjoor_snapshot)) == 4


def test_one_document_per_page_never_per_verse(ganjoor_snapshot: Path):
    documents = list(_corpus(ganjoor_snapshot).documents())
    ids = sorted(d.document_id for d in documents)
    assert ids == [
        "ganjoor:hafez:100",
        "ganjoor:khayyam:101",
        "ganjoor:saadi:103",
        "ganjoor:saadi:104",
    ], "a page with no verses, or with only a note, is not a document"
    ghazal = next(d for d in documents if d.document_id.endswith(":100"))
    assert ghazal.text_fa.count("\n") == 1, "both hemistichs, one document"


def test_provenance_survives_the_ingest(ganjoor_snapshot: Path):
    ghazal = next(iter(_corpus(ganjoor_snapshot).documents()))
    assert ghazal.author == "حافظ"
    assert ghazal.title == "غزل شمارهٔ ۱"
    assert ghazal.century == 14
    assert ghazal.extra["url"].startswith("https://ganjoor.net/")


def test_the_document_id_names_the_poet_not_the_book(ganjoor_snapshot: Path):
    """A poem sits in a book category, so the poet must come from elsewhere."""
    ids = [d.document_id for d in _corpus(ganjoor_snapshot).documents()]
    assert "ganjoor:hafez:100" in ids
    assert "ganjoor:khayyam:101" in ids
    assert not any("ghazal" in i or "robaee" in i for i in ids)


def _page(snapshot: Path, poem_id: int) -> Document:
    return next(
        d
        for d in _corpus(snapshot).documents()
        if d.document_id.endswith(f":{poem_id}")
    )


def test_the_source_s_note_is_kept_but_not_counted(ganjoor_snapshot: Path):
    """Position 5 is Ganjoor's Comment: the source's own words, not the text."""
    robaee = _page(ganjoor_snapshot, 101)
    assert robaee.text_fa == "برخیز و بیا که روز نو آمد"
    assert [u.kind for u in robaee.units] == ["half", "note"]
    assert robaee.units[1].lines[0].text == "این یادداشت گردآورنده است"
    assert not robaee.units[1].counted


def test_prose_is_text_and_a_unit_of_its_own(ganjoor_snapshot: Path):
    """Position −1 is Ganjoor's Paragraph: prose, counted like any line.

    Until 2026-11-13 the adapter took 3 for prose and dropped it, while the
    real prose (−1) was counted all along — see FINDINGS.
    """
    preface = _page(ganjoor_snapshot, 103)
    assert [u.kind for u in preface.units] == ["prose", "couplet"]
    assert preface.text_fa.splitlines()[0].startswith("این یک بند نثر است.")
    assert preface.units[1].lines[1].position == "second"


def test_every_position_in_ganjoor_s_enum_becomes_a_unit(ganjoor_snapshot: Path):
    """A band couplet (2 then 3), a band line alone, free verse, a lone half."""
    story = _page(ganjoor_snapshot, 104)
    assert [(u.kind, [one.position for one in u.lines]) for u in story.units] == [
        ("prose", ["prose"]),
        ("couplet", ["band_first", "band_second"]),
        ("half", ["band_first"]),
        ("half", ["free"]),
        ("half", ["second"]),
    ], "the empty line is skipped, as before"
    # 3 is the second half of a band couplet — counted, not dropped.
    assert "بند دوم این سرود" in story.text_fa


def test_a_text_knows_its_work_and_section(ganjoor_snapshot: Path):
    ghazal = _page(ganjoor_snapshot, 100)
    assert (ghazal.work, ghazal.section) == ("غزلیات", ())
    story = _page(ganjoor_snapshot, 104)
    assert (story.work, story.section, story.title) == (
        "گلستان",
        ("باب نخست",),
        "حکایت شمارهٔ ۱",
    )
    assert story.order == 104


def test_the_units_are_counted_by_kind(ganjoor_snapshot: Path):
    corpus = _corpus(ganjoor_snapshot)
    list(corpus.documents())
    assert corpus.units_by_kind() == {"couplet": 3, "half": 4, "note": 1, "prose": 2}


def test_a_position_outside_ganjoor_s_enum_fails_loudly():
    with pytest.raises(UnknownPositionError, match="7"):
        units_of([(7, "سطری با جایگاهی ناشناخته")])


def test_a_poet_with_no_century_gets_none_not_a_guess(ganjoor_snapshot: Path):
    corpus = _corpus(ganjoor_snapshot)
    documents = list(corpus.documents())
    khayyam = next(d for d in documents if "khayyam" in d.document_id)
    assert khayyam.century is None
    assert corpus.poets_without_a_century() == ["khayyam"]


def test_a_missing_dump_fails_loudly(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Ganjoor dump not found"):
        GanjoorCorpus(tmp_path / "nope.db")


def test_the_licence_is_stated(ganjoor_snapshot: Path):
    assert _corpus(ganjoor_snapshot).licence.strip()


def test_the_licence_is_also_stated_in_persian(ganjoor_snapshot: Path):
    """The reader is Persian and the corpus screen showed them English.

    Ganjoor's own answer to *are your data free of copyright* is «لزوماً خیر!»,
    so this is nearer the source than the English beside it rather than a
    translation away from it. Both are kept: the English is what the ingest log
    and NOTICE carry.
    """
    corpus = _corpus(ganjoor_snapshot)
    assert corpus.licence_fa.strip()
    assert corpus.licence_fa != corpus.licence
    # A Persian sentence, not a slug and not a transliteration.
    assert re.search(r"[؀-ۿ]", corpus.licence_fa)
    # It must still carry the warning, not only the friendly half.
    assert "لزوماً" in corpus.licence_fa
