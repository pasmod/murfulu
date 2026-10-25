"""Values this project holds instead of the lexicon's, and why.

The lexicon belongs to karbon and is mounted read-only. Nothing here writes to
it. These are values applied **as readings are read**, so the rest of the
system sees what this project believes is right without anything being changed
upstream.

**Why this exists at all.** Waiting for another repository is never a good
reason for a word to be built on the wrong stem. The working rule is: build
what we believe is right now, record it for karbon
(``docs/UPSTREAM.md``), and settle it with the linguist afterwards
(``docs/FOR_THE_LINGUIST.md``). An override is the machinery for that.

**It is not a fork, and it is built so it cannot become one.**

*Every override records what it replaced.* ``was`` is checked against the
snapshot when the override is applied, and an override whose ``was`` no longer
matches is **refused** — because that means karbon changed the value and
nobody looked. A silent override on top of a moved target is the one way this
file could do damage.

*Every override is unconfirmed until somebody rules.* karbon was built from the
linguist's own rules and much of it was checked by hand, so a difference is at
least as likely to be his later correction as an error.

*Two kinds, and they are not the same act.* A **correction** changes a field of
an existing reading. An **addition** is a second reading of a spelling the
lexicon does not have — never a replacement, because one spelling with two
readings is a shape this system already models: مرد is *mard* and *mord*.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from murfulu.lexicon.entries import Reading

#: The authored file, beside the rule pack.
OVERRIDES_FILE = "lexicon_overrides.yaml"

#: Fields of a reading a correction may change. Deliberately short: a stem is
#: a fact about a verb, and everything else is either identity or evidence.
CORRECTABLE = (
    "past_stem_fa",
    "past_stem_latin",
    "present_stem_fa",
    "present_stem_latin",
)


class OverrideError(ValueError):
    """Raised when an override does not make sense, or no longer applies."""


@dataclass(frozen=True)
class Correction:
    """One field of one reading, held differently from the snapshot."""

    headword_fa: str
    field: str
    value: str
    #: What the snapshot says. Checked before the override is applied.
    was: str
    source: str
    why: str
    confirmed: bool = False


@dataclass(frozen=True)
class Addition:
    """A reading the lexicon does not have."""

    headword_fa: str
    latin: str
    fields: dict[str, Any]
    source: str
    why: str
    confirmed: bool = False


@dataclass(frozen=True)
class Overrides:
    """Everything held differently, keyed by headword."""

    #: The snapshots these values were checked against. An override is only
    #: applied to a snapshot listed here: the `was` values were read from it,
    #: and a different snapshot — a fixture, or karbon's next release — has to
    #: be re-measured, not assumed. This is also what keeps the authored table
    #: out of every fixture-based test.
    #:
    #: **A list since karbon 1.2.0 (2026-10-18).** With one name the table
    #: dropped out the moment the lexicon moved, with nothing to say so; a new
    #: snapshot is now *added* here once every row has been re-read on it, and
    #: a snapshot not listed is reported by :class:`~murfulu.lexicon.store.Lexicon`
    #: and refused by a test against the configured one.
    lexicon_snapshots: tuple[str, ...] = ()
    corrections: tuple[Correction, ...] = ()
    additions: tuple[Addition, ...] = ()

    def applies_to(self, snapshot_id: str) -> bool:
        """True when this table was checked against this snapshot.

        An entry is a snapshot name (``lexicon-20261012``) or a full id with
        its content hash. A name matches only the whole name before the colon,
        so ``lexicon-2026101`` cannot match by prefix.
        """
        name = snapshot_id.split(":", 1)[0]
        return any(entry in (name, snapshot_id) for entry in self.lexicon_snapshots)

    def corrections_for(self, headword_fa: str) -> tuple[Correction, ...]:
        """Corrections that apply to one headword."""
        return tuple(one for one in self.corrections if one.headword_fa == headword_fa)

    def additions_for(self, headword_fa: str) -> tuple[Addition, ...]:
        """Readings to add for one headword."""
        return tuple(one for one in self.additions if one.headword_fa == headword_fa)

    def __len__(self) -> int:
        """How many values are held differently in all."""
        return len(self.corrections) + len(self.additions)

    @property
    def unconfirmed(self) -> int:
        """How many are still waiting on a ruling."""
        pending = [one for one in self.corrections if not one.confirmed]
        return len(pending) + sum(1 for one in self.additions if not one.confirmed)


def _correction(raw: dict[str, Any]) -> Correction:
    field = raw.get("field")
    if field not in CORRECTABLE:
        raise OverrideError(
            f"{raw.get('headword_fa')!r}: {field!r} is not one of "
            f"{', '.join(CORRECTABLE)}"
        )
    for required in ("headword_fa", "value", "was", "source", "why"):
        if not (raw.get(required) or "").strip():
            raise OverrideError(
                f"{raw.get('headword_fa')!r}: an override with no {required} "
                f"cannot be reviewed or undone"
            )
    return Correction(
        headword_fa=raw["headword_fa"],
        field=field,
        value=raw["value"],
        was=raw["was"],
        source=raw["source"],
        why=raw["why"],
        confirmed=bool(raw.get("confirmed")),
    )


def _addition(raw: dict[str, Any]) -> Addition:
    for required in ("headword_fa", "latin", "source", "why"):
        if not (raw.get(required) or "").strip():
            raise OverrideError(f"an addition with no {required}")
    known = {
        "past_stem_fa",
        "past_stem_latin",
        "present_stem_fa",
        "present_stem_latin",
        "lexicon_category",
    }
    return Addition(
        headword_fa=raw["headword_fa"],
        latin=raw["latin"],
        fields={key: raw[key] for key in known if key in raw},
        source=raw["source"],
        why=raw["why"],
        confirmed=bool(raw.get("confirmed")),
    )


def load(directory: Path | None = None) -> Overrides:
    """Read the authored file, or return nothing when there is none."""
    path = (directory or default_directory()) / OVERRIDES_FILE
    if not path.is_file():
        return Overrides()
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return Overrides(
        lexicon_snapshots=_snapshots(document),
        corrections=tuple(_correction(raw) for raw in document.get("corrections", [])),
        additions=tuple(_addition(raw) for raw in document.get("additions", [])),
    )


def _snapshots(document: dict[str, Any]) -> tuple[str, ...]:
    """The snapshots the file was checked against, which it must name.

    ``lexicon_snapshots`` is a list; the single ``lexicon_snapshot`` of the
    first version is still read, so an older copy of the file means what it
    meant.
    """
    listed = document.get("lexicon_snapshots")
    if listed is None and document.get("lexicon_snapshot"):
        listed = [document["lexicon_snapshot"]]
    names = tuple(str(one).strip() for one in (listed or []) if str(one).strip())
    if not names:
        raise OverrideError(
            "the overrides file names no lexicon_snapshots; the `was` values "
            "were read from specific snapshots and mean nothing without them"
        )
    return names


def default_directory() -> Path:
    """Where the rule pack lives. Configuration, never a literal."""
    configured = os.environ.get("MURFULU_RULES_PATH")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / "rules"


@lru_cache(maxsize=1)
def loaded() -> Overrides:
    """The overrides, read once."""
    return load()


def apply_to(reading: Reading, overrides: Overrides | None = None) -> Reading:
    """Return this reading with any override applied.

    Raises :class:`OverrideError` when an override's ``was`` no longer matches
    the snapshot. That means karbon changed the value underneath us, and
    applying the override anyway would silently overwrite somebody's work —
    exactly the failure this file has to be incapable of.
    """
    held = overrides if overrides is not None else loaded()
    changed = reading
    for correction in held.corrections_for(reading.spelling_fa):
        current = getattr(changed, correction.field, None)
        if current != correction.was:
            raise OverrideError(
                f"{correction.headword_fa}: the override expects "
                f"{correction.field} to be {correction.was!r} and the snapshot "
                f"now says {current!r}. Somebody changed it upstream — check "
                f"docs/FOR_THE_LINGUIST.md L1 before touching this."
            )
        # The field name is validated against CORRECTABLE at load time, and
        # every correctable field is a string; mypy cannot see through the
        # dynamic keyword, hence the narrow ignore.
        changed = replace(changed, **{correction.field: correction.value})  # type: ignore[arg-type]
    return changed
