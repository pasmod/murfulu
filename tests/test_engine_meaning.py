"""Grouping repeated forms, and saying what a word means."""

import pytest

from murfulu.engine import (
    Word,
    apply,
    compose,
    deduplicate,
    generate,
)
from murfulu.rules.pack import load

PACK = load()
ROW = Word("row", "رو", "karbon_do")


# -- meaning -----------------------------------------------------------------


def test_the_meaning_the_build_plan_names():
    """The word namak + dān is the place salt is kept."""
    form = apply(PACK, PACK.by_id("N-048"), Word("namak", "نمک", "nam"))
    assert form.latin == "Namakdān"
    assert form.fa == "نمکدان"

    meaning = compose(PACK, form)
    assert meaning.text_fa == "جایی که نمک در آن است"
    assert meaning


@pytest.mark.parametrize("rule_id", ["N-057", "N-062", "N-068"])
def test_every_place_rule_gives_the_same_kind_of_meaning(rule_id: str):
    """Golestān, Meykade, Dānešgāh — all tagged Jā, all get the place gloss."""
    form = apply(PACK, PACK.by_id(rule_id), Word("gol", "گل", "nam"))
    assert compose(PACK, form).text_fa == "جایی که گل در آن است"


def test_a_word_with_no_written_template_gets_no_meaning():
    """Silence, not invention. 42 of 43 templates are still unwritten."""
    form = apply(PACK, PACK.by_id("N-050"), Word("čaman", "چمن", "nam"))
    meaning = compose(PACK, form)
    assert meaning.text_fa is None
    assert not meaning
    assert meaning.missing_templates == ("Anbuhi",)


def test_a_rule_with_no_tag_at_all_has_nothing_to_say():
    meaning = compose(
        PACK, apply(PACK, PACK.by_id("V-010"), Word("goft", "گفت", "karbon_yek"))
    )
    assert not meaning
    assert meaning.missing_templates == ()


def test_the_meaning_talks_about_the_persian_stem():
    """The reader reads Persian, so the gloss names the Persian word."""
    form = apply(PACK, PACK.by_id("N-048"), Word("namak", "نمک", "nam"))
    assert "نمک" in compose(PACK, form).text_fa


# -- grouping ----------------------------------------------------------------


def test_a_form_reached_two_ways_appears_once_with_two_paths():
    groups = deduplicate(generate(PACK, ROW, max_depth=1).forms)
    both = next(g for g in groups if g.latin == "ravāndan")
    assert len(both.paths) == 2
    assert {p[0].rule_id for p in both.paths} == {"V-001", "V-002"}


def test_grouping_reduces_the_count_without_losing_a_path():
    forms = generate(PACK, ROW, max_depth=2).forms
    groups = deduplicate(forms)
    assert len(groups) < len(forms)
    assert sum(len(g.paths) for g in groups) == len(forms)


def test_the_shortest_path_comes_first():
    for group in deduplicate(generate(PACK, ROW, max_depth=2).forms):
        lengths = [len(p) for p in group.paths]
        assert lengths == sorted(lengths)
        assert group.depth == lengths[0]
        assert group.shortest_path == group.paths[0]


def test_case_is_not_folded():
    """Gofte the noun and gofte the adjective are two different words."""
    noun = Word("Gofte", "گفته", "nam")
    adjective = Word("gofte", "گفته", "barnam")
    groups = deduplicate(
        generate(PACK, noun, max_depth=1).forms
        + generate(PACK, adjective, max_depth=1).forms
    )
    keys = {g.key for g in groups}
    assert len({k for k in keys if k[0].lower() == k[0]}) > 0


def test_the_word_class_is_part_of_the_key():
    """The same string in two classes stays two words."""
    forms = generate(PACK, Word("row", "رو", "karbon_do"), max_depth=1).forms
    rave = [g for g in deduplicate(forms) if g.latin.lower() == "rave"]
    assert len(rave) > 1, "Rave the noun and rave the participle are different"
    assert len({g.word_class for g in rave}) == len(rave)


def test_grouping_is_stable():
    forms = generate(PACK, ROW, max_depth=2).forms
    assert [g.key for g in deduplicate(forms)] == [g.key for g in deduplicate(forms)]
