"""Put a new corpus version beside the one it replaces, before releasing it.

    python tools/compare_versions.py --report data/corpus_report-v7.json \
        data/corpus_report-v8.json \
        --derivations build/derivations-v7.jsonl build/derivations-v8.jsonl

**Why this is a tool and not a paragraph.** ENGINEERING has said since v6 that
five numbers must be compared before a version is released. v6 was released
without anyone comparing them, and four of the five were identical to v4
because the poet-century table had not been loaded — a silent failure that
leaves a corpus where every poem is undated and only one blank chart to show
it. A check nobody runs is not a check.

The five, in the order they are printed: ``documents``, ``tokens``,
``spellings``, ``spellings_linked``, and ``documents_without_century``.

**A moved number is reported, never judged.** Rebuilding on the same corpus
text should move none of them, and rebuilding on new text should move all of
them; which of those was intended is the reader's to know. The exit status is
0 either way, because this tool measures and does not decide.

``--derivations`` additionally counts what the build pass produced: records,
the paths behind them, attested forms, and every rule that gained or lost
forms. That last one is the point when a version exists to remove a rule's
output: it says whether only that rule moved.

``--attributable-to N-020 N-023`` goes further and matches the two files record
by record, so "nothing else moved" is a measurement rather than an impression.
Four of its six lines must read zero.

``--function-words`` does the same for a version whose only change is
``rules/function_words.yaml`` (v13 → v14): record by record, every difference
must be a listed spelling's attestation, or follow from one — a grounding
that rested on such a form, a sister list of a rule that made one. Everything
else must read zero.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

#: The five the release check is written on. Order matters: it is the order
#: ENGINEERING prints them in, and `documents_without_century` is last because
#: it is the one that has actually failed.
RELEASE_FIGURES = (
    "documents",
    "tokens",
    "spellings",
    "spellings_linked",
    "documents_without_century",
)


def _row(name: str, before: object, after: object) -> str:
    """One comparison line, saying plainly whether the number moved."""
    if isinstance(before, int) and isinstance(after, int):
        delta = after - before
        moved = "same" if delta == 0 else f"{delta:+,}"
        return f"  {name:<28} {before:>12,}  {after:>12,}   {moved}"
    return f"  {name:<28} {before!s:>12}  {after!s:>12}   " + (
        "same" if before == after else "changed"
    )


def compare_reports(before: Path, after: Path) -> None:
    """Print the five release figures side by side."""
    old = json.loads(before.read_text(encoding="utf-8"))
    new = json.loads(after.read_text(encoding="utf-8"))
    print(
        f"corpus report      {old.get('corpus_version')} -> {new.get('corpus_version')}"
    )
    for name in RELEASE_FIGURES:
        print(_row(name, old.get(name), new.get(name)))
    if old.get("lexicon_snapshot_id") != new.get("lexicon_snapshot_id"):
        print(
            f"  lexicon snapshot moved: {old.get('lexicon_snapshot_id')} -> "
            f"{new.get('lexicon_snapshot_id')}"
        )


def _derivation_counts(source: Path) -> tuple[Counter[str], dict[str, int]]:
    """Per-rule form counts, and the totals the version is described by.

    A rule is counted once per record it helped build, over **every** path.
    Counted from `paths` and not from the flat field beside them, which was
    `rule_chain` and carried the first path alone until 2026-08-14 — counting
    from it understated a rule by however many forms it reaches as an
    alternative route. That field is now `built_by` and is the same union this
    computes, but `paths` remains the source of truth for both.
    """
    per_rule: Counter[str] = Counter()
    totals = {"records": 0, "paths": 0, "attested": 0, "function_word": 0}
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            paths = record.get("paths") or []
            totals["records"] += 1
            totals["paths"] += len(paths)
            # A function word's letters credit nothing (since v14): counted on
            # their own line, never as attested.
            homograph = bool(record.get("attestation_function_word"))
            totals["function_word"] += homograph
            totals["attested"] += (
                record.get("attestation") not in (None, "none") and not homograph
            )
            rules: set[str] = set()
            for path in paths:
                rules.update(path.get("rule_ids") or ())
            for rule in rules:
                per_rule[rule] += 1
    return per_rule, totals


def compare_derivations(before: Path, after: Path) -> None:
    """Print the build totals, then every rule whose output count moved."""
    old_rules, old_totals = _derivation_counts(before)
    new_rules, new_totals = _derivation_counts(after)
    print(f"\nderivations        {before.name} -> {after.name}")
    for name in ("records", "paths", "attested", "function_word"):
        print(_row(name, old_totals[name], new_totals[name]))

    moved = sorted(
        (
            (rule, old_rules.get(rule, 0), new_rules.get(rule, 0))
            for rule in set(old_rules) | set(new_rules)
            if old_rules.get(rule, 0) != new_rules.get(rule, 0)
        ),
        key=lambda row: row[1] - row[2],
        reverse=True,
    )
    if not moved:
        print("  no rule's output count moved")
        return
    print(f"  {len(moved)} rules moved:")
    for rule, was, now in moved:
        print(_row(rule, was, now))


def _paths(record: dict[str, object]) -> frozenset[tuple[str, ...]]:
    """A record's derivations, as a set of rule chains."""
    paths = record.get("paths") or []
    assert isinstance(paths, list)
    return frozenset(tuple(path.get("rule_ids") or ()) for path in paths)


