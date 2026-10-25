"""The FastAPI application object and its liveness route.

Only wiring lives here. Feature routes are added as routers and hold no logic
themselves — see the package docstring.
"""

from typing import Any

from fastapi import FastAPI, Response, status

from murfulu import __version__
from murfulu.api import (
    accounts,
    compound,
    feedback,
    generate,
    proposals,
    rules,
    rulings,
    search,
)
from murfulu.lexicon.store import Lexicon
from murfulu.search.indices import connect

app = FastAPI(
    title="murfulu",
    version=__version__,
    description="Persian word generation from stems and word-formation rules",
)

app.include_router(rules.router)
app.include_router(generate.router)
app.include_router(compound.router)
app.include_router(rulings.router)
app.include_router(search.router)
app.include_router(feedback.router)
app.include_router(accounts.router)
app.include_router(proposals.router)


def _lexicon_reads() -> str:
    """Read one row out of the snapshot, or say why that failed.

    A count is not a formality here. The snapshot is in SQLite **WAL** journal
    mode and `./data` is mounted read-only, so a reader that cannot find the
    `-shm` file beside it cannot open the database at all — and the failure
    arrives as a 500 from `/generate` rather than from anything that looks like
    the lexicon. See S9.
    """
    with Lexicon.open() as lexicon:
        lexicon.count_active()
    return "ok"


def _cluster_answers() -> str:
    """Ask Elasticsearch whether it is there, without reading a document."""
    if not connect().ping():
        raise RuntimeError("the cluster did not answer")
    return "ok"


#: What `/health` checks, in the order it reports them. Each is a callable
#: that returns "ok" or raises; the reason travels back as the value, so a
#: reader is told *which* half is down rather than only that something is.
CHECKS = {"lexicon": _lexicon_reads, "elasticsearch": _cluster_answers}


@app.get("/health")
def health(response: Response) -> dict[str, Any]:
    """Report whether the service can do its work, not merely that it is up.

    It used to return a hardcoded `ok`, so it went on saying so while every
    build answered 500 — the exact failure recorded as S9, and the mirror of
    the `web` healthcheck that reported unhealthy through two hours of serving
    200. **A signal that cannot be wrong is not a signal**, so this one reads
    a row and asks the cluster, and answers 503 when either refuses.
    """
    parts: dict[str, str] = {}
    for name, check in CHECKS.items():
        try:
            parts[name] = check()
        except Exception as error:  # noqa: BLE001 — any failure is a failure
            parts[name] = f"failed: {error}"
    unwell = [name for name, state in parts.items() if state != "ok"]
    if unwell:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "degraded" if unwell else "ok",
        "version": __version__,
        "checks": parts,
    }
