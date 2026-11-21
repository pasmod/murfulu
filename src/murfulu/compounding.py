"""Every compound the pack licenses for one word.

The sister of :mod:`murfulu.generation`, and it exists for the same reason:
the engine joins two words, the lexicon says which words there are, and
something has to put the two together without either of them knowing about a
database.

**Why this is not part of `/generate`.** It was measured before it was
designed: one ordinary noun makes **3,071** compounds, and the corpus holds
between **0.5% and 3.3%** of them. Folding that into a route whose answer is
already megabytes would bury it. So compounding gets its own route, and what
it returns is the *attested* pairings with the count of everything else beside
them — the same shape as a build group that opens at twenty and says what it
folds.

**Where the partners come from is what keeps this a sum.** A slot rule pins
one side to the caller's word and takes any verb stem on the other, so a noun
is asked against 3,071 stems rather than against every word in the dictionary.
Two free sides — N-104, *sar + ā + pā* — is a product over 43,225 headwords
and is offered only when the caller names the second word.

Nothing here asks the corpus. Attestation, the inflection check and the
ranking all belong to the route, because the engine may not know about
Elasticsearch.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from murfulu.engine.affix import CannotApplyError, Word
from murfulu.engine.compound import Filler, Verb, fill, fill_slot, parts_used
from murfulu.engine.compound import front_classes as slot_front_classes
from murfulu.generation import WordNotFoundError, ordered
from murfulu.lexicon.bank import is_excluded, word_classes_of
from murfulu.lexicon.categories import UnmappableCategoryError
from murfulu.lexicon.entries import Reading
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import Rule, RulePack

#: The two kinds of compounding rule this module drives. `template` fills a
#: pattern from one verb's two stems; `slot` joins a word to a verb stem with
#: nothing between them.
TEMPLATE = "template"
SLOT = "slot"


@dataclass(frozen=True)
class Pairing:
    """One compound, and the two words it joins.

    Both halves are kept rather than only the result, because the whole
    question a reader has about a compound is *what was joined to what* — and
    because the second half is the part they did not choose.
    """

    latin: str
    fa: str
    word_class: str
    rule_id: str
    front_fa: str
    front_latin: str
    behind_fa: str
    behind_latin: str
    #: Which side the caller's own word filled. A compound is not symmetrical
    #: and a reader has to know which half was theirs.
    role: str = "front"

    #: What each half **is** — `nam`, `karbon_do` — which is the rule's own
    #: condition applied to these two words. The rule label says *نام + کاربن
    #: دو*; these say which word answered which side of it.
    front_class: str = ""
    behind_class: str = ""

    #: The infinitive the behind half is a stem of, where there is one. A
    #: slot rule puts any verb stem behind the caller's word, so this is the
    #: only thing that makes the second half checkable.
    behind_of_fa: str = ""
    behind_of_latin: str = ""


@dataclass(frozen=True)
class Result:
    """Every compound one reading licenses, with what was tried."""

    reading: Reading
    pairings: list[Pairing] = field(default_factory=list)
    #: How many partner words were offered to the rules. The denominator of
    #: everything the route says about coverage.
    partners_tried: int = 0
    #: Rules that could not be exercised from this reading at all, with why.
    #: Absent is not the same as *built nothing*.
    skipped: dict[str, str] = field(default_factory=dict)

    #: What this reading counts as — `nam`, `karnam` — and what the slot rules
    #: want in front. **A word can be shut out of every compounding rule
    #: without anything being wrong**: کار is filed اسم معنی, which the source
    #: grammar makes a کارنام, and all six slot rules take a نام. That is L18,
    #: and a screen showing a bare ۰ cannot say it. Both sides are carried so
    #: the sentence can be written from data rather than guessed at.
    front_classes: tuple[str, ...] = ()
    slot_wants: tuple[str, ...] = ()


@dataclass(frozen=True)
class Partners:
    """The verb stems a slot rule may put behind a word.

    Read once and reused: it is one pass over every verb in the snapshot, and
    a route that rebuilt it per request would read 1,705 rows to answer one
    question.
    """

    verbs: tuple[Verb, ...] = ()

    def __len__(self) -> int:
        """How many verbs are on offer, not how many stems."""
        return len(self.verbs)


def partners_from(lexicon: Lexicon) -> Partners:
    """Every verb in the snapshot that has both stems written."""
    found = []
    for reading in lexicon.infinitives():
        # A verb the linguist keeps out of word formation is no partner either.
        if not reading.has_both_stems or is_excluded(reading):
            continue
        found.append(
            Verb(
                past_stem=Word(
                    latin=reading.past_stem_latin or "",
                    fa=reading.past_stem_fa or "",
                    word_class="karbon_yek",
                ),
                present_stem=Word(
                    latin=reading.present_stem_latin or "",
                    fa=reading.present_stem_fa or "",
                    word_class="karbon_do",
                ),
                infinitive=Word(
                    latin=reading.latin,
                    fa=reading.spelling_fa,
                    word_class="nabesudkarvaze",
                ),
            )
        )
    return Partners(verbs=tuple(found))


def _as_verb(reading: Reading) -> Verb | None:
    """The reading seen as a verb, or None when it is not one.

    None too for a verb the linguist keeps out of word formation.
    """
    if is_excluded(reading) or not (reading.is_infinitive and reading.has_both_stems):
        return None
    return Verb(
        past_stem=Word(
            latin=reading.past_stem_latin or "",
            fa=reading.past_stem_fa or "",
            word_class="karbon_yek",
        ),
        present_stem=Word(
            latin=reading.present_stem_latin or "",
            fa=reading.present_stem_fa or "",
            word_class="karbon_do",
        ),
        infinitive=Word(
            latin=reading.latin,
            fa=reading.spelling_fa,
            word_class="nabesudkarvaze",
        ),
    )


def _as_words(reading: Reading) -> list[Word]:
    """The reading as the plain words a slot's front may hold."""
    try:
        classes = word_classes_of(reading)
    except UnmappableCategoryError:
        # A category we deliberately did not map. Not an error, and an empty
        # answer here is the honest one.
        return []
    return [
        Word(latin=latin, fa=reading.spelling_fa, word_class=name)
        for name in classes
        for latin in reading.all_latin
    ]


