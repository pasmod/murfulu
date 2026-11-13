"""The level a built word is shown with, and the order it puts the list in.

The project lead's choice of 2026-11-13: one of three levels per word —
familiar, well-formed, weakly backed — with the three figures behind a
button, and the list sorted by level first. The level is decided by the API
because a deep answer is ranked and paged there (``_ranked``); the browser
sorts steps 1 and 2 the same way.
"""

from __future__ import annotations

import pytest

from murfulu.api.generate import _form, _ranked, _rule_counts
from murfulu.engine.affix import Step
from murfulu.engine.dedupe import GroupedForm
from murfulu.rules.pack import loaded as pack
from murfulu.scoring import level, stored
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


class TestTheLevel:
    def test_familiar_is_the_word_under_its_own_reading_in_ten_poems(self) -> None:
        chain = level.chain_of(_form_of("dānā", DANA).shortest_path)
        assert level.assess(_found(Level.READING, 2118), chain).level == level.FAMILIAR
        assert level.assess(_found(Level.READING, 10), chain).level == level.FAMILIAR
        # Nine poems is not familiar; the rule decides instead.
        assert level.assess(_found(Level.READING, 9), chain).level == level.WELL_FORMED

    def test_the_letters_alone_never_make_a_word_familiar(self) -> None:
        """دانست is in 1,273 poems as "he knew", not as the noun built."""
        chain = level.chain_of(_form_of("Dānest", DANA).shortest_path)
        letters = _found(Level.SPELLING, 1273, spelling_unlinked=True)
        assert level.assess(letters, chain).level == level.WELL_FORMED

    def test_a_function_words_count_never_makes_a_word_familiar(self) -> None:
        chain = level.chain_of(_form_of("Keh", DANA).shortest_path)
        keh = _found(Level.SPELLING, 0, function_word="conjunction")
        assessed = level.assess(keh, chain)
        assert assessed.level == level.WELL_FORMED
        assert assessed.corpus_mark is None

    def test_a_rule_in_the_lowest_third_makes_it_weakly_backed(self) -> None:
        chain = level.chain_of(_form_of("zirdānā", ZIRDANA).shortest_path)
        assessed = level.assess(_found(Level.NONE), chain)
        assert assessed.level == level.WEAK
        assert assessed.weakest is not None
        assert (assessed.weakest.rule_id, assessed.weakest.attested) == ("V-076", 1)

    def test_a_middle_rule_is_ordinary_not_weak(self) -> None:
        """vā- realises 0.49%, the middle third: an ordinary rule here."""
        chain = level.chain_of(_form_of("vādānā", VADANA).shortest_path)
        assessed = level.assess(_found(Level.NONE), chain)
        assert assessed.level == level.WELL_FORMED
        assert assessed.weakest is not None and assessed.weakest.rule_id == "V-070"

    def test_an_unasked_corpus_gives_no_level(self) -> None:
        chain = level.chain_of(_form_of("dānā", DANA).shortest_path)
        assert level.assess(None, chain).level is None

    def test_a_chain_nobody_measured_gives_no_level(self) -> None:
        """Not measured is never a level, and never weakly backed."""
        chain = level.chain_of(_form_of("x", (("N-999", "-x"),)).shortest_path)
        assessed = level.assess(_found(Level.NONE), chain)
        assert assessed.level is None and assessed.weakest is None

    def test_it_is_served_as_unconfirmed(self) -> None:
        chain = level.chain_of(_form_of("dānā", DANA).shortest_path)
        served = level.assess(_found(Level.READING, 2118), chain).as_json()
        assert served["confirmed"] is False
        assert served["level"] == level.FAMILIAR


class TestTheMarks:
    @pytest.mark.parametrize(
        ("found", "mark"),
        [
            (None, None),
            (_found(Level.NONE), 0),
            (_found(Level.SPELLING, 2), 1),
            (_found(Level.READING, 9), 1),
            (_found(Level.READING, 44), 2),
            (_found(Level.READING, 999), 2),
            (_found(Level.READING, 1000), 3),
        ],
    )
    def test_the_corpus_by_poems(
        self, found: Attestation | None, mark: int | None
    ) -> None:
        assert level.corpus_mark(found) == mark

    def test_the_rule_by_its_weakest_third(self) -> None:
        chain = level.chain_of(_form_of("vādānā", VADANA).shortest_path)
        assert level.assess(_found(Level.NONE), chain).rule_mark == 2

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
    def test_the_meaning_folded_to_three(
        self, band: str | None, mark: int | None
    ) -> None:
        chain = level.chain_of(_form_of("dānā", DANA).shortest_path)
        assert level.assess(_found(Level.NONE), chain, band).meaning_mark == mark


class TestTheOrder:
    def test_familiar_then_well_formed_then_unknown_then_weak(self) -> None:
        ranked = sorted(
            [level.WEAK, None, level.FAMILIAR, level.WELL_FORMED], key=level.order
        )
        assert ranked == [level.FAMILIAR, level.WELL_FORMED, None, level.WEAK]

    def test_the_route_ranks_the_level_before_the_rules_median(self) -> None:
        """A weak chain no longer outranks a well-formed one on its median.

        zirdānā's chain realises 0.01% and 8.97%, a median of 4.49%; vādān's
        one rule realises 0.49%. The median put zirdānā first. The level puts
        it last, because zir- almost never makes a word the corpus has — the
        project lead's order of 2026-11-13. This fails on the old ranking.
        """
        zirdana = _form_of("zirdānā", ZIRDANA)
        vadan = _form_of("vādān", (("V-070", "vā-"),))
        none = _found(Level.NONE)
        order = [f.latin for f in _ranked([zirdana, vadan], lambda _: none, None)]
        assert order == ["vādān", "zirdānā"]

    def test_within_a_level_the_old_order_holds(self) -> None:
        many = _form_of("dānā", DANA)
        few = _form_of("dānande", DANA)
        counts = {"dānā": 2118, "dānande": 306}

        def found(form: GroupedForm) -> Attestation:
            return _found(Level.READING, counts[form.latin])

        assert [f.latin for f in _ranked([few, many], found, None)] == [
            "dānā",
            "dānande",
        ]


class TestWhatIsServed:
    def test_each_form_carries_its_level_and_each_rule_its_third(self) -> None:
        served = _form(pack(), _form_of("zirdānā", ZIRDANA), None, _found(Level.NONE))
        assert served["level"]["level"] == level.WEAK
        assert served["level"]["weakest_rule"]["affix"] == "zir-"
        assert served["level"]["marks"]["corpus"] == 0
        assert [step["built"]["band"] for step in served["paths"][0]] == ["low", "high"]

    def test_an_unmeasured_rule_has_no_third(self) -> None:
        assert _rule_counts("N-999") is None
        assert MEASURED.band("N-999") is None
        assert MEASURED.band("nowhere") is None
