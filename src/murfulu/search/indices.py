"""Create indices and move aliases.

Nothing ever writes to a live index. A pipeline run builds
``word_types-v3``, fills it, and only then does the alias ``word_types`` swap
across in one atomic step. So a rebuild cannot half-replace what the app is
serving, the previous version stays queryable until it is deliberately dropped,
and every attestation figure stays tied to the version that produced it.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from elasticsearch import Elasticsearch

from murfulu.search.mappings import MAPPINGS, SETTINGS

#: Where Elasticsearch is. Configuration, never a literal in the code.
URL_VARIABLE = "MURFULU_ELASTICSEARCH_URL"
DEFAULT_URL = "http://localhost:9200"

#: A corpus version is a short, file-safe token: ``v1``, ``2026-08-11``.
_VERSION_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class UnknownIndexError(KeyError):
    """Raised for an alias that is not one of the three we define."""


def index_name(alias: str, version: str) -> str:
    """The concrete index behind an alias, e.g. ``word_types-v3``."""
    if alias not in MAPPINGS:
        raise UnknownIndexError(
            f"{alias!r} is not one of {', '.join(sorted(MAPPINGS))}"
        )
    if not _VERSION_PATTERN.match(version):
        raise ValueError(
            f"corpus version {version!r} must be lower-case and start with a "
            f"letter or digit"
        )
    return f"{alias}-{version}"


def connect(url: str | None = None) -> Elasticsearch:
    """Open a client against the configured cluster."""
    return Elasticsearch(url or os.environ.get(URL_VARIABLE) or DEFAULT_URL)


@dataclass
class IndexAdmin:
    """Create, fill and release versioned indices."""

    client: Elasticsearch

    def create(self, alias: str, version: str) -> str:
        """Create the concrete index for one alias and version."""
        name = index_name(alias, version)
        self.client.indices.create(
            index=name, mappings=MAPPINGS[alias], settings=SETTINGS
        )
        return name

    def create_all(self, version: str) -> list[str]:
        """Create all three indices for a corpus version."""
        return [self.create(alias, version) for alias in sorted(MAPPINGS)]

    def release(self, alias: str, version: str) -> str:
        """Point the alias at this version, atomically.

        The remove and the add go in one request. There is no moment where the
        alias points at nothing, and no moment where it points at two indices.
        """
        name = index_name(alias, version)
        actions: list[dict[str, Any]] = []
        for existing in self.indices_behind(alias):
            actions.append({"remove": {"index": existing, "alias": alias}})
        actions.append({"add": {"index": name, "alias": alias}})
        self.client.indices.update_aliases(actions=actions)
        return name

    def release_all(self, version: str) -> list[str]:
        """Swap all three aliases to one corpus version."""
        return [self.release(alias, version) for alias in sorted(MAPPINGS)]

    def indices_behind(self, alias: str) -> list[str]:
        """Which concrete indices the alias currently points at."""
        if not self.client.indices.exists_alias(name=alias):
            return []
        return sorted(self.client.indices.get_alias(name=alias).body)

    def current_version(self, alias: str) -> str | None:
        """The corpus version the alias is serving, or None."""
        behind = self.indices_behind(alias)
        return behind[0][len(alias) + 1 :] if behind else None

    def drop(self, alias: str, version: str) -> None:
        """Delete one old index. Deliberate — never part of a release."""
        self.client.indices.delete(index=index_name(alias, version))
