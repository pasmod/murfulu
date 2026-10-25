r"""Measure which of a rule's claimed outputs are really another word.

    MURFULU_EMBED_MODEL=~/Projects/mosaic/mana/data/models/bge-m3 \
        python tools/flag_homograph_claims.py --corpus-version v2 \
            --sisters build/sisters-v2-all.json

The affix pass says *rule R formed corpus word W*. Sometimes it is wrong in a
way no letter-level check can catch: **شاهدان is the plural of شاهد, not
شاه + -dān**. The two derivations spell the same word, both are attested, and
only the meaning tells them apart.

A word's vector is the mean of BGE-m3 embeddings of up to six corpus lines
containing it — the construction the pilot validated at 93% against 33%
chance. What is compared to what is where the work is.

**Two checks, because one of them has a blind spot that was measured, not
assumed.**

*rule fit*  the word against the centroid of the words its rule claims, that
            word left out. **Blind where it is needed most:** with 14 claims of
            which most are plural-ان homographs, the homographs *are* the
            centroid, and شاهدان sits comfortably inside it.
*base fit*  the word against the word it was built from. Per claim, so no
            amount of contamination in the rule can hide it: نمکدان is about
            salt and نمک is salt; شاهدان is about witnesses and شاه is a king.

A claim either check doubts is doubted. They are reported apart, because they
fail in different places and a future corpus will move them differently.

**Neither check uses an absolute cosine, and the first attempt shows why.**
Claims sit at 0.811 against their own rule and 0.780 against every other, with
a standard deviation of 0.05 apiece — two distributions that overlap almost
entirely. Any absolute cut flags nearly everything or nothing.

So both statistics are **ranks**: what share of the candidates a claim has
nothing to do with fit the word better. Under the null — the claim is
unrelated — a rank among unrelated candidates is uniform, so the null density
is exactly 1 and needs no tuning. That is checked rather than believed: the
rule-fit null is also constructed from the data, and comes out at a median of
0.495.

Output is ``build/suspect-claims-<version>.json``. ``run_precompute.py
--suspect-claims`` reads it: doubted claims are **ranked last, never dropped**
in the sister lists, and held out of the affix map's assertions.

Like the other embedding tools this needs torch and a local model, so it runs
outside the app's own environment. The app only reads what it writes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from homograph_fit import (
    MIN_LINES,
    _describe,
    _normalise,
    base_fit,
    constructed_null,
    cut_from,
    embed,
    gather_lines,
    rule_fit,
)

MODEL_VARIABLE = "MURFULU_EMBED_MODEL"
ROOT = Path(__file__).resolve().parents[1]

#: A rule needs enough claimed outputs for a centroid to mean anything. The
#: same bar the semantic artefact uses, for the same reason.
MIN_CLAIMS = 10


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-version", default="v2")
    parser.add_argument(
        "--sisters",
        type=Path,
        default=None,
        help="run_precompute.py --sisters-out --sisters-keep 0 wrote this",
    )
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None, help="a markdown table")
    return parser.parse_args(argv)


def claims(path: Path) -> dict[str, list[dict[str, Any]]]:
    """Rule id → its claimed corpus outputs, for rules big enough to measure."""
    stored = json.loads(path.read_text(encoding="utf-8"))["sisters"]
    return {rule: rows for rule, rows in stored.items() if len(rows) >= MIN_CLAIMS}


def _write_report(
    path: Path,
    flagged: dict[str, list[dict[str, Any]]],
    checkable: dict[str, set[str]],
) -> None:
    """The per-rule table, worst-hit rules first."""
    rows = sorted(flagged.items(), key=lambda kv: -len(kv[1]) / len(checkable[kv[0]]))
    lines = [
        "| rule | measured claims | doubted | share | the worst of them |",
        "|---|---|---|---|---|",
    ]
    for rule, found in rows:
        total = len(checkable[rule])
        worst = "، ".join(row["form_fa"] for row in found[:4])
        lines.append(
            f"| {rule} | {total} | {len(found)} | {len(found) / total:.0%} | {worst} |"
        )
    clean = [rule for rule in checkable if rule not in flagged]
    lines += ["", f"rules with nothing doubted: {len(clean)} of {len(checkable)}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0915 - one linear pass
    """Embed every claimed output and its base, measure both checks, flag."""
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

    sisters_path = arguments.sisters or (ROOT / "build" / f"sisters-{version}-all.json")
    by_rule = claims(sisters_path)
    print(f"rules with >= {MIN_CLAIMS} claimed outputs: {len(by_rule)}")
    print(f"claims to measure: {sum(len(rows) for rows in by_rule.values()):,}")

    wanted: set[str] = set()
    bases: set[str] = set()
    for rows in by_rule.values():
        for row in rows:
            wanted.add(_normalise(row["form_fa"]))
            if row.get("base_fa"):
                bases.add(_normalise(row["base_fa"]))
    print(f"distinct words: {len(wanted):,}, distinct bases: {len(bases):,}")

    lines = gather_lines(wanted | bases)
    usable = {word: found for word, found in lines.items() if len(found) >= MIN_LINES}
    print(f"with >= {MIN_LINES} corpus lines: {len(usable):,}")

    model = SentenceTransformer(str(Path(model_path).expanduser()))
    word_order = sorted(usable)
    matrix = embed(word_order, usable, model, np)
    row_of = {word: index for index, word in enumerate(word_order)}

    measured: dict[str, list[str]] = {}
    stacks: dict[str, Any] = {}
    for rule, rows in by_rule.items():
        words = sorted({_normalise(r["form_fa"]) for r in rows} & set(row_of))
        if len(words) >= MIN_CLAIMS:
            measured[rule] = words
            stacks[rule] = np.vstack([matrix[row_of[word]] for word in words])
    order_of_rules = sorted(measured)
    print(f"rules with a measurable centroid: {len(order_of_rules)}")

    centres = []
    for rule in order_of_rules:
        centre = stacks[rule].sum(axis=0)
        centres.append(centre / np.linalg.norm(centre))
    claimed = np.zeros((len(word_order), len(order_of_rules)), dtype=bool)
    rows_of = {}
    for column, rule in enumerate(order_of_rules):
        rows_of[rule] = np.array([row_of[word] for word in measured[rule]])
        claimed[rows_of[rule], column] = True
    against_rules = matrix @ np.vstack(centres).T

    by_rule_share, rule_shares, cosines = rule_fit(
        order_of_rules, measured, rows_of, stacks, against_rules, claimed, np
    )
    null = constructed_null(against_rules, claimed, np)
    rule_cut = cut_from(rule_shares, np)
    print()
    print(
        f"rule fit   claims median {np.median(rule_shares):.3f}, "
        f"constructed null median {np.median(null):.3f} (uniform, as assumed)"
    )
    print(f"           own-rule cosine mean {cosines.mean():.3f} — the cut is a rank")
    print(f"           cut {rule_cut:.3f}")

    base_order = sorted(bases & set(row_of))
    base_row = {base: index for index, base in enumerate(base_order)}
    against_bases = matrix @ np.vstack([matrix[row_of[b]] for b in base_order]).T
    # Every claim, not only those of rules big enough for a centroid. This
    # check needs no centroid, and the rules it saves are exactly the small
    # ones the other check cannot see into: -dān has 14 claims, of which 11
    # occur once in the whole corpus, so it never gets a centroid at all.
    pairs = [
        (rule, word, base)
        for rule, rows in by_rule.items()
        for row in rows
        if (word := _normalise(row["form_fa"])) in row_of
        and (base := _normalise(row.get("base_fa") or "")) in base_row
    ]
    by_base_share = base_fit(pairs, row_of, base_row, against_bases)
    base_shares = np.array(list(by_base_share.values()))
    base_cut = cut_from(base_shares, np)
    print(
        f"base fit   {len(by_base_share):,} claims with a base we could embed, "
        f"median {np.median(base_shares):.3f}, cut {base_cut:.3f}"
    )

    flagged: dict[str, list[dict[str, Any]]] = {}
    latin_of = {
        (rule, _normalise(row["form_fa"])): row["form_latin"]
        for rule, rows in by_rule.items()
        for row in rows
    }
    # Every claim either check could reach. A rule too small for a centroid
    # still has its base check, so it is still counted here.
    checkable: dict[str, set[str]] = {}
    for rule, word in list(by_rule_share) + list(by_base_share):
        checkable.setdefault(rule, set()).add(word)

    doubted_by_rule = doubted_by_base = 0
    for rule, reachable in checkable.items():
        found = []
        for word in sorted(reachable):
            by_rule_value = by_rule_share.get((rule, word))
            by_base_value = by_base_share.get((rule, word))
            fails_rule = by_rule_value is not None and by_rule_value > rule_cut
            fails_base = by_base_value is not None and by_base_value > base_cut
            if not (fails_rule or fails_base):
                continue
            doubted_by_rule += fails_rule
            doubted_by_base += fails_base
            found.append(
                {
                    "form_fa": word,
                    "form_latin": latin_of.get((rule, word), ""),
                    "rule_fit_outranked": (
                        None if by_rule_value is None else round(by_rule_value, 4)
                    ),
                    "base_fit_outranked": (
                        None if by_base_value is None else round(by_base_value, 4)
                    ),
                    "failed": ["rule"] * fails_rule + ["base"] * fails_base,
                }
            )
        if found:
            found.sort(key=lambda row: -(row["base_fit_outranked"] or 0))
            flagged[rule] = found

    total_flagged = sum(len(rows) for rows in flagged.values())
    measurable = sum(len(words) for words in checkable.values())
    print()
    print(
        f"doubted    {total_flagged:,} of {measurable:,} measurable claims "
        f"({total_flagged / measurable:.1%}) across {len(flagged)} rules"
    )
    print(
        f"           {doubted_by_rule:,} by rule fit, {doubted_by_base:,} by base fit"
    )

    out = arguments.out or (ROOT / "build" / f"suspect-claims-{version}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "corpus_version": version,
                "model": Path(model_path).name,
                "min_claims": MIN_CLAIMS,
                "rule_fit_cut": round(rule_cut, 4),
                "base_fit_cut": round(base_cut, 4),
                "distributions": {
                    "rule_fit_claims": _describe(rule_shares, np),
                    "rule_fit_null": _describe(null, np),
                    "base_fit_claims": _describe(base_shares, np),
                    "own_rule_cosine": _describe(cosines, np),
                },
                "claims_measurable": measurable,
                "claims_doubted": total_flagged,
                "doubted_by_rule_fit": doubted_by_rule,
                "doubted_by_base_fit": doubted_by_base,
                "rules_measured": len(order_of_rules),
                "flagged": flagged,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")

    if arguments.report:
        _write_report(arguments.report, flagged, checkable)
        print(f"wrote {arguments.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