def _compounding_rules(pack: RulePack, kind: str) -> list[Rule]:
    return [rule for rule in pack.rules if rule.kind == kind and rule.active]


def templates_for(
    pack: RulePack, first: Filler, second: Filler | None = None
) -> list[Pairing]:
    """Every template that can be filled from these one or two verbs.

    `fill` refuses a rule whose slots say *the same verb* when a second is
    given, and one that says *a different verb* when none is — so the caller
    passes what it has and the engine decides which rules apply.
    """
    made = []
    for rule in _compounding_rules(pack, TEMPLATE):
        try:
            form = fill(rule, first, second)
        except (CannotApplyError, ValueError, KeyError):
            continue
        # The halves the rule actually used, which are not always the past
        # stem in front and the present stem behind.
        parts = parts_used(rule, first, second)
        front, behind = (parts + parts)[:2] if parts else (None, None)
        made.append(
            Pairing(
                latin=form.latin,
                fa=form.fa,
                word_class=form.word_class,
                rule_id=rule.id,
                front_fa=front.fa if front else "",
                front_latin=front.latin if front else "",
                behind_fa=behind.fa if behind else "",
                behind_latin=behind.latin if behind else "",
                role="both",
                front_class=front.word_class if front else "",
                behind_class=behind.word_class if behind else "",
            )
        )
    return made


def _from_templates(pack: RulePack, reading: Reading) -> tuple[list[Pairing], str]:
    """The patterns that draw both halves from one verb.

    A template needs a verb, so a noun gets nothing here and is told why
    rather than shown an empty list.
    """
    verb = _as_verb(reading)
    if verb is None:
        return [], "a template joins one verb's two stems; this is not a verb"
    return templates_for(pack, verb), ""


