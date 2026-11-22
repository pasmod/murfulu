"""Automatic suggestions for the most frequent unsure spellings, shown, never applied.

The list of unsure spellings (:mod:`.unsure`) asks a person to decide a
reading once for every like place. For each listed spelling there is now an
**automatic suggestion** beside it: one reading, and how often a reading at
that certainty was right when it was tested (the project lead's request of
2026-11-22). **Unconfirmed, and nothing is decided by it**: the screens show
it, a person accepts it with the decide controls or does not, and a decision
acts only at a model rebuild someone starts by hand, as before.

**How the suggestions were made, offline.** A language model read each
listed spelling **blind**: the word with its two neighbours from the
spelling's first example line in the list, its vowel signs and the answer
hidden, and gave a reading in Behnevis letters with its own certainty, 0 to
100. **The certainty was calibrated** on 1,200 vowel-marked words of the
poets the model behind the reading screen did not learn from: for each band
of certainty, how many readings the editions' marks accept
(:func:`murfulu.search.harakat.fits`), and the exact 95 % lower bound of that
share. Two limits travel with every suggestion: the test words are the hard
ones editions mark, not these frequent words; and one line was read per
spelling, so where a spelling has several readings the suggestion is the
reading in that line, not necessarily everywhere.

**The file** sits beside the model, ``behnevis-suggest-v22.json`` beside
``behnevis-v22.json``, and is not in git: its rows quote corpus words and
the list's places. ``tools/import_reading_suggestions.py`` writes it from the
offline readings::

    {"format": 1,
     "meta": {"made": "2026-11-22", "corpus_version": "v22",
              "list": "behnevis-unsure-v22.json", "list_measured": "2026-11-21",
              "method": "...",
              "calibration": {"words": 1200, "note": "...",
                              "bands": [{"from": 0, "to": 50, "words": 241,
                                         "right": 153, "share": 0.635,
                                         "at_least": 0.581}, ...]}},
     "suggestions": {
        "بود": {"latin": "bud", "as_read": "bud", "certainty": 95,
                "context": "واکرده [بود]",
                "place": {"document_id": "...", "unit": 15, "line": 0, "word": 5},
                "marked": {"checked": 1464, "fit": 1}}}}

``latin`` is the reading as a spelling's reading: the ezafe the line gave it
(*sar-e*) taken off; ``as_read`` is as it was read in the line. ``place`` is
the list's example the line was, or null; ``marked`` is how many of the
spelling's vowel-marked places in the corpus the reading fits, or null.

**What is served** with a listed spelling (:meth:`Suggestions.of`): the
reading, the certainty and its band's measured share, and ``matches`` — the
readings the list offers that are the suggestion, compared without case,
accents, ezafe or the mark for ع (:func:`same`), since the suggestion writes
no capitals and karbon mostly writes ع with a vowel letter (UPSTREAM A19).
A spelling the list offers no such reading for gets the suggestion to type.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from murfulu.behnevis.letters import latin_key

#: The file format this module writes and reads.
FORMAT = 1

#: The ezafe a reading carries in its line: *sar-e*, *xāne-ye*, in any case
#: and with or without the accent Behnevis may write on it (*-é*).
_EZAFE = re.compile(r"-(?:y?[eé])$", re.IGNORECASE)

#: Behnevis's mark for ع and ء (*tabˈ*).
_GLOTTAL = "ˈ"


def without_ezafe(reading: str) -> str:
    """The reading without the ezafe its line gave it: *sar-e* → *sar*.

    Composed first, so a decomposed accent (*e* and U+0301) is the same *é*.
    """
    return _EZAFE.sub("", unicodedata.normalize("NFC", reading.strip()))


def folded(reading: str) -> str:
    """A reading as a suggestion is compared: no ezafe, case, accents or ع mark.

    Within one spelling the letters are the same, so the mark for ع never
    tells two of its readings apart; karbon mostly writes ع with a vowel
    letter instead (UPSTREAM A19), and the suggestion writes no capitals.
    """
    return latin_key(without_ezafe(reading)).replace(_GLOTTAL, "")


def same(one: str, other: str) -> bool:
    """Whether two readings are the same reading, as :func:`folded` compares."""
    return bool(folded(one)) and folded(one) == folded(other)


def offered(listed: Mapping[str, Any]) -> list[str]:
    """The readings the list's panel offers, in its order: the bank's first.

    The same order the decide panel shows them in (``readingsOf`` in the
    web's list): what the bank or the function-word list holds, then what the
    model read at the unsure places, then what it offered there.
    """
    return list(
        dict.fromkeys(
            [
                *listed.get("known", []),
                *(latin for latin, _ in listed.get("read_as", [])),
                *(latin for latin, _ in listed.get("offered", [])),
            ]
        )
    )


def matching(reading: str, readings: Iterable[str]) -> list[str]:
    """The readings that are this one, as :func:`same` compares, in their order."""
    return [one for one in dict.fromkeys(readings) if same(reading, one)]


@dataclass(frozen=True)
class Band:
    """One band of certainty and how often its readings were right in the test.

    ``low`` is in the band and ``high`` is not, except 100, which the last
    band holds. ``at_least`` is the exact 95 % lower bound of ``share``.
    """

    low: float
    high: float
    words: int
    right: int
    share: float
    at_least: float

    def holds(self, certainty: float) -> bool:
        """Whether a certainty falls in this band."""
        return self.low <= certainty < self.high or certainty == self.high == 100

    def to_dict(self) -> dict[str, Any]:
        """The band as the file keeps it: whole numbers where they are whole."""
        return {
            "from": int(self.low) if self.low.is_integer() else self.low,
            "to": int(self.high) if self.high.is_integer() else self.high,
            "words": self.words,
            "right": self.right,
            "share": self.share,
            "at_least": self.at_least,
        }


def bands_from(raw: Iterable[Mapping[str, Any]]) -> tuple[Band, ...]:
    """The calibration's bands, checked to cover 0 to 100 without a gap.

    A band's share must be its right words over its words, as written to
    three places, and its lower bound may not exceed it: a table that says
    otherwise is not served.
    """
    bands = tuple(
        Band(
            float(one["from"]),
            float(one["to"]),
            int(one["words"]),
            int(one["right"]),
            float(one["share"]),
            float(one["at_least"]),
        )
        for one in raw
    )
    if not bands or bands[0].low != 0 or bands[-1].high != 100:
        raise ValueError("the calibration bands do not cover 0 to 100")
    for before, after in zip(bands, bands[1:], strict=False):
        if before.high != after.low:
            raise ValueError(f"a gap or overlap between bands at {before.high}")
    for band in bands:
        # In order and of some width: a band running backwards would put one
        # certainty in two bands, and band_of would take the first silently.
        if not (math.isfinite(band.low) and math.isfinite(band.high)) or not (
            0 <= band.low < band.high <= 100
        ):
            raise ValueError(f"band {band.low}-{band.high}: not in order within 0-100")
        if band.words <= 0 or not 0 <= band.right <= band.words:
            raise ValueError(f"band {band.low}-{band.high}: impossible counts")
        if abs(band.share - band.right / band.words) > 0.0005:
            raise ValueError(f"band {band.low}-{band.high}: share is not right/words")
        if not 0 <= band.at_least <= band.share:
            raise ValueError(f"band {band.low}-{band.high}: lower bound above share")
    return bands


def band_of(certainty: float, bands: Iterable[Band]) -> Band | None:
    """The band a certainty falls in, or None outside 0 to 100."""
    return next((band for band in bands if band.holds(certainty)), None)


@dataclass(frozen=True)
class Suggestions:
    """The suggestions beside one model, as the API serves them."""

    meta: dict[str, Any]
    rows: dict[str, dict[str, Any]]
    bands: tuple[Band, ...]

    def about(self) -> dict[str, Any]:
        """What the screens say of the suggestions as a whole."""
        calibration = self.meta.get("calibration") or {}
        return {
            "made": self.meta.get("made"),
            "corpus_version": self.meta.get("corpus_version"),
            "spellings": len(self.rows),
            "tested_words": calibration.get("words"),
            "bands": [band.to_dict() for band in self.bands],
        }

    def of(self, listed: Mapping[str, Any]) -> dict[str, Any] | None:
        """The suggestion for a listed spelling, as served with it, or None."""
        row = self.rows.get(listed.get("spelling") or "")
        if row is None:
            return None
        latin = row["latin"]
        certainty = row["certainty"]
        band = band_of(certainty, self.bands)
        matches = matching(latin, offered(listed))
        known = set(listed.get("known", []))
        return {
            "latin": latin,
            "as_read": row.get("as_read") or latin,
            "certainty": certainty,
            # How often a reading at this certainty was right in the test,
            # and the 95 % lower bound of that share.
            "right_share": band.share if band else None,
            "right_at_least": band.at_least if band else None,
            "band": [band.to_dict()["from"], band.to_dict()["to"]] if band else None,
            # How many test words the shares were measured on.
            "tested_words": (self.meta.get("calibration") or {}).get("words"),
            "context": row.get("context"),
            "place": row.get("place"),
            # The readings the panel offers that are this suggestion; empty
            # when none is, and the suggestion is to be typed.
            "matches": matches,
            # Whether the bank (or the function-word list) holds it.
            "in_bank": any(one in known for one in matches),
            "marked": row.get("marked"),
        }


def path_beside(model: Path) -> Path:
    """The suggestions that go with a model: ``behnevis-suggest-v22.json``.

    A model named otherwise gets ``<name>.suggest.json`` beside it, never
    the model's own path.
    """
    if model.name.startswith("behnevis-"):
        return model.with_name(model.name.replace("behnevis-", "behnevis-suggest-", 1))
    return model.with_name(f"{model.stem}.suggest.json")


_PLACE = ("document_id", "unit", "line", "word")


def _row_ok(spelling: Any, row: Any) -> bool:
    """Whether a row holds what :meth:`Suggestions.of` serves, of the right kinds.

    The screens read every field it passes on, so a context that is not text
    or a place without its four parts is refused here, not met in a browser.
    """
    if not (isinstance(spelling, str) and spelling and isinstance(row, dict)):
        return False
    latin, certainty = row.get("latin"), row.get("certainty")
    context, place, marked = row.get("context"), row.get("place"), row.get("marked")
    return (
        isinstance(latin, str)
        and bool(folded(latin))
        and isinstance(row.get("as_read", latin), str)
        and isinstance(certainty, int | float)
        and not isinstance(certainty, bool)
        and 0 <= certainty <= 100
        and (context is None or (isinstance(context, str) and "[" in context))
        and (
            place is None
            or (
                isinstance(place, dict)
                and isinstance(place.get("document_id"), str)
                and all(isinstance(place.get(k), int) for k in _PLACE[1:])
            )
        )
        and (
            marked is None
            or (
                isinstance(marked, dict)
                and isinstance(marked.get("checked"), int)
                and isinstance(marked.get("fit"), int)
                and 0 <= marked["fit"] <= marked["checked"]
            )
        )
    )


def write(
    path: Path, meta: dict[str, Any], suggestions: dict[str, dict[str, Any]]
) -> None:
    """The suggestions as one JSON file, in the format :func:`read` reads."""
    bands_from(meta["calibration"]["bands"])  # never write a table read refuses
    bad = [s for s, row in suggestions.items() if not _row_ok(s, row)]
    if bad:
        raise ValueError(f"{len(bad)} rows lack a reading or a certainty: {bad[:5]}")
    path.write_text(
        json.dumps(
            {"format": FORMAT, "meta": meta, "suggestions": suggestions},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def read(path: Path) -> Suggestions:
    """The suggestions as :func:`write` wrote them; ValueError if they are not."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("format") != FORMAT:
        raise ValueError(f"not a suggestions file of format {FORMAT}: {path}")
    meta = raw["meta"]
    rows = raw["suggestions"]
    bad = [s for s, row in rows.items() if not _row_ok(s, row)]
    if bad:
        raise ValueError(f"{len(bad)} rows lack a reading or a certainty: {bad[:5]}")
    return Suggestions(meta, rows, bands_from(meta["calibration"]["bands"]))
