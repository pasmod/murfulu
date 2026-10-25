"""Read-only access to the lexicon snapshot.

Opened read-only at the SQLite level, not by convention: the snapshot belongs
to karbon and we never write to it.

Deleted rows are excluded everywhere. The snapshot keeps them — 6,238 of the
51,817 rows are soft-deleted — and a query that forgets the filter silently
resurrects retracted readings.

**Where this project holds a different value, it is applied on the way out**
(:mod:`murfulu.lexicon.overrides`), never written back. Waiting for another
repository is not a good reason for a word to be built on the wrong stem, and
every override records what it replaced so it can be dropped in one line.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections import OrderedDict
from collections.abc import Iterable, Iterator
from pathlib import Path
from types import TracebackType

from murfulu.lexicon.behnevis import is_readable, repair
from murfulu.lexicon.entries import Reading
from murfulu.lexicon.overrides import Overrides
from murfulu.lexicon.overrides import apply_to as apply_overrides
from murfulu.lexicon.overrides import loaded as loaded_overrides
from murfulu.lexicon.snapshot import Snapshot, open_snapshot

_COLUMNS = """
    id, headword, headword_normalized, phonemic, pos,
    past_stem_fa, past_stem_lat, present_stem_fa, present_stem_lat,
    transitivity, confidence, needs_review, stem_rule, phonemic_variants,
    definition_preview
