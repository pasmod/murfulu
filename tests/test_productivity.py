"""Rule productivity, and the round trip the measurement depends on.

Everything runs against the fixture lexicon and the fixture corpus. The
productivity numbers here are tiny; what is checked is that they mean what they
say — especially the difference between *measured as zero* and *not measurable*.
"""

import json
from pathlib import Path as FilePath

import pytest

from murfulu.corpus import link, wordtypes
from murfulu.corpus.ganjoor import GanjoorCorpus
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import RulePack, load
from murfulu.scoring.attestation import Index
from murfulu.scoring.precompute import Precompute, input_readings, run
from murfulu.scoring.productivity import (
    EXPECTED_BAND,
    NO_ELIGIBLE_BASE,
    UNMEASURABLE_KINDS,
    RuleStatistics,
    measure,
)
from murfulu.scoring.reload import from_document, read_jsonl


@pytest.fixture(scope="module")
def pack() -> RulePack:
    """The real rule pack. It is data in the repository, not a fixture."""
    return load()


@pytest.fixture
def attestation(ganjoor_snapshot: FilePath, lexicon_snapshot: FilePath) -> Index:
    corpus = wordtypes.build(GanjoorCorpus(ganjoor_snapshot, centuries={"hafez": 8}))
    with Lexicon.open(lexicon_snapshot) as opened:
        linked = link.link(corpus, opened)
    return Index.from_link(linked, corpus_version="fixture-v1")


@pytest.fixture
def job(pack: RulePack, lexicon_snapshot: FilePath, attestation: Index) -> Precompute:
    with Lexicon.open(lexicon_snapshot) as lexicon:
        return run(
            pack,
            input_readings(lexicon),
            depth=2,
            attestation=attestation,
            corpus_version="fixture-v1",
        )


@pytest.fixture
def statistics(pack: RulePack, job: Precompute) -> RuleStatistics:
    return measure(pack, job.derivations())


# -- every rule is accounted for ---------------------------------------------


def test_every_rule_in_the_pack_gets_a_row(pack: RulePack, statistics: RuleStatistics):
    """No rule is silently left out; the ones that cannot be measured say so."""
    assert set(statistics.by_rule) == {rule.id for rule in pack.rules}
    assert len(statistics.measured) + len(statistics.unmeasured) == len(pack.rules)


def test_a_rule_that_never_fired_says_why(pack: RulePack, statistics: RuleStatistics):
    """Not a productivity of zero. An absence, with a reason."""
    for productivity in statistics.unmeasured:
        assert productivity.types_built == 0
        assert productivity.unmeasurable_reason
        assert productivity.realisation_rate is None
        assert productivity.potential_p is None


def test_stem_and_compounding_rules_name_their_own_reason(
    pack: RulePack, statistics: RuleStatistics
):
    """A stem rule is a different operation; compounding is never precomputed."""
    for rule in pack.rules:
        if rule.kind in UNMEASURABLE_KINDS:
            row = statistics.by_rule[rule.id]
            assert row.unmeasurable_reason == UNMEASURABLE_KINDS[rule.kind]


def test_a_rule_with_no_eligible_base_says_so(
    pack: RulePack, statistics: RuleStatistics
):
    unmeasured = {p.rule_id for p in statistics.unmeasured}
    reasons = {statistics.by_rule[r].unmeasurable_reason for r in unmeasured}
    assert NO_ELIGIBLE_BASE in reasons


def test_a_rule_that_fired_but_is_unattested_is_measured_at_zero(
    statistics: RuleStatistics,
):
    """Building forms nobody wrote is a result, not a missing measurement."""
    fired_unattested = [
        p for p in statistics.measured if p.types_built and not p.types_attested
    ]
    assert fired_unattested, "the fixture corpus should leave most rules unattested"
    for productivity in fired_unattested:
        assert productivity.realisation_rate == 0.0
        assert productivity.potential_p is None
        assert not productivity.unmeasurable_reason


# -- the numbers themselves --------------------------------------------------


def test_only_the_last_rule_of_a_path_is_credited(
    pack: RulePack, job: Precompute, statistics: RuleStatistics
):
    """The earlier rules made the base, and the base is its own word."""
    total_credited = sum(p.types_built for p in statistics.by_rule.values())
    reachable = sum(
        len({path.rule_ids[-1] for path in d.paths if path.rule_ids})
        for d in job.derivations()
    )
    assert total_credited == reachable


