"""The authored side of the system: Postgres.

What lives here is what cannot be rebuilt by re-running a batch job — the
rule pack as loaded from YAML, the expert's verdicts, the accounts that gave
them, and the registry of corpus versions those verdicts were given under.
Everything countable and rebuildable lives in Elasticsearch instead; the rule
of thumb is in ``docs/ARCHITECTURE.md``.

What this module does **not** own:

- the derivation cache. ``docs/ARCHITECTURE.md`` sketches a ``derivations``
  table here and also says every live result is cached in the ``derivations``
  *index*. Only one of those can be true, and the index is the one that exists
  and is written by :mod:`murfulu.search.derivations`. A cache is rebuildable,
  so by the document's own rule it belongs in Elasticsearch. No table is
  created for it.
- authentication. Roles are stored; how someone proves who they are is PLAN
  task 6.3 and gets its own migration.

Schema changes go through Alembic migrations in ``migrations/``, never by hand
— see ``docs/ENGINEERING.md``.
"""

from murfulu.db.base import Base
from murfulu.db.config import URL_VARIABLE, DatabaseNotConfiguredError, resolve_url
from murfulu.db.session import create_engine, session_scope

__all__ = [
    "URL_VARIABLE",
    "Base",
    "DatabaseNotConfiguredError",
    "create_engine",
    "resolve_url",
    "session_scope",
]
