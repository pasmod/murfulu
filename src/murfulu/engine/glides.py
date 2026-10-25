"""Join two pieces of a word when a vowel meets a vowel.

Persian does not let two vowels touch, so a *y* slips between them: *dānā* + *i*
becomes *dānāyi*. The source grammar lists 17 such joins.

How the table works
-------------------
Each rule gives a left vowel, a right vowel and a result. Two shapes appear, and
which one a rule is can be read off the result itself:

**The result starts with the left vowel** — it spells out the whole join, both
vowels and the glide, so the affix's own first vowel is already inside it::

    gu + eš   →  g + "uye" + š    = guyeš      (u + e → uye)
    dānā + i  →  dān + "āyi" + "" = dānāyi     (ā + i → āyi)

**The result does not** — it replaces the left vowel only, and the affix is
added whole::

    row + eš  →  r + "av" + eš    = raveš      (ow + e → av)
    row + am  →  r + "av" + am    = ravam      (ow + a → av)

All 17 rules follow one or the other, so nothing here is special-cased.
"""

from __future__ import annotations

from dataclasses import dataclass

from murfulu.rules.pack import Glide, RulePack

#: The glide consonant, in both scripts. When a glide rule's result contains
#: it, the Persian form needs the letter too — دانا + ی = دانایی. Without this
#: the Latin gets the y and the Persian does not, which silently produces a
#: different word: گوش ("ear") instead of گویش.
GLIDE_LATIN = "y"
GLIDE_FA = "ی"

#: The other glide consonant. Two rules insert it — G-09 (*taze + i = Tāzegi*)
#: and G-10 (*morde + ān = Mordegān*) — and in Persian it does more than
#: appear: it takes the place of the base's final ه. تازه + ی is **تازگی**.
GAF_LATIN = "g"
GAF_FA = "گ"

#: The silent ه, which is what the Latin writes as a final *e*.
SILENT_HE = "ه"

#: A final ه standing after ا is **always pronounced** — شاه, ماه, راه, گاه,
#: کلاه, پناه. The silent ه writes a short *e*, and a short vowel cannot follow
#: a long ā, so the two never collide on this ending. This is the one place the
#: Persian spelling settles the question on its own; everywhere else it cannot,
#: which is why :func:`join_fa` reads the Latin.
SOUNDED_HE_AFTER = "اه"


def join_fa(base_fa: str, base_latin: str, infix_fa: str, affix_fa: str) -> str:
    """Join the Persian side, where it is not plain concatenation.

    **One rule, and it is the difference between زندگی and زندهگی.** A base
    whose Persian ends in a silent ه loses it when a گ follows — from a glide
    (تازه + ی = تازگی) or from an affix that begins with one (دره + گاه =
    درگاه, بنده + گی = بندگی). The Latin keeps the *e* either way, because in
    Latin the vowel is written and in Persian the گ carries it.

    **Silent is decided by the Latin, not by the letter.** شاه ends in ه too,
    and its ه is a consonant — *šāh* ends in *h*, not *e* — so شاه + گان stays
    شاهگان. Reading it off the Latin is exact where guessing from the Persian
    alone would not be.

    **Exact only if the Latin is right, and for one whole ending it is not.**
    karbon transliterates a *pronounced* final ه as **e**: شاه is held as
    `Šāe`, ماه as `Māe`, راه as `Rae`, گاه as `Gāe` — **777 of the 803 readings
    ending in ـاه**, and 457 of the 463 ending in ـگاه. Read off those, this
    rule deletes a consonant: building one step from شاه gave **شاگان، شاگین،
    شاگیدن**, and over 40 sampled readings **550 of 1,935 forms — 28% — lost
    the ه**. Found 2026-08-20 by a coining run that could not analyse گلوگاه.

    So the ـاه ending overrules the Latin, and only that ending: a final ه
    after ا is always a consonant, because the silent ه writes a short *e* and
    a short vowel cannot follow a long ā. **Unconfirmed**, and narrow on
    purpose — کوه is *kuh* and میوه is *mive*, both written وه, and no rule
    over the Persian alone can tell those two apart. Those stay wrong until
    karbon is fixed; the fault is [UPSTREAM A9](../../../docs/UPSTREAM.md) and
    nothing here works around the data anywhere else.

    Measured before it was written: 38,932 forms spelled this join wrong, and
    at least 658 of them are words the corpus has — زندگی 4,571 times, مژگان
    3,977, بندگی 2,583 — which the wrong spelling reported as never written.

    **Unconfirmed.** The rule is standard Persian orthography and the source
    grammar's own examples (*Tāzegi*, *Mordegān*) assume it, but the Behnevis
    joining specification has not been extracted — see OPEN_QUESTIONS M and K,
    and FOR_THE_LINGUIST L7.
    """
    following = infix_fa + affix_fa
    if (
        following.startswith(GAF_FA)
        and base_fa.endswith(SILENT_HE)
        and not base_fa.endswith(SOUNDED_HE_AFTER)
        and base_latin.lower().endswith("e")
    ):
        return base_fa[:-1] + following
    return base_fa + following


