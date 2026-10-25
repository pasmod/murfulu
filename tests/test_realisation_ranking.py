"""Ranking a deep answer by how often its rules produce real words.

**Why this exists.** The build screen offers three steps, and three steps is
17,717 words for one verb, of which fifty are words the corpus has. The answer
has to be paged, and a page of an unranked list is a random handful — so the
route ranks first. What it ranks *on* is the question these check.

The semantic score cannot do this job, and that is not a fault in it. A base's
vector is the average of up to six corpus lines using the word, so a word
nobody has written can never have one; the score is therefore measured on the
first step alone, and 12,999 of a verb's 17,717 forms share 22 values between
them. Asking about the **rules** instead — how often each one's output turns
out to be a word — is what separates *hamandišande* from *hamandišidbāngāne*.
"""

from __future__ import annotations

import pytest

from murfulu.api.generate import _ranked, _realisation
from murfulu.engine.affix import Step
from murfulu.engine.dedupe import GroupedForm
from murfulu.scoring import stored

#: The two chains, with each rule's measured realisation rate from v9. The good
#: word and the nonsense one are both three steps from the same verb and
#: neither is in the corpus, so nothing above this criterion can tell them
#: apart.
HAMANDIŠANDE = ("V-005", "V-062", "V-022")  # 27.8%, 0.04%, 21.8%
HAMANDIŠIDBĀNGĀNE = ("V-015", "N-015", "N-066")  # 0.12%, 0.22%, 0.02%

MEASURED = stored.Measured(
    corpus_version="v9",
    by_rule={
        "V-005": {"rule_id": "V-005", "measured": True, "realisation_rate": 0.2777},
        "V-062": {"rule_id": "V-062", "measured": True, "realisation_rate": 0.0004},
        "V-022": {"rule_id": "V-022", "measured": True, "realisation_rate": 0.2184},
        "V-015": {"rule_id": "V-015", "measured": True, "realisation_rate": 0.0012},
        "N-015": {"rule_id": "N-015", "measured": True, "realisation_rate": 0.0022},
        "N-066": {"rule_id": "N-066", "measured": True, "realisation_rate": 0.0002},
        # The run reached this rule and could not measure it. Not a zero.
        "N-999": {"rule_id": "N-999", "measured": False, "realisation_rate": None},
    },
)


def _form(latin: str, chain: tuple[str, ...], base: str = "base") -> GroupedForm:
    """One form and its chain.

    ``base`` is what every step ran on, which is what a grounding check asks
    about.
    """
    path = tuple(Step(rule_id=rule, affix="-x", base_latin=base) for rule in chain)
    return GroupedForm(latin=latin, fa=latin, word_class="nam", paths=(path,))


def _with(measurements: stored.Measured, monkeypatch: pytest.MonkeyPatch) -> None:
    """Serve these measurements instead of the configured file.

    ``neutral_realisation`` is cached for the life of the process, so it is
    swapped for its uncached original rather than cleared: a cleared cache
    would refill with test data and the next test would read it.
    """
    monkeypatch.setattr(stored, "loaded", lambda: measurements)
    monkeypatch.setattr(
        stored, "neutral_realisation", stored.neutral_realisation.__wrapped__
    )


