"""The liveness route the container healthcheck depends on.

It used to return a hardcoded `ok`. That is why it went on reporting a well
service through a walkthrough in which **every** build answered 500: the
lexicon snapshot could not be opened and nothing asked it to be. So the tests
here are mostly about the unhappy path, which is the only path that was ever
wrong.

The checks are patched rather than run, because the suite must pass with no
cluster and no snapshot — and a health test that needs a healthy system to run
tests nothing.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from murfulu.api import app as app_module
from murfulu.api.app import app


@pytest.fixture
def checks(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """The health checks, replaced with ones that pass."""
    patched: dict[str, Any] = {"lexicon": lambda: "ok", "elasticsearch": lambda: "ok"}
    monkeypatch.setattr(app_module, "CHECKS", patched)
    return patched


def test_health_reports_ok_when_both_halves_answer(checks: dict[str, Any]) -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["checks"] == {"lexicon": "ok", "elasticsearch": "ok"}


def test_a_dead_lexicon_is_not_reported_as_healthy(checks: dict[str, Any]) -> None:
    """S9: the snapshot cannot be opened and /generate answers 500."""

    def refuse() -> str:
        raise RuntimeError("unable to open database file")

    checks["lexicon"] = refuse

    response = TestClient(app).get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert "unable to open database file" in response.json()["checks"]["lexicon"]


def test_the_answer_says_which_half_is_down(checks: dict[str, Any]) -> None:
    """Naming the failing half is the whole point of checking two things."""

    def refuse() -> str:
        raise RuntimeError("the cluster did not answer")

    checks["elasticsearch"] = refuse

    parts = TestClient(app).get("/health").json()["checks"]

    assert parts["lexicon"] == "ok"
    assert parts["elasticsearch"].startswith("failed:")


def test_one_check_failing_does_not_stop_the_other_running(
    checks: dict[str, Any],
) -> None:
    """Both are reported, so a reader is never told to fix them one at a time."""

    def refuse() -> str:
        raise RuntimeError("down")

    checks["lexicon"] = refuse
    checks["elasticsearch"] = refuse

    parts = TestClient(app).get("/health").json()["checks"]

    assert set(parts) == {"lexicon", "elasticsearch"}
    assert all(state.startswith("failed:") for state in parts.values())


def test_openapi_renders() -> None:
    response = TestClient(app).get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "murfulu"
