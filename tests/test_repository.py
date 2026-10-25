"""Every source file is actually in the repository.

This exists because one was not. ``.gitignore`` carried ``build/`` for the
batch job's output — the derivation dump, the affix map, the sister forms —
and a pattern with no leading slash matches at **every depth**, so it also
matched ``web/src/screens/build/``. The whole build screen, nine files and
task 7.4's entire deliverable, was never committed.

Nothing noticed, because everything that runs here runs against the working
tree. The tests passed, the container built, the screen worked. Only a fresh
clone would have failed, and by then the work would have been a week old.

So the check is: nothing under the source trees may be ignored. It skips where
git is not available rather than failing, because that is a normal state
inside a build container.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: Trees that hold source, and nothing generated. Everything in them belongs
#: in the repository.
SOURCE_TREES = ("src/murfulu", "tests", "tools", "migrations", "web/src", "web/tests")

#: What a build leaves inside a source tree and nobody commits.
GENERATED = ("__pycache__", ".pyc", ".tsbuildinfo")


def _git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _available() -> bool:
    """Whether these tests can run at all.

    **`check=False` does not cover a missing git.** It suppresses a non-zero
    exit; a binary that is not on PATH raises `FileNotFoundError` out of
    `subprocess.run` before there is an exit code to inspect. The API image
    has no git in it, so every one of these tests **errored** in CI rather than
    skipping — seven red tests for the whole of 2026-08-14 and 15, saying
    nothing about the repository and hiding whatever else went red behind them.
    """
    try:
        return _git("rev-parse", "--is-inside-work-tree").returncode == 0
    except OSError:
        # No git on PATH. Nothing here can be checked, and that is a skip.
        return False


def _source_files(tree: Path) -> list[Path]:
    return [
        path
        for path in tree.rglob("*")
        if path.is_file() and not any(mark in str(path) for mark in GENERATED)
    ]


@pytest.mark.parametrize("tree", SOURCE_TREES)
def test_no_source_file_is_ignored(tree: str) -> None:
    """A source file matching an ignore rule is invisible, not missing."""
    if not _available():
        pytest.skip("not a git work tree")
    directory = ROOT / tree
    if not directory.is_dir():
        pytest.skip(f"{tree} is not here")

    paths = [str(path.relative_to(ROOT)) for path in _source_files(directory)]
    assert paths, f"{tree} has no files at all"

    # `check-ignore` prints the paths it would ignore and exits 1 when there
    # are none, which is the answer we want.
    ignored = _git("check-ignore", "--no-index", *paths)
    assert not ignored.stdout.strip(), (
        f"these source files are ignored and will never be committed:\n{ignored.stdout}"
    )


def test_the_generated_output_is_still_ignored() -> None:
    """The rule that caused it was right about its own directory.

    Anchoring it fixed the collision; it must not have stopped working.
    """
    if not _available():
        pytest.skip("not a git work tree")
    checked = _git("check-ignore", "--no-index", "build/derivations-v1.jsonl")
    assert checked.stdout.strip(), "the batch job's output is no longer ignored"


def test_the_guard_skips_rather_than_erroring_without_git(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A container with no git must skip these, not fail them.

    The API image has none, so for two days every test in this file errored in
    CI and reported nothing about the repository — while hiding whatever else
    had gone red behind seven failures that were not about the code.
    """

    def missing(*_args: object, **_kwargs: object) -> None:
        raise FileNotFoundError(2, "No such file or directory: 'git'")

    monkeypatch.setattr(subprocess, "run", missing)
    assert _available() is False
