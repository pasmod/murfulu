"""The one account everything behind the password wall acts as.

**Why there is only one.** Until 2026-08-17 an account proved itself with an
API token and carried a role, and a reader needed two credentials to be useful:
the site password to see anything and an expert token to answer anything. The
project lead's call is that this is one credential too many for a research app
with one reviewer — so the wall is the whole of the authentication, and
everyone who passes it is this account.

**The wall is not weaker for it.** Caddy still refuses every request without
the password, and nothing but Caddy publishes a port. What has gone is a second
credential *behind* the first, which was protecting the same people from
themselves.

**The account survives, and that is deliberate.** Feedback, rulings and
proposals all point at an author, and they are append-only precisely so a
judgement keeps the person who made it. Removing the column would have thrown
away the authorship on records already stored, and would have made a later
change of mind unrecoverable. So there is exactly one row, everything points at
it, and adding accounts back is a migration rather than an archaeology.

**What was given up, stated plainly.** ``docs/REVIEW.md`` treats the feedback
set as a research artefact and its export carries a per-author pseudonym so
that two reviewers' verdicts on the same word can be compared. With one
identity there is only ever one rater, so **inter-rater agreement cannot be
measured** on anything recorded from now on. The nine rows collected before the
change keep their own authors and remain comparable.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from murfulu.db.models.people import User

#: The handle the single account answers to. A handle, never a person's name:
#: the repository is public and names no individuals.
SITE_USERNAME = "murfulu"


def account(session: Session) -> User:
    """The site account, created on first use.

    Created here rather than by a migration or a setup command, because an app
    that cannot record a verdict until somebody remembered to run a script is
    the failure this change exists to remove.

    **The oldest existing account is adopted if there is one.** A store that
    already holds accounts from before this change keeps writing under the
    first of them, so records made either side of the change point at the same
    author and the history does not split at an upgrade.
    """
    found = session.scalars(select(User).where(User.username == SITE_USERNAME)).first()
    if found is not None:
        return found
    existing = session.scalars(select(User).order_by(User.id)).first()
    if existing is not None:
        return existing
    made = User(username=SITE_USERNAME, display_name=None, active=True)
    session.add(made)
    session.flush()
    return made