def _from_slots(
    pack: RulePack, reading: Reading, partners: Partners
) -> tuple[list[Pairing], str, tuple[str, ...]]:
    """The six slot rules: the caller's word in front, any verb stem behind.

    Returns what was built, why nothing was where nothing was, and the front
    classes the rules ask for — which is half of the answer to *why zero*.
    """
    fronts = _as_words(reading)
    # **Not `wanted`.** The inner loop over `rule.input_types` binds that name
    # for the *behind* class, so the front classes came back as `karbon_do`
    # on every successful reading — caught against دست before it shipped.
    front_wanted = tuple(
        sorted(
            {
                name
                for rule in _compounding_rules(pack, SLOT)
                for name in slot_front_classes(rule)
            }
        )
    )
    if not fronts:
        return (
            [],
            "no word class is mapped for this reading's category",
            front_wanted,
        )
    made = []
    fits = False
    for rule in _compounding_rules(pack, SLOT):
        allowed = slot_front_classes(rule)
        for front in fronts:
            if front.word_class not in allowed:
                continue
            fits = True
            for verb in partners.verbs:
                for wanted in rule.input_types:
                    try:
                        behind = verb.stem(wanted)
                        form = fill_slot(rule, front, behind)
                    except (CannotApplyError, ValueError, KeyError):
                        continue
                    made.append(
                        Pairing(
                            latin=form.latin,
                            fa=form.fa,
                            word_class=form.word_class,
                            rule_id=rule.id,
                            front_fa=front.fa,
                            front_latin=front.latin,
                            behind_fa=behind.fa,
                            behind_latin=behind.latin,
                            role="front",
                            front_class=front.word_class,
                            behind_class=behind.word_class,
                            behind_of_fa=verb.infinitive.fa if verb.infinitive else "",
                            behind_of_latin=(
                                verb.infinitive.latin if verb.infinitive else ""
                            ),
                        )
                    )
    if not fits:
        # Mapped, and refused by every rule. A different fact from *not
        # mapped*, and the one that leaves a reader looking at a bare zero.
        have = ", ".join(sorted({front.word_class for front in fronts}))
        return (
            [],
            f"the slot rules take {', '.join(front_wanted)} in front; this "
            f"reading is {have}",
            front_wanted,
        )
    return made, "", front_wanted


def from_reading(pack: RulePack, reading: Reading, partners: Partners) -> Result:
    """Every compound this one reading licenses.

    Duplicates are kept, because two rules producing the same letters is
    information: V-078 and V-079 both write *soxanguy* and mean different
    things by it — the doer and the done-to.
    """
    made: list[Pairing] = []
    skipped: dict[str, str] = {}

    from_slots, why_not, wanted = _from_slots(pack, reading, partners)
    made += from_slots
    if why_not:
        skipped[SLOT] = why_not

    from_templates, why_not = _from_templates(pack, reading)
    made += from_templates
    if why_not:
        skipped[TEMPLATE] = why_not

    return Result(
        reading=reading,
        pairings=made,
        partners_tried=len(partners),
        skipped=skipped,
        front_classes=tuple(sorted({one.word_class for one in _as_words(reading)})),
        slot_wants=wanted,
    )


def from_word(
    lexicon: Lexicon, pack: RulePack, word: str, partners: Partners
) -> list[Result]:
    """Look a word up and compound from every reading of it.

    One result per reading, never a merged pile — the same rule `/generate`
    follows, and for the same reason: مرد is *mard* and *mord*.
    """
    readings = _own(lexicon, _readings_for(lexicon, word))
    return [from_reading(pack, reading, partners) for reading in ordered(readings)]


def _own(lexicon: Lexicon, readings: list[Reading]) -> list[Reading]:
    """`own_readings` against every entry written with the same letters.

    Not only against what the lookup returned: asked for *Dal* by its Latin,
    the lexicon returns the tree alone, and the heart that owns *Del* has to
    be fetched to be seen.
    """
    siblings = {
        spelling: lexicon.by_spelling(spelling)
        for spelling in {reading.spelling_fa for reading in readings}
    }
    return own_readings(readings, siblings)


def own_readings(
    readings: list[Reading], siblings: dict[str, list[Reading]] | None = None
) -> list[Reading]:
    """Each reading with only the second readings that are its own.

    karbon lists a second reading on some entries that is **another entry's own
    reading of the same letters**. دل is four entries — *Dal* (a tree, in the
    Hamadan dialect), *Dol* (an ailment), *Del* (the heart) and the adjective
    *dall* — and the first two both carry *Del* as their second reading. Built
    from, it filed دلبر and دلدار under the tree and the ailment as well as
    under the heart, and the page opened on the tree. Measured on karbon 1.3.2:
    447 readings in 372 spellings carry another entry's reading this way.

    Such a variant is dropped from the reading that borrows it. The entry whose
    reading it is still builds those letters with that Latin, because a
    compound drops the front's capital; where the two entries are of different
    classes, only the owner's rules build them now. Compared without case, as
    the corpus check compares (*nami* is *Nami*). A second reading that no
    other entry has — آبرو's *Ābrov* — is kept.

    **Only entries with the same letters count.** A lookup by Latin can return
    two spellings — *Čoquk* is چغوک, and چقوک's *Čaquk* lists *Čoquk* as its
    second reading — and that variant is چقوک's own, not چغوک's. ``siblings``
    maps a spelling to every entry written that way; without it, the readings
    passed in are their own siblings.
    """
    kept = []
    for reading in readings:
        group = (siblings or {}).get(reading.spelling_fa) or [
            one for one in readings if one.spelling_fa == reading.spelling_fa
        ]
        others = {one.latin.lower() for one in group if _entry(one) != _entry(reading)}
        variants = tuple(
            one for one in reading.latin_variants if one.lower() not in others
        )
        kept.append(
            reading
            if variants == reading.latin_variants
            else replace(reading, latin_variants=variants)
        )
    return kept


