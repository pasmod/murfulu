"""Put the offline automatic readings beside the model, and say what they hold.

    python tools/import_reading_suggestions.py v22 READINGS.json \
        > data/behnevis-suggest-v22.md

``READINGS.json`` is made outside the repository (2026-11-22): one row per
spelling of ``data/behnevis-unsure-<version>.json``, read blind by a language
model from the spelling's first example line (the word and its two
neighbours), with the model's certainty and the calibration measured on
held-out vowel-marked words (:mod:`murfulu.behnevis.suggest` says how).
Its rows carry ``rank``, ``spelling``, ``kind``, ``context``,
``example_line``, ``document_id``, a reading and a certainty; the two last
are found by their names' endings (``…_reading``, ``…_certainty``), or named
with ``--reading-field`` and ``--certainty-field``.

Writes ``data/behnevis-suggest-<version>.json`` beside the model (not in git:
it quotes corpus words and places), in the small format the API reads, and a
report on standard output. **Refuses** a file whose rows do not match the
list (a spelling not listed, another rank or kind, an example line the list
does not hold) or whose calibration bands disagree with the rows' measured
shares, rather than serve readings against the wrong list.

Checks each reading against the editions' vowel signs where the corpus marks
the spelling (``data/behnevis-marked-<version>.jsonl``, if it is there):
how many marked places it fits, beside the bank's own readings. The checks
and the conversion are :mod:`murfulu.behnevis.offline`. No Elasticsearch, no
lexicon, no database.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any

from murfulu.behnevis import suggest, unsure
from murfulu.behnevis.offline import (
    METHOD,
    MIN_MARKED,
    Marks,
    column,
    convert,
    marked_fits,
)

DATA = Path(__file__).resolve().parents[1] / "data"

#: How many rows the report's tables show.
SHOWN = 25


def _share(part: int, whole: int) -> str:
    return f"{part / whole:.0%}" if whole else "—"


def report(
    version: str,
    meta: dict[str, Any],
    listed: list[dict[str, Any]],
    found: suggest.Suggestions,
    fits: dict[str, Marks] | None,
) -> list[str]:
    """The report, as Markdown lines. No corpus line is quoted."""
    served = {one["spelling"]: found.of(one) for one in listed}
    out = [
        "# Automatic suggestions for the most frequent unsure spellings, "
        f"corpus {version}",
        "",
        "Written by `tools/import_reading_suggestions.py` (the file the API reads:",
        "`src/murfulu/behnevis/suggest.py`). **Unconfirmed, and only shown**: a",
        "person accepts a suggestion with the list's decide controls or does not.",
        "",
        "## 0. How they were made",
        "",
        f"{METHOD[0].upper()}{METHOD[1:]}. Made {meta['made']}, offline, one row per",
        f"spelling of `behnevis-unsure-{version}.json` (measured "
        f"{meta['list_measured']}).",
        "What the certainty is worth was measured on "
        f"{meta['calibration']['words']:,} held-out",
        "vowel-marked words of the poets the reading screen's model did not learn",
        "from (*right*: the editions' marks accept the reading; *at least*: the exact",
        "95 % lower bound):",
        "",
        "| certainty | test words | right | at least | listed spellings |",
        "|---|---:|---:|---:|---:|",
    ]
    per_band = Counter(
        tuple(one["band"]) for one in served.values() if one and one["band"]
    )
    for band in found.bands:
        out.append(
            f"| {band.low:g}–{band.high:g} | {band.words:,} | {band.share:.0%} | "
            f"{band.at_least:.0%} | {per_band[(band.low, band.high)]:,} |"
        )
    out += [
        "",
        "Limits: the test words are the hard ones editions mark, not these frequent",
        "words; one line was read per spelling, so where a spelling has several",
        "readings the suggestion is the reading in that line, not necessarily",
        "everywhere.",
        "",
        "## 1. What they offer, by kind",
        "",
        "*In the bank*: one of the bank's (or the function-word list's) readings, the",
        "same when case, accents, the ezafe and the mark for ع are set aside.",
        "*Offered*: a reading the panel offers that the bank lacks (what the model",
        "read or built). *To type*: none the panel offers; a person types it, and it",
        "goes to karbon's list like any typed reading. *Several*: the bank holds the",
        "letters with and without a capital (*Xod*, *xod*); the suggestion writes no",
        "capitals, so the screen marks both and leaves the choice to the person.",
        "",
        "| kind | spellings | in the bank | offered | to type | several |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for kind in unsure.KINDS:
        mine = [m for o in listed if o["kind"] == kind and (m := served[o["spelling"]])]
        bank = sum(1 for one in mine if one["in_bank"])
        other = sum(1 for one in mine if one["matches"] and not one["in_bank"])
        typed = sum(1 for one in mine if not one["matches"])
        several = sum(1 for one in mine if len(one["matches"]) > 1)
        out.append(
            f"| {kind} | {len(mine):,} | {bank:,} | {other:,} | {typed:,} | "
            f"{several:,} |"
        )
    out.append("")
    if fits is None:
        return [
            *out,
            "No marked places file beside the model: sections 2 and 3 not measured.",
        ]
    return [
        *out,
        *_against_marks(listed, served, fits),
        *_one_differs(listed, served, fits),
    ]


def _against_marks(
    listed: list[dict[str, Any]],
    served: Mapping[str, dict[str, Any] | None],
    fits: dict[str, Marks],
) -> list[str]:
    counted = Counter[str]()
    weak = []
    for one in listed:
        mine, marks = served[one["spelling"]], fits[one["spelling"]]
        if mine is None or marks.checked[mine["latin"]] < MIN_MARKED:
            continue
        kind, latin = one["kind"], mine["latin"]
        counted[kind] += 1
        counted[f"{kind}:checked"] += marks.checked[latin]
        counted[f"{kind}:fit"] += marks.fit[latin]
        best = max(one["known"], key=marks.share, default=None)
        if best is not None:
            counted[f"{kind}:bank_checked"] += marks.checked[best]
            counted[f"{kind}:bank_fit"] += marks.fit[best]
        if marks.share(latin) < 0.5:
            weak.append((one, mine, marks))
    out = [
        "## 2. Against the editions' marks, on these spellings",
        "",
        f"Spellings whose suggestion can be lined up with at least {MIN_MARKED} of",
        "their marked places (a place a reading cannot be lined up with says",
        "nothing of it). *The bank's best*: of the bank's readings, the one that",
        "fits the largest share of the places it is checked on.",
        "",
        "| kind | spellings | places checked | the suggestion fits | "
        "the bank's best fits |",
        "|---|---:|---:|---:|---:|",
    ]
    for kind in unsure.KINDS:
        checked = counted[f"{kind}:checked"]
        bank = _share(counted[f"{kind}:bank_fit"], counted[f"{kind}:bank_checked"])
        out.append(
            f"| {kind} | {counted[kind]:,} | {checked:,} | "
            f"{_share(counted[f'{kind}:fit'], checked)} | {bank} |"
        )
    weak.sort(key=lambda w: -w[0]["unsure"])
    out += [
        "",
        f"**{len(weak):,} suggestions fit fewer than half of the marked places they",
        "are checked on**; the screen says so beside them. The most unsure:",
        "",
        "| spelling | unsure | suggestion | certainty | fits marked places |",
        "|---|---:|---|---:|---:|",
    ]
    for one, mine, marks in weak[:SHOWN]:
        out.append(
            f"| {one['spelling']} | {one['unsure']:,} | {mine['latin']} | "
            f"{mine['certainty']:g} | {marks.of(mine['latin'])} |"
        )
    return [
        *out,
        "",
        "Limits: editions mark the hard places, and often the classical reading",
        "(*bovad*) where the suggestion gives today's (*bud*); the signs check only",
        "the letters they mark.",
        "",
    ]


def _one_differs(
    listed: list[dict[str, Any]],
    served: Mapping[str, dict[str, Any] | None],
    fits: dict[str, Marks],
) -> list[str]:
    differ = [
        (one, mine)
        for one in listed
        if one["kind"] == unsure.ONE
        and (mine := served[one["spelling"]]) is not None
        and not mine["in_bank"]
    ]
    differ.sort(key=lambda pair: -pair[0]["unsure"])
    out = [
        "## 3. Where the bank holds one reading and the suggestion another",
        "",
        f"**{len(differ):,} spellings**, candidates for a fault in karbon's word bank",
        "(UPSTREAM A20), to be weighed with the marks: where the editions' signs fit",
        "the suggestion and not the bank's reading, the bank is the likelier fault.",
        "",
        "| spelling | unsure | the bank's reading | suggestion | certainty | "
        "marks fit the suggestion | marks fit the bank's |",
        "|---|---:|---|---|---:|---:|---:|",
    ]
    backed = 0
    for i, (one, mine) in enumerate(differ):
        bank, marks = one["known"][0], fits[one["spelling"]]
        latin = mine["latin"]
        if marks.checked[latin] >= MIN_MARKED and marks.share(latin) > marks.share(
            bank
        ):
            backed += 1
        if i < SHOWN:
            out.append(
                f"| {one['spelling']} | {one['unsure']:,} | {bank} | {mine['latin']} | "
                f"{mine['certainty']:g} | {marks.of(mine['latin'])} | "
                f"{marks.of(bank)} |"
            )
    return [
        *out,
        "",
        f"Of the {len(differ):,}, the editions' marks back the suggestion over the",
        f"bank's reading (checked on at least {MIN_MARKED} marked places, a larger",
        "share fits) for",
        f"**{backed:,}**.",
        "",
    ]


def main(argv: list[str] | None = None) -> int:
    """Check and convert the readings, write the file, print the report."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("version", help="corpus version, e.g. v22")
    parser.add_argument("readings", type=Path, help="the offline readings (JSON)")
    parser.add_argument("--reading-field", default=None)
    parser.add_argument("--certainty-field", default=None)
    parser.add_argument("--data", type=Path, default=DATA, help="the model's folder")
    args = parser.parse_args(argv)

    model = args.data / f"behnevis-{args.version}.json"
    list_meta, listed = unsure.read(unsure.path_beside(model))
    if list_meta.get("corpus_version") != args.version:
        raise SystemExit(f"the list is for {list_meta.get('corpus_version')}")
    raw = json.loads(args.readings.read_text(encoding="utf-8"))
    given = raw["meta"]
    if given.get("corpus_version") != args.version:
        raise SystemExit(f"the readings are for {given.get('corpus_version')}")
    rows = raw["readings"]
    try:
        reading_field = column(rows, "_reading", str, args.reading_field)
        certainty_field = column(rows, "_certainty", (int, float), args.certainty_field)
    except ValueError as unclear:
        raise SystemExit(str(unclear)) from None
    calibration = given["calibration"]
    bands = suggest.bands_from(
        {**band, "at_least": band.get("at_least", band.get("lower_95"))}
        for band in calibration["bands"]
    )
    converted, problems = convert(rows, listed, reading_field, certainty_field, bands)
    if problems or len(converted) != len(listed):
        for one in problems[:20]:
            print(one, file=sys.stderr)
        raise SystemExit(
            f"{len(problems)} rows refused, {len(converted):,} of {len(listed):,} "
            "listed spellings read: nothing written"
        )

    marked_path = args.data / f"behnevis-marked-{args.version}.jsonl"
    fits = None
    if marked_path.is_file():
        known = {one["spelling"]: one["known"] for one in listed}
        wanted = {s: [row["latin"], *known[s]] for s, row in converted.items()}
        with marked_path.open(encoding="utf-8") as lines:
            fits = marked_fits(wanted, (json.loads(line) for line in lines))
        for spelling, row in converted.items():
            marks, latin = fits[spelling], row["latin"]
            if marks.checked[latin]:
                row["marked"] = {
                    "checked": marks.checked[latin],
                    "fit": marks.fit[latin],
                }

    meta = {
        "made": given.get("made") or date.today().isoformat(),
        "corpus_version": args.version,
        "list": unsure.path_beside(model).name,
        "list_measured": list_meta.get("measured"),
        "method": METHOD,
        "calibration": {
            "words": calibration["words"],
            "note": "held-out vowel-marked words; right = fits the edition's marks",
            "bands": [band.to_dict() for band in bands],
        },
        "marked_checked": fits is not None,
    }
    out = suggest.path_beside(model)
    suggest.write(out, meta, converted)
    found = suggest.read(out)
    print(f"written: {out} ({len(converted):,} spellings)", file=sys.stderr)
    print("\n".join(report(args.version, meta, listed, found, fits)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
