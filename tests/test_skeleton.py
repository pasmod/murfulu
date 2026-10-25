"""Every module in the package layout exists, imports and says what it owns."""

import importlib

import pytest

MODULES = [
    "murfulu",
    "murfulu.rules",
    "murfulu.engine",
    "murfulu.scoring",
    "murfulu.lexicon",
    "murfulu.search",
    "murfulu.corpus",
    "murfulu.api",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name: str) -> None:
    importlib.import_module(name)


@pytest.mark.parametrize("name", MODULES)
def test_module_has_a_docstring(name: str) -> None:
    doc = importlib.import_module(name).__doc__
    assert doc is not None and doc.strip(), f"{name} has no docstring"
