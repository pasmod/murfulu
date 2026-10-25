"""Read back the productivity a run measured.

The numbers are produced by a batch job — ``tools/run_productivity.py`` — and
read by the app. Nothing recomputes them on request: they take a full
precompute to produce, and a figure that changed between two page loads would
not be a measurement.

**The file is configuration, like the lexicon snapshot.** It carries the
corpus version in its name and in its contents, because none of these numbers
means anything without it, and the app refuses to serve a file whose version
does not match the one it was asked for.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from statistics import median
from typing import Any

#: Where the measured productivity lives. Never a literal in the code.
PATH_VARIABLE = "MURFULU_PRODUCTIVITY_PATH"


@dataclass(frozen=True)
class Measured:
    """Every rule's row from one run, keyed by rule id."""

    corpus_version: str = ""
    by_rule: dict[str, dict[str, Any]] = field(default_factory=dict)

    def for_rule(self, rule_id: str) -> dict[str, Any] | None:
        """One rule's measurement, or nothing if the run never reached it."""
        return self.by_rule.get(rule_id)

    def __len__(self) -> int:
        """How many rules the run has a row for."""
        return len(self.by_rule)

    def realisation(self, rule_id: str) -> float | None:
        """How often this rule's output turns out to be a word, or ``None``.

        ``None`` where the run could not measure the rule at all — 33 of 195 —
        and that is *not measured*, never a rate of zero. See
        :func:`neutral_realisation` for what a caller should do with it.
        """
        row = self.by_rule.get(rule_id)
        if row is None or not row.get("measured"):
            return None
        rate = row.get("realisation_rate")
        return float(rate) if rate is not None else None


def path() -> Path | None:
    """The configured file, if there is one and it exists."""
    configured = os.environ.get(PATH_VARIABLE)
    if not configured:
        return None
    found = Path(configured).expanduser()
    return found if found.is_file() else None


@lru_cache(maxsize=1)
def loaded() -> Measured:
    """The measurements, read once.

    An empty result is a legitimate answer and not an error: a machine that
    has never run the precompute has no productivity to show, and the
    interface says so rather than showing zeros that look like measurements.
    """
    found = path()
    if found is None:
        return Measured()
    document = json.loads(found.read_text(encoding="utf-8"))
    rows = {row["rule_id"]: row for row in document.get("rules", [])}
    return Measured(corpus_version=document.get("corpus_version", ""), by_rule=rows)


@lru_cache(maxsize=1)
def neutral_realisation() -> float | None:
    """The middle rule's realisation rate — what an *unmeasured* rule counts as.

    A chain is ranked on how often its rules produce words the corpus has, and
    33 of 195 rules were never measured. Counting those as zero would say the
    run had looked and found nothing, which is the one thing this project does
    not let a number say: **not measured is never a low score.** So an
    unmeasured rule is filled in at the median of the measured ones — no
    information, no opinion.

    Chosen before it was needed rather than after: on both verbs it was tested
    against, treating the unmeasured as zero, as neutral, or as perfect moved
    nothing at all, because those chains are fully measured. It matters for
    chains that are not, and there the neutral fill is the honest one.

    ``None`` where nothing has been measured, which is a machine that has never
    run the precompute.
    """
    rates = [
        rate
        for rule_id in loaded().by_rule
        if (rate := loaded().realisation(rule_id)) is not None
    ]
    return median(rates) if rates else None
