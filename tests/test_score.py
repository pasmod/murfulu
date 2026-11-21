"""The two values a built word is shown with, and the order they put it in.

The project lead's choice of 2026-11-21 (second): how well the word is built,
0 to 100 from its rules alone, and what the corpus says, kept apart — so a
good word the old poetry never used does not sink for that. The API decides
both because a deep answer is ranked and paged there (``_ranked``); the
browser sorts steps 1 and 2 the same way.
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


class TestTheBuildValue:
    @pytest.mark.parametrize(
        ("rate", "points"),
        [(0.0, 0), (0.0001, 0), (0.001, 33), (0.01, 67), (0.1, 100), (0.31, 100)],
    )
    def test_a_log_scale_from_one_in_ten_thousand_to_one_in_ten(
        self, rate: float, points: int
    ) -> None:
        assert score.build_points(rate) == points

    def test_the_weakest_rule_decides(self) -> None:
        """zir- (1 of 7,830) under -ā (748 of 8,337): zir- is the chain's rule."""
        scored = _scored(_found(Level.NONE), ZIRDANA, "zirdānā")
        assert scored.weakest is not None and scored.weakest.rule_id == "V-076"
        assert scored.build == 4

    def test_it_is_the_same_whether_the_corpus_has_the_word_or_not(self) -> None:
        """The point of the split: a good word the poets never used keeps it."""
        absent = _scored(_found(Level.NONE), DANA)
        known = _scored(_found(Level.READING, 2118), DANA)
        assert absent.build == known.build == 98

    def test_an_unmeasured_chain_takes_the_middle_measured_rate(self) -> None:
        """Not measured is never a low value: the median of the three rates."""
        scored = _scored(_found(Level.NONE), (("N-999", "-x"),), "x")
        assert scored.weakest is None
        assert scored.build == score.build_points(38 / 7835) == 56

    def test_an_unmeasured_step_counts_too_never_skipped(self) -> None:
        """An unmeasured step counts at the median, never skipped.

        -ā is measured (8.97%), N-999 is not: the chain is no better than the
        median for its unmeasured step, never the full 98 of -ā alone.
        """
        scored = _scored(_found(Level.NONE), (("N-999", "-x"), ("V-024", "-ā")), "x")
        assert scored.build == score.build_points(38 / 7835) == 56
        assert scored.weakest is None


class TestTheCorpusAnswer:
    def test_the_word_under_its_reading(self) -> None:
        assert score.corpus_kind(_found(Level.READING, 2118)) == "reading"

    def test_letters_nobody_reads_otherwise_may_be_it(self) -> None:
        """گفتار: written 4,813 times, no lexicon entry to say how it is read."""
        letters = _found(Level.SPELLING, 4813, spelling_unlinked=True)
        assert score.corpus_kind(letters) == "letters"

    def test_a_recorded_alternate_or_another_case_is_this_word(self) -> None:
        """*jehān* beside *Jahān*: the index does not mark it another word's."""
        assert (
            score.corpus_kind(_found(Level.SPELLING, 9, other_readings=("Jahān",)))
            == "letters"
        )

    def test_another_words_letters_are_other(self) -> None:
        """روی is *Rui*, face; که is the conjunction; رفتی is "you went"."""
        rui = _found(
            Level.SPELLING, 31_830, other_readings=("Rui",), headword_homograph=True
        )
        keh = _found(Level.SPELLING, 0, function_word="conjunction")
        assert score.corpus_kind(rui) == "other"
        assert score.corpus_kind(keh) == "other"
        assert score.corpus_kind(_found(Level.SPELLING, 500), inflected=True) == "other"

    def test_not_written_and_not_asked(self) -> None:
        assert score.corpus_kind(_found(Level.NONE)) == "none"
        assert score.corpus_kind(None) is None

    def test_the_texts_travel_with_it(self) -> None:
        assert _scored(_found(Level.READING, 306), DANA).texts == 306
        assert _scored(None, DANA).texts is None


class TestWhatIsServed:
    def test_each_form_carries_both_values_and_each_rule_its_third(self) -> None:
        served = _form(pack(), _form_of("zirdānā", ZIRDANA), None, _found(Level.NONE))
        assert served["score"]["build"] == 4
        assert served["score"]["corpus"] == "none"
        assert served["score"]["confirmed"] is False
        assert served["score"]["weakest_rule"]["affix"] == "zir-"
        assert "value" not in served["score"] and "level" not in served
        assert [step["built"]["band"] for step in served["paths"][0]] == ["low", "high"]

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
    def test_the_meaning_is_beside_the_values_not_in_them(
        self, band: str | None, mark: int | None
    ) -> None:
        plain = _scored(_found(Level.NONE), DANA)
        banded = _scored(_found(Level.NONE), DANA, typicality_band=band)
        assert banded.meaning_mark == mark
        assert banded.build == plain.build

    def test_an_unmeasured_rule_has_no_third(self) -> None:
        assert _rule_counts("N-999") is None
        assert MEASURED.band("N-999") is None
        assert MEASURED.band("nowhere") is None


class TestTheOrder:
    def test_a_well_built_new_word_comes_before_a_weakly_built_known_one(self) -> None:
        """The complaint the split answers.

        vādān (absent, vā- 0.49%) used to sit below anything the corpus had;
        now it sits above zirdānā even when the corpus has zirdānā once.
        """
        zirdana = _form_of("zirdānā", ZIRDANA)
        vadan = _form_of("vādān", (("V-070", "vā-"),))
        counts = {"zirdānā": _found(Level.READING, 1), "vādān": _found(Level.NONE)}
        order = [
            f.latin for f in _ranked([zirdana, vadan], lambda f: counts[f.latin], None)
        ]
        assert order == ["vādān", "zirdānā"]

    def test_the_corpus_answer_outranks_the_older_tie_breakers(self) -> None:
        """The corpus's answer decides before the older keys do.

        Equal build values: letters that may be the word come before a function
        word's letters, although the function word has more texts — the order
        the older keys alone would give the other way round.
        """
        letters = _form_of("kehin", DANA)
        keh = _form_of("Keh", DANA)
        found = {
            "kehin": _found(Level.SPELLING, 5, spelling_unlinked=True),
            "Keh": _found(Level.SPELLING, 500, function_word="conjunction"),
        }
        ranked = _ranked([keh, letters], lambda f: found[f.latin], None)
        assert [f.latin for f in ranked] == ["kehin", "Keh"]

    def test_between_equal_build_values_the_corpus_decides(self) -> None:
        many = _form_of("dānā", DANA)
        few = _form_of("dānande", DANA)
        none = _form_of("dānāk", DANA)
        found = {
            "dānā": _found(Level.READING, 2118),
            "dānande": _found(Level.READING, 306),
            "dānāk": _found(Level.NONE),
        }
        ranked = _ranked([none, few, many], lambda f: found[f.latin], None)
        assert [f.latin for f in ranked] == ["dānā", "dānande", "dānāk"]
