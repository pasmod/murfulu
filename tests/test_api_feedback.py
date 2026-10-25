"""The feedback route, end to end over HTTP.

Pointed at a SQLite file rather than Postgres, because the models are the same
on both and the route has no Postgres in it. What only Postgres can prove —
that the table refuses an UPDATE — is in ``test_db_live.py``.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from murfulu.api.app import app
from murfulu.db.models import Base


def _as(_who: str = "") -> dict[str, str]:
    """No credential at all. Kept so the call sites read unchanged.

    Every route behind the password wall is open as of 2026-08-17 — there is
    one account and no roles. See murfulu.db.site.
    """
    return {}


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    url = f"sqlite:///{tmp_path / 'authored.sqlite'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    monkeypatch.setenv("MURFULU_DATABASE_URL", url)
    yield TestClient(app)


VERDICT = {
    "category": "linguistic",
    "target_type": "derivation",
    "target_id": "Raftorow:karnam",
    "verdict": "wrong",
    "note": "این واژه نیست",
    "context": {"form_fa": "رفت‌ورو", "rule_chain": ["V-046"]},
    "corpus_version": "v3",
}


def test_a_verdict_is_stored_and_comes_back(client: TestClient):
    written = client.post("/feedback", json=VERDICT, headers=_as())
    assert written.status_code == 201, written.text
    assert written.json()["owner"] == "murfulu"

    read = client.get(
        "/feedback",
        params={"target_type": "derivation", "target_id": "Raftorow:karnam"},
        headers=_as(),
    ).json()
    assert read["returned"] == 1
    stored = read["feedback"][0]
    assert stored["verdict"] == "wrong"
    assert stored["note"] == "این واژه نیست"
    assert stored["context"]["rule_chain"] == ["V-046"]
    assert stored["corpus_version"] == "v3"
    assert stored["created_at"]


def test_anyone_behind_the_wall_may_report_a_bug(client: TestClient):
    reported = client.post(
        "/feedback",
        json={
            "category": "bug",
            "target_type": "app",
            "note": "the search button does nothing",
            "context": {"screen": "search"},
        },
        headers=_as(),
    )
    assert reported.status_code == 201
    assert reported.json()["verdict"] is None


def test_feedback_about_the_lexicon_is_filed_under_karbon(client: TestClient):
    client.post(
        "/feedback",
        json={
            "category": "data",
            "target_type": "lexicon_entry",
            "target_id": "پهن",
            "note": "the reading should be pahn, not pen",
        },
        headers=_as(),
    )
    theirs = client.get("/feedback", params={"owner": "karbon"}, headers=_as()).json()
    assert [row["target_id"] for row in theirs["feedback"]] == ["پهن"]
    ours = client.get("/feedback", params={"owner": "murfulu"}, headers=_as()).json()
    assert ours["returned"] == 0


def test_a_bug_report_may_not_carry_a_verdict(client: TestClient):
    refused = client.post(
        "/feedback",
        json={"category": "bug", "target_type": "app", "verdict": "good"},
        headers=_as(),
    )
    assert refused.status_code == 400


def test_a_linguistic_note_without_a_verdict_is_refused(client: TestClient):
    refused = client.post("/feedback", json={**VERDICT, "verdict": None}, headers=_as())
    assert refused.status_code == 400


def test_an_unknown_verdict_is_named_in_the_refusal(client: TestClient):
    refused = client.post(
        "/feedback", json={**VERDICT, "verdict": "excellent"}, headers=_as()
    )
    assert refused.status_code == 400
    assert "unsure" in refused.json()["detail"]


def test_an_unknown_target_type_is_refused(client: TestClient):
    refused = client.post(
        "/feedback", json={**VERDICT, "target_type": "poem"}, headers=_as()
    )
    assert refused.status_code == 400


def test_feedback_is_append_only_over_http(client: TestClient):
    """There is no route that edits or withdraws a record, and that is the point."""
    written = client.post("/feedback", json=VERDICT, headers=_as()).json()
    paths = {route.path for route in app.routes}
    assert "/feedback/{feedback_id}" not in paths
    for method in ("put", "patch", "delete"):
        answered = getattr(client, method)(f"/feedback/{written['id']}", headers=_as())
        assert answered.status_code in {404, 405}


def test_with_no_database_configured_the_route_says_so(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("MURFULU_DATABASE_URL", raising=False)
    answered = TestClient(app).get("/feedback", headers={"Authorization": "Bearer x"})
    assert answered.status_code == 503
    assert "not reachable" in answered.json()["detail"]
