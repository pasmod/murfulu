"""The Ganjoor adapter, against a fixture with the real schema."""

import re
from pathlib import Path

import pytest

from murfulu.corpus.contract import check_adapter
from murfulu.corpus.ganjoor import GanjoorCorpus

CENTURIES = {"hafez": 14}


def _corpus(snapshot: Path) -> GanjoorCorpus:
    return GanjoorCorpus(snapshot, centuries=CENTURIES)


def test_it_passes_the_shared_adapter_test(ganjoor_snapshot: Path):
    assert check_adapter(_corpus(ganjoor_snapshot)) == 2


def test_one_document_per_poem_never_per_verse(ganjoor_snapshot: Path):
    documents = list(_corpus(ganjoor_snapshot).documents())
    assert len(documents) == 2, "the poem with no verses is not a document"
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


def test_prose_paragraphs_are_left_out(ganjoor_snapshot: Path):
    """Prose belongs to a later ingest pass, not to the poetry one."""
    robaee = next(
        d for d in _corpus(ganjoor_snapshot).documents() if "khayyam" in d.document_id
    )
    assert "نثر" not in robaee.text_fa
    assert robaee.text_fa == "برخیز بتا بیا ز بهر دل ما"


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
