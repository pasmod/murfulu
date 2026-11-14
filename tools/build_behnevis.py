"""Build the automatic-Behnevis model from the word bank and the vowel-marked corpus.

    python tools/build_behnevis.py v17

Reads the lexicon snapshot (``MURFULU_LEXICON_PATH``) and the corpus version's
``documents`` and ``word_types`` indices, and writes three files under data/,
none of them in git (they are derived from karbon's data, NOTICE):

``behnevis-v17.json``           the model: letter counts, the corpus's answers
                                among several readings, and how often a single
                                bank reading agrees with the text's signs
``behnevis-answered-v17.jsonl`` every place where the text's own signs leave
                                exactly one of a spelling's readings — what the
                                choice model learns from and is measured on
``behnevis-counts-v17.json``    each spelling's count in the corpus, so the
                                evaluation weighs words as text weighs them
``behnevis-marked-v17.jsonl``   every marked word of a Persian line, with its
                                neighbours and author: what the evaluation
                                hides the signs of and checks the model against

Read-only on Elasticsearch and the lexicon.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from elasticsearch.helpers import scan

from murfulu.behnevis.choice import Answered, ChoiceModel
from murfulu.behnevis.inflect import Inflector
from murfulu.behnevis.letters import LetterModel
from murfulu.behnevis.transcribe import (
    Transcriber,
    bank_from,
    key,
    load_function_readings,
)
from murfulu.corpus.inflection import Analyser, held_from
from murfulu.lexicon.store import Lexicon
from murfulu.search import harakat
from murfulu.search.indices import connect
from murfulu.search.texts import _source_line, _units, tokens

DATA = Path(__file__).resolve().parents[1] / "data"

#: A line where more than this share of the words carry signs is taken as a
#: quotation — in Ganjoor mostly Arabic, which editions vowel throughout — and
#: not learned from: its «مِن» is not the Persian *man*, and counting it made a
#: single bank reading look wrong two times in three (the first build,
#: 2026-11-14). Persian lines carry a sign on a word here and there.
MAX_SIGNED_SHARE = 0.3


def main(argv: list[str] | None = None) -> int:
    """Build and write the model for one corpus version."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("version", help="corpus version, e.g. v17")
    args = parser.parse_args(argv)
    version = args.version

    with Lexicon.open() as lexicon:
        # Every spelling a reading has: رخ is *rex*, and *rox* too.
        readings = list(lexicon.all_readings())
        pairs = [
            (r.spelling_fa, latin) for r in readings for latin in r.all_latin if latin
        ]
        snapshot = lexicon.snapshot_id
        inflector = Inflector.from_readings(readings, Analyser(held_from(lexicon)))
    bank = bank_from(pairs)
    letters = LetterModel.train(pairs)
    functions = load_function_readings()
    print(
        f"bank: {len(bank):,} spellings; letters learned from {letters.trained_on:,} "
        f"(not aligned: {letters.not_aligned})"
    )

    client = connect()
    counts: Counter[str] = Counter()
    spelled: dict[str, int] = {}
    for hit in scan(
        client,
        index=f"word_types-{version}",
        query={"query": {"exists": {"field": "total_count"}}},
        _source=["spelling_fa", "total_count"],
    ):
        source = hit["_source"]
        # Every reading of a spelling carries the spelling's count: keep it once.
        spelled[source["spelling_fa"]] = max(
            spelled.get(source["spelling_fa"], 0), source["total_count"] or 0
        )
    # Keyed by the spelling as the corpus writes it, half-spaces and all: the
    # evaluation reads each as written, so the inflection analysis sees it.
    for spelling, n in spelled.items():
        counts[spelling] += n

    answered: list[Answered] = []
    covered: dict[str, list[int]] = {}
    quoted = 0
    marked = (DATA / f"behnevis-marked-{version}.jsonl").open("w", encoding="utf-8")
    for hit in scan(
        client,
        index=f"documents-{version}",
        query={"query": {"match_all": {}}},
        _source=["units", "text_fa", "author"],
    ):
        source = hit["_source"]
        for unit in _units(source):
            if unit.get("kind") == "note":
                continue
            for line in unit.get("lines") or []:
                for piece in _source_line(line):
                    words = [
                        (t.fa, key(t.spelling)) for t in tokens(piece) if t.spelling
                    ]
                    signed = sum(harakat.has_signs(w) for w, _ in words)
                    if not signed:
                        continue
                    if signed > MAX_SIGNED_SHARE * len(words):
                        quoted += signed
                        continue
                    for i, (written, spelling) in enumerate(words):
                        if not harakat.has_signs(written):
                            continue
                        before = words[i - 1][1] if i else None
                        after = words[i + 1][1] if i + 1 < len(words) else None
                        marked.write(
                            json.dumps(
                                {
                                    "written": written,
                                    "spelling": spelling,
                                    "before": before,
                                    "after": after,
                                    "author": source.get("author") or "",
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                        function = functions.get(spelling, ())
                        candidates = list(
                            dict.fromkeys((*function, *bank.get(spelling, ())))
                        )
                        if not candidates:
                            continue
                        verdicts = [harakat.fits(written, c) for c in candidates]
                        confirmed = [
                            c for c, v in zip(candidates, verdicts, strict=True) if v
                        ]
                        tally = covered.setdefault(spelling, [0, 0])
                        if confirmed:
                            tally[0] += 1
                        elif all(v is False for v in verdicts):
                            tally[1] += 1
                        # Answered only when the signs confirm one reading and
                        # rule every other out; one they cannot judge leaves
                        # the question open.
                        others_out = all(
                            v is False
                            for c, v in zip(candidates, verdicts, strict=True)
                            if c not in confirmed
                        )
                        if len(candidates) >= 2 and len(confirmed) == 1 and others_out:
                            answered.append(
                                Answered(
                                    spelling,
                                    confirmed[0],
                                    before,
                                    after,
                                    source.get("author") or "",
                                )
                            )

    marked.close()
    hits = sum(h for h, _ in covered.values())
    misses = sum(m for _, m in covered.values())
    print(
        f"answered places: {len(answered):,}; marked words whose signs fit a "
        f"candidate: {hits:,}, fit none: {misses:,}; signed words left out as "
        f"quotations: {quoted:,}"
    )
    # How often a pattern family's one built reading fits the signs, over the
    # marked words that neither the bank nor the function list reads.
    with (DATA / f"behnevis-marked-{version}.jsonl").open(encoding="utf-8") as lines:
        fitted = inflector.measure(
            (json.loads(line) for line in lines),
            lambda spelling: bool(bank.get(spelling) or functions.get(spelling)),
        )
    print(
        "inflected, one built reading, fits the signs:",
        {k: f"{v[0]}/{v[1]}" for k, v in sorted(fitted.items())},
    )
    transcriber = Transcriber(
        bank=bank,
        letters=letters,
        choice=ChoiceModel.train(answered),
        functions=functions,
        covered={k: (v[0], v[1]) for k, v in covered.items()},
        inflected_fit=fitted,
    )
    transcriber.save(
        DATA / f"behnevis-{version}.json",
        {
            "corpus_version": version,
            "lexicon_snapshot_id": snapshot,
            "answered": len(answered),
            "marked_fit": hits,
            "marked_fit_none": misses,
            "max_signed_share": MAX_SIGNED_SHARE,
            "quoted_signed_words": quoted,
        },
    )
    with (DATA / f"behnevis-answered-{version}.jsonl").open(
        "w", encoding="utf-8"
    ) as out:
        for one in answered:
            out.write(json.dumps(asdict(one), ensure_ascii=False) + "\n")
    (DATA / f"behnevis-counts-{version}.json").write_text(
        json.dumps(dict(counts), ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"written: data/behnevis-{version}.json and its -answered, -marked and "
        f"-counts files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
