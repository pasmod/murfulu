"""The rule pack as karbon receives it: a mirror, not a second copy.

``docs/DECISIONS.md`` settles the shape: **one master, one mirror**. The YAML
here is the master and the linguist's edits land in it; karbon carries a copy
so its own morphology work has the rules available, updated by pull request.
Two editable copies would be two rule sets within a month.

So the mirror is defined as narrowly as it can be:

**Byte-identical, file for file.** The pack is copied, not transformed. That
makes "is the mirror current?" a comparison anyone can run, in either
repository, without loading anything or agreeing on a schema. A transformed
export would need its own version, its own tests, and a way to tell a
transformation bug from a stale copy.

**Plus a manifest that says where it came from** — the rule-pack version, the
files with their hashes, and the sentence that stops somebody editing the copy.

This module computes the mirror and compares it. It writes nothing and it
opens nothing: sending it is a pull request against somebody else's
repository, and those go on the project lead's word.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

#: What karbon receives. Everything :mod:`murfulu.rules.pack` loads, so the
#: mirror can be loaded by the same code, and nothing else — the source
#: transcriptions and the id register are working material.
MIRRORED = (
    "verb_stems.yaml",
    "nominals.yaml",
    "glides.yaml",
    "stem_rules.yaml",
    "semantic_tags.yaml",
    "stem_forms.yaml",
    "decisions.yaml",
)

#: The manifest's name inside the mirror directory.
MANIFEST = "MIRROR.md"

#: Written into the manifest, in English, because it is read in the other
#: repository. It is the whole point of the manifest.
WARNING = (
    "This directory is a mirror. The master is the murfulu repository and "
    "every change is made there; a change made here is lost at the next "
    "update and does not reach the rule pack anyone runs."
)


def digest(text: str) -> str:
    """A short content hash, so the manifest names what it copied."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class MirroredFile:
    """One file of the pack, as it will sit in the other repository."""

    name: str
    text: str

    @property
    def digest(self) -> str:
        """The content hash recorded in the manifest."""
        return digest(self.text)


@dataclass
class Mirror:
    """The whole mirror: the files, and the manifest describing them."""

    rule_pack_version: str = ""
    source_commit: str = ""
    files: list[MirroredFile] = field(default_factory=list)

    def manifest(self) -> str:
        """The provenance note that travels with the copy."""
        lines = [
            "# murfulu rule pack — mirror",
            "",
            WARNING,
            "",
            f"- rule pack version: `{self.rule_pack_version}`",
            f"- generated from murfulu commit: `{self.source_commit or 'unknown'}`",
            "",
            "| file | sha256 (first 12) |",
            "|---|---|",
        ]
        lines += [f"| `{one.name}` | `{one.digest}` |" for one in self.files]
        lines += [
            "",
            "To check this copy is current, compare these files with "
            "`rules/` in murfulu. They are byte-identical or the mirror is "
            "stale; there is no third state.",
            "",
        ]
        return "\n".join(lines)

    def as_written(self) -> dict[str, str]:
        """Every path in the mirror directory and what it should contain."""
        return {one.name: one.text for one in self.files} | {MANIFEST: self.manifest()}


@dataclass(frozen=True)
class Difference:
    """One file that does not match, and how."""

    name: str
    #: ``missing``, ``differs`` or ``extra``.
    state: str

    def __str__(self) -> str:
        """One line for the command's output."""
        return f"{self.name}: {self.state}"


def build(directory: Path, version: str, commit: str = "") -> Mirror:
    """Read the pack and produce the mirror it should be copied to."""
    files = []
    for name in MIRRORED:
        path = directory / name
        if not path.is_file():
            # A missing file is a fault in the pack, not in the mirror, and
            # copying seven of eight silently would hide it.
            raise FileNotFoundError(f"the rule pack has no {name}")
        files.append(MirroredFile(name=name, text=path.read_text(encoding="utf-8")))
    return Mirror(rule_pack_version=version, source_commit=commit, files=files)


def compare(mirror: Mirror, destination: Path) -> list[Difference]:
    """What differs between the mirror and what is already there.

    An empty list means the copy is current. The manifest is compared like any
    other file **except for its commit line**, which changes with every commit
    here and would report every mirror as stale.
    """
    wanted = mirror.as_written()
    differences: list[Difference] = []

    for name, text in wanted.items():
        path = destination / name
        if not path.is_file():
            differences.append(Difference(name, "missing"))
            continue
        found = path.read_text(encoding="utf-8")
        if name == MANIFEST:
            if _without_commit(found) != _without_commit(text):
                differences.append(Difference(name, "differs"))
        elif found != text:
            differences.append(Difference(name, "differs"))

    if destination.is_dir():
        for path in sorted(destination.iterdir()):
            if path.is_file() and path.name not in wanted:
                differences.append(Difference(path.name, "extra"))

    return differences


def _without_commit(manifest: str) -> str:
    """The manifest minus the line that changes on every commit."""
    return "\n".join(
        line
        for line in manifest.splitlines()
        if not line.startswith("- generated from murfulu commit:")
    )