"""

# `deleted_at is null` is not optional. See the module docstring.
_ACTIVE = "deleted_at IS NULL"

#: Every column this module reads. A snapshot without one of them is refused
#: when it is opened, by name, rather than failing on the first query that
#: happens to touch it.
REQUIRED_COLUMNS = frozenset(
    part.strip() for part in _COLUMNS.replace("\n", " ").split(",")
) | {"deleted_at"}

#: Columns karbon has shipped and stopped shipping, which nothing here reads.
#: **karbon 1.2.0 (lexicon-20261012) dropped both.** ``notes`` held karbon's
#: own provenance markers, among them ``[v7:badbracket]`` on 335 rows, 60 of
#: them without ``needs_review`` (UPSTREAM A2c); murfulu never read it, so its
#: absence changes no output — but the signal is gone for every consumer, and
#: that is now karbon's to fold into ``needs_review`` (A2c). Listed so that an
#: audit can say "dropped upstream" instead of leaving a reader to wonder.
NOT_SHIPPED_SINCE_1_2_0 = ("file_path", "notes")

_log = logging.getLogger(__name__)

#: Snapshot ids already warned about, so a process opening the lexicon per
#: request says it once and not ten thousand times.
_warned: set[str] = set()


class SnapshotSchemaError(RuntimeError):
    """Raised when a snapshot lacks a column this module reads."""


def _open_mode(path: Path) -> str:
    """`immutable=1` where it is safe, `mode=ro` where it is not.

    **The problem this solves.** The snapshot is in SQLite **WAL** journal mode
    and `./data` is mounted read-only in the container, so a WAL reader cannot
    create the `-shm` file it needs — and any host process that opens the file
    read-write leaves one behind and then takes it away again. `/generate`
    answers a bare 500 until the API is restarted. That is S9.

    `immutable=1` is the flag for exactly this: it promises the file will not
    change, so SQLite skips locking and the shared-memory index altogether and
    a read-only mount is enough.

    **The promise has to be true, so it is checked rather than assumed.** With
    `immutable=1` SQLite ignores the write-ahead log completely, so a snapshot
    with pending WAL content would be read as though those transactions had
    never happened — silently, and wrongly. A non-empty `-wal` beside the file
    means somebody has written to it, so this falls back to `mode=ro`, which is
    slower to open and correct.

    What it costs either way: **the snapshot may not be swapped under a running
    process.** It could not safely be before this change either; now that is
    stated rather than discovered.
    """
    journal = path.with_name(path.name + "-wal")
    try:
        pending = journal.is_file() and journal.stat().st_size > 0
    except OSError:  # pragma: no cover - a stat that fails is not a promise
        pending = True
    return "mode=ro" if pending else "immutable=1"


class Lexicon:
    """A read-only view of one lexicon snapshot.

    Use as a context manager, or call :meth:`close` when finished::

        with Lexicon.open() as lexicon:
            entry = lexicon.by_spelling("رفتن")
    """

    def __init__(self, snapshot: Snapshot, overrides: Overrides | None = None) -> None:
        self.snapshot = snapshot
        #: What this project holds differently. Passed in for a test; read
        #: from `rules/lexicon_overrides.yaml` otherwise — and dropped unless
        #: it was written against **this** snapshot, which is what keeps it
        #: away from fixtures and from karbon's next release alike.
        held = overrides if overrides is not None else loaded_overrides()
        applies = held.applies_to(snapshot.snapshot_id)
        self._overrides = held if applies else Overrides()
        #: How many authored values were held and **not** applied because the
        #: table was never checked against this snapshot. Zero when there is
        #: nothing to drop. Never silent: logged here, printed by the build
        #: tools, and refused by a test against the configured snapshot.
        self.overrides_dropped = 0 if applies else len(held)
        if self.overrides_dropped and snapshot.snapshot_id not in _warned:
            _warned.add(snapshot.snapshot_id)
            _log.warning(
                "lexicon overrides NOT applied: %d held for %s, none checked "
                "against %s — re-read each row on it and list it in "
                "rules/lexicon_overrides.yaml",
                self.overrides_dropped,
                ", ".join(held.lexicon_snapshots),
                snapshot.snapshot_id,
            )
        uri = f"file:{snapshot.path.as_posix()}?{_open_mode(snapshot.path)}"
        self._connection = sqlite3.connect(uri, uri=True)
        self._connection.row_factory = sqlite3.Row
        self._check_schema()

    @classmethod
    def open(
        cls, path: str | Path | None = None, overrides: Overrides | None = None
    ) -> Lexicon:
        """Open the configured snapshot, or the one at ``path``."""
        return cls(open_snapshot(path), overrides)

    @property
    def snapshot_id(self) -> str:
        """The id every reading from this lexicon carries."""
        return self.snapshot.snapshot_id

    @property
    def overrides_applied(self) -> int:
        """How many authored values are held over this snapshot."""
        return len(self._overrides)

    def describe_overrides(self) -> str:
        """One line for a build log: applied, or dropped and why."""
        if self.overrides_dropped:
            return (
                f"NOT APPLIED — {self.overrides_dropped} held, none checked "
                f"against {self.snapshot_id}"
            )
        return (
            f"{self.overrides_applied} applied on {self.snapshot_id} "
            f"({self._overrides.unconfirmed} unconfirmed)"
        )

    def _check_schema(self) -> None:
        """Refuse a snapshot that lacks a column this module reads."""
        present = {
            row[1] for row in self._connection.execute("PRAGMA table_info(infinitives)")
        }
        missing = sorted(REQUIRED_COLUMNS - present)
        if missing:
            self._connection.close()
            raise SnapshotSchemaError(
                f"{self.snapshot_id} has no column {', '.join(missing)} in "
                f"`infinitives`; murfulu reads it (lexicon/store.py)"
            )

    def close(self) -> None:
        """Close the underlying connection."""
        self._connection.close()

    def __enter__(self) -> Lexicon:
        """Return the open lexicon."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the connection on the way out."""
        self.close()

    # -- lookups ---------------------------------------------------------

    def by_spelling(self, spelling: str) -> list[Reading]:
        """Every reading written this way, e.g. مرد → *mard* and *mord*."""
        return self._query("headword = ?", (spelling,))

    def by_normalized_spelling(self, spelling: str) -> list[Reading]:
        """As :meth:`by_spelling`, against the lexicon's normalised column."""
        return self._query("headword_normalized = ?", (spelling,))

    def by_latin(self, latin: str) -> list[Reading]:
        """Every reading with this Latin form. Case-sensitive on purpose.

        *Gofte* (a noun) and *gofte* (an adjective) are two different words in
        Behnevis, and folding case would merge them.

        **A second reading counts.** آبرو is *Ābrav* **or** *Ābrov* and کنار is
        *Kanār* or *Kenār*: the dictionary records both and commits to neither.
        Question P settled in 2026-08-11 that generation builds from every
        reading — and lookup was left matching the primary column alone, so
        **7,106 of the 7,181 second readings could not be found at all** and a
        caller typing a reading karbon itself records got a 404. Measured and
        fixed 2026-08-15; only 8 second readings collide with another word's
        primary, and all eight are the same word spelled two ways.

        The variants are stored lower-case and :func:`_variants` puts the
        primary's capitalisation back, so the column is matched against the
        lower-cased query and the result is then filtered on the **cased**
        reading. That way *Kenār* finds کنار and the rule that case is meaning
        still holds.

        **The lower-casing is Python's and not SQLite's.** SQLite's ``lower()``
        is ASCII only: it leaves *Ā* alone, so ``Ābrov`` never matched the
        stored ``ābrov`` and every reading beginning with a long vowel stayed
        unreachable — the same fault in miniature, found by testing the fix.
        """
        found = self._query("phonemic = ?", (latin,))
        seen = {(one.spelling_fa, one.latin) for one in found}
        for reading in self._query(
            "EXISTS (SELECT 1 FROM json_each(phonemic_variants) "
            "WHERE json_each.value IN (?, ?))",
            (latin, latin.lower()),
        ):
            key = (reading.spelling_fa, reading.latin)
            if key not in seen and latin in reading.all_latin:
                seen.add(key)
                found.append(reading)
        return found

    def by_stem(self, latin: str) -> list[Reading]:
        """Every verb one of whose stems is written this way.

        A stem is not a headword. *raft* and *row* are columns on رفتن, not
        entries of their own, so :meth:`by_latin` cannot find them — and half
        the words the grammar builds are built on a stem. Decomposing
        *Raftār* means asking this question, not the headword one.
        """
        return self._query(
            "(past_stem_lat = ? OR present_stem_lat = ?)", (latin, latin)
        )

    def infinitives(self) -> Iterator[Reading]:
        """Every verb in the snapshot, in id order."""
        yield from self._query("pos = 'مصدر'")

    def all_readings(self) -> Iterator[Reading]:
        """Every reading in the snapshot, in id order.

        One pass over 45,579 rows. Used to build a lookup index, which is far
        cheaper than one query per corpus spelling.
        """
        yield from self._query("1 = 1")

    def count_active(self) -> int:
        """How many rows the snapshot holds once deleted ones are excluded."""
        row = self._connection.execute(
            f"SELECT COUNT(*) FROM infinitives WHERE {_ACTIVE}"  # noqa: S608
        ).fetchone()
        return int(row[0])

    # -- internals -------------------------------------------------------

    def _query(self, where: str, parameters: tuple[str, ...] = ()) -> list[Reading]:
        rows = self._connection.execute(
            f"SELECT {_COLUMNS} FROM infinitives "  # noqa: S608
            f"WHERE {_ACTIVE} AND {where} ORDER BY id",
            parameters,
        ).fetchall()
        return self._collapse(rows)

    def _collapse(self, rows: Iterable[sqlite3.Row]) -> list[Reading]:
        """Group rows into readings, keyed on spelling plus Latin form.

        Rows that share both are the dictionary listing one word several times.
        They become one reading carrying every source id.
        """
        grouped: OrderedDict[tuple[str, str], list[sqlite3.Row]] = OrderedDict()
        for row in rows:
            grouped.setdefault((row["headword"], row["phonemic"]), []).append(row)
        # One place, so nothing can read the snapshot around the overrides.
        readings = [
            apply_overrides(self._build(group), self._overrides)
            for group in grouped.values()
        ]
        return readings + self._added(readings)

    def _added(self, found: list[Reading]) -> list[Reading]:
        """Readings the lexicon does not have, for spellings it was asked about.

        An addition is a **second reading of a spelling**, never a
        replacement — the same shape as مرد being *mard* and *mord*. It is only
        offered for a spelling this query already returned something for, so a
        lookup for something else cannot pick it up by accident.
        """
        if not self._overrides.additions:
            return []
        spellings = {reading.spelling_fa for reading in found}
        extra = []
        for addition in self._overrides.additions:
            if addition.headword_fa not in spellings:
                continue
            if any(reading.latin == addition.latin for reading in found):
                continue
            extra.append(
                Reading(
                    spelling_fa=addition.headword_fa,
                    spelling_normalized=addition.headword_fa,
                    latin=addition.latin,
                    lexicon_categories=(addition.fields.get("lexicon_category"),),
                    past_stem_fa=addition.fields.get("past_stem_fa"),
                    past_stem_latin=addition.fields.get("past_stem_latin"),
                    present_stem_fa=addition.fields.get("present_stem_fa"),
                    present_stem_latin=addition.fields.get("present_stem_latin"),
                    # Flagged, because nobody has ruled on it yet.
                    needs_review=True,
                    source_entry_ids=(),
                    sense_count=1,
                    snapshot_id=self.snapshot_id,
                )
            )
        return extra

    def _build(self, group: list[sqlite3.Row]) -> Reading:
        first = group[0]
        categories: list[str | None] = []
        for row in group:
            if row["pos"] not in categories:
                categories.append(row["pos"])
        # A letter from another alphabet is repaired here, on the one path
        # every reading comes out through. It is not an override: nobody
        # believes a Greek omicron. See murfulu.lexicon.behnevis.
        latin = repair(first["phonemic"]) or ""
        past_latin = repair(_first(group, "past_stem_lat"))
        present_latin = repair(_first(group, "present_stem_lat"))
        return Reading(
            spelling_fa=first["headword"],
            spelling_normalized=first["headword_normalized"],
            latin=latin,
            lexicon_categories=tuple(categories),
            past_stem_fa=_first(group, "past_stem_fa"),
            past_stem_latin=past_latin,
            present_stem_fa=_first(group, "present_stem_fa"),
            present_stem_latin=present_latin,
            # A collapsed reading takes the first sense's definition. The
            # others are still reachable by their source_entry_ids, and
            # joining four Dehkhoda previews would read as nonsense.
            definition_fa=_first(group, "definition_preview"),
            transitivity=_first(group, "transitivity"),
            phonemic_confidence=_first_float(group, "confidence"),
            # Flagged if any of the collapsed rows is flagged: a doubt about
            # one sense is a doubt about the reading. A character the repair
            # could not read flags it too, because what was meant is a guess
            # and this project does not guess one.
            needs_review=any(bool(row["needs_review"]) for row in group)
            or not all(is_readable(one) for one in (latin, past_latin, present_latin)),
            latin_variants=_variants(group, latin),
            karbon_stem_rule=_first_int(group, "stem_rule"),
            source_entry_ids=tuple(int(row["id"]) for row in group),
            sense_count=len(group),
            snapshot_id=self.snapshot_id,
        )


