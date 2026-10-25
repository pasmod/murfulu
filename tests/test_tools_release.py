"""The two batch tools must be able to build a version without serving it.

`run_ingest.py` has had `--no-release` since the beginning and
`run_precompute.py` had no equivalent, so writing a new `derivations` version
put it into service in the same breath. That is the wrong default for the one
job whose whole purpose may be to replace a version that was serving forms
nobody had checked — corpus v8 exists because v7 served 115,682 of them.

The flag is asserted here rather than left to a live cluster, because the
failure it guards against is silent: the alias moves, the write succeeded, and
nothing looks wrong.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"


def _tool(name: str) -> ModuleType:
    """Import a file from `tools/`, which is not a package."""
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("name", ["run_ingest", "run_precompute"])
def test_a_version_can_be_built_without_being_released(name: str) -> None:
    tool = _tool(name)
    assert tool._parse(["--corpus-version", "v8"]).no_release is False
    assert tool._parse(["--corpus-version", "v8", "--no-release"]).no_release is True
