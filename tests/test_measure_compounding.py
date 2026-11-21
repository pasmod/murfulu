"""The second productivity pass, and the merge that puts it in one file.

The compounding rules reported `types_built: 0` for as long as they existed,
with a reason that was wrong three times running — most recently "nothing
calls it yet", which stopped being true the morning `/compound` was written.
A zero beside a rule that builds 28 million forms is worse than no figure.

What matters in the merge is what it must **not** do: touch a row it did not
measure, or move a figure into a file belonging to another corpus version.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

from murfulu.lexicon.entries import Reading

TOOLS = Path(__file__).resolve().parent.parent / "tools"


def _tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "measure_compounding", TOOLS / "measure_compounding.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered before it runs: a dataclass looks its module up by name.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _file(path: Path, version: str = "v8") -> Path:
    path.write_text(
        json.dumps(
            {
                "corpus_version": version,
                "rules": [
                    {"rule_id": "N-048", "types_built": 24153, "band": "middle"},
                    {"rule_id": "V-078", "types_built": 0, "band": None},
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_only_the_rules_it_measured_are_touched(tmp_path: Path) -> None:
    tool = _tool()
    target = _file(tmp_path / "productivity.json")

    changed = tool._merge(
        target,
        {"V-078": {"types_built": 28896536, "unmeasurable_reason": ""}},
        "v8",
    )

    rows = {
        row["rule_id"]: row
        for row in json.loads(target.read_text(encoding="utf-8"))["rules"]
    }
    assert changed == 1
    assert rows["V-078"]["types_built"] == 28896536
    assert rows["V-078"]["measured"] is True
    # The affix rule is left exactly as it was, band and all.
    assert rows["N-048"]["types_built"] == 24153
    assert rows["N-048"]["band"] == "middle"


def test_a_measured_compounding_rule_gets_no_band(tmp_path: Path) -> None:
    """The bands are cut from the affixation rates; a product is not on that scale."""
    tool = _tool()
    target = _file(tmp_path / "productivity.json")

    tool._merge(target, {"V-078": {"types_built": 10, "unmeasurable_reason": ""}}, "v8")

    rows = {
        row["rule_id"]: row
        for row in json.loads(target.read_text(encoding="utf-8"))["rules"]
    }
    assert rows["V-078"]["band"] is None
    assert rows["V-078"]["measured_by"] == "tools/measure_compounding.py"


def test_a_rule_with_no_pool_is_not_marked_measured(tmp_path: Path) -> None:
    """A refusal with a reason is not a measurement of zero."""
    tool = _tool()
    target = _file(tmp_path / "productivity.json")

    tool._merge(target, {"V-078": {"unmeasurable_reason": "no pool"}}, "v8")

    rows = {
        row["rule_id"]: row
        for row in json.loads(target.read_text(encoding="utf-8"))["rules"]
    }
    assert rows["V-078"]["measured"] is False
    assert rows["V-078"]["unmeasurable_reason"] == "no pool"


def test_a_figure_never_moves_into_another_versions_file(tmp_path: Path) -> None:
    """Every one of these numbers is about one corpus and only that one."""
    tool = _tool()
    target = _file(tmp_path / "productivity.json", version="v7")

    with pytest.raises(SystemExit):
        tool._merge(target, {"V-078": {"types_built": 1}}, "v8")


# --- Per second half (`--heads`, 2026-11-21) --------------------------------


def _word(
    spelling: str,
    latin: str,
    *variants: str,
    groups: tuple[str, ...] = (),
    category: str = "اسم ذات",
    stems: tuple[str, str, str, str] | None = None,
    row: int = 0,
) -> Reading:
    past_fa, past_latin, present_fa, present_latin = stems or (None, None, None, None)
    return Reading(
        spelling_fa=spelling,
        spelling_normalized=spelling,
        latin=latin,
        latin_variants=variants,
        lexicon_categories=(category,),
        bank_groups=groups,
        past_stem_fa=past_fa,
        past_stem_latin=past_latin,
        present_stem_fa=present_fa,
        present_stem_latin=present_latin,
        source_entry_ids=(row,) if row else (),
    )


class _Bank:
    """A lexicon that is only its readings, which is all `_readings` asks of it."""

    def __init__(self, *readings: Reading) -> None:
        self.readings = readings

    def all_readings(self) -> Iterator[Reading]:
        return iter(self.readings)


NOUN = ("نام",)
COMPOUND = "صفت مرکب"

#: دل the heart and the tree; دم the breath, which lists *Dam*, and دم *dam*,
#: which is not a noun; three verbs, one of them with a one-letter stem; and
#: the compounds the dictionary holds — one spelled with an Arabic yeh, one
#: with a capital.
BANK = _Bank(
    _word("دل", "Del", groups=NOUN, row=1),
    _word("دل", "Dal", groups=NOUN, row=2),
    _word("دم", "Dom", "Dam", groups=NOUN, row=3),
    _word("دم", "dam", groups=("کاربهر",), row=4),
    _word("دخت", "Doxt", groups=NOUN, row=5),
    _word("بردن", "bordan", category="مصدر", stems=("برد", "bord", "بر", "bar")),
    _word("گرفتن", "gereftan", category="مصدر", stems=("گرفت", "gereft", "گير", "gir")),
    _word("ساختن", "sāxtan", category="مصدر", stems=("ساخت", "sāxt", "ساز", "sāz")),
    _word("ریدن", "ridan", category="مصدر", stems=("رید", "rid", "ر", "r")),
    _word("دلبر", "Delbar", category=COMPOUND),
    _word("دلگير", "delgir", category=COMPOUND),
    _word("دمساز", "damsāz", category=COMPOUND),
    _word("دختر", "doxtar"),
    # Its letters and reading are دل + ساز exactly, and the dictionary does not
    # call it a compound.
    _word("دلساز", "delsāz"),
)


def _heads(corpus: set[str]) -> dict[str, object]:
    """V-078 over :data:`BANK` and the given corpus."""
    from murfulu.rules.pack import loaded

    tool = _tool()
    row = tool._heads(loaded().by_id("V-078"), tool._readings(BANK), corpus)
    assert isinstance(row, dict)
    return row


def test_a_half_counts_only_a_dictionary_compound_under_the_joined_reading() -> None:
    """دلبر is *delbar*, a compound: it confirms بر as *bar* — once, for دل.

    The capital is a word class showing (*Delbar* is *delbar*), and the Arabic
    yeh of دلگير folds into the Persian one, as the corpus's spellings do.
    """
    row = _heads({"دلبر", "دلگیر"})

    assert row["by_behind"] == {"بر": {"bar": 1}, "گیر": {"gir": 1}}
    # دل, دم, دخت, دختر and دلساز: a front is a spelling, however many entries
    # it has.
    assert row["fronts"] == 5


def test_a_word_the_dictionary_does_not_call_a_compound_confirms_nothing() -> None:
    """دختر and دلساز have the corpus and split well: not compounds, so nothing.

    And ر is one letter, which is not counted at all (SHORTEST_HALF).
    """
    tool = _tool()
    bank = tool._readings(BANK)

    assert _heads({"دختر"})["by_behind"] == {}
    # دلساز is دل + ساز, letters and reading alike — and no compound.
    assert _heads({"دلساز"})["by_behind"] == {}
    assert bank.set_aside == {"ر"}
    assert "ر" not in bank.stems["karbon_do"]


def test_a_compound_the_corpus_lacks_confirms_nothing() -> None:
    """دلبر is in the dictionary; with no text that has it, بر gets nothing."""
    assert _heads(set())["by_behind"] == {}


def test_a_borrowed_reading_does_not_make_a_noun_s_compound() -> None:
    """دم's *Dom* lists *Dam*, which is دم *dam* — not a noun.

    Without the page's cleanup دمساز, *damsāz*, was counted as a noun's
    compound; with it, the noun دم is *dom* only.
    """
    assert _heads({"دمساز"})["by_behind"] == {}


def test_every_half_measured_is_kept_so_a_zero_is_not_unmeasured() -> None:
    """The file lists every half, so an absent count is a measured zero."""
    tool = _tool()
    bank = tool._readings(BANK)

    assert bank.stems["karbon_do"] == {"بر": {"bar"}, "گیر": {"gir"}, "ساز": {"sāz"}}
    assert _heads({"دلبر"})["behinds"] == 3


def test_a_template_rule_has_no_halves() -> None:
    """Both halves of a template come from the reader's own verb."""
    from murfulu.rules.pack import loaded

    tool = _tool()
    template = next(rule for rule in loaded().rules if rule.kind == "template")

    assert tool._heads(template, tool._readings(_Bank()), set()) is None


def test_an_index_of_another_version_is_refused() -> None:
    """`--index word_types-v22` once wrote v22's figures under the name v8."""
    tool = _tool()

    tool.same_version("v22", {"v22"})
    with pytest.raises(SystemExit, match="v8"):
        tool.same_version("v8", {"v22"})
    with pytest.raises(SystemExit):
        tool.same_version("v22", {"v21", "v22"})


def test_the_command_refuses_an_index_of_another_version_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The check has to run, not only exist: the default version is v8."""
    tool = _tool()
    monkeypatch.setattr(tool, "_corpus_from_index", lambda index: ({"دلبر"}, {"v22"}))
    out = tmp_path / "heads.json"

    with pytest.raises(SystemExit, match="v8"):
        tool.main(["--index", "word_types-v22", "--heads", str(out)])
    assert not out.exists()
