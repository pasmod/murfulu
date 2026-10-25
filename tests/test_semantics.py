"""The semantic part of the score, read from the artefact.

What matters is the boundary: *not measured* is None and never a number, the
app never embeds anything, and the score is one part beside the others.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from murfulu.scoring import semantics


@pytest.fixture
def artefact(tmp_path: Path) -> Path:
    """Two rules, three bases, three dimensions — enough for the geometry."""
    document = {
        "corpus_version": "v-test",
        "model": "fixture",
        "rules": {
            # a rule whose usual bases point along x
            "V-010": {"vector": [1.0, 0.0, 0.0], "bases": 12},
            # and one along y
            "V-041": {"vector": [0.0, 1.0, 0.0], "bases": 10},
        },
        "bases": {
            "raft": [1.0, 0.0, 0.0],
            "sard": [0.0, 1.0, 0.0],
            "miyane": [0.7071, 0.7071, 0.0],
        },
    }
    path = tmp_path / "semantic.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_a_base_scores_high_on_the_rule_it_fits(artefact: Path):
    loaded = semantics.load(artefact)
    fits = loaded.typicality("V-010", "raft")
    assert fits is not None and fits.score == pytest.approx(1.0)
    other = loaded.typicality("V-041", "raft")
    assert other is not None and other.score == pytest.approx(0.0)


def test_a_middle_base_scores_in_the_middle(artefact: Path):
    loaded = semantics.load(artefact)
    middle = loaded.typicality("V-010", "miyane")
    assert middle is not None
    assert 0.6 < middle.score < 0.8


def test_the_answer_carries_its_own_evidence(artefact: Path):
    """How many bases the centroid rests on travels with the score."""
    found = semantics.load(artefact).typicality("V-010", "raft")
    assert found is not None
    assert found.bases == 12
    assert found.rule_id == "V-010"


def test_not_measured_is_none_never_a_number(artefact: Path):
    """Every unanswerable case is None, and none may look like a low score.

    A rule with no centroid, a base with no vector, no artefact at all.
    """
    loaded = semantics.load(artefact)
    assert loaded.typicality("N-999", "raft") is None
    assert loaded.typicality("V-010", "nist") is None
    assert semantics.Semantics().typicality("V-010", "raft") is None


def test_no_artefact_configured_means_an_empty_answer(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv(semantics.PATH_VARIABLE, raising=False)
    semantics.loaded.cache_clear()
    try:
        assert len(semantics.loaded()) == 0
    finally:
        semantics.loaded.cache_clear()


def test_the_app_never_embeds():
    """The artefact is built outside; the app only reads. No torch here."""
    source = Path(semantics.__file__).read_text(encoding="utf-8")
    imports = [
        line for line in source.splitlines() if line.startswith(("import ", "from "))
    ]
    for forbidden in ("torch", "sentence_transformers", "numpy"):
        assert not any(forbidden in line for line in imports), forbidden


# -- what a rule's centre is made of, for a screen ---------------------------


def test_a_rule_centre_carries_its_size_and_its_nearest_bases():
    """A count alone says nothing a reader can check against the rule."""
    loaded = semantics.Semantics(
        rules={"V-010": ((1.0, 0.0), 402)},
        typical_bases={
            "V-010": (
                {"latin": "goft", "fa": "گفت", "typicality": 0.89},
                {"latin": "raft", "fa": "رفت", "typicality": 0.87},
            )
        },
    )
    found = loaded.centre("V-010")
    assert found is not None
    assert found.bases == 402
    assert [one["fa"] for one in found.typical] == ["گفت", "رفت"]


def test_a_rule_with_no_centroid_has_no_centre_rather_than_an_empty_one():
    """None is *not measured*. A zero would read as nothing typical."""
    assert semantics.Semantics().centre("V-010") is None


def test_the_typical_bases_are_read_from_the_artefact(tmp_path: Path):
    artefact = tmp_path / "semantic.json"
    artefact.write_text(
        json.dumps(
            {
                "corpus_version": "fixture",
                "rules": {
                    "V-010": {
                        "vector": [1.0, 0.0],
                        "bases": 3,
                        "typical_bases": [
                            {"latin": "goft", "fa": "گفت", "typicality": 0.9}
                        ],
                    }
                },
                "bases": {"goft": [1.0, 0.0]},
            }
        ),
        encoding="utf-8",
    )
    centre = semantics.load(artefact).centre("V-010")
    assert centre is not None
    assert centre.typical[0]["latin"] == "goft"
