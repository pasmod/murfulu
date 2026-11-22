"""The offline readings for the list of unsure spellings, checked and converted.

The automatic suggestions (:mod:`.suggest`) are made outside the repository
and come in as one JSON file: ``meta`` (with the calibration) and
``readings``, one row per listed spelling with ``rank``, ``spelling``,
``kind``, ``context``, ``example_line``, ``document_id``, a reading and a
certainty. This module turns those rows into the small file the API reads,
refusing any that does not match the list, and measures each reading against
the editions' vowel signs where the corpus marks the spelling.
``tools/import_reading_suggestions.py`` runs it and writes the report.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from murfulu.behnevis import suggest, unsure
from murfulu.search import harakat

#: What the file says of how the readings were made. No product is named:
#: what matters to a reader is that it was blind and offline, and measured.
METHOD = (
    "read offline and blind by a language model: each listed spelling with its "
    "two neighbours from its first example line, vowel signs and answer hidden; "
    "a reading in Behnevis letters and the model's own certainty, 0 to 100"
)

#: How many marked places a spelling needs before they are read as a sign.
MIN_MARKED = unsure.MIN_MARKED


def column(
    rows: list[Mapping[str, Any]],
    ending: str,
    kind: type | tuple[type, ...],
    named: str | None,
) -> str:
    """The rows' field for the reading or the certainty.

    The one named, or else the one field whose name so ends and whose value
    is of the kind wanted in the first row (``matches_a_bank_reading`` ends
    like a reading and is a flag).
    """
    keys = set(rows[0]) if rows else set()
    if named:
        if named not in keys:
            raise ValueError(f"no field {named!r} in the readings")
        return named
    found = sorted(
        k
        for k in keys
        if k.endswith(ending)
        and isinstance(rows[0][k], kind)
        and not isinstance(rows[0][k], bool)
    )
    if len(found) != 1:
        raise ValueError(f"cannot tell the {ending} field: {found}; name it")
    return found[0]


def convert(
    rows: list[Mapping[str, Any]],
    listed: list[dict[str, Any]],
    reading_field: str,
    certainty_field: str,
    bands: tuple[suggest.Band, ...],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """The rows in the file's format, keyed by spelling, and what is wrong with them.

    A row must name a listed spelling with the list's rank and kind, a
    reading and a certainty from 0 to 100; its example line must be one of
    the list's examples, whose place it takes. Where a row carries the share
    measured for its certainty, it must be its band's.
    """
    by_spelling = {one["spelling"]: one for one in listed}
    out: dict[str, dict[str, Any]] = {}
    problems: list[str] = []
    for row in rows:
        spelling = str(row.get("spelling") or "")
        one = by_spelling.get(spelling)
        if one is None:
            problems.append(f"{spelling}: not in the list")
            continue
        if spelling in out:
            problems.append(f"{spelling}: twice")
            continue
        if row.get("rank") != one["rank"] or row.get("kind") != one["kind"]:
            problems.append(f"{spelling}: rank or kind differs from the list")
            continue
        reading = row.get(reading_field)
        certainty = row.get(certainty_field)
        if not isinstance(reading, str) or not suggest.folded(reading):
            problems.append(f"{spelling}: no reading")
            continue
        if (
            isinstance(certainty, bool)
            or not isinstance(certainty, int | float)
            or not 0 <= certainty <= 100
        ):
            problems.append(f"{spelling}: certainty {certainty!r}")
            continue
        band = suggest.band_of(certainty, bands)
        measured = row.get("measured_right_share")
        if band is None or (measured is not None and abs(measured - band.share) > 1e-6):
            problems.append(f"{spelling}: share {measured} is not its band's")
            continue
        example = next(
            (
                place
                for place in one.get("examples", [])
                if place.get("document_id") == row.get("document_id")
                and place.get("text") == row.get("example_line")
            ),
            None,
        )
        if example is None:
            problems.append(f"{spelling}: its example line is not the list's")
            continue
        context = row.get("context")
        if context is not None and (
            not isinstance(context, str) or f"[{spelling}]" not in context
        ):
            problems.append(f"{spelling}: its context does not hold the spelling")
            continue
        out[spelling] = {
            "latin": suggest.without_ezafe(reading),
            "as_read": reading.strip(),
            "certainty": int(certainty) if certainty == int(certainty) else certainty,
            "context": context,
            "place": {k: example[k] for k in ("document_id", "unit", "line", "word")},
            "marked": None,
        }
    return out, problems


@dataclass
class Marks:
    """One spelling's marked places, read against each of its readings.

    For each reading: the places it can be lined up with (``checked``:
    ``harakat.fits`` says True or False) and those whose signs accept it
    (``fit``). A place it cannot be lined up with says nothing of it — الله
    marked «اللَّه» against *allāh*, whose ā the script does not write — and
    is not counted, so two readings may be checked on different places.
    """

    checked: Counter[str] = field(default_factory=Counter)
    fit: Counter[str] = field(default_factory=Counter)

    def share(self, reading: str) -> float:
        """The share of its checked places a reading fits; 0 where none was checked."""
        return (
            self.fit[reading] / self.checked[reading] if self.checked[reading] else 0.0
        )

    def of(self, reading: str) -> str:
        """«k of n», or «—» where no place was checked."""
        n = self.checked[reading]
        return f"{self.fit[reading]:,} of {n:,}" if n else "—"


def marked_fits(
    readings: Mapping[str, Iterable[str]], marked: Iterable[Mapping[str, Any]]
) -> dict[str, Marks]:
    """Per spelling: the marked places each reading is checked on, and fits."""
    wanted = {s: list(dict.fromkeys(r)) for s, r in readings.items()}
    out = {s: Marks() for s in wanted}
    for row in marked:
        spelling = row.get("spelling") or ""
        if spelling not in wanted:
            continue
        for reading in wanted[spelling]:
            fit = harakat.fits(row["written"], reading)
            if fit is not None:
                out[spelling].checked[reading] += 1
                out[spelling].fit[reading] += fit
    return out
