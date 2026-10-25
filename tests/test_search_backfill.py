"""Which corpus words a rule is entitled to claim it formed.

The whole task turns on one question: a derivation and a corpus spelling can
look alike without being the same word. *Pahnā* was built with *-nā*; *Fanā*
is an Arabic loan that ends in those letters. Claiming the second would put a
false derivation in front of a reader, so the rules for claiming are the
subject of most of this module.
"""

from pathlib import Path

import pytest

from murfulu.scoring.attestation import Attestation, Level
from murfulu.scoring.records import Derivation
from murfulu.scoring.records import Path as DerivationPath
from murfulu.search.backfill import AffixMap, build

#: The reason string the map records. Its wording is not the point of a test.
ANY_REASON = "far from the words this rule usually makes"


def _derivation(
    latin: str,
    fa: str,
    level: Level,
    *,
    unlinked: bool = False,
    others: tuple[str, ...] = (),
    rule_id: str = "V-010",
    affix: str = "-ār",
) -> Derivation:
    return Derivation(
        form_latin=latin,
        form_fa=fa,
        output_type="karnam",
        paths=(
            DerivationPath(
                base_latin="goft",
                base_fa="گفت",
                base_type="karbon_yek",
                rule_ids=(rule_id,),
                affixes=(affix,),
            ),
        ),
        semantic_tags=("Jā",),
        attestation=Attestation(
            level=level,
            corpus_version="v1",
            total_count=10,
            spelling_unlinked=unlinked,
            other_readings=others,
        ),
    )


# -- who may claim what ------------------------------------------------------


def test_a_confirmed_reading_is_claimed():
    """The corpus has the spelling and the lexicon reads it our way."""
    formed = build([_derivation("Didār", "دیدار", Level.READING)], "v1")
    assert formed.by_word_type["دیدار:Didār"]["affixes"] == ["-ār"]
    assert formed.by_word_type["دیدار:Didār"]["rule_ids"] == ["V-010"]


def test_a_spelling_with_no_reading_is_proposed_not_claimed():
    """Nothing contradicts us, and nothing confirms us either.

    Claiming these was the first version of this pass, and the real corpus
    refuted it: it attached *-nā* to مولانا and eighty more Arabic phrases
    ending in the possessive نا. An unlinked spelling means the lexicon knows
    nothing about the word, including whether it is Persian.
    """
    formed = build(
        [_derivation("Goftār", "گفتار", Level.SPELLING, unlinked=True)], "v1"
    )
    assert not formed.by_word_type
    # The unlinked word type carries an empty Latin side in its id.
    assert "گفتار:" in formed.proposed
    assert formed.refused_homographs == 0


def test_a_proposal_never_reaches_the_index():
    """The index asserts; the proposal list asks."""
    formed = build(
        [_derivation("Goftār", "گفتار", Level.SPELLING, unlinked=True)], "v1"
    )
    assert formed.fields_for("گفتار:") == {
        "affixes": [],
        "rule_ids": [],
        "semantic_tags": [],
    }


def test_a_spelling_the_corpus_reads_otherwise_is_refused():
    """Claiming it would say a word we did not build was built by our rule."""
    formed = build(
        [_derivation("Mardār", "مرد", Level.SPELLING, others=("mard", "mord"))],
        "v1",
    )
    assert not formed.by_word_type
    assert formed.refused_homographs == 1


def test_a_word_nobody_wrote_claims_nothing():
    formed = build([_derivation("Rowšannā", "روشننا", Level.NONE)], "v1")
    assert not formed.by_word_type
    assert formed.refused_homographs == 0


def test_an_unchecked_run_claims_nothing():
    """No corpus means the question was never asked."""
    plain = Derivation(form_latin="X", form_fa="ایکس", output_type="nam", paths=())
    assert not build([plain], "v1").by_word_type


# -- what gets attached ------------------------------------------------------


def test_two_rules_reaching_one_word_both_get_credit():
    word = "دیدار"
    first = _derivation("Didār", word, Level.READING, rule_id="V-010", affix="-ār")
    second = _derivation("Didār", word, Level.READING, rule_id="V-011", affix="-ār")
    formed = build([first, second], "v1")
    entry = formed.by_word_type["دیدار:Didār"]
    assert entry["rule_ids"] == ["V-010", "V-011"]
    # One affix, listed once: the two rules spell it the same way.
    assert entry["affixes"] == ["-ār"]


