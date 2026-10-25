"""Opening a connection, and the unit of work around a write.

One engine per URL, because an engine holds a connection pool and building a
second one per request would open a second pool. Sessions are cheap and are
made per unit of work.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine
from sqlalchemy import create_engine as _create_engine
from sqlalchemy.orm import Session, sessionmaker

from murfulu.db.config import resolve_url


@lru_cache(maxsize=8)
def _engine_for(url: str, echo: bool) -> Engine:
    return _create_engine(url, echo=echo, future=True)


def create_engine(url: str | None = None, echo: bool = False) -> Engine:
    """The engine for one URL, built once and reused.

    The URL is resolved *before* the cache is consulted, so that pointing the
    environment at another database really does hand back another engine.
    Caching on the argument instead would cache ``None``.
    """
    return _engine_for(resolve_url(url), echo)


def session_factory(url: str | None = None) -> sessionmaker[Session]:
    """A factory making sessions against the configured database."""
    return sessionmaker(bind=create_engine(url), expire_on_commit=False)


@contextmanager
def session_scope(url: str | None = None) -> Iterator[Session]:
    """One unit of work: commit on success, roll back on anything else.

    The rollback matters more than usual here. Feedback is append-only, so a
    half-written batch cannot be tidied up afterwards by deleting it.
    """
    session = session_factory(url)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
