"""Where the database is.

The URL is configuration, never a literal in the code, for the same reason the
lexicon path is: the container, the test run and a developer's machine all
point somewhere different and none of them may require an edit.
"""

from __future__ import annotations

import os

#: Environment variable holding the connection URL.
URL_VARIABLE = "MURFULU_DATABASE_URL"

#: What ``postgresql://`` is rewritten to. SQLAlchemy reads a bare
#: ``postgresql://`` as psycopg *2*, which is not what we install, and the
#: failure is an import error a long way from the URL that caused it.
_DRIVER = "postgresql+psycopg://"

_BARE = "postgresql://"


class DatabaseNotConfiguredError(RuntimeError):
    """Raised when no URL was given and none is in the environment."""


def resolve_url(url: str | None = None) -> str:
    """Return the connection URL, from the argument or from the environment."""
    configured = url or os.environ.get(URL_VARIABLE)
    if not configured:
        raise DatabaseNotConfiguredError(
            f"no database URL given and {URL_VARIABLE} is not set"
        )
    return with_driver(configured)


def with_driver(url: str) -> str:
    """Name the driver explicitly, leaving any other URL untouched.

    ``docker-compose.yml`` writes the plain form because that is what a
    Postgres URL looks like everywhere else. Rewriting it here means the
    compose file stays readable and no other component has to know which
    driver we install.
    """
    if url.startswith(_BARE):
        return _DRIVER + url[len(_BARE) :]
    return url
