"""Run the derivation precompute and report what it cost.

Applies every rule to every applicable lexicon entry, checks each result
against the corpus, and writes the ``derivations`` records out.

    python tools/run_precompute.py --out build/derivations.jsonl
    python tools/run_precompute.py --corpus-version v1 --elasticsearch
    python tools/run_precompute.py --corpus-version v1 --elasticsearch --no-release

``--no-release`` writes ``derivations-<version>`` and leaves the alias where it
is, which is what ``run_ingest.py`` has always done. Without it a new version
goes into service in the same breath as it is written, so nobody can look at it
first — and the whole reason this version exists may be that the last one was
serving forms nobody had checked.

The corpus pass is the slow half — counting 25 million words and linking them
to the lexicon — so ``--no-corpus`` skips it and every form comes back with no
attestation rather than a wrong one.

Run time and output size are printed at the end. They are the numbers PLAN
task 5.2 asks for, and the numbers that decide whether the pool widens.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from murfulu.corpus import link, wordtypes
from murfulu.corpus.function_words import loaded as function_words
from murfulu.corpus.ganjoor import GanjoorCorpus
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import loaded
from murfulu.scoring.attestation import Index
from murfulu.scoring.precompute import (
    DEFAULT_DEPTH,
    REVIEWED_CATEGORIES,
    Precompute,
    input_readings,
)
from murfulu.scoring.precompute import run as run_precompute
from murfulu.scoring.semantics import PATH_VARIABLE as SEMANTIC_PATH_VARIABLE
from murfulu.scoring.semantics import loaded as semantics
from murfulu.scoring.sisters import SisterForms, SuspectClaims
from murfulu.search.backfill import build as build_affix_map


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write the records as JSON lines")
    parser.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    parser.add_argument(
        "--categories",
        nargs="*",
        default=list(REVIEWED_CATEGORIES),
        help="lexicon categories to generate from",
    )
    parser.add_argument(
        "--no-corpus",
        action="store_true",
        help="skip attestation; every form comes back unchecked",
    )
    parser.add_argument(
        "--no-semantics",
        action="store_true",
        help="skip typicality; every form's semantic part is null",
    )
    parser.add_argument("--corpus-version", default="v1")
    parser.add_argument(
        "--sisters",
        type=int,
        default=8,
        help="how many attested siblings to store on each word; 0 for none",
    )
    parser.add_argument(
        "--sisters-out", type=Path, help="write each rule's attested output here"
    )
    parser.add_argument(
        "--sisters-keep",
        type=int,
        default=50,
        help="rows per rule in --sisters-out; 0 writes every one",
    )
    parser.add_argument(
        "--suspect-claims",
        type=Path,
        help="what tools/flag_homograph_claims.py wrote; ranks doubted "
        "claims last instead of dropping them",
    )
    parser.add_argument(
        "--affix-map-out",
        type=Path,
        help="write which corpus word types each rule formed, for run_ingest.py",
    )
    parser.add_argument(
        "--elasticsearch",
        action="store_true",
        help="also write into derivations-<corpus-version>",
    )
    parser.add_argument(
        "--no-release",
        action="store_true",
        help="write the index but leave the derivations alias where it is",
    )
    return parser.parse_args(argv)


def _attestation(corpus_version: str) -> Index:
    """Count the corpus and link it to the lexicon, so forms can be checked."""
    started = time.monotonic()
    corpus = wordtypes.build(GanjoorCorpus())
    print(
        f"corpus         {corpus.document_count:,} documents, "
        f"{corpus.token_count:,} words, {len(corpus):,} spellings "
        f"({time.monotonic() - started:,.0f}s)"
    )
    with Lexicon.open() as lexicon:
        linked = link.link(corpus, lexicon)
    print(f"link           {linked.coverage.summary()}")
    listed = function_words()
    print(
        f"function words {len(listed)} spellings credit nothing "
        f"(rules/function_words.yaml {listed.version})"
    )
    return Index.from_link(linked, corpus_version=corpus_version, listed=listed)


def _write_jsonl(path: Path, job: Precompute) -> int:
    """Write one JSON object per line and return the file size in bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for derivation in job.derivations():
            handle.write(json.dumps(derivation.as_document(), ensure_ascii=False))
            handle.write("\n")
    return path.stat().st_size