def attribute(before: Path, after: Path, rules: set[str]) -> None:
    """Check that every difference between the two is one of `rules` and no more.

    The per-rule counts above say what moved; this says whether anything moved
    that should not have. A version built to remove one rule's output has to
    answer for every record it also lost, and the honest way to answer is to
    match the two files record by record rather than to compare totals.

    Four of the six lines below must be zero, or the rebuild did something
    besides what it was for.
    """
    was: dict[str, frozenset[tuple[str, ...]]] = {}
    with before.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            was[record["id"]] = _paths(record)

    counts = dict.fromkeys(
        ("unchanged", "gone", "gone_other", "shrank", "shrank_other", "appeared"), 0
    )
    seen = set()
    with after.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            seen.add(record["id"])
            now = _paths(record)
            previously = was.get(record["id"])
            if previously is None:
                counts["appeared"] += 1
            elif now == previously:
                counts["unchanged"] += 1
            elif now < previously:
                lost = previously - now
                key = (
                    "shrank"
                    if all(rules & set(chain) for chain in lost)
                    else "shrank_other"
                )
                counts[key] += 1
            else:
                counts["appeared"] += 1

    for rule_id, chains in was.items():
        if rule_id in seen:
            continue
        key = "gone" if all(rules & set(chain) for chain in chains) else "gone_other"
        counts[key] += 1

    lines = (
        ("unchanged", "unchanged", ""),
        ("gone", "gone, every path one of these rules", ""),
        ("gone_other", "gone for another reason", "   must be 0"),
        ("shrank", "kept, lost only these rules paths", ""),
        ("shrank_other", "kept, lost another path", "   must be 0"),
        ("appeared", "gained a path, or newly appeared", "   must be 0"),
    )
    print(f"\nattributable to    {', '.join(sorted(rules))}")
    for key, label, note in lines:
        print(f"  {label:<40} {counts[key]:>12,}{note}")


#: What a function-word change may move, field by field. Everything else in a
#: record is hashed together and must not move at all.
_EVIDENCE = (
    "attestation",
    "attested_count",
    "attested_docs",
    "attested_authors",
    "attested_first_century",
    "attested_last_century",
    "attestation_unlinked",
    "attested_other_readings",
    "attestation_function_word",
)
_FOLLOWS = ("base_attested", "sister_forms")
_IGNORED = ("generated_at", "corpus_version")


def _fingerprint(record: dict[str, Any]) -> tuple[str, str, str, str]:
    """Evidence, grounding, sisters, and a hash of everything else."""
    rest = {
        key: value
        for key, value in record.items()
        if key not in _EVIDENCE + _FOLLOWS + _IGNORED
    }

    def digest(value: object) -> str:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        return hashlib.blake2b(text.encode(), digest_size=8).hexdigest()

    return (
        digest([record.get(key) for key in _EVIDENCE]),
        digest(record.get("base_attested")),
        digest(record.get("sister_forms")),
        digest(rest),
    )


def _last_rules(record: dict[str, Any]) -> set[str]:
    return {
        path["rule_ids"][-1] for path in record.get("paths") or () if path["rule_ids"]
    }


