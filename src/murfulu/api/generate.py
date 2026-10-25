"""Build words from a Persian word, and explain any one of them.

``/generate`` is the whole system in one call: the lexicon says what the word
is, the rule pack says what may be done to it, the engine does it. The route
itself calls :mod:`murfulu.generation` and reshapes the answer — no rule, no
score and no query lives here.

Two things the response is careful to keep:

**One result per reading, never a merged pile.** مرد is *mard* and *mord*, two
different words, and merging them would invent a third.

**Every form carries its derivation.** A generated word that cannot state how
it was built is a bug, not a feature — that is the requirement the concept
documents state most insistently.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from functools import lru_cache
from statistics import median
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from murfulu import generation
from murfulu.engine.affix import Step
from murfulu.engine.dedupe import GroupedForm
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import Rule, RulePack, loaded
from murfulu.scoring import inflected, stored
from murfulu.scoring.attestation import Attestation, Index, Level
from murfulu.scoring.grounding import IsGrounded, grounded
from murfulu.scoring.semantics import loaded as semantics
from murfulu.scoring.spread import loaded as spread

router = APIRouter(tags=["generate"])

#: The deepest a request may ask for. The engine's own hard stop.
MAX_DEPTH = 5


def _step(pack: RulePack, step: Step, worded: bool = True) -> dict[str, Any]:
    """One rule application, said in a way a reader can follow.

    ``worded=False`` keeps the derivation and drops the wording: which rule,
    which affix, applied to what, and any stem change or glide. **The
    derivation itself is never optional** — a form that cannot say what built
    it is a defect here, settled after the *sāzāyi* incident — but the Persian
    label and explanation belong to the *rule*, not to the form, and repeating
    them once per step is what makes the answer unreadable in bulk: بلند at
    depth 2 carries 8,731 steps, and the sentences are 43% of the bytes. A
    caller that wants them fetches each rule once from ``/rules``.
    """
    if not worded:
        return {
            "rule_id": step.rule_id,
            "affix": step.affix,
            "applied_to": step.base_latin,
            "stem_form": step.stem_form,
            "glide_id": step.glide_id,
        }
    rule = pack.by_id(step.rule_id)
    return {
        "rule_id": step.rule_id,
        "affix": step.affix,
        "applied_to": step.base_latin,
        "label_fa": getattr(rule, "label_fa", None),
        "explanation_fa": rule.explanation_fa,
        # **What this rule means, which is often the only thing telling it
        # apart from its neighbours.** وارفتنی is built four ways, and all four
        # attach the same `vā-` to the same stem by the same mechanics —
        # V-070..V-073 share a word for word identical `explanation_fa`. What
        # separates them is the sense the prefix carries: پس، دوباره، باز،
        # آخشیج. The build screen printed the same sentence four times and the
        # reader could not see why there were four; the project lead asked what
        # it meant on 2026-08-18 and there was no answer on the screen.
        #
        # The Persian is the tag's own `gloss_fa`, read from the rule pack and
        # never written here. Only under `worded` — it is wording, and the
        # unworded shape exists precisely to keep 8,731 steps readable.
        "tags_fa": [
            found.gloss_fa
            for found in (
                pack.tag_for(label) for label in getattr(rule, "semantic_tags", ())
            )
            if found is not None
        ],
        # **This rule's own record, as counts rather than as a rate.**
        # The form-level `realisation` is a *median* over the chain, chosen so
        # one number can rank a list — and read as a sentence it describes no
        # rule in it. وارفته's two steps realise 0.67% and 9.18%; their median,
        # 4.9%, is true of neither. Asked what «۱۰۰ واژه» meant on 2026-08-18
        # the answer was that there was no hundred: the denominators are 5,196
        # and 6,926. So the screen gets what was counted and does the arithmetic
        # nowhere.
        #
        # `null` where the run never measured this rule — never a zero, which
        # would read as *this rule has made nothing*.
        "built": _rule_counts(step.rule_id),
        # Set when the base is written one way and behaves another — *row*
        # becoming *rav*. Shown, so nothing changes silently.
        "stem_form": step.stem_form,
        "glide_id": step.glide_id,
        "glide_alternatives": list(step.glide_alternatives),
        # What the source says this rule takes beyond its word class, and
        # whether this base met it. **null is not false**: most rules state no
        # such condition, and two state one nobody has ruled on yet.
        "condition_met": step.condition_met,
        "condition_text": step.condition_text or None,
    }


def _rule_counts(rule_id: str) -> dict[str, Any] | None:
    """How many words one rule built, and how many of them the corpus has.

    Counts, never a rate: a reader can check *5,196 built, 35 found* against
    the rule and disagree with it. A percentage asks them to trust a method
    they were never shown, and 0.67% happens to be an **ordinary** rule on this
    corpus, which is the opposite of how it reads.
    """
    row = stored.loaded().for_rule(rule_id)
    if row is None or not row.get("measured"):
        return None
    return {
        "types": row.get("types_built"),
        "attested": row.get("types_attested"),
        "corpus_version": row.get("corpus_version") or "",
    }


def _evidence(attestation: Attestation | None) -> dict[str, Any] | None:
    """What the corpus says about a built form, or nothing if it was not asked.

    ``None`` and *not found* are different answers and must not look the same:
    the first means the corpus was never consulted, the second that it was and
    the word is not in it.
    """
    if attestation is None:
        return None
    return {
        "level": attestation.level.value,
        "corpus_version": attestation.corpus_version,
        "total_count": attestation.total_count,
        "doc_count": attestation.doc_count,
        "author_count": attestation.author_count,
        "first_century": attestation.first_century,
        "last_century": attestation.last_century,
        "other_readings": list(attestation.other_readings),
        "unlinked": attestation.spelling_unlinked,
        # The class of the function word these letters almost always are, or
        # null. When set the counts above are zero and mean *unknown*: the
        # occurrences are that word's (murfulu.corpus.function_words).
        "function_word": attestation.function_word or None,
        "wording": attestation.describe(),
    }


@lru_cache(maxsize=1)
def _stems_to_verbs() -> dict[str, tuple[str, ...]]:
    """Every verb stem in the snapshot, to the infinitives written on it.

    **A bare stem is not checkable.** The typical-bases list read «رو ۹۰٪ ·
    آور ۹۰٪ · هز ۹۰٪», and a reader who cannot place هز cannot judge whether
    the rule's centre is where we say it is. The infinitive is the name they
    know. One pass over the verbs, kept for the process: the file behind it
    does not change while the app runs.

    A stem can belong to more than one verb — ور is وشتن's here and نمودن and
    نماییدن share نما — so this maps to all of them and the caller decides how
    many to print.
    """
    found: dict[str, list[str]] = {}
    try:
        with Lexicon.open() as lexicon:
            for reading in lexicon.infinitives():
                for stem in (reading.past_stem_latin, reading.present_stem_latin):
                    if not stem:
                        continue
                    written = found.setdefault(stem, [])
                    if reading.spelling_fa not in written:
                        written.append(reading.spelling_fa)
    except Exception:  # noqa: BLE001 — a missing lexicon must not lose the score
        return {}
    return {stem: tuple(verbs) for stem, verbs in found.items()}


def _typicality(form: GroupedForm) -> dict[str, Any] | None:
    """The semantic part of the score for this form, or None.

    Measured on the **first step of the shortest path**: the base there is a
    dictionary stem with a precomputed vector, and the question is the one the
    pilot validated — does this base resemble the bases this rule usually
    takes? Deeper steps stand on generated intermediates that have no vector,
    and a made-up number is worse than none.
    """
    steps = form.shortest_path
    if not steps:
        return None
    first = steps[0]
    found = semantics().typicality(first.rule_id, first.base_latin)
    if found is None:
        return None
    # Where the score sits among all of them. The cosine never leaves the
    # middle on this corpus — 0.554 to 0.914, with the middle half between
    # 0.800 and 0.852 — so 84% reads as a good mark and is the median. The
    # band comes from a measured distribution (tools/measure_typicality_
    # spread.py); null where nothing has been measured, never a guess.
    measured = spread()
    centre = semantics().centre(found.rule_id)
    return {
        "typicality": found.score,
        "rule_id": found.rule_id,
        "base": found.base_latin,
        "bases_measured": found.bases,
        "band": measured.band_for(found.score),
        "median": measured.median,
        "lowest": measured.lowest,
        "highest": measured.highest,
        # **What the number is measured against, so it can be argued with.**
        # `Centre` was built for exactly this and nothing read it: *this rule's
        # centre was built from 67 bases and the nearest are these*. A bare 85%
        # asks a reader to know what a cosine is; شد ۹۱٪ · کرد ۸۹٪ · raft ۸۵٪
        # asks them only to read a list, and it says the true thing the bare
        # figure hid — raft is further out than every one of them.
        # The rule as the reader met it on every other row: its own sentence,
        # not only its id. The block used to say «دستور V-034» and leave the
        # reader to remember what V-034 was.
        "rule_says_fa": getattr(loaded().by_id(found.rule_id), "explanation_fa", None),
        "typical": [
            {
                "latin": one.get("latin"),
                "fa": one.get("fa"),
                "typicality": one.get("typicality"),
                # Which verbs this stem belongs to. Empty for a nominal rule,
                # whose bases are nouns and have no infinitive.
                "of": list(_stems_to_verbs().get(str(one.get("latin")), ())[:2]),
            }
            for one in (centre.typical if centre else ())
        ],
    }


def _realisation(form: GroupedForm) -> dict[str, Any] | None:
    """How often the rules in this form's chain produce words the corpus has.

    **The part of the score that can speak where the semantic one cannot.**
    A typicality is measured on the *first* step, because the base there is a
    dictionary word with a vector and every step after it stands on something
    the engine invented — and a vector here is the average of up to six corpus
    lines using the word, so a word nobody has written can never have one. On
    a three-step answer that leaves 17,679 of 17,679 forms scored on their
    first step alone: 12,999 of them share 22 values between them, in ties two
    thousand deep. It cannot order a list that size, and was never meant to.

    This can, because it asks about the **rules** rather than about the words
    they made. Measured on اندیشیدن at depth 3, where *hamandišande* is the
    word PLAN 9.10 exists to reach: it sat at 10,551 of 17,717 and sits at 676
    with this in the sort. *vāguyande* moves from 9,590 to 994.

    Summarised by the **median** of the chain, not the weakest link: the good
    chain and the nonsense one differ by 180× on the median and by 2× on their
    weakest rule, because one weak rule in a strong chain is common — *ham-*
    realises 0.04% and *-ande* 21.8%, in the same word.
    """
    neutral = stored.neutral_realisation()
    if neutral is None:
        # Nothing has been measured at all — a machine with no precompute.
        return None

    rates: list[float] = []
    measured = 0
    for step in form.shortest_path:
        rate = stored.loaded().realisation(step.rule_id)
        if rate is None:
            # Not measured, so it counts as neither good nor bad.
            rates.append(neutral)
        else:
            rates.append(rate)
            measured += 1
    if not rates:
        return None
    return {
        "median": median(rates),
        "steps_measured": measured,
        "steps": len(rates),
    }


def _inflection(form: GroupedForm) -> dict[str, Any] | None:
    """How this form also reads, if it reads as an inflection of a held word.

    Nothing is decided here. `shared_with` names the rules whose affix is
    spelled the same way, and a non-empty list means the letters cannot tell
    word formation from inflection — which is the case 95.5% of the time.
    """
    found = inflected.reading(form.fa)
    if found is None:
        return None
    return {
        "base": found.base,
        "pattern": found.pattern_id,
        "label_fa": found.label_fa,
        "shared_with": list(found.shared_with),
    }


def _form(
    pack: RulePack,
    form: GroupedForm,
    meaning_fa: str | None,
    attestation: Attestation | None = None,
    base_attested: bool | None = None,
    worded: bool = True,
) -> dict[str, Any]:
    return {
        "form_latin": form.latin,
        "form_fa": form.fa,
        "word_class": form.word_class,
        "depth": form.depth,
        "semantic_tags": list(form.semantic_tags),
        "meaning_fa": meaning_fa,
        "attestation": _evidence(attestation),
        # Whether some route to this form rests on written ground throughout —
        # measured on رفتن, 231 of its 476 two-step words are built on an
        # intermediate nobody ever wrote, and a form's own attestation cannot
        # see that. **null means the corpus was not asked**, never "no".
        "base_attested": base_attested,
        # One part of the score, never the score: how much the first step's
        # base resembles the bases its rule usually takes. None is "not
        # measured" — most rules have no centroid — never a low score.
        "semantic": _typicality(form),
        # The other part, and the one that can speak about a deep chain: how
        # often the rules on the way here produce words the corpus has. See
        # _realisation for why the semantic score cannot do this job.
        "realisation": _realisation(form),
        # Whether these letters *also* read as an inflection of a word the
        # dictionary already holds — رفتی is "you went" before it is anything
        # we built. It is why the form ranks where it does, so it is served
        # rather than left to be inferred from an unexplained position.
        # **`shared_with` is the honest half**: 95.5% of inflection-shaped
        # forms are spelled by a derivational rule too, so the letters cannot
        # settle it and the reader is told they cannot. null is *not one*, or
        # *not asked* where no lexicon is configured.
        "inflection": _inflection(form),
        "paths": [[_step(pack, step, worded) for step in path] for path in form.paths],
    }


#: Persian and Arabic letters. A word written in these is not a Behnevis form.
_PERSIAN_SCRIPT = re.compile(r"[؀-ۿ]")


def _in_behnevis_please(word: str) -> str:
    """Refuse a Persian spelling the lexicon does not hold, and say that is why.

    Reached only when :func:`_behnevis_forms` found nothing, so the reason is
    never *this route does not take Persian* — since S11 it does. The reason is
    that nobody knows how these letters are read, and this project does not
    guess: reading Persian script into Behnevis without diacritics measured
    5.8% correct.
    """
    return (
        f"{word!r} is not in the lexicon, so there is no reading to take apart. "
        f"Write it in Behnevis — Goftār rather than گفتار. A Persian spelling "
        f"the lexicon does hold is analysed directly."
    )


def _behnevis_forms(word: str) -> list[str]:
    """Every Behnevis reading the lexicon records for a Persian spelling.

    **Looked up, never transliterated.** Reading Persian script into Behnevis
    without diacritics was measured at 5.8% correct, so a guess here would put
    a wrong base under a real chain of rules and the answer would look exactly
    as confident as a right one. The dictionary either knows the spelling or
    it does not.
    """
    try:
        with Lexicon.open() as lexicon:
            readings = lexicon.by_spelling(word) or lexicon.by_normalized_spelling(word)
    except Exception:  # noqa: BLE001 - a lookup that fails is not an answer
        return []
    found: list[str] = []
    for reading in readings:
        for latin in reading.all_latin:
            if latin and latin not in found:
                found.append(latin)
    return found


def _merged(word: str, results: list[tuple[str, Any]]) -> Any:
    """One answer over however many readings the spelling had.

    A Persian spelling with two readings gives two analyses, and the caller
    asked about the spelling. The accounts are concatenated in reading order
    and sorted the way one analysis already sorts its own — fewest steps first
    — so the shortest account leads whichever reading it came from.

    The two lists beside the accounts are unions rather than either one's:
    an affix tried without a base under *Kanār* was still tried, and a form
    that only differs in case is worth reporting whichever reading built it.
    """
    from murfulu.analysis import Result

    if len(results) == 1:
        return results[0][1]
    merged = Result(form=word)
    for _, one in results:
        merged.analyses.extend(one.analyses)
    merged.analyses.sort(key=lambda one: (one.depth, one.base.latin))
    merged.unmatched_affixes = sorted(
        {affix for _, one in results for affix in one.unmatched_affixes}
    )
    # Only worth saying when nothing rebuilt the word as it was written — the
    # same condition one analysis applies to itself.
    if not merged.analyses:
        merged.built_in_another_case = sorted(
            {form for _, one in results for form in one.built_in_another_case}
        )
    return merged


def _base_evidence(found: Any) -> dict[tuple[str, str], Attestation]:
    """What the corpus has for each account's **base**, in one query.

    Keyed on the spelling *and* the reading, because that is what decides the
    level: the corpus having the letters is a weaker fact than its having this
    word, and ناخدا is exactly the case where the difference matters.

    Elasticsearch not being there is not a failure of analysis: the rules still
    say how the word is made. Every base then carries no attestation at all,
    which the interface shows as *not checked* rather than *not found* — the
    same rule the build screen has always followed.
    """
    from elasticsearch import ApiError, TransportError

    from murfulu.search.attested import look_up
    from murfulu.search.indices import connect

    bases = {
        (account.base.spelling_fa, account.base.latin)
        for account in found.analyses
        if account.base.spelling_fa
    }
    if not bases:
        return {}
    try:
        index = look_up(connect(), {spelling for spelling, _ in bases})
    except (ApiError, TransportError, OSError):
        return {}
    return {base: index.look_up(*base) for base in bases}


def _take_apart(word: str, depth: int) -> dict[str, Any]:
    """What one word could have been built from, each account rebuilt.

    **The Persian spelling is accepted, by looking it up.** This route rebuilds
    forward and compares Latin against Latin, so a word in Persian script
    matched nothing and came back as an empty list of accounts —
    indistinguishable from *this word cannot be built*, which is a wrong answer
    given confidently. The rule pack's own examples دانشمند and گفتگو were
    among the casualties. `/generate` has always taken either alphabet and a
    caller has every reason to expect this one does too. That was S11.

    So a Persian spelling is looked up and **every reading is analysed**, the
    way `/generate` does it — کنار is *Kanār* or *Kenār* and the dictionary
    commits to neither, so answering on one of them would be a choice nobody
    made. `analysed_as` says which forms were taken apart and each account
    carries its own.

    A spelling the lexicon does not hold is still refused, and that is the
    honest half: nothing here may guess the Behnevis.
    """
    from murfulu import analysis

    asked_in_persian = bool(_PERSIAN_SCRIPT.search(word))
    forms = _behnevis_forms(word) if asked_in_persian else [word]
    if asked_in_persian and not forms:
        raise HTTPException(400, _in_behnevis_please(word))

    pack = loaded()
    results: list[tuple[str, Any]] = []
    try:
        with Lexicon.open() as lexicon:
            for form in forms:
                one = analysis.explain(lexicon, pack, form, depth=depth)
                results.append((form, one))
            snapshot = lexicon.snapshot_id
    except Exception as unavailable:  # noqa: BLE001 - reported, not swallowed
        raise HTTPException(
            503, f"the lexicon is not readable: {unavailable}"
        ) from None

    found = _merged(word, results)
    accounted = _base_evidence(found)

    return {
        "word": word,
        # Which Behnevis form each account was taken apart from. The same as
        # `word` unless the caller wrote Persian, in which case it is every
        # reading the dictionary records for that spelling.
        "analysed_as": forms,
        "depth": depth,
        "rule_pack_version": pack.version,
        "lexicon_snapshot_id": snapshot,
        # **`rebuilt`, not `explained`.** It was called `explained` until
        # 2026-08-17 and that is a bigger claim than the route can make: it
        # means only that a chain of real rules reproduces these letters from
        # a dictionary entry. It says nothing about whether the result is the
        # word anyone means. `/explain?word=Nāxodāgāhi` came back true on
        # ناخدا, a ship's captain, and `Hamzamāni` on a base of `Zam`; both
        # accounts are right about the letters and useless about the word, and
        # a language model reading the API stopped trusting the flag. That is
        # S21, and the flag is renamed rather than taught to judge meaning —
        # refusing those would need a judgement this project does not make in
        # code. What is served instead is evidence: see `base.attestation`.
        "rebuilt": found.explained,
        # **Whether an empty answer means "no" or "we did not finish looking".**
        # The engine stops at 20,000 forms per base; افکندن reaches 20,050 at
        # three steps, so درافکندگی — the word the coining experiment called
        # the engine's largest gap — was reported as impossible when every rule
        # its chain needs exists and fires. False here means the caller must
        # not print *this word cannot be built*.
        "settled": found.settled,
        # Which bases ran out of room, so the caveat names something rather
        # than being a bare flag.
        "searched_partially": list(found.searched_partially),
        # The same letters in another case, where those rebuild and these
        # do not. Case is meaning in Behnevis so the two are different
        # words and are never merged — but an empty answer that is really
        # a casing mistake is indistinguishable from "cannot be built",
        # and a caller measured ten false negatives before noticing.
        "built_in_another_case": list(found.built_in_another_case),
        "accounts": [
            {
                # Which Behnevis form this account takes apart. Constant unless
                # the caller wrote a Persian spelling with two readings.
                "form_latin": account.form,
                "base": {
                    "latin": account.base.latin,
                    "spelling_fa": account.base.spelling_fa,
                    "lexicon_category": account.base.lexicon_category,
                    # How much of the corpus the **base** itself has, which is
                    # the one thing we already hold that separates a parse a
                    # reader would accept from one that is merely arithmetic.
                    # Hamzamāni's base is `Zam`; Nāxodāgāhi's is ناخدا, a ship's
                    # captain. Neither is refused — this is evidence and not a
                    # verdict, and null means the corpus was never asked, never
                    # that the base is absent.
                    "attestation": _evidence(
                        accounted.get((account.base.spelling_fa, account.base.latin))
                    ),
                },
                "depth": account.depth,
                "steps": [
                    {
                        "rule_id": step.rule_id,
                        "affix": step.affix,
                        "affix_fa": step.affix_fa,
                        "label_fa": step.label_fa,
                        "explanation_fa": step.explanation_fa,
                        "applied_to": step.applied_to,
                        "stem_form": step.stem_form,
                        # Where the *y* of *guyande* came from. The account is
                        # built forward, so it knows.
                        "glide_id": step.glide_id,
                    }
                    for step in account.steps
                ],
            }
            for account in found.analyses
        ],
        # Affixes whose shape fits but whose remainder is in no dictionary.
        # Saying which were tried is more useful than silence.
        "affixes_tried_without_a_base": found.unmatched_affixes,
    }


#: Forms per reading when the caller says nothing. Chosen against the measured
#: cost of one: بلند's answer is 1,380 bytes a form, so 200 is a few hundred
#: kilobytes — an answer a caller can read — where the whole of it is 3.94 MB.
DEFAULT_LIMIT = 200

#: The most any single request may ask for. Above this a caller should page;
#: `limit=0` is the deliberate way to ask for everything and is not capped,
#: because our own build screen genuinely needs the lot.
MAX_LIMIT = 2000


def _page(forms: list[GroupedForm], offset: int, limit: int) -> list[GroupedForm]:
    """One slice of a reading's forms. ``limit=0`` means all of them."""
    if limit == 0:
        return forms[offset:]
    return forms[offset : offset + limit]


