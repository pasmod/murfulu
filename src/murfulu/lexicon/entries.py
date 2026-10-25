"""What a lexicon lookup returns.

The unit of record is a **reading**, not a spelling: مرد is two words, *mard*
and *mord*, and they must never be merged. Rows that carry the same spelling
*and* the same reading are the dictionary listing one word in several senses;
those collapse into one reading, but every source row id is kept so the senses
stay reachable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: The lexicon category that marks an infinitive. Verbs are the only entries
#: that carry stems.
INFINITIVE_CATEGORY = "مصدر"


@dataclass(frozen=True)
class Reading:
    """One word: one spelling with one Latin form.

    ``source_entry_ids`` and ``sense_count`` are what make a collapsed record
    honest — a reading built from four dictionary entries says so, and each
    entry can still be looked up.
    """

    spelling_fa: str
    spelling_normalized: str
    latin: str

    #: Other readings the lexicon records for this same word — آبرو is *Ābrav*
    #: **or** *Ābrov*. Real alternatives, not spelling noise: 7,212 rows carry
    #: one. Generating from only the first would build a whole family of words
    #: on a reading the dictionary does not commit to.
    latin_variants: tuple[str, ...] = ()

    #: The lexicon's own categories (اسم ذات، صفت مرکب، مصدر…). Plural because
    #: collapsed rows do not always agree; ``lexicon_category`` is the first.
    #: Mapping these to the word classes the rules match on is a separate task.
    lexicon_categories: tuple[str | None, ...] = ()

    past_stem_fa: str | None = None
    past_stem_latin: str | None = None
    present_stem_fa: str | None = None
    present_stem_latin: str | None = None

    #: The dictionary's own definition, as the snapshot holds it. **A preview,
    #: not a definition**: karbon cuts it at 200 characters and 12,072 of the
    #: 43,816 are cut mid-word, so it is shown as an opening rather than as a
    #: complete sense. Every word class has one for 100% of its rows **except
    #: مصدر, which has none at all** — so a verb, which is what the build
    #: screen mostly starts from, still says nothing about what it means.
    definition_fa: str | None = None

    transitivity: str | None = None
    phonemic_confidence: float | None = None
    needs_review: bool = False

    #: karbon's own stem-rule number. Stored, clearly labelled, and **never
    #: used for logic** — it does not correspond to the source grammar's rules
    #: 1–9. See docs/LEXICON_ANALYSIS.md.
    karbon_stem_rule: int | None = None

    source_entry_ids: tuple[int, ...] = field(default_factory=tuple)
    sense_count: int = 0

    #: Which snapshot this came out of. Travels with the record.
    snapshot_id: str = ""

    @property
    def lexicon_category(self) -> str | None:
        """The first of the collapsed rows' categories, or None."""
        return self.lexicon_categories[0] if self.lexicon_categories else None

    @property
    def all_latin(self) -> tuple[str, ...]:
        """Every reading of this word, the primary one first."""
        return (self.latin, *self.latin_variants)

    @property
    def is_infinitive(self) -> bool:
        """True when the lexicon calls this a مصدر."""
        return INFINITIVE_CATEGORY in self.lexicon_categories

    @property
    def has_both_stems(self) -> bool:
        """True when both Latin stems are present."""
        return bool(self.past_stem_latin and self.present_stem_latin)
