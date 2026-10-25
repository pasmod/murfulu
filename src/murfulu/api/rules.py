"""What the rule pack holds: the rules themselves, and the affixes by meaning.

Two routes over one loaded pack. Neither touches a database, because the rule
pack is data in the repository — which is also why they answer instantly and
work on a machine with no infrastructure at all.

``/affixes`` exists because of the founding complaint: a writer who wants an
affix meaning *place* has to open a grammar book. Here the semantic tag is the
key, and every affix carrying it comes back with the rules that use it.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from murfulu.rules import word_classes
from murfulu.rules.pack import Glide, Rule, RulePack, loaded
from murfulu.rules.types import WORD_CLASSES, traditional_term
from murfulu.scoring import stored
from murfulu.scoring.semantics import Semantics
from murfulu.scoring.semantics import loaded as semantics

router = APIRouter(tags=["rules"])

#: Internal key for rules the source gives no semantic tag. Never a tag name
#: and never returned as one.
_UNTAGGED = ""


def _as_json(rule: Rule) -> dict[str, Any]:
    """One rule, as the interface shows it.

    The Farsi label and explanation are not decoration: the interface is in
    Farsi and a rule that cannot be read in Farsi cannot be shown to anyone.
    """
    return {
        "id": rule.id,
        # The letter before the number. Derivable from the id, and the screen
        # filters on it — which it could not do while this was missing, so
        # every family button quietly emptied the list.
        "family": rule.family,
        "kind": rule.kind,
        "affix": rule.affix,
        "affix_fa": rule.affix_fa,
        "input_types": list(rule.input_types),
        "output_types": list(rule.output_types),
        # How a compounding rule joins two words, and what may fill each side.
        # The pack has carried both since the transcription — V-021 is
        # `{a} + o + na + {b}` with slot b constrained to the same verb and
        # negated — and this route served neither, so a caller saw `kind:
        # template` with an affix of `‒` and nothing to say what the template
        # was. A language model given the API hand-assembled compounds instead
        # of reading the pattern, because the pattern was not there to read.
        # Null on the 179 affix rules, which is what they are.
        "pattern": rule.pattern,
        "pattern_fa": rule.pattern_fa,
        "slots": [dict(slot) for slot in rule.slots],
        "semantic_tags": list(rule.semantic_tags),
        "strength": rule.strength,
        "label_fa": rule.label_fa,
        "explanation_fa": rule.explanation_fa,
        "examples": list(rule.examples),
        "source": rule.source,
        "needs_expert_check": rule.needs_expert_check,
        "notes": list(rule.notes),
        "active": rule.active,
        # Empty while the rule applies, and required by the pack the moment it
        # does not. Only the glide branch served it, so a retired affix rule
        # showed as switched off with no reason — which reads as somebody
        # disabling it rather than as a ruling.
        "retired_reason": rule.retired_reason,
        # The reason in Persian, which is the only one a reader of this
        # interface can use. The screen showed a **بازنشسته** badge and stopped
        # there, so a reader was told that a rule no longer applies and never
        # why — for N-090 the why is the whole of the interesting part. Empty
        # where nobody has authored it: the interface may not invent Persian,
        # so an empty string means the badge alone. See S14.
        "retired_reason_fa": rule.retired_reason_fa,
    }


def _glide_as_json(glide: Glide) -> dict[str, Any]:
    """One glide rule, in its own shape rather than an affix rule's.

    A glide has no affix, no input class and no semantic tag: it says what
    happens where two vowels meet. Serving it with those fields set to null
    would put blanks on screen exactly where an affix goes, so it carries
    ``kind: "glide"`` and its three own fields instead — the same shape
    ``/rules/{id}`` has always returned for one.
    """
    return {
        "id": glide.id,
        "family": "G",
        "kind": "glide",
        "left": glide.left,
        "right": glide.right,
        "result": glide.result,
        "examples": list(glide.examples),
        "explanation_fa": glide.explanation_fa,
        "active": glide.active,
        "retired_reason": glide.retired_reason,
        "retired_reason_fa": glide.retired_reason_fa,
    }


def _pack() -> RulePack:
    return loaded()


@router.get("/rules")
def list_rules(
    family: str | None = Query(None, description="V, N, G or S"),
    takes: str | None = Query(None, description="word class the rule accepts"),
    tag: str | None = Query(None, description="semantic tag"),
    flagged: bool = Query(False, description="only rules the source left unclear"),
) -> dict[str, Any]:
    """Every rule in the pack, filtered.

    Retired rules are included and marked, never hidden: a stored derivation
    can name a rule that no longer applies, and the reader still has to be
    able to look it up.
    """
    pack = _pack()
    found = pack.rules
    if family:
        found = [r for r in found if r.family == family.upper()]
    if takes:
        found = [r for r in found if takes in r.input_types]
    if tag:
        found = [r for r in found if tag in r.semantic_tags]
    if flagged:
        found = [r for r in found if r.needs_expert_check]

    # The glide rules, which were served nowhere while the screen offered a
    # button for their family — so every reader who pressed it got an empty
    # list, and a build result naming `G-10` had nothing to link to.
    # A glide takes no word class, carries no tag and is never flagged for
    # review, so the three filters that ask about those exclude it rather
    # than matching it vacuously.
    glides: list[Glide] = []
    if not (takes or tag or flagged) and family in (None, "G", "g"):
        glides = list(pack.glides)

    measured = stored.loaded()
    vectors = semantics()
    return {
        "rule_pack_version": pack.version,
        "count": len(found) + len(glides),
        "word_classes": _word_classes(),
        # Empty when no precompute has been run here. That is a legitimate
        # state, not an error, and the interface says so rather than showing
        # zeros that look like measurements.
        "corpus_version": measured.corpus_version or None,
        "measured_rules": len(measured),
        # How many rules have a semantic centre at all. Most do not, and the
        # screen has to be able to say *this rule has none* rather than leave
        # a blank that reads as nothing typical.
        "semantic_rules": len(vectors),
        "rules": [
            {
                **_as_json(rule),
                "productivity": measured.for_rule(rule.id),
                "semantic": _centre(vectors, rule.id),
            }
            for rule in found
        ]
        # A glide is not measured for productivity and has no semantic centre:
        # it does not build a word, it decides a letter at a join. Those keys
        # are absent rather than null, so nothing downstream reads a missing
        # measurement as a low one.
        + [_glide_as_json(glide) for glide in pack.glides if glide in glides],
    }


def _centre(vectors: Semantics, rule_id: str) -> dict[str, Any] | None:
    """What this rule's semantic centre is made of, straight from the artefact.

    Nothing is computed here and nothing is worded here. The count is how many
    attested bases the centroid was built from; the examples are the bases
    nearest it, ranked by the batch job that had the vectors. A rule with no
    centroid returns ``None`` — *not measured*, which the screen states.
    """
    found = vectors.centre(rule_id)
    if found is None:
        return None
    return {"bases": found.bases, "typical_bases": [dict(one) for one in found.typical]}


def _word_classes() -> list[dict[str, Any]]:
    """The closed set of word classes, under both vocabularies.

    The interface has to explain *kārnām* without a manual, and it may not
    invent the Persian to do it. Until 2026-08-17 the only Persian in the data
    was the **traditional** term — اسم مصدر for `karnam` — so every screen
    labelled its groups in the vocabulary this project exists to replace, while
    docs/FRONTEND.md said the coined term should be primary and the
    traditional one a tooltip. That was S3, and it is closed by authoring the
    terms rather than by deriving them — the word class table beside the rules,
    loaded by :mod:`murfulu.rules.word_classes`.

    **`label_fa` is what to print and `traditional_fa` is the tooltip.** Where
    a class has no coined term — `nedayi`, the vocative, whose own name is
    Arabic-derived — `label_fa` falls back to the traditional one and
    `label_is_traditional` says it fell back, so a screen never shows the old
    vocabulary as though it were the new. `term_confirmed` is false on the four
    the linguist has not yet ruled on (L17); they are shown, not hidden.
    """
    table = word_classes.loaded()
    return [
        {
            "name": name,
            "label_fa": entry.label_fa,
            "label_is_traditional": entry.label_is_traditional,
            "coined_fa": entry.coined_fa,
            "traditional_fa": traditional_term(name),
            "behnevis": entry.behnevis,
            "explanation_fa": entry.explanation_fa,
            "term_confirmed": entry.confirmed,
            "description_en": WORD_CLASSES[name],
        }
        for name, entry in table.items()
    ]


@router.get("/rules/{rule_id}")
def get_rule(rule_id: str) -> dict[str, Any]:
    """One rule by its permanent id, with everything the list carries.

    **The detail route used to serve less than the list**, which is backwards:
    a caller asking about one rule got the pack's description and none of the
    measurement, while a caller asking about all 212 and filtering got both.
    The fields were simply absent, and an absent measurement reads as *not
    measured* — so N-020 looked unmeasured rather than deliberately building
    nothing. Found by a language model given the API, which had to keep the
    whole list cached to read one rule's productivity out of it. See S17.

    A glide is served in its own shape, as it always has been, and carries
    neither key: it does not build a word, so there is nothing to measure.
    """
    pack = _pack()
    try:
        found = pack.by_id(rule_id)
    except KeyError:
        raise HTTPException(404, f"no rule {rule_id!r} in the pack") from None
    if not isinstance(found, Rule):
        return _glide_as_json(found)

    measured = stored.loaded()
    return {
        **_as_json(found),
        "productivity": measured.for_rule(found.id),
        "semantic": _centre(semantics(), found.id),
        # The same context the list gives, because a figure has to say which
        # corpus it was measured on wherever it is read. None here means no
        # precompute has been run against this checkout, which is legitimate.
        "corpus_version": measured.corpus_version or None,
        "rule_pack_version": pack.version,
    }


@router.get("/affixes")
def list_affixes(
    tag: str | None = Query(None, description="show only affixes with this meaning"),
) -> dict[str, Any]:
    """Affixes grouped by what they mean.

    One affix can carry several meanings and one meaning several affixes, so
    the answer is grouped by tag rather than by affix.

    **Affixes the source records no meaning for are returned separately**, not
    as a group with a blank name. Measured on the pack: **81 of 189 affixes**
    carry no semantic tag, so the screen that answers *which affix means
    "place"* covers a little over half of them. Mixing those into the meanings
    would let a reader believe the other half had been checked and found to
    mean nothing.
    """
    pack = _pack()
    grouped: dict[str, dict[str, Any]] = {}
    for rule in pack.rules:
        if not rule.active or not rule.affix:
            continue
        for label in rule.semantic_tags or (_UNTAGGED,):
            if tag and label != tag:
                continue
            entry = grouped.setdefault(
                label,
                {"tag": label, "gloss_fa": None, "gloss_en": None, "affixes": []},
            )
            declared = pack.tag_for(label)
            if declared:
                entry["gloss_fa"] = declared.gloss_fa
                entry["gloss_en"] = declared.gloss_en
            entry["affixes"].append(
                {
                    "affix": rule.affix,
                    "affix_fa": rule.affix_fa,
                    "rule_id": rule.id,
                    "kind": rule.kind,
                    "output_types": list(rule.output_types),
                    "examples": list(rule.examples),
                }
            )
    untagged = grouped.pop(_UNTAGGED, None)
    return {
        "rule_pack_version": pack.version,
        "count": len(grouped),
        "meanings": [grouped[key] for key in sorted(grouped)],
        # Not a meaning. The source simply says nothing about these.
        "without_a_meaning": untagged["affixes"] if untagged else [],
    }