def _variants(group: list[sqlite3.Row], primary: str) -> tuple[str, ...]:
    """Readings the lexicon lists besides the primary one.

    The stored variants are always lower-case while the primary carries its
    capitalisation, and case is meaning in Behnevis — so the primary's case is
    applied to each variant. They are the same word in the same class, only
    pronounced differently.
    """
    found: list[str] = []
    for row in group:
        raw = row["phonemic_variants"]
        if not raw:
            continue
        try:
            listed = json.loads(raw)
        except (TypeError, ValueError):
            continue
        for listed_reading in listed:
            if not isinstance(listed_reading, str):
                continue
            # The variant list repeats whatever the primary field holds, so it
            # carries the same look-alike letters and needs the same repair.
            reading = repair(listed_reading) or ""
            if reading.lower() == primary.lower():
                continue
            cased = (
                reading[0].upper() + reading[1:]
                if primary[:1].isupper() and reading
                else reading
            )
            if cased not in found:
                found.append(cased)
    return tuple(found)


def _first(group: list[sqlite3.Row], column: str) -> str | None:
    """First non-null value of a column across the collapsed rows.

    Null is handled explicitly rather than by comparison: 11 rows have a null
    category, and SQL comparisons skip those silently.
    """
    for row in group:
        if row[column] is not None:
            value: str = row[column]
            return value
    return None


def _first_float(group: list[sqlite3.Row], column: str) -> float | None:
    """As :func:`_first`, for a real-valued column."""
    for row in group:
        if row[column] is not None:
            return float(row[column])
    return None


def _first_int(group: list[sqlite3.Row], column: str) -> int | None:
    """As :func:`_first`, for an integer column."""
    for row in group:
        if row[column] is not None:
            return int(row[column])
    return None
