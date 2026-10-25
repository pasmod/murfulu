"""Who may do what, over HTTP. Since 2026-08-17 the answer is *everyone*.

This file used to be the done test for PLAN 6.3: an expert verdict refused for
a normal account, on the strength of the token rather than of what the request
body claimed. **Both the token and the role are gone.** A reader needed the
site password to see anything and an expert token to answer anything, and the
project lead's call is that a research app with one reviewer does not need two
credentials.

So what is checked here is the opposite of what it was, and one thing that did
not change: **the routes that read the rule pack still need nothing at all**,
and the store still answers 503 rather than a traceback when it is not there.

The wall itself is Caddy's and is not exercised here — it is in front of the
whole site, including this API, and `docs/DEPLOY.md` §6 is where it is checked.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from murfulu.api.app import app
from murfulu.db.models import Base, User
from murfulu.db.site import SITE_USERNAME, account

VERDICT = {
    "category": "linguistic",
    "target_type": "derivation",
    "target_id": "Raftorow:karnam",
    "verdict": "wrong",
    "note": "این واژه نیست",
}


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """An empty store. No accounts: the site account makes itself."""
    url = f"sqlite:///{tmp_path / 'authored.sqlite'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    monkeypatch.setenv("MURFULU_DATABASE_URL", url)
    yield url


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_a_verdict_needs_no_credential_at_all(client: TestClient, store: str):
    """The site password is the whole of the authentication."""
    made = client.post("/feedback", json=VERDICT)

    assert made.status_code == 201


def test_the_account_makes_itself_on_first_use(client: TestClient, store: str):
    """Nothing has to be set up first.

    An app that cannot record a verdict until somebody remembered to run a
    script is the failure this change removes.
    """
    body = client.get("/me").json()

    assert body["username"] == SITE_USERNAME
    assert body["may_leave_a_verdict"] is True


def test_the_account_route_says_nothing_about_who_else_is_there(
    client: TestClient, store: str
):
    """The handle and the permission, and no more.

    There is nobody else, and a route that listed accounts would be a
    directory.
    """
    body = client.get("/me").json()

    assert set(body) == {"username", "may_leave_a_verdict"}
    # The role went with the roles. A constant in this answer would read as a
    # distinction somebody still makes.
    assert "role" not in body


def test_every_record_carries_the_same_author(client: TestClient, store: str):
    """Authorship survives the change, which is why `users` was kept.

    It is also what was given up: one identity means inter-rater agreement
    cannot be measured across anything recorded from here on.
    """
    for _ in range(2):
        assert client.post("/feedback", json=VERDICT).status_code == 201
    asked = {"target_type": "derivation", "target_id": "Raftorow:karnam"}
    rows = client.get("/feedback", params=asked).json()

    authors = {row["author_id"] for row in rows["feedback"]}
    assert len(authors) == 1


def test_an_existing_account_is_adopted_rather_than_joined(
    client: TestClient, store: str
):
    """A store from before the change keeps writing under its first account.

    Otherwise the history splits at an upgrade: records made either side of it
    would point at different authors for the same person.
    """
    engine = create_engine(store)
    with Session(engine) as session:
        session.add(User(username="expert-1"))
        session.commit()
    engine.dispose()

    body = client.get("/me").json()

    assert body["username"] == "expert-1"


def test_the_site_account_is_created_once_not_per_request(store: str):
    """Two calls must not leave two rows behind."""
    engine = create_engine(store)
    with Session(engine) as session:
        first = account(session).id
        session.commit()
    with Session(engine) as session:
        second = account(session).id
        session.commit()
    with Session(engine) as session:
        assert first == second
        assert session.query(User).count() == 1
    engine.dispose()


def test_the_search_routes_stay_open(client: TestClient, store: str):
    """Reading the rule pack needs no store at all, and never did."""
    assert client.get("/rules").status_code == 200
    assert client.get("/affixes").status_code == 200


def test_a_store_that_is_not_there_is_a_503_not_a_traceback(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    """The commoner of the two failures, and the one still worth handling."""
    monkeypatch.delenv("MURFULU_DATABASE_URL", raising=False)

    assert client.get("/me").status_code == 503
