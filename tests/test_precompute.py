"""The derivation precompute: generate everything, merge it, ask the corpus.

Everything here runs against the fixture lexicon and the fixture corpus. The
real snapshot is 28 MB and the real corpus is 325 MB, and neither belongs in a
test.
"""

from pathlib import Path

import pytest

from murfulu.corpus import link, wordtypes
from murfulu.corpus.ganjoor import GanjoorCorpus
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import RulePack, load
from murfulu.scoring.attestation import Index, Level
from murfulu.scoring.precompute import (
    REVIEWED_CATEGORIES,
    Precompute,
    input_readings,
    run,
)


@pytest.fixture(scope="module")
def pack() -> RulePack:
    """The real rule pack. It is data in the repository, not a fixture."""
    return load()


@pytest.fixture
def lexicon(lexicon_snapshot: Path):
    """The fixture snapshot, opened read-only."""
    with Lexicon.open(lexicon_snapshot) as opened:
        yield opened


@pytest.fixture
def attestation(ganjoor_snapshot: Path, lexicon_snapshot: Path) -> Index:
    """Corpus evidence built from the fixture poems."""
    corpus = wordtypes.build(GanjoorCorpus(ganjoor_snapshot, centuries={"hafez": 8}))
    with Lexicon.open(lexicon_snapshot) as opened:
        linked = link.link(corpus, opened)
    return Index.from_link(linked, corpus_version="fixture-v1")


# -- the input pool ----------------------------------------------------------


def test_the_pool_is_the_fully_reviewed_categories(lexicon: Lexicon):
    """Verbs, adjectives and abstract nouns. Not concrete nouns or compounds."""
    categories = {r.lexicon_category for r in input_readings(lexicon)}
    assert categories <= set(REVIEWED_CATEGORIES)
    # The fixture holds مرد (اسم ذات) and آبرو (اسم مرکب); neither is in scope.
    assert "اسم ذات" not in categories
    assert "اسم مرکب" not in categories


def test_the_pool_can_be_widened_by_asking(lexicon: Lexicon):
    """Extending to all nominals is a decision, so it is a parameter."""
    widened = list(input_readings(lexicon, ["مصدر", "اسم ذات"]))
    assert {r.lexicon_category for r in widened} == {"مصدر", "اسم ذات"}


# -- what a run produces -----------------------------------------------------


def test_a_verb_produces_its_family(pack: RulePack, lexicon: Lexicon):
    job = run(pack, input_readings(lexicon), depth=2)
    forms = {d.form_latin for d in job.derivations()}
    assert {"Raftār", "Raveš", "ravande", "Ravandegi"} <= forms


def test_every_word_appears_once(pack: RulePack, lexicon: Lexicon):
    """The whole point of merging: one document per form and output class."""
    ids = [d.id for d in job_ids(pack, lexicon)]
    assert len(ids) == len(set(ids))


def job_ids(pack: RulePack, lexicon: Lexicon):
    """The derivations of one run, for tests that only need the records."""
    return run(pack, input_readings(lexicon), depth=2).derivations()


def test_two_verbs_reaching_one_form_keep_both_derivations(
    pack: RulePack, lexicon: Lexicon
):
    """A merged record must not lose the path the second entry contributed."""
    job = run(pack, input_readings(lexicon), depth=2)
    merged = [d for d in job.derivations() if len(d.paths) > 1]
    assert merged, "no form was reachable more than one way"
    for derivation in merged:
        chains = [path.rule_ids for path in derivation.paths]
        assert len(chains) == len(set(chains))


def test_one_rule_reaching_one_form_from_two_entries_keeps_both(
    pack: RulePack, lexicon: Lexicon
):
    """Keying the merge on the rule chain alone loses the second entry.

    Measured on the real snapshot: 95,021 forms are reached by the same rule
    from two different lexicon entries. Dropping one leaves a record that
    still claims a single source.
    """
    from murfulu.scoring.precompute import Precompute

    job = Precompute(pack, depth=1)
    readings = [r for r in input_readings(lexicon) if r.lexicon_category == "مصدر"]
    for reading in readings:
        job.add(reading)
        # The same reading twice is the sharpest case: identical chains,
        # identical source, and it must still collapse to one path.
        job.add(reading)
    job.finish()
    for derivation in job.derivations():
        assert len(derivation.paths) == len(set(derivation.paths))


