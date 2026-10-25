"""Give each corpus spelling its Latin reading, where the lexicon has one.

Corpus text carries no vowels, so a spelling on its own cannot be matched
against a rule — رفتار and روش are just letters. The lexicon supplies the
reading, and this pass joins the two.

**A spelling can be several words.** مرد is *mard* and *mord*, and the corpus
cannot tell which was meant. Both readings are kept, each carrying the same
evidence, because throwing one away would be a guess.

Coverage is reported two ways and they answer different questions. *Type
coverage* is how much of the vocabulary we can read. **Token coverage is how
much of the running text we can read**, and it is the higher and more useful
number, because the words we know are also the words that occur most.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from murfulu.corpus.wordtypes import Corpus, WordType, normalise
from murfulu.lexicon.entries import Reading
from murfulu.lexicon.store import Lexicon


@dataclass(frozen=True)
class LinkedWordType:
    """One corpus spelling with one reading of it, or with none."""

    word: WordType
    #: None when the lexicon has no entry. That pile is the coverage gap and
    #: the review list, not an error.
    reading: Reading | None = None

    @property
    def spelling_fa(self) -> str:
        """The spelling as the corpus writes it."""
        return self.word.spelling_fa

    @property
    def latin(self) -> str | None:
        """The Latin reading, or None if the word is unlinked."""
        return self.reading.latin if self.reading else None

    @property
    def id(self) -> str:
        """``{spelling}:{latin}`` — the identity docs/ARCHITECTURE.md defines."""
        return f"{self.spelling_fa}:{self.latin or ''}"


@dataclass
class Coverage:
    """How much of the corpus the lexicon can read."""

    types_total: int = 0
    types_linked: int = 0
    tokens_total: int = 0
    tokens_linked: int = 0
    #: Spellings with more than one reading. The corpus cannot tell them
    #: apart, so both are kept and this counts how often that happens.
    ambiguous_types: int = 0

    @property
    def type_share(self) -> float:
        """Share of distinct spellings that got a reading."""
        return self.types_linked / self.types_total if self.types_total else 0.0

    @property
    def token_share(self) -> float:
        """Share of running text that got a reading."""
        return self.tokens_linked / self.tokens_total if self.tokens_total else 0.0

    def summary(self) -> str:
        """One line for the ingest log."""
        return (
            f"{self.types_linked:,}/{self.types_total:,} spellings linked "
            f"({self.type_share:.1%}), "
            f"{self.tokens_linked:,}/{self.tokens_total:,} words of text "
            f"({self.token_share:.1%})"
        )


@dataclass
class LinkResult:
    """Every corpus spelling, linked or not, with the coverage figures."""

    linked: list[LinkedWordType] = field(default_factory=list)
    coverage: Coverage = field(default_factory=Coverage)
    lexicon_snapshot_id: str = ""

    @property
    def unlinked(self) -> list[LinkedWordType]:
        """The spellings with no reading — the review list."""
        return [item for item in self.linked if item.reading is None]

    def biggest_gaps(self, limit: int = 20) -> list[LinkedWordType]:
        """The unlinked spellings that occur most. Fix these first."""
        return sorted(self.unlinked, key=lambda i: -i.word.total_count)[:limit]


def _index(lexicon: Lexicon) -> dict[str, list[Reading]]:
    """Every lexicon reading, keyed on the spelling as the corpus writes it.

    Both sides go through the same normalisation. Without it, a lexicon entry
    written with Arabic ي and a corpus word written with Persian ی are two
    different strings and silently fail to meet.
    """
    index: dict[str, list[Reading]] = {}
    for reading in lexicon.all_readings():
        index.setdefault(normalise(reading.spelling_fa), []).append(reading)
    return index


def link(corpus: Corpus, lexicon: Lexicon) -> LinkResult:
    """Attach a Latin reading to every corpus spelling that has one."""
    index = _index(lexicon)
    result = LinkResult(lexicon_snapshot_id=lexicon.snapshot_id)

    for spelling, word in corpus.word_types.items():
        result.coverage.types_total += 1
        result.coverage.tokens_total += word.total_count

        readings = index.get(spelling)
        if not readings:
            result.linked.append(LinkedWordType(word=word))
            continue

        result.coverage.types_linked += 1
        result.coverage.tokens_linked += word.total_count
        if len(readings) > 1:
            result.coverage.ambiguous_types += 1
        # One record per reading: the corpus cannot tell مرد the man from مرد
        # the dead, so both keep the same evidence.
        for reading in readings:
            result.linked.append(LinkedWordType(word=word, reading=reading))

    return result
