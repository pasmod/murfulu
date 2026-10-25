"""Read-only wrapper over the karbon lexicon snapshot.

Owns: every lookup into the lexicon — by spelling, by normalised spelling, by
Latin — and the mapping from the lexicon's own categories to the word classes
the rule pack matches on. The snapshot path comes from configuration and the
snapshot id is recorded with every result derived from it.

This is the only place karbon is imported. If karbon changes, one package
changes.

Does not own: writing. The snapshot is never modified.
"""

from murfulu.lexicon.entries import Reading
from murfulu.lexicon.snapshot import (
    PATH_VARIABLE,
    Snapshot,
    SnapshotMissingError,
    SnapshotNotConfiguredError,
    open_snapshot,
)
from murfulu.lexicon.store import Lexicon

__all__ = [
    "PATH_VARIABLE",
    "Lexicon",
    "Reading",
    "Snapshot",
    "SnapshotMissingError",
    "SnapshotNotConfiguredError",
    "open_snapshot",
]
