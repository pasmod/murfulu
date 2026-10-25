"""Who is calling. Since 2026-08-17 the answer is always the same account.

**There is no token and no role.** A reader used to need two credentials — the
site password to see anything and an expert API token to answer anything — and
the project lead's call is that this is one too many for a research app with
one reviewer. The password wall in front of the whole site is the whole of the
authentication now; everything behind it is :func:`murfulu.db.site.account`.

**What this module still does, and why it is not empty.** Routes ask for a
caller and get one, so nothing downstream had to learn that authorship went
away — feedback, rulings and proposals still record who made them, and are
still append-only for the same reason as before. And a store that cannot be
reached is still a 503 rather than a traceback, which was always the more
common failure of the two.

**What it no longer does is refuse anybody.** There is no 401 here and no 403.
The only door is Caddy's, and a second lock behind a locked door was protecting
the same person from themselves — see docs/REVIEW.md.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from murfulu.db.config import DatabaseNotConfiguredError
from murfulu.db.models.people import User
from murfulu.db.session import session_scope
from murfulu.db.site import account

_UNREACHABLE = "the authored store is not reachable"


def open_session() -> Iterator[Session]:
    """One database session for the length of one request.

    FastAPI resolves a dependency once per request, so the account is read and
    its record written in the same transaction.
    """
    try:
        with session_scope() as session:
            yield session
    except DatabaseNotConfiguredError as unconfigured:
        raise HTTPException(503, f"{_UNREACHABLE}: {unconfigured}") from None
    except SQLAlchemyError as unreachable:
        raise HTTPException(503, f"{_UNREACHABLE}: {unreachable}") from None


def caller(session: Annotated[Session, Depends(open_session)]) -> User:
    """The site account. Created on first use, never refused."""
    return account(session)


#: What a route asks for. ``Caller`` is the site account; ``Expert`` is the
#: same account and is kept as a name so that the routes which used to require
#: a role still read as the ones where a judgement is being recorded. ``Store``
#: is the session both used, so a route reads and writes in one transaction.
Caller = Annotated[User, Depends(caller)]
Expert = Annotated[User, Depends(caller)]
Store = Annotated[Session, Depends(open_session)]
