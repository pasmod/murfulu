"""A function word's letters attest nothing else.

The case that started it: karbon 1.2.0 reads row 28296 «که» as the adjective
*keh*, "small" — correctly — and the link pass credited it with the
conjunction's 609,699 occurrences (data/compare-v12-v13.md). The rule now is
that a spelling on ``rules/function_words.yaml`` credits no count to any
reading or built form written with it; the record says so instead of carrying
the number. A form *built on* such an entry is judged on its own spelling.
"""

from collections import Counter
from collections.abc import Iterator
from pathlib import Path

import pytest

from murfulu.api.generate import _evidence, _standing
from murfulu.corpus.adapter import SourceAdapter
from murfulu.corpus.documents import Document
from murfulu.corpus.function_words import (
    FunctionWord,
    FunctionWordError,
    FunctionWords,
    load,
    loaded,
)
from murfulu.corpus.link import LinkedWordType, link
from murfulu.corpus.wordtypes import WordType, build, normalise
from murfulu.lexicon import Lexicon
from murfulu.scoring import reload
from murfulu.scoring.attestation import Attestation, Index, Level
from murfulu.scoring.productivity import measure
from murfulu.scoring.records import Derivation
from murfulu.scoring.records import Path as DerivationPath
from murfulu.scoring.sisters import collect
from murfulu.search import ingest
from murfulu.search.backfill import FUNCTION_WORD_REASON
from murfulu.search.backfill import build as build_affix_map

KEH = "که"


def _word(spelling: str, total: int, docs: int, authors: int = 1) -> WordType:
    """A counted spelling, as the corpus pass would leave it."""
    word = WordType(spelling_fa=spelling, total_count=total)
    word.documents = {f"d{n}" for n in range(docs)}
    word.authors = Counter({f"poet{n}": 1 for n in range(authors)})
    word.counts_by_century = Counter({6: total})
    return word


def _only(*spellings: str) -> FunctionWords:
    """A list holding just these spellings, as conjunctions."""
    return FunctionWords(
        version="test",
        by_spelling={
            s: FunctionWord(spelling=s, word_class="conjunction", rank=1, count=1)
            for s in spellings
        },
    )


@pytest.fixture
def keh_index() -> Index:
    """The real shape of the case: که read as *keh*, کهتر under no reading."""
    index = Index(corpus_version="v14", function_words=_only(KEH))
    index.add(_word(KEH, 609_699, 101_924, 235), "keh")
    index.add(_word("کهتر", 314, 200, 60), None)
    index.add(_word("گفتار", 4_813, 3_000, 150), "Goftār")
    return index


# -- the list ----------------------------------------------------------------


def test_the_list_loads_and_holds_the_trigger_case():
    listed = loaded()
    assert listed.version
    assert listed.corpus_version == "v13"
    entry = listed.get(KEH)
    assert entry is not None
    assert entry.word_class == "conjunction"
    assert entry.count == 609_699


def test_the_list_stays_small_and_measured():
    """Conservative: a few dozen spellings, each among the commonest written."""
    listed = loaded()
    assert 20 <= len(listed) <= 60
    for entry in listed.by_spelling.values():
        assert entry.spelling == normalise(entry.spelling)
        assert 1 <= entry.rank <= listed.max_rank
        assert entry.count > 0


def test_content_homographs_judged_too_common_are_left_out():
    """می is wine as often as a particle; یک is the lexicon's own *yek*."""
    listed = loaded()
    for spelling in ("می", "یک", "خود", "کان", "زین", "است", "چرا"):
        assert spelling not in listed


def test_the_lookup_folds_arabic_letters():
    """Editions write ك for ک; the list must meet the corpus either way."""
    assert loaded().get("كه") is not None


def _write(directory: Path, body: str) -> Path:
    (directory / "function_words.yaml").write_text(body, encoding="utf-8")
    return directory


def test_a_spelling_listed_twice_is_refused(tmp_path: Path):
    body = (
        "version: 0\nentries:\n"
        "  - {spelling: که, class: conjunction, rank: 3, count: 1}\n"
        "  - {spelling: که, class: conjunction, rank: 3, count: 1}\n"
    )
    with pytest.raises(FunctionWordError, match="twice"):
        load(_write(tmp_path, body))


