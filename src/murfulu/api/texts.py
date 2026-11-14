"""The reading screen's three questions: which text, what it says, what was marked.

    GET /texts?q=حافظ غزل ۳            texts whose heading holds every word
    GET /texts/marked                  readings marked wrong, newest first
    GET /texts/marked?kind=proposed    readings picked or typed for a word in a line
    GET /texts/{document_id}?start=0   one text, word by word, with readings

Thin, like every route: the work is :mod:`murfulu.search.texts`.

**A reading is marked wrong through the feedback store**, not a store of its
own: ``POST /feedback`` with ``category: linguistic``, ``verdict: wrong``,
``target_type: lexicon_entry`` and the reading's id (``spelling:latin``) as the
target. That is what the store is for — a judgement of karbon's data, recorded
append-only, owned by karbon and exported to it, never fixed here. This route
only reads those records back for review.

**A reading picked or typed for a word in a line** goes the same way, with
``verdict: good``: "this reading is right here". The reading need not be in
the bank — that is what makes it a proposal for karbon (2026-11-14,
direction A). The model's reading and confidence go in ``context``.
"""

from __future__ import annotations

from typing import Any

from elasticsearch import ApiError, NotFoundError, TransportError
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from murfulu.api.auth import Caller, Store
from murfulu.behnevis import serve as behnevis
from murfulu.corpus import report
from murfulu.db.models.review import ExpertFeedback
from murfulu.lexicon import bank
from murfulu.search import texts
from murfulu.search.indices import connect

router = APIRouter(tags=["texts"])

_UNREACHABLE = "the search index is not reachable"

#: How many marked readings one page of the review list holds, and the most
#: one read may ask for.
MARKED_PAGE = 50
MARKED_LIMIT = 500


def _labels() -> dict[str, str]:
    """The linguist's group names by key, as the bank screen shows them."""
    return {key: group.label_fa for key, group in bank.loaded().groups.items()}


@router.get("/texts")
def find(
    q: str = Query(
        ..., min_length=1, max_length=120, description="author, work, title"
    ),
    offset: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Texts whose heading holds every word typed, the best match first."""
    try:
        found = texts.find(connect(), q, offset=offset, size=size)
    except NotFoundError:
        raise HTTPException(503, "index 'documents' has not been built") from None
    except (ApiError, TransportError, OSError) as unreachable:
        raise HTTPException(503, f"{_UNREACHABLE}: {unreachable}") from None
    return {"q": q, "offset": offset, "size": size, **found}


def _marked(row: ExpertFeedback) -> dict[str, Any]:
    context = row.context or {}
    spelling, _, latin = (row.target_id or "").partition(":")
    return {
        "id": row.id,
        "target_id": row.target_id,
        "spelling_fa": context.get("spelling_fa") or spelling,
        "latin": context.get("latin") or latin,
        "written": context.get("written"),
        "document_id": context.get("document_id"),
        "unit": context.get("unit"),
        # Where in the unit, so the reading screen can show a saved pick under
        # its word: the line and the word's place in it (sent since
        # 2026-11-14), and the neighbours for the proposals saved before that.
        "line": context.get("line"),
        "word": context.get("word"),
        "before": context.get("before"),
        "after": context.get("after"),
        "heading": context.get("heading"),
        # A proposal also says what the model had read there, and whether the
        # proposed reading is in the bank at all.
        "model_latin": context.get("model_latin"),
        "model_confidence": context.get("model_confidence"),
        "in_bank": context.get("in_bank"),
        "note": row.note,
        "corpus_version": row.corpus_version,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/texts/marked")
def marked(
    _who: Caller,
    session: Store,
    spelling: str | None = Query(
        None, max_length=60, description="only the marks on this spelling's readings"
    ),
    kind: str = Query(
        "wrong",
        pattern="^(wrong|proposed)$",
        description="readings marked wrong, or readings proposed for a word in a line",
    ),
    document_id: str | None = Query(
        None, max_length=200, description="only what was marked or proposed here"
    ),
    unit_from: int | None = Query(None, ge=0, description="only from this unit on"),
    unit_to: int | None = Query(None, ge=0, description="only up to this unit"),
    offset: int = Query(0, ge=0),
    limit: int = Query(MARKED_PAGE, ge=1, le=MARKED_LIMIT),
) -> dict[str, Any]:
    """Readings marked wrong, from this screen or any other, newest first.

    Kept apart from ``GET /feedback`` so the list can be read the way the
    linguist reviews it: one row per mark, with the word and where it stood.
    Paged, with the total, so no mark falls off the end of the list; and
    asked for one spelling at a time by a word's panel, so a reading marked
    long ago still shows as marked however many marks came after it; or for
    one text, so the reading screen shows the readings saved in it.
    """
    where = [
        ExpertFeedback.target_type == "lexicon_entry",
        ExpertFeedback.verdict == ("wrong" if kind == "wrong" else "good"),
    ]
    if spelling:
        # A reading's id is `spelling:latin`; the spelling's marks start so.
        escaped = spelling.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where.append(ExpertFeedback.target_id.like(f"{escaped}:%", escape="\\"))
    if document_id:
        # The reading screen asks for what was saved in the text it shows.
        where.append(ExpertFeedback.context["document_id"].as_string() == document_id)
    # The units of the window the reading screen shows.
    if unit_from is not None:
        where.append(ExpertFeedback.context["unit"].as_integer() >= unit_from)
    if unit_to is not None:
        where.append(ExpertFeedback.context["unit"].as_integer() <= unit_to)
    total = session.scalar(
        select(func.count()).select_from(ExpertFeedback).where(*where)
    )
    statement = (
        select(ExpertFeedback)
        .where(*where)
        .order_by(ExpertFeedback.id.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = [_marked(row) for row in session.scalars(statement)]
    return {
        "total": total or 0,
        "offset": offset,
        "returned": len(rows),
        "marked": rows,
    }


@router.get("/texts/{document_id}")
def read(
    document_id: str,
    start: int = Query(0, ge=0, description="the first unit to return"),
    limit: int = Query(texts.DEFAULT_UNITS, ge=1, le=texts.MAX_UNITS),
) -> dict[str, Any]:
    """One text, a window of its units, word by word, with every reading."""
    try:
        found = texts.read(connect(), document_id, _labels(), start=start, limit=limit)
    except NotFoundError:
        raise HTTPException(404, f"no text {document_id!r}") from None
    except (ApiError, TransportError, OSError) as unreachable:
        raise HTTPException(503, f"{_UNREACHABLE}: {unreachable}") from None
    # What the source is called, for the source line: a fact about the
    # source, read the way the corpus screen reads it.
    found["source_name_fa"] = report.NAME_FA_BY_SOURCE.get(found.get("source_id") or "")
    # The model's reading of each word, when a model is configured.
    transcriber = behnevis.loaded()
    if transcriber is not None:
        behnevis.annotate(found["units"], transcriber)
        found["behnevis"] = {"sure": behnevis.SURE, "mid": behnevis.MID}
    else:
        found["behnevis"] = None
    return found
