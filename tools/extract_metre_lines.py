"""Join Ganjoor's metre labels to a corpus version's poems, for the metre experiment.

    python tools/extract_metre_lines.py v22 --ganjoor CACHE_DIR

``CACHE_DIR`` holds Ganjoor's API answers per category (``cat/<id>.json.gz``,
each with its poems' ``excerpt`` — the first hemistich — and the metre of
each section). Ganjoor labels most of its poems with a metre; the corpus does
not carry it (``documents`` has no such field), so it is joined here.

**The join is by poem id, checked by the first hemistich.** Ganjoor's ids are
stable, but where Ganjoor later inserted a poem into a book, an older snapshot
holds the neighbouring poem's text under an id (found by Sokhan's metre
study, 2026-10-20: about 2,000 poems of 122,000). A poem is kept only when its
first hemistich here is Ganjoor's excerpt, letters compared without signs,
joiners or punctuation; and only when every section is labelled with one
metre.

Writes ``data/behnevis-metre-lines-<version>.jsonl`` (not in git: Ganjoor's
text), one poem per line: id, author, the metre label, and its verse lines
(hemistichs) as written. Prints what was kept and dropped, by poems and by
running words. Read-only on Elasticsearch and the cache.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from collections import Counter
from pathlib import Path

from elasticsearch.helpers import scan

from murfulu.corpus.wordtypes import normalise
from murfulu.search.indices import connect
from murfulu.search.texts import _source_line, _units, tokens

DATA = Path(__file__).resolve().parents[1] / "data"

#: Unit kinds read as verse, as the reading screen reads them (serve.annotate).
VERSE = {"couplet", "half"}

_LETTERS = re.compile(r"[^ء-يٱ-ۓپچژکگی]")


def letters_only(text: str) -> str:
    """A line's letters alone: what the first-hemistich check compares."""
    return _LETTERS.sub("", normalise(text).replace("آ", "ا"))


def ganjoor_metres(cache: Path) -> dict[int, tuple[str, str]]:
    """Poem id → (its one metre label, its excerpt); a poem of several left out."""
    found: dict[int, tuple[str, str]] = {}
    for path in sorted((cache / "cat").glob("*.json.gz")):
        with gzip.open(path) as raw:
            cat = json.load(raw).get("cat") or {}
        for poem in cat.get("poems") or []:
            # Every section labelled, all alike: a poem with an unlabelled
            # section is left out, as its lines cannot be told apart here.
            rhythms: set[str] = {
                str((section.get("ganjoorMetre") or {}).get("rhythm") or "")
                for section in poem.get("mainSections") or []
            }
            if len(rhythms) == 1 and "" not in rhythms:
                found[int(poem["id"])] = (rhythms.pop(), str(poem.get("excerpt") or ""))
    return found


def main(argv: list[str] | None = None) -> int:
    """Write the joined poems and print the counts."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("version", help="corpus version, e.g. v22")
    parser.add_argument(
        "--ganjoor", type=Path, required=True, help="the Ganjoor API cache directory"
    )
    args = parser.parse_args(argv)

    metres = ganjoor_metres(args.ganjoor)
    print(f"Ganjoor poems with one metre: {len(metres):,}")
    poems: Counter[str] = Counter()
    words: Counter[str] = Counter()
    all_words = 0
    out_path = DATA / f"behnevis-metre-lines-{args.version}.jsonl"
    with out_path.open("w", encoding="utf-8") as out:
        for hit in scan(
            connect(),
            index=f"documents-{args.version}",
            query={"query": {"match_all": {}}},
            _source=["document_id", "author", "units", "text_fa"],
        ):
            source = hit["_source"]
            lines = [
                piece
                for unit in _units(source)
                if unit.get("kind") in VERSE
                for line in unit.get("lines") or []
                for piece in _source_line(line)
            ]
            counted = sum(1 for piece in lines for t in tokens(piece) if t.spelling)
            everything = sum(
                1
                for unit in _units(source)
                if unit.get("kind") != "note"
                for line in unit.get("lines") or []
                for piece in _source_line(line)
                for t in tokens(piece)
                if t.spelling
            )
            all_words += everything
            poem_id = int(str(source["document_id"]).rsplit(":", 1)[-1])
            if not lines:
                state = "no verse lines"
            elif poem_id not in metres:
                state = "no metre at Ganjoor"
            elif letters_only(lines[0]) != letters_only(metres[poem_id][1]):
                state = "first hemistich differs"
            else:
                state = "kept"
                out.write(
                    json.dumps(
                        {
                            "poem": poem_id,
                            "author": source.get("author") or "",
                            "metre": metres[poem_id][0],
                            "lines": lines,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            poems[state] += 1
            words[state] += counted
    total_poems, total_words = sum(poems.values()), sum(words.values())
    print(
        f"documents: {total_poems:,}; running words: {all_words:,}, "
        f"of them in verse lines: {total_words:,}"
    )
    for state, n in poems.most_common():
        print(
            f"  {state}: {n:,} documents ({n / total_poems:.1%}), "
            f"{words[state]:,} running words ({words[state] / max(1, total_words):.1%})"
        )
    print(f"written: {out_path.relative_to(DATA.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
