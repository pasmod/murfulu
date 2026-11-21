"""The reading screen's three questions: which text, what it says, what was marked.

    GET /texts?q=حافظ غزل ۳            texts whose heading holds every word
    GET /texts/marked                  readings marked wrong, newest first
    GET /texts/marked?kind=proposed    readings picked or typed for a word in a line
    GET /texts/unsure                  the spellings most often left to a person
    GET /texts/unsure/{spelling}       one of them, and the readings decided for it
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

**A reading decided for every like place of a spelling** (2026-11-21) goes the
same way again, with ``kind: reading_decided`` and its scope in ``context``
(:mod:`murfulu.behnevis.decided`): everywhere, or after or before one word. A
decision taken back is one more record, ``withdrawn``, with ``verdict:
unsure``. The model reads the decisions in force at its next build; until
then these routes only say what was decided.
"""

from __future__ import annotations

from typing import Any

from elasticsearch import ApiError, NotFoundError, TransportError
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, or_, select

from murfulu.api.auth import Caller, Store
from murfulu.behnevis import decided
from murfulu.behnevis import serve as behnevis
from murfulu.behnevis.transcribe import key
from murfulu.behnevis.vowels import vocalise, vocalise_written
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
    spelling = context.get("spelling_fa") or spelling
    latin = context.get("latin") or latin
    written = context.get("written")
    return {
        "id": row.id,
        "target_id": row.target_id,
        "spelling_fa": spelling,
        # The spelling and the word as written with this reading's short
        # vowels, for display only; the plain ones stay the keys (DECISIONS
        # 2026-11-21). A source's own marks are never replaced.
        "spelling_fa_marked": vocalise(spelling, latin) if spelling and latin else None,
        "latin": latin,
        "written": written,
        "written_marked": (
            vocalise_written(written, latin) if written and latin else None
        ),
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
    if kind == "proposed":
        # A reading decided for every like place is not a pick for one word
        # (2026-11-21): it is listed by `/texts/unsure`, and a decision taken
        # back must not stay under the word it was made from.
        decision = ExpertFeedback.context["kind"].as_string()
        where.append(or_(decision.is_(None), decision != decided.KIND))
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


def _decisions(
    session: Any, spellings: set[str] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """The decisions in force, by keyed spelling, newest first.

    Read whole and reduced here (:func:`decided.current`): decisions are few,
    a spelling is stored as the screen counted it, and only the newest for
    each spelling and scope is in force.
    """
    rows = session.scalars(
        select(ExpertFeedback).where(
            ExpertFeedback.target_type == "lexicon_entry",
            ExpertFeedback.context["kind"].as_string() == decided.KIND,
        )
    )
    found: list[decided.Decision] = []
    by_id: dict[int, ExpertFeedback] = {}
    for row in rows:
        one = decided.from_record(row.context or {}, row.id)
        if one is not None and (spellings is None or one.spelling in spellings):
            found.append(one)
            by_id[row.id] = row
    out: dict[str, list[dict[str, Any]]] = {}
    for one in decided.current(found):
        row = by_id[one.order]
        context = row.context or {}
        out.setdefault(one.spelling, []).append(
            {
                "id": row.id,
                "latin": one.latin,
                "scope": one.scope,
                # As the screen sent it, half-spaces and all, for display.
                "scope_word": context.get("scope_word") if one.word else None,
                "in_bank": context.get("in_bank"),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )
    return out


def _listed() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The measured list, or a 503 that says it is not there."""
    found = behnevis.unsure_list()
    if found is None:
        raise HTTPException(
            503, "the list of unsure spellings has not been measured for this model"
        )
    return found


@router.get("/texts/unsure")
def unsure_spellings(
    _who: Caller,
    session: Store,
    kind: str | None = Query(
        None,
        pattern="^(choice|one|missing)$",
        description="only spellings needing this kind of decision",
    ),
    offset: int = Query(0, ge=0),
    size: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    """The spellings the reading screen most often leaves to a person, the most first.

    Measured by ``tools/measure_unsure_spellings.py`` over the whole corpus,
    as the screen reads it, and kept beside the model; each comes with the
    readings decided for it so far.
    """
    meta, listed = _listed()
    chosen = [one for one in listed if kind is None or one["kind"] == kind]
    page = chosen[offset : offset + size]
    decisions = _decisions(session, {one["spelling"] for one in page})
    return {
        "meta": meta,
        "total": len(chosen),
        "offset": offset,
        "size": size,
        "spellings": [
            {**one, "decided": decisions.get(one["spelling"], [])} for one in page
        ],
    }


@router.get("/texts/unsure/{spelling}")
def unsure_spelling(_who: Caller, session: Store, spelling: str) -> dict[str, Any]:
    """One spelling: its place in the list, if it is listed, and its decisions.

    The reading screen's word panel asks for it, to say how many places a
    decision would reach. A spelling outside the list, or a model without
    one, still answers, with ``listed: null``.
    """
    keyed = key(spelling)
    found = behnevis.unsure_list()
    listed = None
    if found is not None:
        listed = next((one for one in found[1] if one["spelling"] == keyed), None)
    return {
        "spelling": keyed,
        "listed": listed,
        "decided": _decisions(session, {keyed}).get(keyed, []),
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
        # The poem's metre weighs each verse half's readings, where it is known
        # and the step is on (DECISIONS 2026-11-21).
        metre = behnevis.metre_of(document_id)
        behnevis.annotate(found["units"], transcriber, metre)
        found["behnevis"] = {"sure": behnevis.SURE, "mid": behnevis.MID, "metre": metre}
    else:
        found["behnevis"] = None
    return found