def test_an_unknown_class_is_refused(tmp_path: Path):
    body = "version: 0\nentries:\n  - {spelling: که, class: conjuction}\n"
    with pytest.raises(FunctionWordError, match="class"):
        load(_write(tmp_path, body))


def test_an_unnormalised_spelling_is_refused(tmp_path: Path):
    body = "version: 0\nentries:\n  - {spelling: كه, class: conjunction}\n"
    with pytest.raises(FunctionWordError, match="normalised"):
        load(_write(tmp_path, body))


# -- the rule ----------------------------------------------------------------


def test_keh_is_no_longer_attested_by_the_conjunction(keh_index: Index):
    """The trigger case: *keh* confirmed by the lexicon, credited nothing."""
    found = keh_index.look_up(KEH, "keh")
    assert found.level is Level.SPELLING
    assert found.function_word == "conjunction"
    assert (found.total_count, found.doc_count, found.author_count) == (0, 0, 0)
    assert found.first_century is None
    assert "609" not in found.describe()
    assert "attestation is unknown" in found.describe()


def test_every_form_written_with_those_letters_gets_the_same_answer(
    keh_index: Index,
):
    """*Keh* the noun and *Koh* from کهیدن borrowed the same 609,699."""
    for latin in ("Keh", "Koh"):
        found = keh_index.look_up(KEH, latin)
        assert found.function_word == "conjunction"
        assert found.total_count == 0
        assert found.other_readings == ("keh",)


def test_a_form_built_on_keh_is_judged_on_its_own_spelling(keh_index: Index):
    """کهتر is not که: its 314 occurrences are its own evidence, as before."""
    found = keh_index.look_up("کهتر", "kehtar")
    assert found.level is Level.SPELLING
    assert not found.function_word
    assert found.total_count == 314
    assert found.spelling_unlinked


def test_an_ordinary_word_is_unaffected(keh_index: Index):
    found = keh_index.look_up("گفتار", "Goftār")
    assert found.level is Level.READING
    assert not found.function_word
    assert found.total_count == 4_813


def test_a_word_nobody_wrote_is_still_not_found(keh_index: Index):
    assert keh_index.look_up("کهک", "kehak").level is Level.NONE


class _Poems(SourceAdapter):
    @property
    def source_id(self) -> str:
        return "fixture"

    @property
    def licence(self) -> str:
        return "written for this test"

    def documents(self) -> Iterator[Document]:
        yield Document(
            source_id="fixture",
            document_id="fixture:1",
            text_fa="مرد رفتن مرد",
            author="poet",
            century=6,
        )


def test_the_link_pass_and_the_list_meet(lexicon_snapshot: Path):
    """Through the real link pass, a listed spelling's readings lose the count.

    The reading next to it keeps its own.
    """
    with Lexicon.open(lexicon_snapshot) as lexicon:
        linked = link(build(_Poems()), lexicon)
    index = Index.from_link(linked, "fixture-v1", listed=_only("مرد"))
    assert index.look_up("مرد", "mard").function_word
    assert index.look_up("مرد", "mard").total_count == 0
    assert index.look_up("رفتن", "raftan").level is Level.READING
    assert index.look_up("رفتن", "raftan").total_count == 1


def test_the_default_index_applies_the_authored_list():
    """Batch and live build their index differently; both must apply it."""
    index = Index(corpus_version="v14")
    index.add(_word(KEH, 609_699, 101_924), "keh")
    assert index.look_up(KEH, "keh").function_word == "conjunction"


# -- what reads the answer ---------------------------------------------------


def _derivation(latin: str, fa: str, found: Attestation, rule: str) -> Derivation:
    return Derivation(
        form_latin=latin,
        form_fa=fa,
        output_type="karnam",
        paths=(
            DerivationPath(
                base_latin="keh",
                base_fa=KEH,
                base_type="karbon_do",
                rule_ids=(rule,),
                affixes=("‒",),
            ),
        ),
        attestation=found,
    )