@dataclass(frozen=True)
class Join:
    """The result of joining a base to an affix."""

    latin: str
    #: What to put between the two halves on the Persian side.
    infix_fa: str = ""
    #: Which glide rule fired, or None when the vowels never met.
    glide_id: str | None = None
    #: Other glide rules that matched the same pair of vowels. Non-empty means
    #: the source grammar is ambiguous here — see G-09 and G-17.
    alternatives: tuple[str, ...] = ()


def _applies(glide: Glide, base: str, affix: str) -> bool:
    return (
        glide.active
        and base.lower().endswith(glide.left.lower())
        and affix.lower().startswith(glide.right.lower())
    )


def matching(pack: RulePack, base: str, affix: str) -> list[Glide]:
    """Every active glide rule for this meeting of vowels, in id order."""
    return sorted(
        (g for g in pack.glides if _applies(g, base, affix)), key=lambda g: g.id
    )


def apply(glide: Glide, base: str, affix: str) -> str:
    """Join ``base`` and ``affix`` under one glide rule."""
    stem = base[: len(base) - len(glide.left)]
    if glide.result.lower().startswith(glide.left.lower()):
        # The result spells the whole join, so the affix's first vowel is
        # already accounted for.
        return stem + glide.result + affix[len(glide.right) :]
    # The result replaces the left vowel only.
    return stem + glide.result + affix


def unapply(glide: Glide, affix: str, form: str) -> str | None:
    """The base this join would have started from, or ``None`` if it did not.

    The exact reverse of :func:`apply`, off the same two shapes and the same
    table — nothing about the *y* is written out as a sound change here.

    **The engine could build these words and then could not read them back.**
    *gu* + *-ande* gives *guyande* and *ā* + *-ande* gives *āyande*, but the
    decomposer only ever removed the affix as a string, which left *guy* and
    *āy* — remainders that are in no dictionary and never were. Measured
    2026-08-20 over the live lexicon: **19 of 19** one-step forms with a glide
    in them, 13 from گفتن and 6 from آمدن, were built and then reported as
    words that cannot be built. Undoing *row* → *rav* worked because it comes
    from ``stem_forms``; the glide table was simply never run backwards.

    Which is the *sāzāyi* rule broken in the one place it matters: a form the
    engine put together, it must be able to take apart.
    """
    if not glide.active:
        return None
    if not affix.lower().startswith(glide.right.lower()):
        return None
    if glide.result.lower().startswith(glide.left.lower()):
        # The result spells the whole join, so the affix's own first vowel is
        # inside it and only the rest of the affix follows: uya + nde.
        ending = glide.result + affix[len(glide.right) :]
    else:
        # The result replaced the left vowel only, and the affix is whole.
        ending = glide.result + affix
    if len(form) < len(ending) or not form.lower().endswith(ending.lower()):
        return None
    # Never empty: what is put back is the rule's own left vowel. *Āyande* is
    # built from *ā* alone, and the base is that vowel.
    return form[: len(form) - len(ending)] + glide.left


def undo(pack: RulePack, affix: str, form: str) -> list[tuple[str, str]]:
    """Every base this word could have if a glide fired at this suffix.

    Proposals, not answers — the same standing as everything else the
    decomposer offers. A base survives by being in the lexicon and by
    building the word again.
    """
    found: list[tuple[str, str]] = []
    for glide in pack.glides:
        base = unapply(glide, affix, form)
        if base is not None:
            found.append((base, glide.id))
    return found


def join(pack: RulePack, base: str, affix: str) -> Join:
    """Join a base to a suffix, applying a glide rule if the vowels meet."""
    if not base or not affix:
        return Join(latin=base + affix)
    candidates = matching(pack, base, affix)
    if not candidates:
        return Join(latin=base + affix)
    chosen, *rest = candidates
    return Join(
        latin=apply(chosen, base, affix),
        infix_fa=_infix_fa(chosen),
        glide_id=chosen.id,
        alternatives=tuple(g.id for g in rest),
    )


def _infix_fa(glide: Glide) -> str:
    """The letter the Persian needs at this join, if any.

    Whichever consonant the rule's result puts between the vowels — *y* in
    *dānāyi*, *g* in *Tāzegi* — has to appear in the Persian too, or the two
    scripts drift into different words.
    """
    if GLIDE_LATIN in glide.result:
        return GLIDE_FA
    return GAF_FA if GAF_LATIN in glide.result else ""


def ambiguous_pairs(pack: RulePack) -> dict[tuple[str, str], list[str]]:
    """Vowel pairs more than one active rule claims.

    The grammar has at least one: *e* meeting *i* is G-09 (*taze + i = Tāzegi*)
    and also G-17 (*rafte + i = raftei*). Reported rather than hidden, because
    which applies depends on the suffix, not on the vowels.
    """
    seen: dict[tuple[str, str], list[str]] = {}
    for glide in pack.glides:
        if glide.active:
            seen.setdefault((glide.left, glide.right), []).append(glide.id)
    return {pair: ids for pair, ids in seen.items() if len(ids) > 1}