def _entry(reading: Reading) -> tuple[str, str, tuple[int, ...]]:
    """What makes a reading one dictionary entry, whichever lookup returned it."""
    return (reading.spelling_fa, reading.latin, reading.source_entry_ids)


def from_two_words(
    lexicon: Lexicon, pack: RulePack, word: str, partner: str
) -> list[Result]:
    """Join two named words, every way the pack allows.

    This is the only way to reach the rules with two free sides. It also lets
    a caller ask about one specific pairing rather than about a noun's whole
    3,071, which is what somebody coining a word actually wants.

    A partner that is a verb is offered through **both** its stems, never
    through its infinitive — the same rule the rest of the system follows.

    **Naming a partner must not lose the templates**, which is what the first
    version did: `/compound?word=بودن` gave *Budonabud* and
    `?word=بودن&partner=بودن` gave nothing, because the two words were joined
    as plain words and a template needs whole verbs. Both halves are now
    offered as verbs where they are verbs — which is also the only way to
    reach V-017, V-019, V-043 and V-047, the four rules that join *two
    different* verbs and were unreachable by any route.
    """
    fronts = _own(lexicon, _readings_for(lexicon, word))
    behinds = _own(lexicon, _readings_for(lexicon, partner))

    results = []
    for reading in ordered(fronts):
        made = []
        front_verb = _as_verb(reading)
        for front in _as_words(reading):
            for other in behinds:
                for behind in _as_words(other):
                    made += joined(pack, front, behind)
                other_verb = _as_verb(other)
                if other_verb is not None:
                    made += joined(pack, front, other_verb.present_stem)
                    made += joined(pack, front, other_verb.past_stem)
        made += _templates_across(pack, front_verb, behinds)
        results.append(
            Result(reading=reading, pairings=made, partners_tried=len(behinds))
        )
    return results


def _templates_across(
    pack: RulePack, front_verb: Verb | None, behinds: list[Reading]
) -> list[Pairing]:
    """Templates between the front verb and each partner that is also a verb.

    Two calls per pair, because the pack has both kinds and each refuses the
    other's shape: with a second verb only the *different verb* rules fire,
    and with none only the *same verb* rules do. Asking for a verb against
    itself is how a caller reaches the same-verb templates by name.
    """
    if front_verb is None:
        return []
    made: list[Pairing] = []
    for other in behinds:
        other_verb = _as_verb(other)
        if other_verb is None:
            continue
        made += templates_for(pack, front_verb, other_verb)
        if other_verb == front_verb:
            made += templates_for(pack, front_verb)
    return made


def _readings_for(lexicon: Lexicon, word: str) -> list[Reading]:
    """Every reading of a word, by spelling or by Latin form."""
    found = (
        lexicon.by_spelling(word)
        or lexicon.by_normalized_spelling(word)
        or lexicon.by_latin(word)
    )
    if not found:
        raise WordNotFoundError(f"the lexicon has no entry for {word!r}")
    return found


def joined(pack: RulePack, front: Word, behind: Word) -> list[Pairing]:
    """Two words the caller named, put through every rule that accepts them.

    This is the only way to reach the rules with two free sides — N-104 joins
    two nouns, which over the whole dictionary would be a product of 43,225
    against itself. Naming the second word turns it back into one answer.
    """
    made = []
    for rule in pack.rules:
        if not rule.active or rule.kind not in (SLOT, TEMPLATE):
            continue
        try:
            if rule.kind == SLOT:
                if front.word_class not in slot_front_classes(rule):
                    continue
                form = fill_slot(rule, front, behind)
            else:
                form = fill(rule, front, behind)
        except (CannotApplyError, ValueError, KeyError):
            continue
        made.append(
            Pairing(
                latin=form.latin,
                fa=form.fa,
                word_class=form.word_class,
                rule_id=rule.id,
                front_fa=front.fa,
                front_latin=front.latin,
                behind_fa=behind.fa,
                behind_latin=behind.latin,
                role="both",
            )
        )
    return made
