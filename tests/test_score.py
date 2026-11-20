"""The score a built word is shown with, and the order it puts the list in.

The project lead's choice of 2026-11-21: one score from 0 to 100 per word, in
place of the three levels of 2026-11-13 — up to 70 from the corpus and up to
30 from the chain's weakest rule — so the list can be sorted and filtered by
it. The API decides it because a deep answer is ranked and paged there
(``_ranked``); the browser sorts steps 1 and 2 the same way.
"""

from __future__ import annotations

import pytest

from murfulu.api.generate import _form, _ranked, _rule_counts
from murfulu.engine.affix import Step
from murfulu.engine.dedupe import GroupedForm
from murfulu.rules.pack import loaded as pack
from murfulu.scoring import score, stored
from murfulu.scoring.attestation import Attestation, Level

#: Bands as the productivity run writes them, from v16's own figures: -ā is
#: in the top third, vā- in the middle, zir- (1 of 7,830) and ham- (1 of
#: 13,598) in the lowest.
MEASURED = stored.Measured(
    corpus_version="v16",
    by_rule={
        "V-024": {
            "rule_id": "V-024",
            "measured": True,
            "realisation_rate": 0.0897,
            "types_built": 8337,
            "types_attested": 748,
            "band": "high",
        },
        "V-070": {
            "rule_id": "V-070",
            "measured": True,
            "realisation_rate": 0.0049,
            "types_built": 7835,
            "types_attested": 38,
            "band": "middle",
        },
        "V-076": {
            "rule_id": "V-076",
            "measured": True,
            "realisation_rate": 0.0001,
            "types_built": 7830,
            "types_attested": 1,
            "band": "low",
        },
        # Reached and not measured: no band, never a low one.
        "N-999": {"rule_id": "N-999", "measured": False, "realisation_rate": None},
    },
)


@pytest.fixture(autouse=True)
def measured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(stored, "loaded", lambda: MEASURED)
    monkeypatch.setattr(
        stored, "neutral_realisation", stored.neutral_realisation.__wrapped__
    )


def _form_of(latin: str, chain: tuple[tuple[str, str], ...]) -> GroupedForm:
    path = tuple(
        Step(rule_id=rule, affix=affix, base_latin="dān") for rule, affix in chain
    )
    return GroupedForm(
        latin=latin, fa=latin, word_class="karandekarbahr", paths=(path,)
    )


def _found(level_: Level, poems: int = 0, **more: object) -> Attestation:
    return Attestation(
        level=level_,
        corpus_version="v16",
        total_count=poems,
        doc_count=poems,
        author_count=poems,
        **more,  # type: ignore[arg-type]
    )


DANA = (("V-024", "-ā"),)
ZIRDANA = (("V-076", "zir-"), ("V-024", "-ā"))
VADANA = (("V-070", "vā-"), ("V-024", "-ā"))


def _scored(
    found: Attestation | None,
    chain_: tuple[tuple[str, str], ...],
    latin: str = "dānā",
    **more: object,
) -> score.Score:
    return score.assess(
        found, score.chain_of(_form_of(latin, chain_).shortest_path), **more
    )  # type: ignore[arg-type]


class TestTheCorpusPart:
    @pytest.mark.parametrize(
        ("texts", "points"),
        [(1, 30), (10, 43), (100, 57), (1000, 70), (50_000, 70)],
    )
    def test_the_word_under_its_reading_climbs_from_30_to_70(
        self, texts: int, points: int
    ) -> None:
        assert round(score.corpus_points(_found(Level.READING, texts)) or 0) == points

    def test_letters_nobody_reads_otherwise_count_half(self) -> None:
        """گفتار: written 4,813 times, no lexicon entry to say how it is read."""
        letters = _found(Level.SPELLING, 1000, spelling_unlinked=True)
        assert score.corpus_points(letters) == 35

    def test_letters_the_lexicon_reads_as_another_word_count_nothing(self) -> None:
        """روی is *Rui*, face: its 31,830 texts are not *ravi*'s.

        The index says so by marking the letters the bank's headword under
        other readings only (``headword_homograph``).
        """
        other = _found(
            Level.SPELLING, 31_830, other_readings=("Rui",), headword_homograph=True
        )
        assert score.corpus_points(other) == 0

    def test_the_same_reading_in_another_case_is_ours(self) -> None:
        same = _found(Level.SPELLING, 1000, other_readings=("goft",))
        assert score.corpus_points(same) == 35

    def test_a_recorded_alternate_is_ours(self) -> None:
        """A recorded alternate is this word, not another one.

        *jehān* is the bank's alternate of *Jahān*, so the index does not mark
        the letters another word's, and the score must not either — the case
        the first draft missed by reading ``other_readings`` itself.
        """
        alternate = _found(Level.SPELLING, 1000, other_readings=("Jahān",))
        assert score.corpus_points(alternate) == 35

    def test_an_inflection_shaped_spelling_counts_nothing(self) -> None:
        """رفتی is "you went"; its texts say nothing about a built word."""
        letters = _found(Level.SPELLING, 500)
        assert score.corpus_points(letters, inflected=True) == 0

    def test_a_function_words_count_is_never_credited(self) -> None:
        keh = _found(Level.SPELLING, 0, function_word="conjunction")
        assert score.corpus_points(keh) == 0

    def test_the_banks_other_headword_is_never_credited(self) -> None:
        sarv = _found(Level.SPELLING, 900, headword_homograph=True)
        assert score.corpus_points(sarv) == 0

    def test_not_written_is_zero_and_not_asked_is_none(self) -> None:
        assert score.corpus_points(_found(Level.NONE)) == 0
        assert score.corpus_points(None) is None


