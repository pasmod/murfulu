"""The committed rule pack must be what the builder produces.

**Written because it was not.** Three rulings had been edited straight into the
generated files — N-090 and N-099 retired in ``nominals.yaml``, and V-021's
Persian pattern corrected in ``verb_stems.yaml`` — so re-running
``tools/build_rule_pack.py`` silently reverted all three. Found on 2026-08-15
by running it while correcting V-052.

A generated file that carries hand edits is the same failure as a pipeline that
is reproducible in principle and not in practice: nothing fails, and the next
person to run the tool undoes a decision without being told. Every ruling now
lives in ``rules/decisions.yaml``, and this test is what keeps it there.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "rules"


def _tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "build_rule_pack", ROOT / "tools" / "build_rule_pack.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILT = _tool().build(RULES)

FILES = {
    "verb_stems": "verb_stems.yaml",
    "nominals": "nominals.yaml",
    "glides": "glides.yaml",
}


@pytest.mark.parametrize("family", sorted(FILES))
def test_the_committed_pack_is_what_the_builder_writes(family: str) -> None:
    """Rebuilding must be a no-op. If this fails, a hand edit is being lost."""
    committed = yaml.safe_load((RULES / FILES[family]).read_text(encoding="utf-8"))
    assert committed["rules"] == BUILT[family], (
        f"{FILES[family]} differs from what tools/build_rule_pack.py produces. "
        "Put the decision in rules/decisions.yaml rather than in the built file."
    )


def test_the_two_rulings_that_were_lost_survive_a_rebuild() -> None:
    """N-090 and N-099 are retired, and a rebuild keeps them retired."""
    by_id = {r["id"]: r for r in BUILT["nominals"]}
    for rule_id in ("N-090", "N-099"):
        assert by_id[rule_id]["active"] is False, rule_id
        assert by_id[rule_id]["retired_reason"], rule_id


def test_a_ruling_corrects_one_rule_and_not_the_affix_everywhere() -> None:
    """V-052 is the preposition andar-; N-038 is the step-kin ending -andar.

    Both source rows write ``-andar``. Correcting the affix table moved both,
    which is how the difference was found.
    """
    verbs = {r["id"]: r for r in BUILT["verb_stems"]}
    nouns = {r["id"]: r for r in BUILT["nominals"]}

    assert verbs["V-052"]["kind"] == "prefix"
    assert verbs["V-052"]["affix"] == "andar-"
    # The transcription is never rewritten, only the judgement about it.
    assert verbs["V-052"]["affix_source"] == "-andar"

    assert nouns["N-038"]["kind"] == "suffix"
    assert nouns["N-038"]["affix"] == "-andar"


def test_the_negation_survives_a_compounding_pattern() -> None:
    """V-021's pattern is ``{a} + o + na + {b}``; ``na`` is نا, not ن."""
    v021 = next(r for r in BUILT["verb_stems"] if r["id"] == "V-021")
    assert v021["pattern"] == "{a} + o + na + {b}"
    assert v021["pattern_fa"] == "{a}ونا{b}"
