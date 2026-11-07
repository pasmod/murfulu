"""The code example in the README runs, and prints what the README says.

The README's *Try it* block is the first code a visitor runs. It promises 38
words from the two stems of *angixtan* without the lexicon or the corpus, and
the table above it lists four of them. A rule-pack change that moved either
would leave the README wrong without anything failing, so this runs the block
exactly as written.
"""

from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"

_PYTHON_BLOCK = re.compile(r"```python\n(?P<code>.*?)```", re.DOTALL)


def _example() -> str:
    found = _PYTHON_BLOCK.search(README.read_text(encoding="utf-8"))
    assert found, "the README has no python example any more"
    return found["code"]


def test_the_readme_example_prints_the_count_it_promises() -> None:
    code = _example()
    promised = re.search(r"print\(len\(words\)\)\s*#\s*(?P<count>\d+)", code)
    assert promised, "the example no longer states the count it prints"

    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        exec(compile(code, str(README), "exec"), {})  # noqa: S102 - our own README

    lines = printed.getvalue().splitlines()
    assert lines[0] == promised["count"]
    assert len(lines) == 6


def test_the_words_in_the_readme_table_are_among_them() -> None:
    from murfulu.engine import Word, apply_all, deduplicate
    from murfulu.rules.pack import load

    pack = load()
    stems = [
        Word(latin="angiz", fa="انگیز", word_class="karbon_do"),
        Word(latin="angixt", fa="انگیخت", word_class="karbon_yek"),
    ]
    built = {
        (word.latin, word.shortest_path[-1].rule_id)
        for word in deduplicate([f for stem in stems for f in apply_all(pack, stem)])
    }
    for row in [
        ("angizande", "V-022"),
        ("Angizeš", "V-033"),
        ("Angize", "V-034"),
        ("angixte", "V-008"),
    ]:
        assert row in built, f"{row} is in the README table but not built"
