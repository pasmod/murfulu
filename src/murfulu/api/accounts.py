"""Who the caller is. Since 2026-08-17 that is always the same account.

One route, and it exists for one reason: **a screen has to know what the reader
may do before they write something.** It used to answer *may this token leave a
linguistic verdict*, because only an expert could, and offering the option to
everyone and refusing it afterwards loses a note somebody wrote in Persian to a
403.

**There are no roles now**, so the answer is always yes and the field stays
rather than being removed. A client that stopped asking would be a client that
cannot be told *no* again without being rewritten, and this project has already
reversed one decision about roles — a third one was added and taken out again
in a day. The permission is still named as a permission, and it is still
answered in one place instead of being derived in every screen.

It reports that and nothing else. No list of accounts: a route that answered
"who else is there" would be a directory, and there is nobody else.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from murfulu.api.auth import Caller

router = APIRouter(tags=["accounts"])


@router.get("/me")
def me(who: Caller) -> dict[str, Any]:
    """The site account, and what it may do."""
    return {
        "username": who.username,
        # True for everyone behind the password wall. Kept as a permission and
        # not as a role, so the sentence *who may grade a word* still lives in
        # one place — see the module docstring.
        "may_leave_a_verdict": True,
    }
