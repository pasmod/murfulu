r"""Do vectors from our own corpus put same-affix words together? Measure it.

    MURFULU_EMBED_MODEL=~/Projects/mosaic/mana/data/models/bge-m3 \
        python tools/semantic_pilot.py --corpus-version v3

The go/no-go check before any semantic scoring (PLAN 5.6): if word vectors
averaged over this project's own poetry lines cannot put words made by the same
rule near each other, no measure built on them can work.

Method, from the affix-centroid setup in RESEARCH_SCORING.md: per attested
word, up to six corpus lines containing it, embedded and mean-pooled into one
vector. Then leave-one-out — is each word closer to its own rule's centroid
than to every other rule's?

**The first run answered go on three rules: 93% against 33% chance.** Three
rules is a small board, so this now runs over **every rule the artefact has a
centroid for**, which is the honest wider test. Chance falls to 1/57 and the
figure falls with it; what the table shows is *where* it falls.

**Two scores, and the second is not a softer version of the first.** Some of
these rules are the same operation written down more than once — V-010, V-011
and V-012 are all *-ār* on the same input, and no vector can separate them
because there is nothing there to separate. So the run reports strict
accuracy, and accuracy counting **any rule with the same affix** as right. The
gap between the two is the share of the confusion that is the rule pack's
shape rather than the vectors' failure.

Needs torch and a local embedding model; run it in an environment that has
them. Everything else — the corpus, the sisters, the artefact — is the
project's own.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from homograph_fit import MIN_LINES, embed, gather_lines

MODEL_VARIABLE = "MURFULU_EMBED_MODEL"
ROOT = Path(__file__).resolve().parents[1]

#: How many words per rule enter the board. A cap, so one broad rule does not
#: outweigh forty narrow ones — and reported, because a silent cap reads as
#: full coverage.
WORDS_PER_RULE = 40
#: Below this a rule has too few words for leaving one out to mean anything.
MIN_WORDS = 6
#: Words with fewer documents than this are one poet's rhyme, not a word.
MIN_DOCS = 2


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-version", default="v3")
    parser.add_argument("--sisters", type=Path, default=None)
    parser.add_argument("--semantic", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None, help="a markdown table")
    return parser.parse_args(argv)


def board(sisters: Path, artefact: Path) -> dict[str, list[str]]:
    """Rule → the attested words that stand for it, capped and reported.

    Only rules the artefact has a centroid for, because those are the rules
    the running score uses and this is a test of that score.
    """
    with_centroid = set(json.loads(artefact.read_text(encoding="utf-8"))["rules"])
    stored = json.loads(sisters.read_text(encoding="utf-8"))["sisters"]
    chosen: dict[str, list[str]] = {}
    for rule in sorted(with_centroid):
        rows = [
            row
            for row in stored.get(rule, [])
            if row["doc_count"] >= MIN_DOCS and not row.get("suspect")
        ]
        if len(rows) >= MIN_WORDS:
            chosen[rule] = [row["form_fa"] for row in rows[:WORDS_PER_RULE]]
    return chosen


def _affix_of(pack_path: Path) -> dict[str, str]:
    """Rule id → its affix, from the mirror of the pack the batch job reads.

    Two rules with the same affix on the same input are the same operation
    written twice; separating them is not something a vector can be asked to
    do, and the second score says how much of the confusion that accounts for.
    """
    import yaml

    found: dict[str, str] = {}
    for name in ("verb_stems.yaml", "nominals.yaml"):
        document = yaml.safe_load((pack_path / name).read_text(encoding="utf-8"))
        for rule in document.get("rules", []):
            found[rule["id"]] = rule.get("affix") or ""
    return found


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0915 - one linear pass
    """Run the pilot over every rule with a centroid and print the table."""
    arguments = _parse(argv)
    version = arguments.corpus_version
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

    sisters = arguments.sisters or (ROOT / "build" / f"sisters-{version}-all.json")
    artefact = arguments.semantic or (ROOT / "data" / f"semantic-{version}.json")
    wanted = board(sisters, artefact)
    print(f"rules on the board: {len(wanted)}")
    print(f"words per rule: at most {WORDS_PER_RULE}, at least {MIN_WORDS}")

    words = sorted({word for found in wanted.values() for word in found})
    lines = gather_lines(set(words))
    usable = {word: found for word, found in lines.items() if len(found) >= MIN_LINES}
    print(f"words with >= {MIN_LINES} corpus lines: {len(usable):,} of {len(words):,}")

    model = SentenceTransformer(str(Path(model_path).expanduser()))
    order = sorted(usable)
    matrix = embed(order, usable, model, np)
    row_of = {word: index for index, word in enumerate(order)}

    labels: list[str] = []
    rows: list[int] = []
    for rule, found in wanted.items():
        kept = [word for word in found if word in row_of]
        if len(kept) < MIN_WORDS:
            continue
        labels += [rule] * len(kept)
        rows += [row_of[word] for word in kept]
    tags = np.array(labels)
    vectors = matrix[np.array(rows)]
    rules = sorted(set(labels))
    print(f"rules that survived the line requirement: {len(rules)}")
    print(f"words on the board: {len(labels):,}")

    # One sum per rule, so leaving a word out is a subtraction.
    totals = {rule: vectors[tags == rule].sum(axis=0) for rule in rules}
    index_of = {rule: position for position, rule in enumerate(rules)}

    sims = np.zeros((len(labels), len(rules)))
    for position, rule in enumerate(rules):
        mine = tags == rule
        centre = np.tile(totals[rule], (len(labels), 1))
        centre[mine] -= vectors[mine]
        centre = centre / np.linalg.norm(centre, axis=1, keepdims=True)
        sims[:, position] = (vectors * centre).sum(axis=1)

    guessed = np.array([rules[i] for i in sims.argmax(axis=1)])
    correct = guessed == tags
    affix = _affix_of(ROOT / "rules")
    same_affix = np.array(
        [
            bool(affix.get(one)) and affix.get(one) == affix.get(other)
            for one, other in zip(tags, guessed, strict=True)
        ]
    )
    forgiven = correct | same_affix

    own = sims[np.arange(len(labels)), [index_of[t] for t in tags]]
    # Every other cell of the same matrix: the mean of what a word scores
    # against rules that did not make it.
    others_total = sims.sum() - own.sum()
    others_mean = others_total / (len(labels) * (len(rules) - 1))
    print()
    print(f"leave-one-out accuracy   {correct.mean():.1%}")
    print(f"counting the same affix  {forgiven.mean():.1%}")
    print(f"chance                   {1 / len(rules):.1%}")
    print(f"mean cosine, own rule    {own.mean():.3f}")
    print(f"mean cosine, others      {others_mean:.3f}")

    per_rule = {
        rule: (
            int(correct[tags == rule].sum()),
            int(forgiven[tags == rule].sum()),
            int((tags == rule).sum()),
        )
        for rule in rules
    }
    if arguments.report:
        _write_report(arguments.report, per_rule, affix, correct, forgiven, rules)
        print(f"wrote {arguments.report}")
    return 0


def _write_report(
    path: Path,
    per_rule: dict[str, tuple[int, int, int]],
    affix: dict[str, str],
    correct: Any,
    forgiven: Any,
    rules: list[str],
) -> None:
    """The per-rule table, best first, with the totals under it."""
    lines = [
        f"Board: {len(rules)} rules, chance {1 / len(rules):.1%}.",
        "",
        "| rule | affix | words | right | right, same affix |",
        "|---|---|---|---|---|",
    ]
    ordered = sorted(per_rule.items(), key=lambda kv: (-kv[1][1] / kv[1][2], kv[0]))
    for rule, (right, near, total) in ordered:
        lines.append(
            f"| {rule} | {affix.get(rule) or '—'} | {total} | "
            f"{right} ({right / total:.0%}) | {near} ({near / total:.0%}) |"
        )
    lines += [
        "",
        f"Overall {correct.mean():.1%} strict, {forgiven.mean():.1%} counting a "
        f"rule with the same affix as right.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
