"""Compounds: what the pack can join to a word, and which of them anyone wrote.

Persian builds words by compounding at least as much as by affixation, and
**no compound has ever reached a reader here.** The ten template rules have
been implemented and uncalled since session 2; the six slot rules were built
in session 10 and nothing reached them either. This route is what reaches
them.

**The shape follows from a measurement, not from a preference.** One ordinary
noun makes 3,071 compounds and the corpus holds 0.5%–3.3% of them, so a route
that answered with all of them would be 97% noise. It answers with the
attested ones ranked, and says how many it built and set aside — the same
shape as a build group that opens at twenty and states what it folds. Nothing
is hidden; the whole list is one `attested=false` away.

**And an attested compound is marked, never trusted.** سخن's commonest hits
are سخنم and سخنش — *my word*, *his word* — because **میدن's present stem is
the single letter م**, and seven verbs have a one-letter present stem. Those
are possessives, not compounds. The inflection analyser built for S8 reads
them apart, and what it finds is written on the row rather than used to drop
it: which of the two a spelling is, is the linguist's question.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from murfulu import compounding
from murfulu.corpus import inflection
from murfulu.generation import WordNotFoundError
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import RulePack, loaded
from murfulu.scoring.attestation import Attestation, Index, Level
from murfulu.search.attested import look_up
from murfulu.search.indices import connect

router = APIRouter(tags=["compound"])

#: Attested pairings returned by default. The list is short by nature — a
#: noun's 3,071 compounds yield tens, not thousands — so this is a guard
#: against a pathological word rather than the usual case.
DEFAULT_LIMIT = 100


def _page(
    pairings: list[dict[str, Any]], offset: int, limit: int
) -> list[dict[str, Any]]:
    """One slice of a reading's pairings.

    ``limit=0`` means all of them, exactly as on ``/generate``.
    """
    if limit == 0:
        return pairings[offset:]
    return pairings[offset : offset + limit]


@lru_cache(maxsize=1)
def _partners(snapshot_id: str) -> compounding.Partners:
    """Every verb's two stems, read once per snapshot.

    Keyed on the snapshot id so a swapped lexicon is a different cache entry
    rather than a stale one. It is a full pass over 1,705 verbs and would
    otherwise be repeated on every request.
    """
    with Lexicon.open() as lexicon:
        return compounding.partners_from(lexicon)


@lru_cache(maxsize=1)
def _analyser(snapshot_id: str) -> inflection.Analyser:
    """The instrument that reads سخنم as سخن plus a possessive."""
    with Lexicon.open() as lexicon:
        held = inflection.held_from(lexicon)
    return inflection.Analyser(held=held, pack_suffixes=inflection.pack_suffixes())


def _evidence(found: Attestation | None) -> dict[str, Any] | None:
    """What the corpus says, or None when it was never asked.

    None and *not found* are different answers and are never made to look the
    same — the same rule `/generate` follows.
    """
    if found is None:
        return None
    return {
        "level": found.level.value,
        "corpus_version": found.corpus_version,
        "total_count": found.total_count,
        "doc_count": found.doc_count,
        "author_count": found.author_count,
        "first_century": found.first_century,
        "last_century": found.last_century,
        "unlinked": found.spelling_unlinked,
        "function_word": found.function_word or None,
        "wording": found.describe(),
    }


def _also_an_inflection(
    analyser: inflection.Analyser, spelling: str
) -> dict[str, Any] | None:
    """Whether these letters also read as an inflection of a word we hold.

    Reported, never acted on. **A `shared` reading is the common case** —
    6,730 of 7,047 attested built forms measured in session 10 were shared —
    so this marks a row rather than settling it.

    ``control`` rather than ``best``: the analyser refuses to call a spelling
    the lexicon holds an inflection, which is right when it is deciding what a
    corpus word *is* and wrong here. **دلم is a headword** and is also دل plus
    a possessive and also دل joined to میدن's one-letter present stem, and a
    reader weighing its 12,947 documents needs all three. The cost is stated:
    run over the lexicon's own headwords this reading fires on 7.5% of them.
    """
    reading = analyser.control(spelling)
    if reading is None:
        return None
    return {
        "base": reading.base,
        "pattern": reading.pattern.id,
        "label_fa": reading.pattern.label_fa,
        # A derivational rule in the pack writes the same letters, so the two
        # cannot be told apart by spelling alone. Which it is, is the
        # linguist's — see S8.
        "shared_with_rules": list(reading.shared_with),
        "is_shared": reading.is_shared,
    }


def _attested(found: Attestation | None) -> bool:
    """Whether the corpus actually has it.

    `look_up` answers for every spelling it is asked about and says `none`
    where it found nothing, so a missing hit is an `Attestation` and not a
    `None`. Filtering on `is not None` counts every form as attested — which
    it did, and دل reported 5,223 of 5,223.

    Not where the letters are a function word's: written, but as another word,
    and nothing about this one is known (murfulu.corpus.function_words).
    """
    return (
        found is not None and found.level is not Level.NONE and not found.function_word
    )


def _asked(pairings: list[compounding.Pairing]) -> Index | None:
    """Ask the corpus about every compound in one query.

    A cluster that is not there is not a failure of compounding: the rules
    still say what may be joined. Every pairing then carries no attestation at
    all, which reads as *not checked* rather than *not found*.
    """
    from elasticsearch import ApiError, TransportError

    spellings = {pairing.fa for pairing in pairings}
    if not spellings:
        return None
    try:
        return look_up(connect(), spellings)
    except (ApiError, TransportError, OSError):
        return None


def _row(
    pairing: compounding.Pairing,
    pack: RulePack,
    found: Attestation | None,
    inflected: dict[str, Any] | None,
    already_a_word: bool,
) -> dict[str, Any]:
    rule = pack.by_id(pairing.rule_id)
    return {
        "form_latin": pairing.latin,
        "form_fa": pairing.fa,
        "word_class": pairing.word_class,
        "rule_id": pairing.rule_id,
        "label_fa": getattr(rule, "label_fa", None),
        "explanation_fa": rule.explanation_fa,
        # **What each half is, not only what it says.** A row read
        # `دست + ور ← کارنده‌کاربهر V-078` and a reader had no way to see that
        # ور is there as a کاربن دو, still less that it is the present stem of
        # وشتن. Both are on the pairing already; serving them is what lets the
        # screen show the rule being applied rather than its result.
        "front": {
            "fa": pairing.front_fa,
            "latin": pairing.front_latin,
            "type": pairing.front_class or None,
        },
        "behind": {
            "fa": pairing.behind_fa,
            "latin": pairing.behind_latin,
            "type": pairing.behind_class or None,
            # The infinitive the stem was read off. Absent on the template
            # rules, where both halves come from the reader's own verb.
            "of": (
                {"fa": pairing.behind_of_fa, "latin": pairing.behind_of_latin}
                if pairing.behind_of_fa
                else None
            ),
        },
        "role": pairing.role,
        "attestation": _evidence(found),
        "is_attested": _attested(found),
        # Present only where the letters also read as an inflection. Absent is
        # the ordinary case and means nothing was found, not that nothing was
        # looked for — the analyser runs on every attested row.
        "also_an_inflection": inflected,
        # The dictionary already holds this exact spelling. **This is
        # confirmation, not doubt, and it does not sink the row.** دلبر is a
        # headword and is also دل + بر, and those are the same word — the
        # session 9 rule about a count belonging elsewhere is about
        # homographs, where the lexicon reads the spelling as something else.
        # What it does tell a coiner is that this one is taken.
        "already_a_word": already_a_word,
    }


def _ranked(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attested first, then by weight of evidence; inflection-shaped rows last.

    The order follows the one settled for built words: what the corpus has
    outranks what it does not, then the document count.

    **Only one thing sinks a row: its letters also reading as an inflection.**
    دلم carries 12,947 documents and is دل plus a possessive, so its number is
    about a different morphological object and must not put it first. Being
    already in the dictionary does **not** sink anything — دلبر is a headword
    *and* is دل + بر, the same word by both routes, and a coiner wants to see
    it near the top precisely because it proves the pattern works.

    Sinking is what this project does instead of hiding: دلبر and دلم both
    stay on the list, and the difference between them is on the row.
    """

    def key(row: dict[str, Any]) -> tuple[Any, ...]:
        found = row["attestation"]
        return (
            not row["is_attested"],
            row["also_an_inflection"] is not None,
            -(found["doc_count"] if found else 0),
            row["form_latin"],
        )

    return sorted(rows, key=key)