def test_a_rule_that_returns_its_own_input_is_marked_as_echoing(
    pack: RulePack, statistics: RuleStatistics
):
    """A zero-affix rule is attested by construction, not by productivity.

    *Parhiz* is the present stem written as a noun. It was already in the
    corpus before any rule ran, so a realisation rate near 1 says nothing
    about whether the rule coins words.
    """
    zero_affix = [
        r.id
        for r in pack.rules
        if r.kind == "none" and statistics.by_rule[r.id].measured
    ]
    assert zero_affix, "the pack has zero-affix rules and they should be measured"
    for rule_id in zero_affix:
        assert statistics.by_rule[rule_id].echo_share == 1.0


def test_a_real_affix_does_not_echo(statistics: RuleStatistics):
    """*goft* + *-ār* is a different string, so nothing is echoed."""
    assert statistics.by_rule["V-010"].echo_share == 0.0


def test_attested_never_exceeds_built(statistics: RuleStatistics):
    for productivity in statistics.by_rule.values():
        assert productivity.types_attested <= productivity.types_built
        assert productivity.types_confirmed <= productivity.types_attested


def test_confirmed_readings_are_counted_apart(statistics: RuleStatistics):
    """A confirmed reading and a bare spelling are not the same evidence."""
    for productivity in statistics.by_rule.values():
        assert productivity.tokens_confirmed <= productivity.tokens
        assert productivity.hapaxes_confirmed <= productivity.hapaxes


def test_p_is_hapaxes_over_tokens(statistics: RuleStatistics):
    for productivity in statistics.by_rule.values():
        if productivity.tokens:
            expected = productivity.hapaxes / productivity.tokens
            assert productivity.potential_p == pytest.approx(expected)


def test_every_number_is_tied_to_a_corpus_version(statistics: RuleStatistics):
    """A count is only true for the corpus that produced it."""
    assert statistics.corpus_version == "fixture-v1"
    for productivity in statistics.by_rule.values():
        assert productivity.corpus_version == "fixture-v1"
        assert productivity.rule_pack_version


# -- comparing against the authored strength ---------------------------------


def test_bands_come_from_the_measured_spread(statistics: RuleStatistics):
    placed = statistics.bands()
    assert set(placed.values()) <= set(EXPECTED_BAND.values())
    assert set(placed) == {p.rule_id for p in statistics.measured}


def test_a_rule_with_no_authored_strength_cannot_disagree(
    pack: RulePack, statistics: RuleStatistics
):
    """The source states a strength for very few rules. That is the finding."""
    named = {d.rule_id for d in statistics.disagreements()}
    for rule_id in named:
        assert statistics.by_rule[rule_id].authored_strength


def test_disagreements_report_both_sides(statistics: RuleStatistics):
    for disagreement in statistics.disagreements():
        assert disagreement.expected_band != disagreement.measured_band
        assert disagreement.authored_strength in EXPECTED_BAND


def test_the_summary_says_what_could_not_be_measured(statistics: RuleStatistics):
    summary = statistics.summary()
    assert "unmeasured" in summary
    assert "fixture-v1" in summary


# -- the round trip the measurement rests on ---------------------------------


def test_a_record_survives_being_written_and_read(job: Precompute):
    """If this drifts, every later pass measures something else."""
    for original in job.derivations():
        assert from_document(original.as_document()) == original


def test_a_run_read_back_from_a_file_measures_the_same(
    pack: RulePack, job: Precompute, tmp_path: FilePath
):
    written = tmp_path / "derivations.jsonl"
    with written.open("w", encoding="utf-8") as handle:
        for derivation in job.derivations():
            handle.write(json.dumps(derivation.as_document(), ensure_ascii=False))
            handle.write("\n")

    from_memory = measure(pack, job.derivations())
    from_file = measure(pack, read_jsonl(written))
    assert from_file.by_rule == from_memory.by_rule


def test_no_corpus_reads_back_as_unchecked_not_unattested(
    pack: RulePack, lexicon_snapshot: FilePath
):
    """A missing field means the question was not asked."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        unchecked = run(pack, input_readings(lexicon), depth=1)
    for derivation in unchecked.derivations():
        assert from_document(derivation.as_document()).attestation is None