def test_two_spellings_with_one_reading_both_survive(pack: RulePack):
    """The id is the Latin form, so a second Persian spelling must be kept."""
    from murfulu.lexicon.entries import Reading
    from murfulu.scoring.precompute import Precompute

    # خواستن and خاستن: two words, one Behnevis reading.
    shared = [
        Reading(
            spelling_fa=spelling,
            spelling_normalized=spelling,
            latin="xāstan",
            lexicon_categories=("مصدر",),
            past_stem_fa=stem_fa,
            past_stem_latin="xāst",
            present_stem_fa=present_fa,
            present_stem_latin="xāh",
        )
        for spelling, stem_fa, present_fa in (
            ("خواستن", "خواست", "خواه"),
            ("خاستن", "خاست", "خاه"),
        )
    ]
    job = Precompute(pack, depth=1)
    for reading in shared:
        job.add(reading)
    job.finish()

    with_variants = [d for d in job.derivations() if d.form_fa_variants]
    assert with_variants, "the second spelling was thrown away"
    assert job.report.forms_with_two_spellings == len(with_variants)
    for derivation in with_variants:
        assert derivation.form_fa not in derivation.form_fa_variants


def test_paths_are_shortest_first(pack: RulePack, lexicon: Lexicon):
    for derivation in job_ids(pack, lexicon):
        depths = [path.depth for path in derivation.paths]
        assert depths == sorted(depths)
        assert derivation.depth == depths[0]


def test_a_path_says_which_lexicon_entry_it_started_at(
    pack: RulePack, lexicon: Lexicon
):
    """A record merged across entries is useless if it cannot say from where."""
    by_form = {d.form_latin: d for d in job_ids(pack, lexicon)}
    assert by_form["Raftār"].paths[0].source_spelling_fa == "رفتن"
    assert by_form["Goftār"].paths[0].source_spelling_fa == "گفتن"


def test_the_first_step_starts_at_the_lexicon_entrys_own_class(
    pack: RulePack, lexicon: Lexicon
):
    by_form = {d.form_latin: d for d in job_ids(pack, lexicon)}
    assert by_form["Raftār"].paths[0].base_type == "karbon_yek"
    assert by_form["Raveš"].paths[0].base_type == "karbon_do"


def test_a_second_step_starts_at_what_the_first_rule_produced(
    pack: RulePack, lexicon: Lexicon
):
    """*Ravandegi* is built on *ravande*, which V-022 says is a participle."""
    by_form = {d.form_latin: d for d in job_ids(pack, lexicon)}
    two_step = [p for p in by_form["Ravandegi"].paths if p.depth == 2][0]
    made_by = pack.by_id(two_step.rule_ids[0])
    assert two_step.base_type == made_by.output_types[0]


def test_the_verbs_stems_travel_with_every_form(pack: RulePack, lexicon: Lexicon):
    by_form = {d.form_latin: d for d in job_ids(pack, lexicon)}
    assert by_form["Raftār"].stem_1 == "raft"
    assert by_form["Raftār"].stem_2 == "row"


def test_each_record_says_which_snapshot_and_pack_made_it(
    pack: RulePack, lexicon: Lexicon
):
    for derivation in job_ids(pack, lexicon):
        assert derivation.lexicon_snapshot_id == lexicon.snapshot_id
        assert derivation.rule_pack_version == pack.version


# -- attestation -------------------------------------------------------------


def test_attestation_is_attached_to_every_form(
    pack: RulePack, lexicon: Lexicon, attestation: Index
):
    job = run(pack, input_readings(lexicon), depth=1, attestation=attestation)
    levels = {d.attestation.level for d in job.derivations() if d.attestation}
    assert levels
    assert Level.NONE in levels, "the fixture corpus cannot hold every built word"
    assert job.report.by_attestation[Level.NONE.value] > 0


def test_without_a_corpus_nothing_is_claimed(pack: RulePack, lexicon: Lexicon):
    """No corpus must mean *unchecked*, never *not attested*."""
    job = run(pack, input_readings(lexicon), depth=1)
    assert all(d.attestation is None for d in job.derivations())
    assert not job.report.by_attestation


# -- the report --------------------------------------------------------------