class TestTheFigureItself:
    def test_a_chain_is_summarised_by_its_middle_rule(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The median, not the weakest link.

        *ham-* realises 0.04% and *-ande* 21.8% **in the same word**, so one
        weak rule in a strong chain is ordinary. On the weakest link the good
        chain and the nonsense one are within 2× of each other; on the median
        they are 180× apart.
        """
        _with(MEASURED, monkeypatch)
        good = _realisation(_form("hamandišande", HAMANDIŠANDE))
        bad = _realisation(_form("hamandišidbāngāne", HAMANDIŠIDBĀNGĀNE))
        assert good is not None and bad is not None
        assert good["median"] == 0.2184
        assert bad["median"] == 0.0012
        assert good["median"] > bad["median"] * 100

    def test_it_says_how_much_of_the_chain_was_measured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A figure that hides how many rules it rests on is not a measurement."""
        _with(MEASURED, monkeypatch)
        mixed = _realisation(_form("x", ("V-022", "N-999")))
        assert mixed is not None
        assert mixed["steps"] == 2
        assert mixed["steps_measured"] == 1

    def test_an_unmeasured_rule_is_neither_good_nor_bad(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """*Not measured* must never read as a rate of zero.

        An unmeasured rule is filled in at the median of the measured ones, so
        a chain through one lands where a chain with no information should —
        between the good and the bad, not beneath both.
        """
        _with(MEASURED, monkeypatch)
        unknown = _realisation(_form("x", ("N-999",)))
        assert unknown is not None
        assert unknown["median"] == stored.neutral_realisation()
        assert unknown["median"] > 0

    def test_nothing_measured_at_all_is_silence_not_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A machine that has never run the precompute says nothing."""
        _with(stored.Measured(), monkeypatch)
        assert _realisation(_form("x", HAMANDIŠANDE)) is None


class TestTheOrder:
    def test_the_good_word_outranks_the_nonsense(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The only criterion that can tell these two apart.

        Neither is in the corpus and both are three steps from the same verb,
        so everything ranked above this is equal between them.
        """
        _with(MEASURED, monkeypatch)
        forms = [
            _form("hamandišidbāngāne", HAMANDIŠIDBĀNGĀNE),
            _form("hamandišande", HAMANDIŠANDE),
        ]
        order = [f.latin for f in _ranked(forms, lambda _: None, None)]
        assert order == ["hamandišande", "hamandišidbāngāne"]

    def test_it_outranks_the_ground_under_the_chain(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Swapped by the project lead 2026-08-17, and this pins the order.

        Grounding marks بازگوینده as standing on air though the corpus has it —
        the step in between is the infinitive of a prefixed verb, which poets
        had little reason to write. So a strong chain on unwritten ground beats
        a weak chain on written ground; the ground still ranks, one place down.
        """
        _with(MEASURED, monkeypatch)
        strong_but_airborne = _form("hamandišande", HAMANDIŠANDE, base="unwritten")
        weak_but_grounded = _form(
            "hamandišidbāngāne", HAMANDIŠIDBĀNGĀNE, base="written"
        )
        order = [
            f.latin
            for f in _ranked(
                [weak_but_grounded, strong_but_airborne],
                lambda _: None,
                lambda base: base == "written",
            )
        ]
        assert order == ["hamandišande", "hamandišidbāngāne"]

    def test_the_ground_still_ranks_where_the_rules_agree(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Demoted, not dropped.

        Two chains of equal strength are still split by whether the way to
        them is written.
        """
        _with(MEASURED, monkeypatch)
        airborne = _form("alef", HAMANDIŠANDE, base="unwritten")
        grounded_one = _form("beh", HAMANDIŠANDE, base="written")
        order = [
            f.latin
            for f in _ranked(
                [airborne, grounded_one], lambda _: None, lambda b: b == "written"
            )
        ]
        assert order == ["beh", "alef"]

    def test_the_corpus_still_outranks_everything(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A tie-breaker among the unwritten, never a rival to evidence.

        A word with a weak chain that the corpus *has* stays above a word with
        a strong chain that it has not.
        """
        from murfulu.scoring.attestation import Attestation, Level

        _with(MEASURED, monkeypatch)
        written = _form("hamandišidbāngāne", HAMANDIŠIDBĀNGĀNE)
        unwritten = _form("hamandišande", HAMANDIŠANDE)
        found = Attestation(
            level=Level.READING, corpus_version="v9", total_count=9, doc_count=9
        )
        order = [
            f.latin
            for f in _ranked(
                [unwritten, written],
                lambda form: found if form.latin == written.latin else None,
                None,
            )
        ]
        assert order[0] == "hamandišidbāngāne"

    def test_the_same_request_always_gives_the_same_answer(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two forms alike on every measure fall back to the alphabet.

        A page is then stable, so paging cannot skip a word or show it twice.
        """
        _with(MEASURED, monkeypatch)
        forms = [_form("beta", ("V-022",)), _form("alpha", ("V-022",))]
        assert [f.latin for f in _ranked(forms, lambda _: None, None)] == [
            "alpha",
            "beta",
        ]
