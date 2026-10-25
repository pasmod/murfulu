"""Build compound words: *Zadoxord*, *Goftogu*, *Kešākeš*, *Budonabud*.

A compounding rule is a pattern with two typed slots and a letter between them::

    {a} + o + {b}     zad + o + xord   = Zadoxord

The slots are filled from verb stems, and each rule says where the second one
may come from:

``same_verb``        both slots from one verb — *goft* and *gu* give *Goftogu*
``different_verb``   two different verbs — *zadan* and *xordan*
``same_stem``        the same stem twice — *keš* + ā + *keš* = *Kešākeš*
``different_stem``   two different present stems
``negated``          the slot is preceded by *na* — *Budonabud*

Free compounding of any two words is not attempted anywhere in this project.
Only the combinations the source grammar licenses exist, and they exist as
template rules, so this module needs no rules of its own.
"""

from __future__ import annotations

from dataclasses import dataclass

from murfulu.engine.affix import CannotApplyError, DerivedForm, Step, Word, cased
from murfulu.rules.pack import Rule

#: Constraints that need a second, different verb supplied.
NEEDS_SECOND = {"different_verb", "different_stem"}

#: Constraints that say both slots come from one verb, so a second is wrong.
FORBIDS_SECOND = {"same_verb", "same_stem"}


@dataclass(frozen=True)
class Verb:
    """One verb's two stems, which is what a verb compounding rule draws on."""

    past_stem: Word
    present_stem: Word

    #: The infinitive the two stems were read off, where the caller knows it.
    #: **Not used to build anything** — it is carried so a reader can be told
    #: where the half they did not choose came from. دستور is دست + ور and ور
    #: is the present stem of وشتن; without this the screen shows a bare ور
    #: and the reader cannot check the claim, which is the one thing they are
    #: there to do. Optional, because the two-stem rules never need it.
    infinitive: Word | None = None

    def stem(self, word_class: str) -> Word:
        """The stem a slot of this type wants."""
        if word_class == "karbon_yek":
            return self.past_stem
        if word_class == "karbon_do":
            return self.present_stem
        raise CannotApplyError(
            f"a compounding slot asked for {word_class!r}; a verb has only "
            f"karbon_yek and karbon_do"
        )


#: What can fill a slot: a verb, whose two stems the rule picks between, or a
#: plain word for the rules that join nouns (N-104, Sarāsar).
Filler = Verb | Word


def _part(filler: Filler, word_class: str) -> Word:
    if isinstance(filler, Verb):
        return filler.stem(word_class)
    if filler.word_class != word_class:
        raise CannotApplyError(
            f"a slot wants {word_class!r} but was given {filler.word_class!r}"
        )
    return filler


def _needs_second_verb(rule: Rule) -> bool:
    return any(slot.get("constraint") in NEEDS_SECOND for slot in rule.slots)


def _forbids_second(rule: Rule) -> bool:
    """True only when the rule states both halves come from one verb.

    A rule with no constraint at all — N-104, *sar + ā + pā* — may take two
    different words, so silence is not a prohibition.
    """
    return any(slot.get("constraint") in FORBIDS_SECOND for slot in rule.slots)