def test_the_report_counts_what_ran(pack: RulePack, lexicon: Lexicon):
    job = run(pack, input_readings(lexicon), depth=2)
    report = job.report
    assert report.entries == len(list(input_readings(lexicon)))
    assert report.forms_built >= report.forms_unique > 0
    assert sum(report.by_depth.values()) == report.forms_unique
    assert report.seconds >= 0


def test_the_report_names_the_rules_that_never_fired(pack: RulePack, lexicon: Lexicon):
    """A rule with no output has no productivity to measure — PLAN 5.3."""
    job = run(pack, input_readings(lexicon), depth=1)
    silent = job.report.rules_that_never_fired(pack)
    fired = set(job.report.rule_uses)
    assert fired
    assert not (fired & set(silent))


def test_the_summary_states_run_time_and_output_size(pack: RulePack, lexicon: Lexicon):
    """The two figures PLAN task 5.2 asks the first run to report."""
    job = run(pack, input_readings(lexicon), depth=1)
    assert "run time" in job.report.summary()
    assert "output size" in job.report.summary()
    job.report.output_bytes = 2_500_000
    assert "2.5 MB" in job.report.summary()


# -- the stored document -----------------------------------------------------


def test_the_document_only_uses_fields_the_mapping_declares(
    pack: RulePack, lexicon: Lexicon, attestation: Index
):
    """``dynamic: strict`` means an undeclared field fails the write."""
    from murfulu.search.mappings import DERIVATIONS

    declared = set(DERIVATIONS["properties"])
    job = run(pack, input_readings(lexicon), depth=2, attestation=attestation)
    for derivation in job.derivations():
        assert set(derivation.as_document()) <= declared


def test_the_document_id_is_the_dedup_key(pack: RulePack, lexicon: Lexicon):
    for derivation in job_ids(pack, lexicon):
        document = derivation.as_document()
        assert document["id"] == f"{derivation.form_latin}:{derivation.output_type}"


def test_a_stored_record_can_be_read_back_as_json(pack: RulePack, lexicon: Lexicon):
    import json

    for derivation in job_ids(pack, lexicon):
        assert json.loads(json.dumps(derivation.as_document(), ensure_ascii=False))


# -- running the pass by hand ------------------------------------------------


def test_records_can_be_added_one_at_a_time(pack: RulePack, lexicon: Lexicon):
    """The batch job streams entries; it never holds the whole pool."""
    job = Precompute(pack, depth=1)
    for reading in input_readings(lexicon):
        job.add(reading)
    job.finish(seconds=1.5)
    assert job.report.seconds == 1.5
    assert job.report.forms_unique == len(list(job.derivations()))


def test_derivations_can_be_iterated_twice(pack: RulePack, lexicon: Lexicon):
    """A writer that reads the run twice must see the same records."""
    job = run(pack, input_readings(lexicon), depth=1)
    first = [d.id for d in job.derivations()]
    assert first == [d.id for d in job.derivations()]


# -- the two parts the index now carries -------------------------------------


def test_the_ground_under_each_chain_is_written_into_the_record(
    pack: RulePack, lexicon: Lexicon, attestation: Index
):
    """Search and the rules screen need it, not only /generate."""
    job = run(pack, input_readings(lexicon), depth=2, attestation=attestation)
    answers = {d.base_attested for d in job.derivations()}
    assert answers <= {True, False}, "depth 2 is always readable"
    assert True in answers and False in answers

    report = job.report
    assert report.grounded + report.ungrounded + report.grounding_unknown == (
        report.forms_unique
    )


def test_without_a_corpus_the_ground_is_not_established(
    pack: RulePack, lexicon: Lexicon
):
    """None is *not asked*. A stored False would claim an answer we never got."""
    job = run(pack, input_readings(lexicon), depth=2)
    assert all(d.base_attested is None for d in job.derivations())
    assert job.report.grounded == 0


def test_a_grounded_record_does_not_store_a_null(
    pack: RulePack, lexicon: Lexicon, attestation: Index
):
    job = run(pack, input_readings(lexicon), depth=2, attestation=attestation)
    for derivation in job.derivations():
        document = derivation.as_document()
        assert document["base_attested"] is derivation.base_attested

    without = run(pack, input_readings(lexicon), depth=2)
    assert "base_attested" not in next(without.derivations()).as_document()