def _distinct(pairings: list[compounding.Pairing]) -> list[compounding.Pairing]:
    """Drop pairings that are the same join by the same rule.

    Two verbs can share a stem spelling — ستان is the present stem of more
    than one — and each produced its own identical row. Two *rules* writing
    the same letters is kept, because V-078 and V-079 mean the doer and the
    done-to and that is information rather than noise.
    """
    seen = set()
    kept = []
    for pairing in pairings:
        key = (
            pairing.fa,
            pairing.latin,
            pairing.rule_id,
            pairing.front_latin,
            pairing.behind_latin,
        )
        if key in seen:
            continue
        seen.add(key)
        kept.append(pairing)
    return kept


@router.get("/compound")
def compound(
    word: str = Query(..., description="a Persian word, or its Latin reading"),
    partner: str | None = Query(
        None,
        description="a second word to join it to; needed for the two-sided rules",
    ),
    attested: bool = Query(
        True, description="only the pairings the corpus has; false returns every one"
    ),
    limit: int = Query(DEFAULT_LIMIT, ge=0, le=5000, description="rows; 0 for all"),
    offset: int = Query(0, ge=0, description="skip this many pairings of each reading"),
) -> dict[str, Any]:
    """Every compound the pack licenses for this word.

    A slot rule pins one side to your word and takes any verb stem on the
    other, which is a **sum** — 3,071 of them — rather than a product over the
    dictionary. The rules with two free sides need `partner`, because over the
    whole lexicon they are 43,225 against themselves.

    **Paged the way `/generate` is**, with the same three fields — `offset`,
    `returned` and `has_more`. It took a `limit` and no `offset` until
    2026-08-15, so a word with more compounds than the limit had the rest of
    its list unreachable by any request.
    """
    pack = loaded()
    try:
        with Lexicon.open() as lexicon:
            snapshot = lexicon.snapshot_id
            results = (
                compounding.from_two_words(lexicon, pack, word, partner)
                if partner
                else compounding.from_word(lexicon, pack, word, _partners(snapshot))
            )
    except WordNotFoundError as absent:
        raise HTTPException(404, str(absent)) from None
    except Exception as unavailable:  # noqa: BLE001 - reported, never swallowed
        raise HTTPException(
            503, f"the lexicon is not readable: {unavailable}"
        ) from None

    analyser = _analyser(snapshot)
    readings = []
    for result in results:
        pairings = _distinct(result.pairings)
        corpus = _asked(pairings)
        rows = []
        for pairing in pairings:
            found = corpus.look_up(pairing.fa, pairing.latin) if corpus else None
            # Only a row with a number behind it is worth doubting: the two
            # checks exist to say whose number it is.
            checked = _attested(found)
            rows.append(
                _row(
                    pairing,
                    pack,
                    found,
                    _also_an_inflection(analyser, pairing.fa) if checked else None,
                    analyser.held.holds(pairing.fa) if checked else False,
                )
            )
        held = [row for row in rows if row["is_attested"]]
        shown = _ranked(held if attested else rows)
        page = _page(shown, offset, limit)
        readings.append(
            {
                "latin": result.reading.latin,
                "spelling_fa": result.reading.spelling_fa,
                "lexicon_category": result.reading.lexicon_category,
                "needs_review": result.reading.needs_review,
                # The three numbers that make the shown list readable: what was
                # built, what the corpus has, and how many partners were tried.
                # A list of forty means nothing without the 3,071 behind it.
                "built": len(rows),
                "attested": len(held),
                "unattested": len(rows) - len(held),
                "partners_tried": result.partners_tried,
                # Which kinds of compounding this reading could not reach, and
                # why. A noun cannot fill a template; that is not an empty
                # result, it is a different question.
                "skipped": result.skipped,
                # **Why zero can be zero with nothing wrong.** کار is filed
                # اسم معنی, which the source grammar makes a کارنام, and all
                # six slot rules take a نام — so the word is shut out of every
                # compounding rule in the pack (L18; 1,949 readings are in
                # this position). The screen showed «۰ ترکیب» and no reason.
                # Both sides of the mismatch travel so the sentence can be
                # written from the pack's own Persian.
                "word_classes": list(result.front_classes),
                "slot_wants": list(result.slot_wants),
                # The list this request is a window on, before the window is
                # cut: `built` and `attested` count everything, and `attested`
                # decides which of the two is being paged.
                "count": len(shown),
                "offset": offset,
                "returned": len(page),
                "has_more": offset + len(page) < len(shown),
                "pairings": page,
            }
        )

    return {
        "word": word,
        "partner": partner,
        "rule_pack_version": pack.version,
        "lexicon_snapshot_id": snapshot,
        "showing": "attested" if attested else "everything built",
        "readings": readings,
    }