def _write_sisters(path: Path, sisters: SisterForms, keep: int = 50) -> None:
    """Write each rule's best-attested output, with the evidence for each.

    ``keep = 0`` writes every one. That is what the homograph detector reads:
    a capped list would have it measure the distribution of the best-attested
    claims rather than of all of them.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = {
        rule_id: [
            {
                "form_latin": sister.form_latin,
                "form_fa": sister.form_fa,
                "base_fa": sister.base_fa,
                "attestation": sister.level.value,
                "doc_count": sister.doc_count,
                "total_count": sister.total_count,
                "author_count": sister.author_count,
                "suspect": sister.suspect,
                "function_word": sister.function_word,
            }
            for sister in sisters.for_rule(rule_id, limit=keep or None)
        ]
        for rule_id in sorted(sisters.by_rule)
    }
    path.write_text(
        json.dumps(
            {
                "corpus_version": sisters.corpus_version,
                "attested_per_rule": sisters.counts(),
                "suspect_per_rule": sisters.suspect_counts(),
                "function_word_per_rule": sisters.function_word_counts(),
                "sisters": rows,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )


def _suspect_claims(path: Path | None) -> SuspectClaims:
    """The ``(rule, form)`` claims the homograph detector doubted.

    Read as a set rather than trusted as a judgement: the file says a word sits
    far from what its rule usually makes, and this pass ranks it last for that
    reason. Nothing is deleted on its account.
    """
    if path is None:
        return frozenset()
    stored = json.loads(path.read_text(encoding="utf-8"))
    return frozenset(
        (rule, row["form_latin"])
        for rule, rows in stored.get("flagged", {}).items()
        for row in rows
        if row.get("form_latin")
    )


def main(argv: list[str] | None = None) -> int:
    """Run the pass and print the report."""
    arguments = _parse(argv)
    pack = loaded()
    attestation = (
        None if arguments.no_corpus else _attestation(arguments.corpus_version)
    )
    # The artefact is optional and its absence is a legitimate state: every
    # form's semantic part is then null, which is *not measured* and never a
    # low score.
    vectors = None if arguments.no_semantics else semantics()
    if vectors is not None and not len(vectors):
        print(f"semantics      none configured; set {SEMANTIC_PATH_VARIABLE}")
        vectors = None

    with Lexicon.open() as lexicon:
        print(f"overrides      {lexicon.describe_overrides()}")
        readings = list(input_readings(lexicon, arguments.categories))
        print(f"input pool     {len(readings):,} readings from {arguments.categories}")
        job = run_precompute(
            pack,
            readings,
            attestation=attestation,
            semantics=vectors,
            depth=arguments.depth,
            corpus_version=arguments.corpus_version,
            generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )

    written = job.report
    print(
        f"grounding      {written.grounded:,} forms stand on written ground, "
        f"{written.ungrounded:,} do not, {written.grounding_unknown:,} not established"
    )
    print(
        f"typicality     {written.with_typicality:,} forms carry a semantic part "
        f"({len(vectors)} rules have a centroid)"
        if vectors
        else "typicality     no semantic artefact; every form's part is null"
    )

    suspect = _suspect_claims(arguments.suspect_claims)
    if suspect:
        print(f"suspect        {len(suspect):,} claims the detector doubts")

    sisters = job.sisters(limit=arguments.sisters, suspect=suspect)
    with_output = [r for r, found in sisters.by_rule.items() if found]
    print(f"sisters        {len(with_output)} rules have an attested output")
    if arguments.sisters_out:
        _write_sisters(arguments.sisters_out, sisters, keep=arguments.sisters_keep)

    if arguments.affix_map_out:
        formed = build_affix_map(job.derivations(), arguments.corpus_version, suspect)
        print(
            f"affix map      {len(formed):,} corpus word types traced to a rule "
            f"({formed.refused_homographs:,} refused as homographs, "
            f"{formed.contested_claims:,} claims contested)"
        )
        arguments.affix_map_out.parent.mkdir(parents=True, exist_ok=True)
        arguments.affix_map_out.write_text(
            json.dumps(formed.as_document(), ensure_ascii=False),
            encoding="utf-8",
        )

    if arguments.out:
        job.report.output_bytes = _write_jsonl(arguments.out, job)

    if arguments.elasticsearch:
        from murfulu.search import derivations as writer
        from murfulu.search.indices import IndexAdmin, connect

        client = connect()
        admin = IndexAdmin(client)
        admin.create("derivations", arguments.corpus_version)
        result = writer.write(client, arguments.corpus_version, job.derivations())
        print(f"elasticsearch  {result.summary()}")
        if not result.complete:
            print("alias          left alone; the write did not finish")
        elif arguments.no_release:
            print(
                f"built          derivations-{arguments.corpus_version}, "
                f"alias unchanged"
            )
        else:
            admin.release("derivations", arguments.corpus_version)
            print(f"released       derivations now serving {arguments.corpus_version}")

    print(job.report.summary())
    silent = job.report.rules_that_never_fired(pack)
    print(f"rules unused   {len(silent)} of {len(pack.rules)}: {', '.join(silent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