def test_the_semantic_part_is_written_when_there_is_an_artefact(
    pack: RulePack, lexicon: Lexicon
):
    from murfulu.scoring.semantics import Semantics

    # A one-step derivation, because there the stored path's own base *is*
    # the first step's base and the test needs no private state to find it.
    plain = run(pack, input_readings(lexicon), depth=2)
    first = next(d for d in plain.derivations() if d.depth == 1)
    rule_id = first.paths[0].rule_ids[0]
    base = first.paths[0].base_latin

    artefact = Semantics(rules={rule_id: ((1.0, 0.0), 42)}, bases={base: (1.0, 0.0)})
    scored = run(pack, input_readings(lexicon), depth=2, semantics=artefact)
    found = next(d for d in scored.derivations() if d.form_latin == first.form_latin)
    assert found.semantic_typicality == 1.0
    assert found.semantic_bases == 42
    assert scored.report.with_typicality >= 1


def test_a_rule_with_no_centroid_gets_no_score_rather_than_a_low_one(
    pack: RulePack, lexicon: Lexicon
):
    from murfulu.scoring.semantics import Semantics

    scored = run(pack, input_readings(lexicon), depth=2, semantics=Semantics())
    for derivation in scored.derivations():
        assert derivation.semantic_typicality is None
        assert "semantic_typicality" not in derivation.as_document()


def test_both_parts_survive_the_round_trip(
    pack: RulePack, lexicon: Lexicon, attestation: Index
):
    from murfulu.scoring.reload import from_document
    from murfulu.scoring.semantics import Semantics

    artefact = Semantics(rules={"V-010": ((1.0, 0.0), 7)}, bases={"goft": (1.0, 0.0)})
    job = run(
        pack,
        input_readings(lexicon),
        depth=2,
        attestation=attestation,
        semantics=artefact,
    )
    for derivation in job.derivations():
        assert from_document(derivation.as_document()) == derivation


def test_built_by_names_every_rule_that_builds_the_word() -> None:
    """S19: it used to name the shortest derivation and nothing else.

    دندانایی is reached five ways and the field carried the first pair, so a
    filter on it missed four rules that genuinely built the word — 342,511 of
    1,704,021 records in derivations-v7, 20.1% of them.

    `paths` still carries the ordered derivations; this field is a set of
    rules and its order is not a chain.
    """
    from murfulu.scoring.records import Derivation, Path

    reached_two_ways = Derivation(
        form_latin="Dandānāyi",
        form_fa="دندانایی",
        output_type="karnam",
        paths=(
            Path("dandānā", "دندانا", "nam", ("V-024", "V-025")),
            Path("dandānā", "دندانا", "nam", ("N-023", "N-095")),
        ),
    )

    document = reached_two_ways.as_document()

    assert document["built_by"] == ["V-024", "V-025", "N-023", "N-095"]
    # The old name is gone rather than kept beside it. A field called
    # `rule_chain` whose contents are deliberately not a chain is the trap
    # S19 was about, and leaving it as an alias would keep the trap open.
    assert "rule_chain" not in document
    # The shortest chain is still what depth and base_form are about.
    assert document["depth"] == 2
    assert document["base_form"] == "dandānā"


def test_built_by_does_not_repeat_a_rule_two_paths_share() -> None:
    """A set, kept in first-seen order so the field is stable between runs."""
    from murfulu.scoring.records import Derivation, Path

    shared = Derivation(
        form_latin="X",
        form_fa="ایکس",
        output_type="nam",
        paths=(
            Path("a", "ا", "nam", ("N-001", "N-002")),
            Path("a", "ا", "nam", ("N-001", "N-003")),
        ),
    )

    assert shared.as_document()["built_by"] == ["N-001", "N-002", "N-003"]


def test_affixes_and_glides_come_from_every_path_too() -> None:
    """The same defect `built_by` had, fixed with it.

    A word reached two ways named one route's affixes and not the other's,
    and a glide needed on one route only was invisible.
    """
    from murfulu.scoring.records import Derivation, Path

    two_routes = Derivation(
        form_latin="X",
        form_fa="ایکس",
        output_type="nam",
        paths=(
            Path("a", "ا", "nam", ("N-001",), ("-ā",), ()),
            Path("b", "ب", "nam", ("N-002",), ("-i",), ("G-03",)),
        ),
    )

    document = two_routes.as_document()

    assert document["affixes"] == ["-ā", "-i"]
    assert document["glide_rules"] == ["G-03"]
