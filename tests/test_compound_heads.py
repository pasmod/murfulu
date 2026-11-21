"""How well a compound is built: the compounds' own scale, and what it refuses.

The value is per second half (FINDINGS 2026-11-21, *a build value for
compounds*): a noun's page is built by three rules, so a value per rule would
be one number for every row. What is asserted here is the scale the project
lead chose — the best half measured is 100, one compound is 16, none is 0 —
and that *not measured* never comes out as a zero.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from murfulu.scoring import compound_heads
from murfulu.scoring.compound_heads import Heads, read

#: «‑دار» made 73 compounds out of 21,688 nouns, the most of any half; «‑بر»
#: 6 as *bar* and none as *ber*; V-080 has a smaller pool; V-016 takes past
#: stems and made 3 with «‑بست».
FIGURES = {
    "corpus_version": "v22",
    "halves": {
        "karbon_do": {"دار": ["dār"], "بر": ["bar", "ber"], "کار": ["kār"]},
        "karbon_yek": {"بست": ["bast"], "زاد": ["zād"]},
    },
    "set_aside": {"halves": ["ر", "م"], "reason": "one letter"},
    "rules": {
        "V-078": {
            "fronts": 21688,
            "stem_classes": ["karbon_do"],
            "by_behind": {"دار": {"dār": 73}, "بر": {"bar": 6}},
        },
        "V-080": {
            "fronts": 15802,
            "stem_classes": ["karbon_do"],
            "by_behind": {"کار": {"kār": 17}},
        },
        "V-016": {
            "fronts": 21688,
            "stem_classes": ["karbon_yek"],
            "by_behind": {"بست": {"bast": 3}},
        },
    },
}


def heads() -> Heads:
    return read(FIGURES)


def test_the_best_half_is_a_hundred_and_one_compound_is_sixteen() -> None:
    measured = heads()

    best = measured.value("V-078", "دار", "dār")
    assert best is not None and best.build == 100
    assert (best.confirmed, best.fronts) == (73, 21688)
    assert measured.points(1 / 21688) == 16
    assert measured.points(0) == 0


def test_a_half_measured_with_nothing_is_zero() -> None:
    """*ber* was measured and made no compound: a zero, not an absence."""
    value = heads().value("V-078", "بر", "ber")

    assert value is not None and value.build == 0 and value.confirmed == 0


def test_one_scale_for_every_rule() -> None:
    """V-016's best half has 3 compounds: on a scale of its own it would be 100."""
    value = heads().value("V-016", "بست", "bast")

    assert value is not None
    assert value.build == heads().points(3 / 21688) == 32


def test_a_smaller_pool_is_counted_as_a_rate() -> None:
    """V-080 joins 15,802 fronts, so 17 of them is a higher rate than 17 of 21,688."""
    measured = heads()
    value = measured.value("V-080", "کار", "kār")

    assert value is not None
    assert value.build == measured.points(17 / 15802)
    assert value.build > measured.points(17 / 21688)


def test_the_half_is_matched_by_its_reading_as_well() -> None:
    """کش is *keš* and *koš*; بر is *bar* and *ber*: each has its own count."""
    measured = heads()
    bar = measured.value("V-078", "بر", "bar")
    ber = measured.value("V-078", "بر", "ber")

    assert bar is not None and ber is not None
    assert bar.confirmed == 6 and ber.confirmed == 0


@pytest.mark.parametrize(
    ("rule_id", "fa", "latin", "why"),
    [
        ("V-078", "ر", "r", "a one-letter half is set aside"),
        ("V-078", "دوز", "duz", "a stem the measurement never saw"),
        ("V-078", "بر", "bor", "a reading of the half the measurement never saw"),
        ("V-018", "دار", "dār", "a template rule has no halves"),
        ("V-078", "بست", "bast", "a past stem, which V-078 does not take"),
    ],
)
def test_not_measured_is_no_value_never_zero(
    rule_id: str, fa: str, latin: str, why: str
) -> None:
    assert heads().value(rule_id, fa, latin) is None, why


def test_no_file_means_no_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(compound_heads.PATH_VARIABLE, raising=False)
    compound_heads.loaded.cache_clear()
    try:
        assert compound_heads.loaded().value("V-078", "دار", "dār") is None
    finally:
        compound_heads.loaded.cache_clear()


def test_the_configured_file_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    figures = tmp_path / "compound_heads-v22.json"
    figures.write_text(json.dumps(FIGURES, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv(compound_heads.PATH_VARIABLE, str(figures))
    compound_heads.loaded.cache_clear()
    try:
        value = compound_heads.loaded().value("V-078", "دار", "dār")
        assert value is not None and value.build == 100
    finally:
        compound_heads.loaded.cache_clear()
