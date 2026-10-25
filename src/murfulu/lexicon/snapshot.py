"""Where the lexicon snapshot is, and how it is identified.

The path is configuration. It is never written into the code, because the
snapshot is replaced whenever the karbon maintainer supplies a fresher one and
that must not require an edit anywhere.

Every result that came out of a snapshot carries that snapshot's id, so a
stored derivation can always say which version of the lexicon it was built
from.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

#: Environment variable holding the path to the snapshot.
PATH_VARIABLE = "MURFULU_LEXICON_PATH"

#: How much of the file hash goes into the snapshot id. Long enough that a
#: collision is not a practical concern, short enough to read in a log line.
_HASH_LENGTH = 12


class SnapshotNotConfiguredError(RuntimeError):
    """Raised when no snapshot path was given and none is in the environment."""


class SnapshotMissingError(FileNotFoundError):
    """Raised when the configured snapshot path does not exist."""


@dataclass(frozen=True)
class Snapshot:
    """One lexicon file, identified by its name and its contents."""

    path: Path
    snapshot_id: str

    @property
    def name(self) -> str:
        """The file name without its extension, e.g. ``lexicon-20260808``."""
        return self.path.stem


def resolve_path(path: str | Path | None = None) -> Path:
    """Return the snapshot path, from the argument or from the environment."""
    if path is None:
        configured = os.environ.get(PATH_VARIABLE)
        if not configured:
            raise SnapshotNotConfiguredError(
                f"no snapshot path given and {PATH_VARIABLE} is not set"
            )
        path = configured
    resolved = Path(path).expanduser()
    if not resolved.is_file():
        raise SnapshotMissingError(f"lexicon snapshot not found: {resolved}")
    return resolved


def identify(path: Path) -> Snapshot:
    """Build the snapshot id from the file name and a hash of its contents.

    Contents rather than modification time: copying the same snapshot to
    another machine must give the same id, or figures computed on one machine
    cannot be compared with figures computed on another.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    short = digest.hexdigest()[:_HASH_LENGTH]
    return Snapshot(path=path, snapshot_id=f"{path.stem}:{short}")


def open_snapshot(path: str | Path | None = None) -> Snapshot:
    """Resolve and identify a snapshot in one step."""
    return identify(resolve_path(path))
