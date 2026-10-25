"""The project's own name for each word class, as data rather than as prose.

S3: the coined terms — کارنام, کاربن دو, برنام — existed only in
`docs/FINDINGS.md`, so `/rules` served the **traditional** term and the build
screen labelled its groups اسم مصدر, in the vocabulary the project exists to
replace. What is checked here is that the table cannot drift away from the
closed set it names, and that an unconfirmed term is still shown rather than
hidden.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from murfulu.rules import word_classes
from murfulu.rules.types import WORD_CLASSES


def test_every_word_class_has_a_persian_term() -> None:
    """A class with no row here would be labelled in English on screen."""
    table = word_classes.loaded()

    assert set(table) == set(WORD_CLASSES)
    for name, entry in table.items():
        assert entry.label_fa, f"{name} has nothing to print"
        assert entry.explanation_fa, f"{name} has no explanation"


def test_the_coined_term_is_what_gets_printed() -> None:
    """کارنام, not اسم مصدر. That is the whole of S3."""
    karnam = word_classes.loaded()["karnam"]

    assert karnam.coined_fa == "کارنام"
    assert karnam.label_fa == "کارنام"
    assert karnam.traditional_fa == "اسم مصدر"
    assert karnam.label_is_traditional is False


def test_a_class_with_no_coined_term_says_it_fell_back() -> None:
    """The vocative's own name is Arabic-derived, so there is nothing to swap in.

    Printing ندایی silently would present the replaced vocabulary as though it
    were the replacement, and make the gap invisible to everyone.
    """
    vocative = word_classes.loaded()["nedayi"]

    assert vocative.coined_fa is None
    assert vocative.label_fa == vocative.traditional_fa
    assert vocative.label_is_traditional is True


def test_four_terms_are_marked_unconfirmed() -> None:
    """Read off the source's Behnevis by us, not stated by the linguist.

    They are shown, not withheld — the project's standing rule is to build what
    it believes is right and mark it, never to wait. L17 asks for the ruling.
    """
    table = word_classes.loaded()
    unconfirmed = sorted(name for name, one in table.items() if not one.confirmed)

    assert unconfirmed == ["janam", "jonvaze", "nedayi", "pisvaze"]
    for name in unconfirmed:
        assert table[name].label_fa, f"{name} is unconfirmed but must still show"


def test_the_id_and_the_source_behnevis_may_disagree() -> None:
    """`jonvaze` against the source's `Čonvāže`, and the id is the one that stays.

    It comes from the Latin convention this project used before the one
    DECISIONS settled on. An id is permanent — it is written into the rule
    files, the engine and every stored derivation — so the Behnevis is carried
    beside it rather than the id being quietly corrected.
    """
    adverb = word_classes.loaded()["jonvaze"]

    assert adverb.behnevis == "Čonvāže"
    assert adverb.name == "jonvaze"


def test_a_table_naming_a_class_that_does_not_exist_is_refused(tmp_path: Path) -> None:
    """A term for a class nothing can produce is a term nothing can ever show."""
    rows = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "rules" / "word_classes.yaml").read_text(
            encoding="utf-8"
        )
    )
    rows["classes"].append(
        {
            "name": "notaclass",
            "coined_fa": "چیزی",
            "explanation_fa": "چیزی",
            "confirmed": False,
        }
    )
    (tmp_path / "word_classes.yaml").write_text(
        yaml.safe_dump(rows, allow_unicode=True), encoding="utf-8"
    )

    with pytest.raises(
        word_classes.WordClassError, match="not a word class: notaclass"
    ):
        word_classes.load(tmp_path)


def test_a_class_left_out_of_the_table_is_refused(tmp_path: Path) -> None:
    """Silently missing means an English machine id on a Persian screen."""
    rows = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "rules" / "word_classes.yaml").read_text(
            encoding="utf-8"
        )
    )
    rows["classes"] = [one for one in rows["classes"] if one["name"] != "barnam"]
    (tmp_path / "word_classes.yaml").write_text(
        yaml.safe_dump(rows, allow_unicode=True), encoding="utf-8"
    )

    with pytest.raises(
        word_classes.WordClassError, match="no Persian term for: barnam"
    ):
        word_classes.load(tmp_path)
