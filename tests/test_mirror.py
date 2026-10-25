"""The karbon mirror: byte-identical, or stale. There is no third state.

PLAN 8.2's command exports the rule pack for karbon. What matters is that the
copy can be *checked* — one master and one mirror is only a real arrangement
if anybody can tell whether the mirror is current — and that nothing here
sends anything to somebody else's repository.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from murfulu.rules import mirror
from murfulu.rules.pack import loaded as loaded_pack

PACK = Path(__file__).resolve().parents[1] / "rules"


@pytest.fixture
def built() -> mirror.Mirror:
    return mirror.build(PACK, loaded_pack().version, "abc1234")


def test_it_carries_everything_the_loader_reads(built: mirror.Mirror):
    """A mirror the same code cannot load is not a mirror of the pack."""
    assert {one.name for one in built.files} == set(mirror.MIRRORED)
    for name in ("verb_stems.yaml", "nominals.yaml", "glides.yaml"):
        assert name in mirror.MIRRORED


def test_the_files_are_copied_not_transformed(built: mirror.Mirror):
    """The whole checkability of the mirror rests on this."""
    for one in built.files:
        assert one.text == (PACK / one.name).read_text(encoding="utf-8")


def test_the_manifest_says_where_it_came_from(built: mirror.Mirror):
    manifest = built.manifest()
    assert loaded_pack().version in manifest
    assert "abc1234" in manifest
    # And the sentence that stops somebody editing the copy.
    assert "master is the murfulu repository" in manifest
    for one in built.files:
        assert one.digest in manifest


def test_a_missing_pack_file_is_refused_rather_than_copied_around(tmp_path: Path):
    """Copying seven files of eight would hide a fault in the pack itself."""
    (tmp_path / "verb_stems.yaml").write_text("version: 1\nrules: []\n")
    with pytest.raises(FileNotFoundError):
        mirror.build(tmp_path, "0.1.0")


# -- is the copy current? ----------------------------------------------------


def _write(built: mirror.Mirror, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name, text in built.as_written().items():
        (destination / name).write_text(text, encoding="utf-8")


def test_a_freshly_written_mirror_reports_as_current(
    built: mirror.Mirror, tmp_path: Path
):
    _write(built, tmp_path / "mirror")
    assert mirror.compare(built, tmp_path / "mirror") == []


def test_an_empty_directory_reports_every_file_missing(
    built: mirror.Mirror, tmp_path: Path
):
    differences = mirror.compare(built, tmp_path / "nothing")
    assert len(differences) == len(mirror.MIRRORED) + 1
    assert {one.state for one in differences} == {"missing"}


def test_a_changed_file_is_reported(built: mirror.Mirror, tmp_path: Path):
    """The case the whole command exists for."""
    _write(built, tmp_path / "mirror")
    (tmp_path / "mirror" / "nominals.yaml").write_text("version: 0\nrules: []\n")
    differences = mirror.compare(built, tmp_path / "mirror")
    assert [str(one) for one in differences] == ["nominals.yaml: differs"]


def test_a_file_that_is_there_and_should_not_be_is_reported(
    built: mirror.Mirror, tmp_path: Path
):
    """Somebody added a rule file to the copy. That is drift, and it shows."""
    _write(built, tmp_path / "mirror")
    (tmp_path / "mirror" / "extra_rules.yaml").write_text("rules: []\n")
    differences = mirror.compare(built, tmp_path / "mirror")
    assert [str(one) for one in differences] == ["extra_rules.yaml: extra"]


def test_a_new_commit_alone_does_not_make_the_mirror_stale(tmp_path: Path):
    """Otherwise every commit here would report karbon's copy as out of date.

    The manifest names the commit it was generated from, which is worth
    keeping, but the *content* is what decides whether the copy is current.
    """
    version = loaded_pack().version
    first = mirror.build(PACK, version, "aaaaaaa")
    _write(first, tmp_path / "mirror")
    later = mirror.build(PACK, version, "bbbbbbb")
    assert mirror.compare(later, tmp_path / "mirror") == []


def test_a_new_rule_pack_version_does_make_it_stale(tmp_path: Path):
    first = mirror.build(PACK, "0.1.0", "aaaaaaa")
    _write(first, tmp_path / "mirror")
    later = mirror.build(PACK, "0.2.0", "aaaaaaa")
    assert [str(one) for one in mirror.compare(later, tmp_path / "mirror")] == [
        "MIRROR.md: differs"
    ]


# -- what it must not do ------------------------------------------------------


def test_nothing_here_opens_a_pull_request():
    """Sending a change to somebody else's repository is the lead's to do.

    PLAN and CLAUDE.md both say never unasked, and a command that could do it
    would eventually be run by somebody who did not read either.
    """
    for name in ("src/murfulu/rules/mirror.py", "tools/mirror_to_karbon.py"):
        source = (Path(__file__).resolve().parents[1] / name).read_text(
            encoding="utf-8"
        )
        for forbidden in ("gh pr", "pulls", "git push", "create_pull"):
            assert forbidden not in source, f"{name} contains {forbidden!r}"


def test_the_mirror_module_writes_nothing():
    """It computes and compares. The command does the writing, on purpose."""
    source = (
        Path(__file__).resolve().parents[1] / "src/murfulu/rules/mirror.py"
    ).read_text(encoding="utf-8")
    assert "write_text" not in source
    assert "mkdir" not in source
