"""Where one typicality sits among all of them.

The semantic score is a cosine, and on this corpus it **never leaves the
middle**: measured over 583,572 scored forms, every one falls between 0.554
and 0.914, and the middle half between 0.800 and 0.852. Printed as a bare
percentage, 84% reads as a good mark out of a hundred and is in fact the
median — the most ordinary word on the screen.

**A number needs its spread or it is not a measurement.** This is the same
remedy `tools/run_productivity.py` already applies to rule productivity,
where a rule's figure is shown as a band of the measured distribution rather
than raw, and for the same reason: the band can only be worked out where the
whole distribution is, which is a batch job and never a page load.

Nothing here scores anything. It reads cut points a run measured and answers
which slice a value falls in. **An absent artefact is a legitimate state** —
the answer is then ``None``, *not measured*, and the screen shows the figure
without a position rather than inventing one.
"""

from __future__ import annotations

import bisect
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

#: Where the measured spread lives. Never a literal in the code.
PATH_VARIABLE = "MURFULU_TYPICALITY_PATH"

#: The slices, low to high. Five, not three: a tercile over a distribution
#: this narrow puts almost everything in the middle and says nothing.
BANDS: tuple[str, ...] = ("lowest", "low", "middle", "high", "highest")

#: The percentile boundaries between them, so a band is a share of the words
#: rather than a share of the range: the range is 0.554–0.914 and unevenly
#: filled, so equal slices of it would not be equal slices of anything real.
CUTS: tuple[float, ...] = (10.0, 30.0, 70.0, 90.0)


@dataclass(frozen=True)
class Spread:
    """One run's typicality distribution, as the cut points between bands."""

    corpus_version: str = ""
    #: The value at each of :data:`CUTS`, ascending. Empty means not measured.
    boundaries: tuple[float, ...] = ()
    lowest: float | None = None
    highest: float | None = None
    median: float | None = None
    counted: int = 0

    def band_for(self, score: float) -> str | None:
        """Which slice this score falls in, or None if nothing was measured."""
        if not self.boundaries:
            return None
        return BANDS[bisect.bisect_right(self.boundaries, score)]

    def __len__(self) -> int:
        """How many forms the run measured."""
        return self.counted


def path() -> Path | None:
    """The configured file, if there is one and it exists."""
    configured = os.environ.get(PATH_VARIABLE)
    if not configured:
        return None
    found = Path(configured).expanduser()
    return found if found.is_file() else None


@lru_cache(maxsize=1)
def loaded() -> Spread:
    """The spread, read once. An empty one is a legitimate answer."""
    found = path()
    if found is None:
        return Spread()
    document = json.loads(found.read_text(encoding="utf-8"))
    return from_document(document)


def from_document(document: dict[str, object]) -> Spread:
    """Build a spread from what the tool wrote, ignoring a malformed one.

    A file with the wrong number of boundaries is treated as absent rather
    than trusted: a band read off four cut points that are really three would
    be wrong quietly, and *not measured* is the safer of the two answers.
    """
    raw = document.get("boundaries")
    boundaries: tuple[float, ...] = ()
    if isinstance(raw, list) and len(raw) == len(CUTS):
        boundaries = tuple(float(one) for one in raw)
    return Spread(
        corpus_version=str(document.get("corpus_version") or ""),
        boundaries=boundaries,
        lowest=_number(document.get("lowest")),
        highest=_number(document.get("highest")),
        median=_number(document.get("median")),
        counted=int(_number(document.get("counted")) or 0),
    )


def _number(value: object) -> float | None:
    """A float, or None where the tool wrote nothing."""
    return float(value) if isinstance(value, int | float) else None