class TestTheRulePart:
    @pytest.mark.parametrize(
        ("rate", "points"),
        [(0.0, 0), (0.0001, 0), (0.001, 10), (0.01, 20), (0.1, 30), (0.31, 30)],
    )
    def test_a_log_scale_from_one_in_ten_thousand_to_one_in_ten(
        self, rate: float, points: int
    ) -> None:
        assert round(score.rule_points(rate)) == points

    def test_the_weakest_rule_decides(self) -> None:
        """zir- (1 of 7,830) under -ā (748 of 8,337): zir- is the chain's rule."""
        scored = _scored(_found(Level.NONE), ZIRDANA, "zirdānā")
        assert scored.weakest is not None and scored.weakest.rule_id == "V-076"
        assert round(scored.rule) == 1

    def test_an_unmeasured_chain_takes_the_middle_measured_rate(self) -> None:
        """Not measured is never a low score: the median of V-024, V-070, V-076."""
        scored = _scored(_found(Level.NONE), (("N-999", "-x"),), "x")
        assert scored.weakest is None
        assert scored.rule == pytest.approx(score.rule_points(38 / 7835), abs=0.5)


class TestTheScore:
    def test_any_word_the_corpus_has_outranks_any_it_does_not(self) -> None:
        once_weak = _scored(_found(Level.READING, 1), ZIRDANA, "zirdānā").value
        absent_strong = _scored(_found(Level.NONE), DANA).value
        assert once_weak is not None and absent_strong is not None
        assert once_weak >= 30 >= absent_strong

    def test_an_unasked_corpus_gives_no_score(self) -> None:
        assert _scored(None, DANA).value is None

    def test_it_is_served_with_its_parts_and_as_unconfirmed(self) -> None:
        served = _scored(_found(Level.READING, 2118), DANA).as_json()
        assert served["confirmed"] is False
        assert served["corpus"] == 70 and served["rule"] == 30
        assert served["value"] == 100
        assert served["weakest_rule"]["rule_id"] == "V-024"

    @pytest.mark.parametrize(
        ("band", "mark"),
        [
            ("lowest", 1),
            ("low", 1),
            ("middle", 2),
            ("high", 3),
            ("highest", 3),
            (None, None),
        ],
    )
    def test_the_meaning_is_beside_the_score_not_in_it(
        self, band: str | None, mark: int | None
    ) -> None:
        plain = _scored(_found(Level.NONE), DANA)
        banded = _scored(_found(Level.NONE), DANA, typicality_band=band)
        assert banded.meaning_mark == mark
        assert banded.value == plain.value


class TestTheOrder:
    def test_the_route_ranks_by_score_and_the_weak_chain_sinks(self) -> None:
        """The weakest rule ranks, not the chain's median.

        zirdānā's chain realises 0.01% and 8.97%, a median of 4.49%; vādān's
        one rule realises 0.49%. The median put zirdānā first; the weakest rule
        puts it last.
        """
        zirdana = _form_of("zirdānā", ZIRDANA)
        vadan = _form_of("vādān", (("V-070", "vā-"),))
        none = _found(Level.NONE)
        order = [f.latin for f in _ranked([zirdana, vadan], lambda _: none, None)]
        assert order == ["vādān", "zirdānā"]

    def test_more_texts_rank_higher(self) -> None:
        many = _form_of("dānā", DANA)
        few = _form_of("dānande", DANA)
        counts = {"dānā": 2118, "dānande": 306}

        def found(form: GroupedForm) -> Attestation:
            return _found(Level.READING, counts[form.latin])

        assert [f.latin for f in _ranked([few, many], found, None)] == [
            "dānā",
            "dānande",
        ]

    def test_no_score_sorts_last(self) -> None:
        assert sorted([None, 12, 80], key=score.order) == [80, 12, None]


class TestWhatIsServed:
    def test_each_form_carries_its_score_and_each_rule_its_third(self) -> None:
        served = _form(pack(), _form_of("zirdānā", ZIRDANA), None, _found(Level.NONE))
        assert served["score"]["value"] == 1
        assert served["score"]["corpus"] == 0
        assert served["score"]["weakest_rule"]["affix"] == "zir-"
        assert "level" not in served
        assert [step["built"]["band"] for step in served["paths"][0]] == ["low", "high"]

    def test_an_unmeasured_rule_has_no_third(self) -> None:
        assert _rule_counts("N-999") is None
        assert MEASURED.band("N-999") is None
        assert MEASURED.band("nowhere") is None
