"""The linguist's word-bank groups decide what a word feeds (rules/bank_groups.yaml).

Since karbon 1.3.0 the lexicon carries the linguist's own groups, several per
word. Word formation reads them: a reading's classes are the union of its
groups' classes, a وام‌واژه builds nothing, and a snapshot from before the
bank falls back to the dictionary's categories unchanged. One open ruling,
L26 with L18, is a switch and defaults to today's behaviour.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from murfulu.engine.affix import CannotApplyError, Word, apply
from murfulu.engine.compound import fill_slot, front_classes
from murfulu.generation import bases_of
from murfulu.lexicon import bank
from murfulu.lexicon.categories import UnmappableCategoryError
from murfulu.lexicon.entries import Reading
from murfulu.rules.pack import (
    KARNAM_AS_NAM_MARK,
    karnam_counts_as_nam,
    load,
    loaded,
    widen_nam_to_karnam,
)

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules"

#: karbon 1.3.2's groups, as `bank_group` writes them (پیوند‌واژه with a ZWNJ).
KARBON_1_3_2 = {
    "نابسودکارواژه",
    "برنام",
    "نام",
    "کارنام",
    "چون‌واژه",
    "پیش‌واژه",
    "جانام",
    "پسوند",
    "وام‌واژه",
    "کاربهر",
    "صوت",
    "پیوند‌واژه",
}


def _reading(*groups: str, category: str | None = None, **more: object) -> Reading:
    return Reading(
        spelling_fa="هوش",
        spelling_normalized="هوش",
        latin="Huš",
        lexicon_categories=(category,),
        bank_groups=groups,
        **more,  # type: ignore[arg-type]
    )


def test_every_group_karbon_ships_is_listed_once() -> None:
    mapping = bank.load(RULES)
    assert set(mapping.groups) == KARBON_1_3_2


def test_the_linguists_names_are_the_labels() -> None:
    mapping = bank.load(RULES)
    assert all(group.label_fa == group.key for group in mapping.groups.values())


def test_a_reading_feeds_the_union_of_its_groups() -> None:
    mapping = bank.load(RULES)
    assert bank.word_classes_of(_reading("نام", "کارنام"), mapping) == ("nam", "karnam")
    assert bank.word_classes_of(_reading("کاربهر"), mapping) == ("karandekarbahr",)


def test_a_loanword_builds_nothing_whatever_else_it_is() -> None:
    mapping = bank.load(RULES)
    loan = _reading("نام", "وام‌واژه")
    assert bank.is_excluded(loan, mapping)
    with pytest.raises(bank.ExcludedFromWordFormationError):
        bank.word_classes_of(loan, mapping)
    # The subclass is what every caller already catches.
    assert issubclass(bank.ExcludedFromWordFormationError, UnmappableCategoryError)


def test_a_loan_verb_offers_no_stems() -> None:
    verb = Reading(
        spelling_fa="x",
        spelling_normalized="x",
        latin="xidan",
        lexicon_categories=("مصدر",),
        bank_groups=("نابسودکارواژه", "وام‌واژه"),
        past_stem_latin="xid",
        present_stem_latin="x",
    )
    assert bases_of(verb) == []


def test_a_group_that_feeds_no_rule_says_so() -> None:
    mapping = bank.load(RULES)
    for key in ("پسوند", "پیوند‌واژه", "صوت"):
        with pytest.raises(UnmappableCategoryError):
            bank.word_classes_of(_reading(key), mapping)


def test_an_unknown_group_is_refused_by_name() -> None:
    with pytest.raises(bank.UnknownBankGroupError, match="بی‌گروه"):
        bank.word_classes_of(_reading("بی‌گروه"), bank.load(RULES))


def test_a_snapshot_before_the_bank_falls_back_to_its_category() -> None:
    old = _reading(category="اسم معنی")
    assert bank.word_classes_of(old) == ("karnam",)
    assert not bank.is_excluded(old)


def _write(tmp_path: Path, groups: list[dict[str, object]]) -> Path:
    (tmp_path / "bank_groups.yaml").write_text(
        yaml.safe_dump({"groups": groups}, allow_unicode=True), encoding="utf-8"
    )
    return tmp_path


def test_the_loader_refuses_an_excluded_group_that_still_maps(tmp_path: Path) -> None:
    group = {
        "key": "وام‌واژه",
        "label_fa": "وام‌واژه",
        "word_classes": ["nam"],
        "in_word_formation": False,
        "grounding": "linguist",
    }
    with pytest.raises(bank.BankGroupError, match="out of word formation"):
        bank.load(_write(tmp_path, [group]))


def test_the_loader_refuses_an_unknown_class_and_a_repeat(tmp_path: Path) -> None:
    group = {
        "key": "نام",
        "label_fa": "نام",
        "word_classes": ["noun"],
        "grounding": "linguist",
    }
    with pytest.raises(bank.BankGroupError, match="unknown word class"):
        bank.load(_write(tmp_path, [group]))
    good = {
        "key": "نام",
        "label_fa": "نام",
        "word_classes": ["nam"],
        "grounding": "linguist",
    }
    with pytest.raises(bank.BankGroupError, match="twice"):
        bank.load(_write(tmp_path, [good, good]))


# -- the L26 switch -----------------------------------------------------------


def test_the_switch_is_off_as_shipped() -> None:
    """Today's behaviour until the linguist's corrected rules arrive."""
    assert karnam_counts_as_nam(RULES) is False
    assert bank.load(RULES).karnam_counts_as_nam is False
    assert not loaded().version.endswith(KARNAM_AS_NAM_MARK)


def test_off_a_karnam_cannot_take_a_nam_rule() -> None:
    pack = load(RULES)
    rule = pack.by_id("N-071")  # -mand, dānešmand
    with pytest.raises(CannotApplyError):
        apply(pack, rule, Word(latin="Dāneš", fa="دانش", word_class="karnam"))  # type: ignore[arg-type]


def test_on_every_nam_rule_takes_a_karnam_and_nothing_else_moves() -> None:
    pack = load(RULES)
    wide = widen_nam_to_karnam(pack)
    assert wide.version == pack.version + KARNAM_AS_NAM_MARK
    for before, after in zip(pack.rules, wide.rules, strict=True):
        if before.active and "nam" in before.input_types:
            assert "karnam" in after.input_types
        else:
            assert after.input_types == before.input_types
    rule = wide.by_id("N-071")
    built = apply(wide, rule, Word(latin="Dāneš", fa="دانش", word_class="karnam"))  # type: ignore[arg-type]
    assert built.latin.lower() == "dānešmand"
    # Widening twice marks once.
    assert widen_nam_to_karnam(wide).version == wide.version


def test_on_a_karnam_may_stand_in_front_of_a_noun_slot() -> None:
    """L18: soxanguy — سخن is a کارنام, V-078 wants a نام in front."""
    pack = load(RULES)
    rule = pack.by_id("V-078")
    front = Word(latin="Soxan", fa="سخن", word_class="karnam")
    behind = Word(latin="gu", fa="گو", word_class="karbon_do")
    assert "karnam" not in front_classes(rule)  # type: ignore[arg-type]
    with pytest.raises(CannotApplyError):
        fill_slot(rule, front, behind)  # type: ignore[arg-type]
    wide = widen_nam_to_karnam(pack).by_id("V-078")
    assert front_classes(wide) == ("nam", "karnam")  # type: ignore[arg-type]
    assert fill_slot(wide, front, behind).latin.lower().startswith("soxangu")  # type: ignore[arg-type]


def test_the_file_turns_the_switch(tmp_path: Path) -> None:
    for name in ("verb_stems", "nominals", "glides", "stem_rules"):
        (tmp_path / f"{name}.yaml").write_text(
            (RULES / f"{name}.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )
    (tmp_path / "bank_groups.yaml").write_text(
        "switches:\n  karnam_counts_as_nam: true\n", encoding="utf-8"
    )
    assert load(tmp_path).version.endswith(KARNAM_AS_NAM_MARK)


def test_on_a_karnam_fills_a_noun_template_slot() -> None:
    """N-104, نام + ā + نام (Sarāsar): its own slots say نام."""
    from murfulu.engine.compound import fill

    pack = load(RULES)
    front = Word(latin="Sar", fa="سر", word_class="karnam")
    behind = Word(latin="Pā", fa="پا", word_class="nam")
    with pytest.raises(CannotApplyError):
        fill(pack.by_id("N-104"), front, behind)  # type: ignore[arg-type]
    built = fill(widen_nam_to_karnam(pack).by_id("N-104"), front, behind)  # type: ignore[arg-type]
    assert built.latin.lower() == "sarāpā"


def test_a_loan_verb_is_no_compounding_partner(tmp_path: Path) -> None:
    import sqlite3

    from murfulu.compounding import partners_from
    from murfulu.lexicon.overrides import Overrides
    from murfulu.lexicon.store import Lexicon

    from .conftest import FIELDS, SCHEMA

    path = tmp_path / "lexicon-20261111.sqlite"
    connection = sqlite3.connect(path)
    connection.execute(SCHEMA)
    rows = [
        (1, "رفتن", "رفتن", "رفتن", "raftan", "رفت", "raft", "رو", "row",
         1.0, 0, None, None, "مصدر", 1, None),
        (2, "x", "x", "x", "xidan", "xid", "xid", "x", "x",
         1.0, 0, None, None, "مصدر", 1, None),
    ]  # fmt: skip
    connection.executemany(
        f"INSERT INTO infinitives ({FIELDS}) VALUES ({', '.join('?' * 16)})", rows
    )
    connection.execute("CREATE TABLE bank_group (word_id INTEGER, bank_group TEXT)")
    connection.executemany(
        "INSERT INTO bank_group VALUES (?, ?)",
        [(1, "نابسودکارواژه"), (2, "نابسودکارواژه"), (2, "وام‌واژه")],
    )
    connection.execute("CREATE TABLE bank_labels (key TEXT PRIMARY KEY, label_fa TEXT)")
    connection.commit()
    connection.close()
    with Lexicon.open(path, overrides=Overrides()) as lexicon:
        partners = partners_from(lexicon)
    assert [verb.past_stem.latin for verb in partners.verbs] == ["raft"]