def test_the_stored_record_says_so_and_reads_back(keh_index: Index):
    record = _derivation("Keh", KEH, keh_index.look_up(KEH, "Keh"), "V-049")
    stored = record.as_document()
    assert stored["attestation_function_word"] == "conjunction"
    assert stored["attested_count"] == 0
    back = reload.from_document(stored).attestation
    assert back is not None
    assert back.function_word == "conjunction"
    assert back.total_count == 0


def test_an_ordinary_record_carries_no_extra_field(keh_index: Index):
    found = keh_index.look_up("گفتار", "Goftār")
    stored = _derivation("Goftār", "گفتار", found, "V-010").as_document()
    assert "attestation_function_word" not in stored


def test_a_function_word_sister_is_ranked_last_and_kept(keh_index: Index):
    """از was heading V-049's sisters as *Az*. Sunk, never dropped."""
    records = [
        _derivation("Keh", KEH, keh_index.look_up(KEH, "Keh"), "V-049"),
        _derivation("Goftār", "گفتار", keh_index.look_up("گفتار", "Goftār"), "V-049"),
    ]
    found = collect(records, "v14").for_rule("V-049")
    assert [sister.form_latin for sister in found] == ["Goftār", "Keh"]
    assert found[-1].function_word
    assert collect(records, "v14").function_word_counts() == {"V-049": 1}


def test_the_affix_map_contests_the_claim(keh_index: Index):
    """No rule may claim to have formed a function word's letters."""
    record = _derivation("Keh", KEH, keh_index.look_up(KEH, "Keh"), "V-049")
    formed = build_affix_map([record], "v14")
    assert len(formed) == 0
    assert formed.contested == {f"{KEH}:Keh": {"V-049": FUNCTION_WORD_REASON}}


def test_productivity_does_not_count_it(keh_index: Index):
    from murfulu.rules.pack import load as load_pack

    records = [_derivation("Keh", KEH, keh_index.look_up(KEH, "Keh"), "V-049")]
    measured = measure(load_pack(), records).by_rule["V-049"]
    assert measured.types_built == 1
    assert measured.types_attested == 0


def test_the_build_screen_ranks_it_with_borrowed_counts(keh_index: Index):
    """Standing 1: written, but as another word — never 0, *ours*."""
    assert _standing(keh_index.look_up(KEH, "Keh")) == 1
    assert _standing(keh_index.look_up("گفتار", "Goftār")) == 0
    shown = _evidence(keh_index.look_up(KEH, "keh"))
    assert shown is not None
    assert shown["function_word"] == "conjunction"
    assert shown["total_count"] == 0
    assert _evidence(keh_index.look_up("گفتار", "Goftār"))["function_word"] is None


def test_the_entry_document_carries_no_count_and_the_letters_keep_theirs(
    lexicon_snapshot: Path,
):
    """که:keh says *function word, unknown*; the spelling's document counts.

    Nothing dropped, nothing claimed by the wrong word.
    """
    with Lexicon.open(lexicon_snapshot) as lexicon:
        linked = link(build(_Poems()), lexicon)
    pairs = dict(ingest._word_type_pairs(linked.linked, "v14", "", None, _only("مرد")))
    for reading in ("mard", "mord"):
        entry = pairs[f"مرد:{reading}"]
        assert entry["function_word"] == "conjunction"
        assert entry["total_count"] is None
        assert entry["doc_count"] is None
        assert entry["reading_id"] == reading
    letters = pairs["مرد:"]
    assert letters["latin"] is None
    assert letters["function_word"] == "conjunction"
    assert letters["total_count"] == 2
    # One document for the letters, however many readings they have.
    assert sum(1 for key in pairs if key.startswith("مرد:")) == 3
    # An ordinary reading is written exactly as before.
    assert pairs["رفتن:raftan"]["total_count"] == 1
    assert "function_word" not in pairs["رفتن:raftan"]


def test_an_unlinked_function_word_is_marked_and_keeps_its_count():
    item = LinkedWordType(word=_word("و", 1_109_915, 101_974))
    source = ingest.word_type_source(item, "v14", "", None, loaded())
    assert source["function_word"] == "conjunction"
    assert source["total_count"] == 1_109_915