def fill(rule: Rule, first: Filler, second: Filler | None = None) -> DerivedForm:
    """Fill a template rule's slots and return the compound.

    Raises :class:`CannotApplyError` when the rule needs a second verb and none
    was given, rather than quietly compounding a word with itself.
    """
    if rule.kind != "template":
        raise CannotApplyError(f"{rule.id} is a {rule.kind} rule, not a template")
    if not rule.active:
        raise CannotApplyError(f"{rule.id} is retired")

    needs_second = _needs_second_verb(rule)
    if needs_second and second is None:
        raise CannotApplyError(
            f"{rule.id} joins two different verbs; a second verb is required"
        )
    if _forbids_second(rule) and second is not None:
        raise CannotApplyError(
            f"{rule.id} takes both parts from one verb; a second was given"
        )

    latin = (rule.pattern or "").replace(" + ", "")
    fa = rule.pattern_fa or ""
    for index, slot in enumerate(rule.slots):
        source = second if (index and second is not None) else first
        stem = _part(source, slot["type"])
        latin = latin.replace(f"{{{slot['name']}}}", stem.latin)
        fa = fa.replace(f"{{{slot['name']}}}", stem.fa)

    output_type = rule.output_types[0]
    return DerivedForm(
        latin=cased(latin, output_type),
        fa=fa,
        word_class=output_type,
        base_latin=first.past_stem.latin if isinstance(first, Verb) else first.latin,
        base_fa=first.past_stem.fa if isinstance(first, Verb) else first.fa,
        path=(
            Step(
                rule_id=rule.id,
                affix=rule.pattern or "",
                base_latin=first.past_stem.latin
                if isinstance(first, Verb)
                else first.latin,
            ),
        ),
        semantic_tags=rule.semantic_tags,
    )


def parts_used(
    rule: Rule, first: Filler, second: Filler | None = None
) -> tuple[Word, ...]:
    """Which word actually filled each of a template's slots.

    A caller cannot work this out from the rule: slot *b* of V-021 is the same
    verb's **past** stem and slot *a* of V-044 is its **present** stem, so a
    route that reported "past stem in front, present stem behind" named the
    wrong half of every negated template — *Didonadid* was published as دید
    joined to بین. The engine decides it, so the engine says it.
    """
    return tuple(
        _part(second if (index and second is not None) else first, slot["type"])
        for index, slot in enumerate(rule.slots)
    )


#: What a slot rule's ``affix`` says stands in **front**. The rule's own
#: ``input_types`` describe the word behind it, so between the two the whole
#: shape is stated: *Nām-* + kārboné do is "a noun, then a present stem".
FRONT_CLASS: dict[str, tuple[str, ...]] = {
    # soxan + guy, češm + dāšt, dast + duz, xod + parast.
    "Nām-": ("nam",),
    # xoš + nevis, tond + row, dir + yāb — a manner word, not a noun.
    "Čonvāže-": ("barnam",),
}


def front_classes(rule: Rule) -> tuple[str, ...]:
    """Which word classes may stand in front of this slot rule."""
    return FRONT_CLASS.get(rule.affix or "", ())


def fill_slot(rule: Rule, front: Word, behind: Word) -> DerivedForm:
    """Join a slot rule's two words: *soxan* + *guy* → *soxanguy*.

    **Nothing goes between them**, which is what the source's dash means, and
    the front word keeps its own spelling — a compound is two words written
    together, not a stem with something added.
    """
    if rule.kind != "slot":
        raise CannotApplyError(f"{rule.id} is a {rule.kind} rule, not a slot")
    if not rule.active:
        raise CannotApplyError(f"{rule.id} is retired")
    allowed = front_classes(rule)
    if not allowed:
        raise CannotApplyError(
            f"{rule.id} says {rule.affix!r} stands in front, which is not a "
            f"class this knows"
        )
    if front.word_class not in allowed:
        raise CannotApplyError(
            f"{rule.id} wants {list(allowed)} in front, not {front.word_class!r}"
        )
    if behind.word_class not in rule.input_types:
        raise CannotApplyError(
            f"{rule.id} takes {list(rule.input_types)} behind, "
            f"not {behind.word_class!r}"
        )

    output_type = rule.output_types[0]
    return DerivedForm(
        latin=cased(front.latin + behind.latin, output_type),
        fa=front.fa + behind.fa,
        word_class=output_type,
        base_latin=front.latin,
        base_fa=front.fa,
        path=(
            Step(
                rule_id=rule.id,
                # A compound has no affix, so the **other word** goes where one
                # would: it is what a reader needs to see, and it is a word.
                affix=behind.latin,
                base_latin=front.latin,
            ),
        ),
        semantic_tags=rule.semantic_tags,
    )
