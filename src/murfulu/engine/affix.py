"""Apply one rule to one word, in Latin and Persian together.

There is no Latin → Persian converter anywhere in this project. Both forms are
built side by side as the derivation runs: the Latin from the rule's ``affix``,
the Persian from its ``affix_fa``. That is why every affix carries both.

Capitalisation carries meaning in Behnevis. A word used as a noun is written
with a capital first letter, and a word used as an adjective or a participle is
not — which is how *Porsidan* (the asking) is told apart from *porsidan* (to
ask) in writing. The two are verb rows 5 and 6 of the grammar, identical except
for that. So the output's word class decides the case, and nothing else does.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from murfulu.engine.glides import join, join_fa
from murfulu.rules.conditions import check as check_condition
from murfulu.rules.pack import Rule, RulePack

#: Word classes written with a capital first letter: a word being used to name
#: something. Everything else stays lower-case.
CAPITALISED = {"karnam", "nam"}

#: The rule shapes this module can apply. Templates (compounding) need a second
#: word and are PLAN task 2.3; stem rules are a different operation again.
#:
#: **``infix`` was in this set and had no branch below**, so N-020 and N-023
#: fell through to the suffix case and put their affix on the *end*: the source
#: writes ``-nā-`` with a dash on both sides and its example is *delnāčasb* —
#: دل + نا + چسب — and the engine built *časbnā*, چسبنا. Wrong words, silently,
#: **27,361 types each and 115,682 forms in the live index**, reported at
#: middle-band productivity as though measured.
#:
#: They are compounding wearing another name: an infix sits *between two words*,
#: so like a slot or a template it needs a second word and belongs to PLAN 2.3.
#: Removed 2026-08-14 — a rule that builds nothing is better than one that
#: builds the wrong thing, which is this project's rule everywhere else.
SUPPORTED = {"suffix", "prefix", "none"}

#: The infinitive ending, in both scripts. Stem rule S-01 is the authority and
#: states the converse: *removing -an from the end of every infinitive leaves
#: kārbon-e yek*. So a stem plus -an is the infinitive, for every verb.
INFINITIVE = ("an", "ن")


class CannotApplyError(ValueError):
    """Raised when a rule does not fit the word it was given."""


@dataclass(frozen=True)
class Word:
    """A word going into the engine."""

    latin: str
    fa: str
    word_class: str


@dataclass(frozen=True)
class Step:
    """One rule application, kept so every result can explain itself."""

    rule_id: str
    affix: str
    #: What the rule was applied to. Needed to explain a chain, and to see
    #: whether a rule ever ran on the same form twice.
    base_latin: str = ""
    #: Set when the base was written one way and behaves another — *row*
    #: becoming *rav*. Recorded so the result can still explain itself.
    stem_form: str | None = None
    glide_id: str | None = None
    #: Glide rules that also matched. Non-empty means the grammar is ambiguous
    #: at this join, not that the engine was unsure.
    glide_alternatives: tuple[str, ...] = ()
    #: Whether the base met what the source says this rule takes, beyond its
    #: word class. **Three-valued on purpose.** True and False are answers;
    #: ``None`` means the source states no such condition, or states one we
    #: cannot test yet — and neither of those is the same as *failed*.
    #: See :mod:`murfulu.rules.conditions`.
    condition_met: bool | None = None
    #: The source's own words, when there is a condition. Kept so a result can
    #: say **why** rather than only that something did not match.
    condition_text: str = ""


@dataclass(frozen=True)
class DerivedForm:
    """A word the engine built, and how it got there."""

    latin: str
    fa: str
    word_class: str
    base_latin: str
    base_fa: str
    path: tuple[Step, ...] = ()
    semantic_tags: tuple[str, ...] = field(default_factory=tuple)

    def as_word(self) -> Word:
        """Feed this result back in as the base of another rule."""
        return Word(latin=self.latin, fa=self.fa, word_class=self.word_class)


def cased(latin: str, word_class: str) -> str:
    """Capitalise a form if its word class is one used to name something."""
    if not latin:
        return latin
    if word_class in CAPITALISED:
        return latin[0].upper() + latin[1:]
    return latin[0].lower() + latin[1:]


def _bare(affix: str) -> str:
    """The affix without the dashes that mark where it attaches."""
    return affix.strip("-")


def working_form(pack: RulePack, latin: str) -> tuple[str, str | None]:
    """The form a stem takes once something follows it.

    A stem written *row* is *rav* the moment anything is added — vowel or
    consonant. The *ow* spelling is only how it looks standing alone. Returns
    the working form and a note of the change, or the input unchanged.
    """
    for form in pack.stem_forms:
        if latin.lower().endswith(form.written.lower()):
            changed = latin[: len(latin) - len(form.written)] + form.working
            return changed, f"{form.written}->{form.working}"
    return latin, None


def can_apply(rule: Rule, word: Word) -> bool:
    """True when this rule is active, supported here, and fits this word."""
    return (
        rule.active
        and rule.kind in SUPPORTED
        and word.word_class in rule.input_types
        and bool(rule.output_types)
    )


def apply(pack: RulePack, rule: Rule, word: Word) -> DerivedForm:
    """Apply one rule to one word.

    Raises :class:`CannotApplyError` rather than returning something wrong: a
    rule that does not fit has no correct answer to give.
    """
    if not rule.active:
        raise CannotApplyError(f"{rule.id} is retired")
    if rule.kind not in SUPPORTED:
        raise CannotApplyError(
            f"{rule.id} is a {rule.kind} rule; this applies {sorted(SUPPORTED)}"
        )
    if word.word_class not in rule.input_types:
        raise CannotApplyError(
            f"{rule.id} takes {list(rule.input_types)}, not {word.word_class!r}"
        )

    # What the source says about the base, beyond its class. This never stops
    # the rule running — see murfulu/rules/conditions.py for why — it is
    # recorded so the result can be weighed.
    condition, met = check_condition(rule.id, word.latin)

    output_type = rule.output_types[0]
    affix = _bare(rule.affix or "")
    affix_fa = rule.affix_fa or ""
    glide_id: str | None = None
    alternatives: tuple[str, ...] = ()
    stem_form: str | None = None

    if rule.kind == "none" or not affix:
        # The base itself becomes the new word: Parhiz, Sāxt, Darxāst. Nothing
        # follows it, so it keeps the form it is written in. Only its class and
        # its capitalisation change.
        latin, form_fa = word.latin, word.fa
    elif rule.kind == "prefix":
        # A prefix goes in front, so the stem's own ending is untouched. Its
        # *capital* is dropped: سربلند is Sarbaland, not SarBaland.
        #
        # Settled by matching karbon, on the project lead's word, because the
        # linguist is behind that library. Measured over the whole snapshot:
        # **0 of 45,579 readings and 0 of 20,263 compounds carry a capital
        # after the first letter**, and 8,116 rows carry karbon's own
        # `[v7:rule12-cap]` marker, so capitalising the front alone is a rule
        # it applies rather than an accident. Ābādbum, Ābādjāi, Ābāngān.
        #
        # What the result *is* was already written on the first letter by
        # `cased`, so nothing is lost. See FOR_THE_LINGUIST L9.
        latin = affix + word.latin[0].lower() + word.latin[1:]
        form_fa = affix_fa + word.fa

        # **A prefix rule can still have to finish a word.** Seven rules —
        # V-070 to V-076 — take kārbon-e yek and say they produce a
        # nābesudkārvāže, which is an infinitive: *goft* gives *vāgoftan*. The
        # prefix alone left *vāgoft*, a past stem wearing the label of an
        # infinitive, and all seventeen of those rules' own examples end in
        # -an. The ending is S-01's, not a rule invented here.
        if output_type == "nabesudkarvaze" and word.word_class == "karbon_yek":
            latin += INFINITIVE[0]
            form_fa += INFINITIVE[1]
    else:
        # Something now follows the stem, so it takes its working form first.
        base, stem_form = working_form(pack, word.latin)
        joined = join(pack, base, affix)
        latin = joined.latin
        glide_id = joined.glide_id
        alternatives = joined.alternatives
        # The Persian needs the glide letter too, or the Latin and the Persian
        # drift apart into two different words — and where a گ follows, the
        # base's silent ه goes: بنده + گی is بندگی. See glides.join_fa.
        form_fa = join_fa(word.fa, word.latin, joined.infix_fa, affix_fa)

    return DerivedForm(
        latin=cased(latin, output_type),
        fa=form_fa,
        word_class=output_type,
        base_latin=word.latin,
        base_fa=word.fa,
        path=(
            Step(
                rule_id=rule.id,
                affix=rule.affix or "",
                base_latin=word.latin,
                stem_form=stem_form,
                glide_id=glide_id,
                glide_alternatives=alternatives,
                condition_met=met,
                condition_text=condition.source_text if condition else "",
            ),
        ),
        semantic_tags=rule.semantic_tags,
    )


def apply_all(pack: RulePack, word: Word) -> list[DerivedForm]:
    """Every form the pack can build from this word in one step."""
    return [apply(pack, rule, word) for rule in pack.rules if can_apply(rule, word)]


def with_prefix(rule: Rule, word: Word) -> Word:
    """The same word with a rule's prefix in front, and its class unchanged.

    **This is not a derivation and does not produce a word.** It exists for one
    job: a prefixed verb has prefixed stems. *ham-* on *andišidan* gives
    *hamandišidan*, whose kārbon-e yek is *hamandišid* and whose kārbon-e do is
    *hamandiš* — the prefix goes on both, because a Persian verbal prefix is
    transparent and leaves the verb underneath intact. Without those two stems
    nothing can be built from the new verb at all, and *hamandišande* is
    unreachable by any route. See :mod:`murfulu.engine.generate`.

    The join is the prefix branch of :func:`apply` and nothing else: in front,
    the base's capital dropped, no infinitive ending — a stem is not an
    infinitive. Glide rules do not run, for the same reason they do not run in
    :func:`apply`'s prefix branch: nothing follows the base, so its own ending
    is untouched.
    """
    if rule.kind != "prefix":
        raise CannotApplyError(f"{rule.id} is a {rule.kind} rule, not a prefix")
    affix = _bare(rule.affix or "")
    if not affix:
        raise CannotApplyError(f"{rule.id} has no affix to put in front")
    return Word(
        latin=affix + word.latin[0].lower() + word.latin[1:],
        fa=(rule.affix_fa or "") + word.fa,
        word_class=word.word_class,
    )
