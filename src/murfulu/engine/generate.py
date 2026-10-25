"""Feed results back in, so a word grows into its whole family.

*row* gives *ravande*; *ravande* gives *Ravandegi*. Depth is **not** a quality
limit — a three-step word is not worse for being three steps, and generating new
words is the point of the project. Two limits remain, and both are mechanical
rather than linguistic:

**Loops.** Several rules return the type they consume — *nā-* on a barnām gives
a barnām — so a chain can extend forever. Cycle detection stops a rule being
applied to the same form twice on one path.

**Repeated affixes.** That cycle check is not enough on its own, because it
keys on the *form*: *farāz-* on *andišidan* gives *farāzandišidan*, which is a
different form, so the same rule fits again and depth 4 built
*farāzfarāzfarāzandišidan*. So an affix may be added **once per path**, and the
guard keys on the **affix** rather than the rule id: V-059 and V-060 are both
*farāz-* under two semantic tags, N-093 and N-095 are both *-i*, and a rule-id
guard would let one follow the other and build the same wrong word.

**Suffixes were outside that guard until 2026-08-20**, on the reasoning that
*andišidegi* + *-i* is a real pattern. The reasoning was about two *different*
suffixes; what the engine actually built was *Golstānstān*, *Golzārzār*,
*Golkadekade*, *Golāā* and *goftee* — 35 of the 2,335 forms one reading of گل
makes at two steps. Measured before the guard went in, over 120 random
readings: **2,725 of 161,774 forms at depth 2 add one suffix twice — 1,830
distinct spellings, and not one of them appears in the corpus**, against
25,497,189 tokens. That is the same evidence, in the same shape, that settled
the prefix half on 2026-08-15.

**Unconfirmed, and narrower than it sounds.** Only the *same* affix twice is
refused. Two different suffixes still stack, which is what *andišidegi* + *-i*
actually is — but a repeated *-i* is refused with them, because the two are one
string. Question L in docs/OPEN_QUESTIONS.md is where that is recorded.

**Size.** Each step multiplies. A hard stop at five steps bounds it.

**A prefixed verb is entered through its prefixed stems.** A verb is never
entered through its infinitive — the rules attach to kārbon-e yek and kārbon-e
do — so an infinitive the engine *builds* used to be a dead end: *ham-* on
*andišidan* gave *hamandišidan* and nothing could be built from it, which put
*hamandišande* out of reach by every route. When a prefix rule makes an
infinitive, the same prefix now goes on both stems of the verb underneath and
those two are carried on as bases. Nothing is invented by this: a Persian
verbal prefix is transparent, and the stems of *hamandišidan* are the stems of
*andišidan* with *ham-* in front.

**A verb coined with *-idan* is entered through its stems too**, since the
linguist ruled on it (FOR_THE_LINGUIST L16, in the project's Telegram group on
2026-05-16, recorded in the rulings store on 2026-10-17). Such a verb — the
*masdar-e ja'li* of the old grammar, a noun or adjective plus *-idan* — takes
its past stem by removing *-an* and its present stem by removing *-id* from
that: *sereštidan*, *sereštid*, *serešt*. That is V-003, and nothing is
invented: the stems are read off the infinitive by the rule he stated.

**Only *-idan*, and the rest stay dead ends.** The causatives in *-āndan* and
*-ānidan* — V-001, V-002, V-004 — were named in the same message, but their
present stem was not stated, and V-051 is not a coinage of that kind at all.
Guessing would be inventing a stem, so those remain open in
docs/FOR_THE_LINGUIST.md under L16. One entry in :data:`COINED_VERB_ENDINGS`
opens one of them if he rules.

**What it costs, measured rather than estimated.** It was filed as multiplying
generation by thirteen, which is what giving *every* built verb its stems would
cost. Restricted to prefixes it is **1.40**, on 40 real verbs from the snapshot
at both depth 2 and depth 3 — so the derivations file goes from 1.9 GB to
roughly 2.7 GB rather than to 25. Opening the *-idan* coinages (L16) added
**1.018** at depth 2 and **1.037** at depth 3, measured 2026-10-17 over 120
random non-verb readings of lexicon 1.2.0 (257,983 → 262,559 forms at depth 2).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from murfulu.engine.affix import (
    INFINITIVE,
    DerivedForm,
    Step,
    Word,
    apply,
    can_apply,
    with_prefix,
)
from murfulu.rules.pack import Rule, RulePack

#: Hard stop, from docs/ARCHITECTURE.md. Mechanical, not a judgement about
#: whether a long word is a good word.
MAX_DEPTH = 5

#: A backstop on the number of forms one call may build. Each step multiplies,
#: and a runaway generation is a bug, not a result. Reaching it is reported.
MAX_FORMS = 20_000

#: Suffixes that coin a verb whose stems are known, mapped to what is removed
#: from its past stem to leave its present stem, in Latin and in Persian.
#:
#: **Ruled by the linguist** (FOR_THE_LINGUIST L16, Telegram 2026-05-16
#: 11:38): a verb made from a noun or adjective with *-idan* has the past stem
#: *infinitive − an* and the present stem *past stem − id* — *sereštidan*,
#: *sereštid*, *serešt*. *-āndan* and *-ānidan* are deliberately absent: the
#: same message names them and does not state their present stem.
COINED_VERB_ENDINGS: dict[str, tuple[str, str]] = {"idan": ("id", "ید")}


@dataclass(frozen=True)
class Generation:
    """Everything one call produced, and whether it ran to completion."""

    forms: list[DerivedForm]
    depth_reached: int
    #: True when generation stopped because it hit MAX_FORMS rather than
    #: because no rule applied. Reported so a truncated result never looks
    #: complete.
    truncated: bool = False

    def at_depth(self, depth: int) -> list[DerivedForm]:
        """The forms that took exactly this many steps."""
        return [f for f in self.forms if len(f.path) == depth]


def _extend(parent_path: tuple[Step, ...], form: DerivedForm) -> DerivedForm:
    return replace(form, path=parent_path + form.path)


def _prefix(rule: Rule) -> str:
    """The prefix a rule adds, or the empty string when it adds none.

    Keyed on the affix and not the rule id on purpose — see the module note.
    """
    return rule.affix.strip("-") if rule.kind == "prefix" and rule.affix else ""


def _suffix(rule: Rule) -> str:
    """The suffix a rule adds, or the empty string when it adds none.

    Keyed on the affix and not the rule id, for the same reason as
    :func:`_prefix` and with a sharper case: N-093 and N-095 are both *-i*,
    N-074 and N-077 are both *-vār*, so a rule-id guard would let one follow
    the other and build *Goliyi* and *golvārvār* anyway.
    """
    return rule.affix.strip("-") if rule.kind == "suffix" and rule.affix else ""


#: The two stems of the verb a branch is currently inside, or ``None`` when
#: there is no verb or its stems are not known. Ordered as the lexicon holds
#: them: kārbon-e yek, then kārbon-e do.
Stems = tuple[Word, Word] | None


@dataclass(frozen=True)
class _Branch:
    """One place generation may continue from, and what it may not repeat."""

    base: Word
    path: tuple[Step, ...]
    #: The (form, rule) pairs already used on this path.
    seen: frozenset[tuple[str, str]]
    #: The prefixes already on this word.
    prefixes: frozenset[str]
    #: The suffixes already on this word.
    suffixes: frozenset[str]
    stems: Stems = None


def _coined_stems(rule: Rule, built: DerivedForm) -> Stems:
    """The stems of a verb coined with a suffix the linguist has ruled on.

    Read off the infinitive the rule just built, by his rule: remove *-an* for
    the past stem, then the ending in :data:`COINED_VERB_ENDINGS` for the
    present one. ``None`` when the suffix is not ruled on, or the built form
    does not end the way the rule says it must — a dead end rather than a
    stem cut in the wrong place.
    """
    ending = COINED_VERB_ENDINGS.get(_suffix(rule))
    if ending is None:
        return None
    cut_latin, cut_fa = ending
    infinitive_latin, infinitive_fa = INFINITIVE
    ends_as_infinitive = built.latin.endswith(infinitive_latin) and built.fa.endswith(
        infinitive_fa
    )
    if not ends_as_infinitive:
        return None
    past_latin = built.latin[: -len(infinitive_latin)]
    past_fa = built.fa[: -len(infinitive_fa)]
    if not (past_latin.endswith(cut_latin) and past_fa.endswith(cut_fa)):
        return None
    present_latin = past_latin[: -len(cut_latin)]
    present_fa = past_fa[: -len(cut_fa)]
    if not present_latin or not present_fa:
        return None
    return (
        Word(latin=past_latin, fa=past_fa, word_class="karbon_yek"),
        Word(latin=present_latin, fa=present_fa, word_class="karbon_do"),
    )


def _verb_built(
    rule: Rule, base: Word, stems: Stems, built: DerivedForm | None = None
) -> Stems:
    """The stems of the verb a rule just built, when they can be known.

    Four cases.

    **A prefix is transparent**, so a prefixed verb's stems are the stems it
    was built from with the prefix in front.

    **The infinitive ending on a verb's own past stem is not a new verb.**
    V-005 turns *andišid* into *andišidan*, which is the verb we already have
    written out in full — stem rule S-01 states the converse. Its stems are
    unchanged, and saying so is what lets the prefix land on them a step later.

    **A verb coined with *-idan* has stems the linguist stated** (L16):
    *Serešt* gives *sereštidan*, whose stems are *sereštid* and *serešt*. This
    needs no stems from the branch, because the verb is new — it is usually
    coined from a noun, which has none.

    **Anything else is a verb we cannot enter.** The causatives in *-āndan*
    and *-ānidan* coin a verb whose present stem nobody has stated. ``None``
    says the branch ends here rather than continuing on a guess.
    """
    if rule.kind == "suffix" and built is not None:
        coined = _coined_stems(rule, built)
        if coined is not None:
            return coined
    if stems is None:
        return None
    if rule.kind == "prefix":
        # A prefix rule reaching an infinitive takes either the infinitive or
        # the past stem, and in both cases the verb underneath is the one whose
        # stems are being carried. Anything else is not this verb.
        if base.word_class not in ("nabesudkarvaze", "karbon_yek"):
            return None
        return (with_prefix(rule, stems[0]), with_prefix(rule, stems[1]))
    if base.latin == stems[0].latin and (rule.affix or "").strip("-") == INFINITIVE[0]:
        return stems
    return None


def generate(
    pack: RulePack,
    word: Word,
    max_depth: int = MAX_DEPTH,
    max_forms: int = MAX_FORMS,
    stems: Stems = None,
) -> Generation:
    """Build every form reachable from ``word`` within ``max_depth`` steps.

    ``stems`` are the two stems of the verb ``word`` belongs to, when it is a
    verb. Given them, a prefixed verb the engine builds can be entered through
    its own prefixed stems; without them that verb is a dead end. Callers that
    do not know them pass nothing and lose only that.
    """
    forms: list[DerivedForm] = []
    truncated = False
    depth_reached = 0

    frontier = [_Branch(word, (), frozenset(), frozenset(), frozenset(), stems)]

    for depth in range(1, max_depth + 1):
        next_frontier: list[_Branch] = []
        for branch in frontier:
            base = branch.base
            for rule in pack.rules:
                if not can_apply(rule, base):
                    continue
                key = (base.latin, rule.id)
                if key in branch.seen:
                    # This rule already ran on this form further up the chain.
                    continue
                prefix = _prefix(rule)
                if prefix and prefix in branch.prefixes:
                    # This prefix is already on the word — farāzfarāz-.
                    continue
                suffix = _suffix(rule)
                if suffix and suffix in branch.suffixes:
                    # This suffix is already on the word — Golstānstān.
                    continue
                built = _extend(branch.path, apply(pack, rule, base))
                forms.append(built)
                if len(forms) >= max_forms:
                    return Generation(forms, depth, truncated=True)
                seen = branch.seen | {key}
                prefixes = branch.prefixes | {prefix} if prefix else branch.prefixes
                suffixes = branch.suffixes | {suffix} if suffix else branch.suffixes
                carried = branch.stems
                if built.word_class == "nabesudkarvaze":
                    # A verb was built. Its own stems, if they can be known,
                    # become bases in their own right — that is the whole of
                    # this change, and where hamandišande comes from.
                    carried = _verb_built(rule, base, branch.stems, built)
                    if carried is not None and carried != branch.stems:
                        # New stems only. A verb merely written out in full is
                        # the verb we are already standing on, and re-entering
                        # its stems would generate the same family twice.
                        next_frontier += [
                            _Branch(stem, built.path, seen, prefixes, suffixes, carried)
                            for stem in carried
                        ]
                next_frontier.append(
                    _Branch(
                        built.as_word(), built.path, seen, prefixes, suffixes, carried
                    )
                )
        if not next_frontier:
            break
        depth_reached = depth
        frontier = next_frontier

    return Generation(forms, depth_reached, truncated)
