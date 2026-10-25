r"""Build the semantic artefact: base vectors and per-rule base centroids.

    MURFULU_EMBED_MODEL=~/Projects/mosaic/mana/data/models/bge-m3 \
        python tools/build_semantic_vectors.py --corpus-version v1

The question a semantic score answers is the one the pilot validated
(`tools/semantic_pilot.py`, 93% against 33% chance): **does this base resemble
the bases this rule usually takes?** *bāgh* sits among things a keeper can
keep, which is why *bāghbān* works; *raft* does not, which is why *Raftbān*
was never written.

Two things are computed and stored, per corpus version:

**A vector per base** — every verb stem in the lexicon, and every base of an
attested single-step pair. A base's vector is the mean of BGE-m3 embeddings of
up to six corpus lines containing it: the word as the poets used it, not as a
dictionary lists it.

**A centroid per rule** — the mean of its attested bases' vectors, for rules
with at least ten attested pairs. 59 rules clear that bar; the rest get no
centroid and therefore no score, which is the honest outcome for a rule with
nothing to learn from. Each centroid carries **how many bases it was built
from** and the **eight nearest them**, so the rules screen can show what the
centre is made of rather than only a number. Which bases belong to which rule
is known only here — the artefact's vector table is pooled across all of them.

Like the pilot, this needs torch and a local embedding model and therefore
runs **outside** the app's own environment; the app only ever reads the
artefact. Vectors are rounded to four decimals — cosine changes in the fifth
decimal are noise here and the file shrinks threefold.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

MODEL_VARIABLE = "MURFULU_EMBED_MODEL"
GANJOOR_VARIABLE = "MURFULU_GANJOOR_PATH"
ROOT = Path(__file__).resolve().parents[1]

LINES_PER_WORD = 6
MIN_LINES = 2
#: A verse line, not a prose block. One row in the source holds a whole prose
#: paragraph now and then, and a single 20,000-character "line" asks the model
#: for a 158 GiB attention buffer.
MAX_LINE_CHARS = 200
MIN_PAIRS = 10
ROUND = 4
#: How many of a rule's most typical bases the artefact carries, for the
#: rules screen. A handful shows what the centre is made of; the whole list
#: runs to hundreds.
EXAMPLES = 8


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-version", default="v1")
    parser.add_argument(
        "--derivations",
        type=Path,
        default=ROOT / "build" / "derivations-v1.jsonl",
        help="the precompute dump the pairs are read from",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="defaults to data/semantic-<version>.json",
    )
    return parser.parse_args(argv)


# The same folding the corpus counter uses, kept standalone so this tool can
# run in the torch environment where the package is not installed.
_WORD = re.compile(r"[ء-يٱ-ۓ‌]+")
_MARKS = re.compile(r"[ً-ْٰـ]")
_FOLD = str.maketrans({"ي": "ی", "ك": "ک", "ة": "ه", "أ": "ا", "إ": "ا", "ؤ": "و"})


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return _MARKS.sub("", text).translate(_FOLD)


def gather_lines(wanted: set[str], limit: int = LINES_PER_WORD) -> dict[str, list[str]]:
    """Verse lines per wanted word, in one pass over the Ganjoor source.

    **Not Elasticsearch, and the reason is a finding.** The ``documents``
    index analyses text with the stock Persian analyzer, whose stopword list
    swallows exactly the words this needs most — رفت, گفت, شد are stopwords to
    Lucene — so a phrase query for them finds *nothing* in a corpus that
    contains them millions of times. Reading the source and matching whole
    tokens is both correct and honest about what a line contains.
    """
    source = os.environ.get(GANJOOR_VARIABLE)
    if not source:
        raise SystemExit(f"set {GANJOOR_VARIABLE}")
    connection = sqlite3.connect(f"file:{Path(source).expanduser()}?mode=ro", uri=True)
    found: dict[str, list[str]] = defaultdict(list)
    open_slots = {w for w in wanted}
    for (text,) in connection.execute("SELECT text FROM verse WHERE text IS NOT NULL"):
        line = _normalise(text.strip())
        if not line or len(line) > MAX_LINE_CHARS:
            continue
        for token in set(_WORD.findall(line)):
            token = token.strip("‌")
            if token in open_slots:
                found[token].append(line)
                if len(found[token]) >= limit:
                    open_slots.discard(token)
        if not open_slots:
            break
    connection.close()
    return found


def stems() -> dict[str, str]:
    """Every verb stem in the lexicon: Persian spelling → Latin."""
    snapshot = os.environ.get("MURFULU_LEXICON_PATH")
    if not snapshot:
        raise SystemExit("set MURFULU_LEXICON_PATH")
    connection = sqlite3.connect(f"file:{snapshot}?mode=ro", uri=True)
    found: dict[str, str] = {}
    for fa, latin in connection.execute(
        "SELECT past_stem_fa, past_stem_lat FROM infinitives "
        "WHERE deleted_at IS NULL AND past_stem_fa IS NOT NULL"
    ):
        if fa and latin:
            found[fa] = latin
    for fa, latin in connection.execute(
        "SELECT present_stem_fa, present_stem_lat FROM infinitives "
        "WHERE deleted_at IS NULL AND present_stem_fa IS NOT NULL"
    ):
        if fa and latin:
            found[fa] = latin
    connection.close()
    return found


def attested_pairs(dump: Path) -> dict[str, set[tuple[str, str]]]:
    """Rule id → {(base_fa, base_latin)} over attested single-step pairs."""
    rules: dict[str, set[tuple[str, str]]] = {}
    with dump.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("attestation") not in ("reading", "spelling"):
                continue
            for path in record.get("paths", []):
                ids = path.get("rule_ids") or []
                base_fa, base_latin = path.get("base_fa"), path.get("base_form")
                if len(ids) != 1 or not base_fa or not base_latin:
                    continue
                rules.setdefault(ids[0], set()).add((base_fa, base_latin))
    return rules


def main(argv: list[str] | None = None) -> int:
    """Embed every base, centroid every rule, write the artefact."""
    arguments = _parse(argv)
    model_path = os.environ.get(MODEL_VARIABLE)
    if not model_path:
        print(f"set {MODEL_VARIABLE} to a local sentence-embedding model")
        return 1
    try:
        import numpy as np  # type: ignore[import-not-found]
        from sentence_transformers import (  # type: ignore[import-not-found]
            SentenceTransformer,
        )
    except ImportError as absent:
        print(f"this needs an environment with torch installed: {absent}")
        return 1

    rules = attested_pairs(arguments.derivations)
    big = {rule: pairs for rule, pairs in rules.items() if len(pairs) >= MIN_PAIRS}
    print(f"rules with >= {MIN_PAIRS} attested pairs: {len(big)}")

    wanted: dict[str, str] = stems()
    for pairs in big.values():
        for base_fa, base_latin in pairs:
            wanted.setdefault(base_fa, base_latin)
    print(f"bases to embed: {len(wanted)}")

    # lines first (one pass over the source), one embedding pass second
    normalised = {_normalise(fa): (fa, latin) for fa, latin in wanted.items()}
    by_word = gather_lines(set(normalised))
    gathered: list[tuple[str, str, list[str]]] = []
    for token, lines in sorted(by_word.items()):
        if len(lines) >= MIN_LINES:
            fa, latin = normalised[token]
            gathered.append((fa, latin, lines))
    print(f"bases with enough corpus lines: {len(gathered)}")

    model = SentenceTransformer(str(Path(model_path).expanduser()))
    all_lines = [line for _, _, lines in gathered for line in lines]
    print(f"embedding {len(all_lines)} lines…")
    encoded = model.encode(all_lines, batch_size=64, normalize_embeddings=True)

    by_latin: dict[str, list[float]] = {}
    fa_to_latin: dict[str, str] = {}
    at = 0
    for base_fa, base_latin, lines in gathered:
        pooled = encoded[at : at + len(lines)].mean(axis=0)
        at += len(lines)
        pooled = pooled / np.linalg.norm(pooled)
        by_latin[base_latin] = [round(float(x), ROUND) for x in pooled]
        fa_to_latin[base_fa] = base_latin

    centroids: dict[str, dict[str, object]] = {}
    for rule, pairs in sorted(big.items()):
        kept = [
            (fa, latin)
            for fa, latin in sorted(pairs)
            if latin in by_latin and fa in fa_to_latin
        ]
        if len(kept) < MIN_PAIRS:
            continue
        stacked = np.array([by_latin[latin] for _, latin in kept])
        centre = stacked.mean(axis=0)
        centre = centre / np.linalg.norm(centre)
        # The bases nearest the centre, so a screen can show what "typical of
        # this rule" actually looks like rather than only how many there were.
        # Computed here because only this run knows which bases belong to
        # which rule; the artefact holds one pooled table of vectors.
        scored = [
            (round(float(stacked[index] @ centre), ROUND), fa, latin)
            for index, (fa, latin) in enumerate(kept)
        ]
        near = [
            {"latin": latin, "fa": fa, "typicality": score}
            for score, fa, latin in sorted(scored, reverse=True)
        ]
        centroids[rule] = {
            "vector": [round(float(x), ROUND) for x in centre],
            "bases": len(kept),
            "typical_bases": near[:EXAMPLES],
        }
    print(f"rules with a centroid: {len(centroids)}")

    out = arguments.out or (ROOT / "data" / f"semantic-{arguments.corpus_version}.json")
    out.write_text(
        json.dumps(
            {
                "corpus_version": arguments.corpus_version,
                "model": Path(model_path).name,
                "dim": len(next(iter(by_latin.values()))),
                "min_pairs": MIN_PAIRS,
                "rules": centroids,
                "bases": by_latin,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