def function_words(before: Path, after: Path) -> dict[str, int]:
    """Match the two versions record by record and attribute every difference.

    A difference is *attributable* when it is the attestation of a form whose
    spelling is on the list, or follows from one: the record's grounding moved
    and one of its paths stands on a form that lost its credit, or its sister
    list moved and a rule that made it also made a function word's letters.
    """
    from murfulu.corpus.function_words import loaded

    listed = loaded()
    was: dict[str, tuple[str, str, str, str]] = {}
    with before.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            was[record["id"]] = _fingerprint(record)

    # First pass over the new file: which forms lost their credit, and which
    # rules made a function word's letters.
    uncredited: set[str] = set()
    rules_with_one: set[str] = set()
    with after.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("attestation_function_word"):
                uncredited.add(record["form_latin"])
                rules_with_one |= _last_rules(record)

    counts = Counter[str]()
    seen: set[str] = set()
    with after.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            seen.add(record["id"])
            old = was.get(record["id"])
            if old is None:
                counts["appeared"] += 1
                continue
            new = _fingerprint(record)
            if new == old:
                counts["unchanged"] += 1
                continue
            counts["changed"] += 1
            if new[3] != old[3]:
                counts["other_field"] += 1
            if new[0] != old[0]:
                on_list = record["form_fa"] in listed
                counts["evidence_listed" if on_list else "evidence_other"] += 1
            if new[1] != old[1]:
                stands = any(
                    path.get("base_form") in uncredited
                    for path in record.get("paths") or ()
                )
                counts["ground_follows" if stands else "ground_other"] += 1
            if new[2] != old[2]:
                follows = bool(_last_rules(record) & rules_with_one)
                counts["sisters_follow" if follows else "sisters_other"] += 1
    counts["gone"] = sum(1 for key in was if key not in seen)

    lines = (
        ("unchanged", "unchanged", ""),
        ("changed", "changed in some field", ""),
        ("evidence_listed", "evidence moved, spelling on the list", ""),
        ("evidence_other", "evidence moved, spelling not listed", "   must be 0"),
        ("ground_follows", "grounding moved, stood on such a form", ""),
        ("ground_other", "grounding moved otherwise", "   must be 0"),
        ("sisters_follow", "sisters moved, rule made such a form", ""),
        ("sisters_other", "sisters moved otherwise", "   must be 0"),
        ("other_field", "any other field moved", "   must be 0"),
        ("appeared", "appeared", "   must be 0"),
        ("gone", "gone", "   must be 0"),
    )
    print(f"\nfunction words     rules/function_words.yaml {listed.version}")
    for key, label, note in lines:
        print(f"  {label:<40} {counts[key]:>12,}{note}")
    print(
        f"  {len(uncredited):,} forms credited nothing, made by "
        f"{len(rules_with_one)} rules"
    )
    return {key: counts[key] for key, _, _ in lines}


def main(argv: list[str] | None = None) -> int:
    """Compare whichever of the two halves was asked for."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        nargs=2,
        type=Path,
        metavar=("BEFORE", "AFTER"),
        help="the two corpus report files run_ingest.py --report-out wrote",
    )
    parser.add_argument(
        "--derivations",
        nargs=2,
        type=Path,
        metavar=("BEFORE", "AFTER"),
        help="the two JSON-lines files run_precompute.py --out wrote",
    )
    parser.add_argument(
        "--attributable-to",
        nargs="+",
        metavar="RULE",
        help="check every difference is one of these rules; needs --derivations",
    )
    parser.add_argument(
        "--function-words",
        action="store_true",
        help="check every difference follows from the function-word list",
    )
    arguments = parser.parse_args(argv)
    if not arguments.report and not arguments.derivations:
        parser.error("give --report, --derivations, or both")
    if arguments.attributable_to and not arguments.derivations:
        parser.error("--attributable-to needs --derivations")
    if arguments.function_words and not arguments.derivations:
        parser.error("--function-words needs --derivations")
    if arguments.report:
        compare_reports(*arguments.report)
    if arguments.derivations:
        compare_derivations(*arguments.derivations)
    if arguments.attributable_to:
        old, new = arguments.derivations
        attribute(old, new, set(arguments.attributable_to))
    if arguments.function_words:
        function_words(*arguments.derivations)
    return 0


if __name__ == "__main__":
    sys.exit(main())