def test_the_spelling_is_normalised_before_matching():
    """A word type is keyed on the folded spelling, so this must be too."""
    arabic = _derivation("Didār", "ديدار", Level.READING)  # Arabic ي
    formed = build([arabic], "v1")
    assert "دیدار:Didār" in formed.by_word_type  # Persian ی


def test_a_word_type_nobody_formed_gets_empty_lists():
    formed = AffixMap()
    assert formed.fields_for("missing") == {
        "affixes": [],
        "rule_ids": [],
        "semantic_tags": [],
    }


# -- handing it between runs -------------------------------------------------


def test_the_map_survives_being_written_and_read():
    formed = build(
        [
            _derivation("Didār", "دیدار", Level.READING),
            _derivation("Mardār", "مرد", Level.SPELLING, others=("mard",)),
        ],
        "v1",
    )
    again = AffixMap.from_document(formed.as_document())
    assert again.by_word_type == formed.by_word_type
    assert again.proposed == formed.proposed
    assert again.refused_homographs == formed.refused_homographs
    assert again.corpus_version == "v1"


# -- and through the word-type writer ----------------------------------------


def test_the_writer_attaches_the_map(lexicon_snapshot: Path):
    from murfulu.corpus import link, wordtypes
    from murfulu.lexicon.store import Lexicon
    from murfulu.search import ingest
    from tests.test_search_ingest import _Poems

    corpus = wordtypes.build(_Poems())
    with Lexicon.open(lexicon_snapshot) as lexicon:
        linked = link.link(corpus, lexicon)

    target = next(item for item in linked.linked if item.reading)
    formed = AffixMap(
        by_word_type={
            target.id: {
                "affixes": ["-ār"],
                "rule_ids": ["V-010"],
                "semantic_tags": [],
            }
        }
    )

    assert ingest.word_type_source(target, "v1", "", formed)["affixes"] == ["-ār"]
    assert ingest.word_type_source(target, "v1", "")["affixes"] == []


@pytest.mark.parametrize("field", ["affixes", "rule_ids", "semantic_tags"])
def test_the_three_fields_are_always_present(field: str):
    assert field in AffixMap().fields_for("anything")


# -- claims the homograph detector doubts ------------------------------------


def test_a_doubted_claim_is_held_out_of_the_index():
    """`word_types.rule_ids` is an assertion, and a doubted claim is not one.

    It is what puts a word in the search screen's *formed with this affix*
    group. A word we doubt belongs in the other group, which says only that
    the letters match.
    """
    formed = build(
        [_derivation("Šāhdān", "شاهدان", Level.READING, rule_id="N-048")],
        "v1",
        frozenset({("N-048", "Šāhdān")}),
    )
    assert formed.by_word_type == {}
    assert formed.contested == {"شاهدان:Šāhdān": {"N-048": ANY_REASON}}
    assert formed.contested_claims == 1


def test_a_word_keeps_the_rules_nothing_doubts():
    """Doubt is per rule. One rule falling does not silence the others."""
    import dataclasses

    word = _derivation("Goftār", "گفتار", Level.READING)
    word = dataclasses.replace(
        word,
        paths=(
            *word.paths,
            DerivationPath(
                base_latin="goft",
                base_fa="گفت",
                base_type="karbon_yek",
                rule_ids=("V-011",),
                affixes=("-ār",),
            ),
        ),
    )
    formed = build([word], "v1", frozenset({("V-010", "Goftār")}))
    assert formed.by_word_type["گفتار:Goftār"]["rule_ids"] == ["V-011"]
    assert formed.contested["گفتار:Goftār"] == {"V-010": ANY_REASON}


def test_nothing_is_contested_without_a_detector_run():
    formed = build([_derivation("Goftār", "گفتار", Level.READING)], "v1")
    assert formed.contested == {}
    assert formed.by_word_type["گفتار:Goftār"]["rule_ids"] == ["V-010"]


def test_contested_claims_survive_the_round_trip():
    formed = build(
        [_derivation("Šāhdān", "شاهدان", Level.READING, rule_id="N-048")],
        "v1",
        frozenset({("N-048", "Šāhdān")}),
    )
    read_back = AffixMap.from_document(formed.as_document())
    assert read_back.contested == formed.contested