#: Where a form stands on the corpus's own evidence, strongest first. The same
#: three states the build screen has always sorted on, and in the same order:
#: the corpus has it and the count is *this* form's; it has it but the count
#: belongs to another reading of the spelling; it does not have it; it was
#: never asked. An unchecked form is not an absent one, so it sorts on its own.
_UNCHECKED = 3


def _standing(found: Attestation | None) -> int:
    if found is None:
        return _UNCHECKED
    if found.level is Level.NONE:
        return 2
    if found.function_word:
        # Written, as another word: the count is the function word's.
        return 1
    ours = not found.spelling_unlinked and not found.other_readings
    return 0 if ours else 1


def _ranked(
    forms: list[GroupedForm],
    attestation: Callable[[GroupedForm], Attestation | None],
    solid: IsGrounded | None,
) -> list[GroupedForm]:
    """Best first, so that a page is the best page and not an arbitrary slice.

    **This did not used to happen here**, and it did not need to: the build
    screen asked for every form and sorted them itself. At depth 3 that answer
    is 39 MB, so it has to be paged — and a page of an unsorted list is a
    random handful. Ranking moved to where the paging is.

    Strongest corpus evidence, then **whether the form also reads as an
    inflection of a word we already hold**, then how many poems hold it, then
    how often the rules on the chain produce real words, then whether the chain
    rests on written ground, then how much the first base resembles the rule's
    usual bases, then alphabetically so the same request always gives the same
    answer.

    **The inflection test is new on 2026-08-17 and closes the second half of
    S8.** The first half stopped a count belonging to another *reading* from
    ranking a form. What was left was worse and had no fix in the fields we
    hold: where the lexicon knows **no** reading for a spelling, nothing
    separated رفتی — "you went" — from گفتار, which is exactly the word this
    project makes. Both are `unlinked`, so رفتن's screen opened on روی and
    رفتی above رفتار and روش.

    :mod:`murfulu.scoring.inflected` separates them, and it is the only thing
    that can: it asks whether the letters also read as an inflection of
    something the dictionary already holds. It sits **above the count and below
    the evidence level**, because the complaint is precisely that a count which
    may not be this word's outranks everything else.

    Marked and demoted, never dropped — a word the corpus wrote is evidence
    whatever it is evidence of.

    **Grounding used to come first of those two, and the project lead swapped
    them on 2026-08-17.** The reason is that grounding is wrong about a whole
    family of words: it marks *bāzguyande* — بازگوینده, which the corpus
    contains — as standing on air, because the step in between is the
    *infinitive* of a prefixed verb and the poets wrote *they retold* rather
    than *to retell*. A stepping stone missing for that reason says nothing
    about the destination. It still ranks, one place lower, where it is right
    more often than not; what it no longer does is outrank a measure that is
    not wrong about words we can prove are real.

    *hamandišande* moves from 676 of 17,717 to 189 by the swap, and sat at
    10,551 before either criterion existed.

    **`ranked()` in web/src/screens/build/Build.tsx has to say the same
    thing**, because steps 1 and 2 still ask for every form and sort in the
    browser. The two are kept in step by hand; a difference between them shows
    up as a page whose contents and whose order disagree.

    Nothing measured counts as *neither good nor bad* on both of the last two,
    never as worst. A missing figure is silence, and silence must not sink a
    word below one that was measured and scored badly.
    """
    # An unmeasured typicality takes the middle of the measured ones *in this
    # answer* — the same neutral fill `stored.neutral_realisation` makes, and
    # for the same reason. Not the global spread, which is null on a machine
    # that has never measured one; here there is always something to take a
    # middle of, or nothing carries a typicality and they all tie anyway.
    scored = sorted(
        found["typicality"] for form in forms if (found := _typicality(form))
    )
    no_opinion = scored[len(scored) // 2] if scored else 0.0

    def key(form: GroupedForm) -> tuple[Any, ...]:
        found = attestation(form)
        realised = _realisation(form)
        typical = _typicality(form)
        return (
            _standing(found),
            # 1 sinks. An unmeasured lexicon leaves this 0 for every form, so
            # a run without one ranks exactly as it did before — silence must
            # not sink a word.
            1 if inflected.reading(form.fa) else 0,
            -(found.doc_count if found else 0),
            # _realisation has already filled an unmeasured *rule* in at the
            # neutral rate; None here means nothing at all was measured, so
            # every form ties and the next criterion decides.
            -(realised["median"] if realised else 0.0),
            # false sinks; true and "not checked" rank alike, because an
            # unchecked chain is not a broken one.
            1 if (solid and not grounded(form.paths, solid)) else 0,
            -(typical["typicality"] if typical else no_opinion),
            form.latin,
        )

    return sorted(forms, key=key)


def _attestation_for(results: list[generation.Result]) -> Index | None:
    """Ask the corpus about every form this request produced, in one query.

    Elasticsearch not being there is not a failure of generation: the rules
    still say what can be built. Every form then carries no attestation at
    all, which the interface shows as "not checked" rather than "not found".
    """
    from elasticsearch import ApiError, TransportError

    from murfulu.search.attested import look_up
    from murfulu.search.indices import connect

    spellings = {form.fa for result in results for form in result.forms}
    if not spellings:
        return None
    try:
        return look_up(connect(), spellings)
    except (ApiError, TransportError, OSError):
        return None


@router.get("/generate")
def generate(
    word: str = Query(..., description="a Persian word, or its Latin reading"),
    depth: int = Query(2, ge=1, le=MAX_DEPTH),
    attest: bool = Query(True, description="ask the corpus about each form"),
    limit: int = Query(
        DEFAULT_LIMIT,
        ge=0,
        le=MAX_LIMIT,
        description="forms per reading; 0 for every one",
    ),
    offset: int = Query(0, ge=0, description="skip this many forms of each reading"),
    worded: bool = Query(
        True,
        description="carry each step's Persian label and explanation",
    ),
) -> dict[str, Any]:
    """Every word the rules can build from this one.

    A verb is entered through **both** its stems, never through the
    infinitive: *Raftār* comes from *raft* and *Raveš* from *row*, and a
    reader asking about رفتن wants both.

    **The answer is paged, because it was not and could not be used.** بلند at
    depth 2 is 2,856 forms and **3.94 MB**, and one caller stalled outright on
    it. `limit` and `offset` cut each reading's list; `worded=false` keeps
    every derivation and drops the per-step Persian, which is 43% of the bytes
    because 8,731 steps each repeat their rule's label and explanation.

    **Nothing is hidden, only paged**: every reading states how many forms it
    holds in total, how many came back, from where, and whether more remain.
    ``limit=0`` returns the lot, which is what our own build screen asks for —
    it groups by word class and must count every form to say what it folds.
    """
    pack = loaded()
    try:
        with Lexicon.open() as lexicon:
            results = generation.from_word(lexicon, pack, word, depth=depth)
            snapshot = lexicon.snapshot_id
    except generation.WordNotFoundError as absent:
        raise HTTPException(404, str(absent)) from None

    corpus = _attestation_for(results) if attest else None

    def _grounding_for(result: generation.Result) -> IsGrounded | None:
        """Written ground: the starting bases plus every attested form."""
        if corpus is None:
            return None
        solid = {base.latin for base in result.bases}
        for form in result.forms:
            found = corpus.look_up(form.fa, form.latin)
            if (
                found
                and found.level in (Level.READING, Level.SPELLING)
                and not found.function_word
            ):
                solid.add(form.latin)
        return solid.__contains__

    def _look_up(form: GroupedForm) -> Attestation | None:
        return corpus.look_up(form.fa, form.latin) if corpus else None

    # Ranked here and not on the screen, because the answer is paged and a page
    # of an unranked list is a random handful. See _ranked.
    pages = []
    for result in results:
        solid = _grounding_for(result)
        ranked = _ranked(result.forms, _look_up, solid)
        pages.append((result, solid, _page(ranked, offset, limit)))

    return {
        "word": word,
        "depth": depth,
        "rule_pack_version": pack.version,
        "lexicon_snapshot_id": snapshot,
        "corpus_version": corpus.corpus_version if corpus else None,
        "readings": [
            {
                "latin": result.reading.latin,
                "spelling_fa": result.reading.spelling_fa,
                "lexicon_category": result.reading.lexicon_category,
                # The dictionary's own doubt about this reading. 31.5% of the
                # snapshot's active rows carry it, and it was being dropped
                # here — so the screen built 2,612 words from بلند's flagged
                # *Baland* reading without ever saying it was flagged.
                # Reported, never filtered on: it is evidence, not a verdict.
                "needs_review": result.reading.needs_review,
                # The dictionary's own definition of the word being built
                # from. A preview: cut at 200 characters, and no مصدر has
                # one, so a verb still says nothing about what it means.
                "definition_fa": result.reading.definition_fa,
                "latin_variants": list(result.reading.latin_variants),
                "built_from": [
                    {"latin": base.latin, "fa": base.fa, "word_class": base.word_class}
                    for base in result.bases
                ],
                # The engine's own cap, which is a different thing from paging:
                # it means the chain was cut short, not that this answer holds
                # part of it.
                "truncated": result.truncated,
                # Every form this reading built, however few came back.
                "count": len(result.forms),
                "offset": offset,
                "returned": len(page),
                "has_more": offset + len(page) < len(result.forms),
                "forms": [
                    _form(
                        pack,
                        form,
                        (m.text_fa if (m := result.meaning_of(form.latin)) else None),
                        corpus.look_up(form.fa, form.latin) if corpus else None,
                        grounded(form.paths, solid) if solid else None,
                        worded,
                    )
                    for form in page
                ],
            }
            for result, solid, page in pages
        ],
    }


@router.get("/explain")
def explain(
    chain: str | None = Query(None, description="rule ids in order, e.g. V-022,V-023"),
    word: str | None = Query(None, description="a word to take apart"),
    depth: int = Query(2, ge=1, le=MAX_DEPTH),
) -> dict[str, Any]:
    """Explain a chain of rules, or take a word apart.

    Two questions, one route, because they are the same question from
    different ends. ``chain`` says what a derivation *does*; ``word`` asks what
    a word was *made of* — the *sāzāyi* check.

    **Taking a word apart proposes and verifies; it never decides.** Every
    account is rebuilt forward and only what reproduces the word survives, so
    *Mowlānā* is refused rather than announced as a Persian derivation. Where
    more than one account survives, all are returned: *Raveš* can be built
    from two different verbs, and choosing between them is a question about
    meaning.
    """
    if word:
        return _take_apart(word, depth)
    if not chain:
        raise HTTPException(400, "give either a rule chain or a word")
    pack = loaded()
    steps = []
    for rule_id in [part.strip() for part in chain.split(",") if part.strip()]:
        try:
            rule = pack.by_id(rule_id)
        except KeyError:
            raise HTTPException(404, f"no rule {rule_id!r} in the pack") from None
        steps.append(
            {
                "rule_id": rule.id,
                "kind": rule.kind if isinstance(rule, Rule) else "glide",
                "affix": getattr(rule, "affix", None),
                "affix_fa": getattr(rule, "affix_fa", None),
                "input_types": list(getattr(rule, "input_types", ())),
                "output_types": list(getattr(rule, "output_types", ())),
                "label_fa": getattr(rule, "label_fa", None),
                "explanation_fa": rule.explanation_fa,
                "active": rule.active,
            }
        )
    if not steps:
        raise HTTPException(400, "chain names no rule")
    return {"rule_pack_version": pack.version, "chain": steps}
