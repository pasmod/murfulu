"""Persian word in, derived words out.

The one place the three halves of the system meet: the lexicon says what a word
*is*, the rule pack says what may be done to it, and the engine does it. Nothing
below this module imports across those lines — ``engine`` never sees the
lexicon, and ``lexicon`` never sees a rule.

A verb is generated from **both** its stems. *raftan* gives *Raftār* from the
past stem and *Raveš* from the present one, and a reader asking about the verb
wants both.

A word the lexicon reads two ways is generated from **both readings**. آبرو is
*Ābrav* or *Ābrov*, and 7,212 entries are like it. No verb is: the stems are
stored separately and carry no variants.

**The two stems are handed to the engine as a pair, not only one at a time.** A
prefix builds a new verb — *ham-* on *andišidan* — and that verb needs both of
its own stems before anything can be built from it. Only this module knows
them: a present stem is irregular and is read from the lexicon, never worked
out from the past one.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from murfulu.engine import (
    DerivedForm,
    GroupedForm,
    Meaning,
    Word,
    compose,
    deduplicate,
    generate,
)
from murfulu.lexicon.categories import UnmappableCategoryError, word_classes_for
from murfulu.lexicon.entries import Reading
from murfulu.lexicon.store import Lexicon
from murfulu.rules.pack import RulePack

#: How deep to go by default. Two steps reach *Ravandegi*; deeper is generated
#: on request, per docs/ARCHITECTURE.md.
DEFAULT_DEPTH = 2


class WordNotFoundError(LookupError):
    """Raised when the lexicon has no reading for the word asked about."""


@dataclass(frozen=True)
class Result:
    """Everything one word produced, with what it was built from."""

    reading: Reading
    forms: list[GroupedForm] = field(default_factory=list)
    meanings: dict[str, Meaning] = field(default_factory=dict)
    #: The starting points used. A verb has two; anything else has one.
    bases: tuple[Word, ...] = ()
    truncated: bool = False

    def meaning_of(self, latin: str) -> Meaning | None:
        """What a form means, if any of its tags has a written template."""
        return self.meanings.get(latin)


def bases_of(reading: Reading) -> list[Word]:
    """The starting points a reading offers.

    A verb is entered through its two stems, never through the infinitive: the
    rules attach to *kārbon-e yek* and *kārbon-e do*, not to *raftan*.
    """
    if reading.is_infinitive and reading.has_both_stems:
        return [
            Word(
                latin=reading.past_stem_latin or "",
                fa=reading.past_stem_fa or "",
                word_class="karbon_yek",
            ),
            Word(
                latin=reading.present_stem_latin or "",
                fa=reading.present_stem_fa or "",
                word_class="karbon_do",
            ),
        ]

    try:
        classes = word_classes_for(reading.lexicon_category)
    except UnmappableCategoryError:
        # A category we deliberately did not map. Not an error: it means we
        # decided not to guess, and the caller should see an empty result.
        return []
    # Every reading the lexicon records, not only the first. آبرو is Ābrav
    # *or* Ābrov, and building on one alone would produce a whole family of
    # words on a reading the dictionary does not commit to.
    return [
        Word(latin=latin, fa=reading.spelling_fa, word_class=name)
        for name in classes
        for latin in reading.all_latin
    ]


def from_reading(
    pack: RulePack, reading: Reading, depth: int = DEFAULT_DEPTH
) -> Result:
    """Build everything reachable from one lexicon reading."""
    bases = bases_of(reading)
    # A verb's two stems, so a verb the engine *builds* can be entered through
    # its own prefixed stems: ham- on andišidan gives hamandišidan, whose
    # kārbon-e do is hamandiš, which is the only route to hamandišande. The
    # engine cannot work this out alone — a present stem is irregular and is
    # read from the lexicon, never from the past stem.
    stems = (bases[0], bases[1]) if reading.is_infinitive and len(bases) == 2 else None
    built = []
    truncated = False
    for base in bases:
        run = generate(pack, base, max_depth=depth, stems=stems)
        built.extend(run.forms)
        truncated = truncated or run.truncated

    forms = deduplicate(built)
    meanings = {}
    for form in forms:
        meaning = compose(pack, _as_derived(form))
        if meaning:
            meanings[form.latin] = meaning

    return Result(
        reading=reading,
        forms=forms,
        meanings=meanings,
        bases=tuple(bases),
        truncated=truncated,
    )


def _as_derived(form: GroupedForm) -> DerivedForm:
    """A grouped form seen as a single derivation, for composing its meaning."""
    return DerivedForm(
        latin=form.latin,
        fa=form.fa,
        word_class=form.word_class,
        base_latin=form.base_latin,
        base_fa=form.base_fa,
        path=form.shortest_path,
        semantic_tags=form.semantic_tags,
    )


def from_word(
    lexicon: Lexicon,
    pack: RulePack,
    word: str,
    depth: int = DEFAULT_DEPTH,
) -> list[Result]:
    """Look a Persian word up and build from every reading of it.

    One spelling can be several words — مرد is *mard* and *mord* — so this
    returns one result per reading, never a merged pile.
    """
    readings = lexicon.by_spelling(word)
    if not readings:
        readings = lexicon.by_normalized_spelling(word)
    if not readings:
        readings = lexicon.by_latin(word)
    if not readings:
        raise WordNotFoundError(
            f"{word!r} is not in lexicon snapshot {lexicon.snapshot_id}"
        )
    return [from_reading(pack, reading, depth) for reading in ordered(readings)]


def ordered(readings: list[Reading]) -> list[Reading]:
    """Put the readings the dictionary trusts first.

    They arrived in the lexicon's row order, which is arbitrary, and the screen
    opens on the first — so بلند opened on **Baland**, which the dictionary has
    itself flagged ``needs_review`` at confidence 0.4, and built *Sarbalandi*.
    Its clean reading is *boland*, and the same snapshot spells سربلند
    ``sarboland``, so it contradicted itself.

    **This is an order, not a filter.** Every reading is still returned, still
    built from, and still reachable; only which one the screen opens on
    changes. The dictionary's own flag decides it, so no reading of Persian is
    being made here — which of بلند's readings is right is the linguist's, and
    is open question S13.
    """
    return sorted(
        readings,
        key=lambda reading: (
            reading.needs_review,
            -(reading.phonemic_confidence or 0.0),
        ),
    )
