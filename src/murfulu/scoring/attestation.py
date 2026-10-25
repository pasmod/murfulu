"""Has this word ever actually been used.

Three answers, and the difference between them matters:

``reading``   the corpus has this spelling **and** the lexicon reads it the way
              we built it. The strongest answer.
``spelling``  the corpus has the spelling, but under a different reading — or
              under none, because the lexicon has no entry. The letters exist;
              the word we built may not.
``none``      not found. **Never "does not exist"** — only "not found in this
              corpus", and the corpus version is carried with the answer.

**And one kind of ``spelling`` that credits nothing.** Where the letters are,
almost always, a function word — که, از, را, listed in
``rules/function_words.yaml`` — their count is that word's. The adjective *keh*
was being credited with the conjunction's 609,699 occurrences. Such a form
comes back at level ``spelling`` with ``function_word`` set and **no count**:
"homograph of a function word, attestation unknown". Decided here, on the
spelling alone, so the entry, every form written with the same letters, the
batch job and a live request all get the same answer.

Lookups are batched. Generation produces hundreds of candidates at once and
asking one at a time is the only part of the whole path that would be slow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from murfulu.corpus.function_words import FunctionWords
from murfulu.corpus.function_words import loaded as _the_list
from murfulu.corpus.link import LinkResult
from murfulu.corpus.wordtypes import WordType, normalise


class Level(str, Enum):
    """How strongly the corpus attests a form."""

    READING = "reading"
    SPELLING = "spelling"
    NONE = "none"


@dataclass(frozen=True)
class Attestation:
    """What the corpus says about one form."""

    level: Level
    #: Which corpus was asked. A count is only true for one version.
    corpus_version: str = ""
    total_count: int = 0
    doc_count: int = 0
    author_count: int = 0
    first_century: int | None = None
    last_century: int | None = None
    #: Readings the corpus has for this spelling other than the one asked
    #: about. Non-empty at level ``spelling`` and worth showing: it says what
    #: the letters usually mean instead.
    other_readings: tuple[str, ...] = ()

    #: True when the corpus has the spelling but the **lexicon** has no reading
    #: for it at all. Then ``spelling`` reflects a gap in the dictionary, not a
    #: doubt about the word — گفتار is written 4,813 times and is plainly a
    #: real word, but no lexicon entry exists to confirm how it is read.
    spelling_unlinked: bool = False

    #: Set when the letters are, almost always, a function word — its class,
    #: e.g. ``conjunction`` for که. The count is then that word's and **none of
    #: it is credited**: the counts above are zero and mean *unknown*, not
    #: *never written*. See ``rules/function_words.yaml``.
    function_word: str = ""

    @property
    def found(self) -> bool:
        """True at either level of attestation."""
        return self.level is not Level.NONE

    def describe(self) -> str:
        """A phrase for the interface. Never claims a word does not exist."""
        if self.level is Level.NONE:
            return f"not found in corpus {self.corpus_version or 'unknown'}"
        if self.function_word:
            return (
                f"homograph of a function word ({self.function_word}): the "
                f"corpus count is that word's, so attestation is unknown"
            )
        evidence = (
            f"{self.total_count} occurrences in {self.doc_count} documents "
            f"by {self.author_count} authors"
        )
        if self.level is Level.READING:
            return evidence
        if self.spelling_unlinked:
            return f"{evidence}, but the lexicon has no reading for this spelling"
        return f"{evidence}, read as {' or '.join(self.other_readings)}"


@dataclass
class Index:
    """Corpus evidence, arranged for batched lookup."""

    corpus_version: str = ""
    #: normalised spelling → {latin or "" → the word type it was linked as}
    _by_spelling: dict[str, dict[str, WordType]] = field(default_factory=dict)
    #: Spellings whose count is a function word's. Read from the rules by
    #: default, so every index — batch or live — applies the same list.
    function_words: FunctionWords = field(default_factory=_the_list)

    @classmethod
    def from_link(
        cls,
        result: LinkResult,
        corpus_version: str = "",
        listed: FunctionWords | None = None,
    ) -> Index:
        """Build the index from a finished link pass."""
        index = cls(corpus_version=corpus_version or result.lexicon_snapshot_id)
        if listed is not None:
            index.function_words = listed
        for item in result.linked:
            spelling = normalise(item.spelling_fa)
            index._by_spelling.setdefault(spelling, {})[item.latin or ""] = item.word
        return index

    def add(self, word: WordType, latin: str | None) -> None:
        """Record one corpus reading, whatever built it.

        The link pass is one way to fill this index and a query against the
        ``word_types`` index is another. Both go through here, so the three
        levels of evidence are decided in one place and cannot drift apart
        between the batch job and the live request.
        """
        spelling = normalise(word.spelling_fa)
        self._by_spelling.setdefault(spelling, {})[latin or ""] = word

    def look_up(self, form_fa: str, form_latin: str) -> Attestation:
        """Ask about one form."""
        spelling = normalise(form_fa)
        readings = self._by_spelling.get(spelling)
        if not readings:
            return Attestation(level=Level.NONE, corpus_version=self.corpus_version)

        listed = self.function_words.get(spelling)
        if listed is not None:
            # The letters are written, and they are another word's. Nothing is
            # credited — not even to a reading the lexicon confirms, which is
            # exactly the case of *keh* — and the record says why.
            return Attestation(
                level=Level.SPELLING,
                corpus_version=self.corpus_version,
                other_readings=tuple(
                    sorted(r for r in readings if r and r != form_latin)
                ),
                function_word=listed.word_class,
            )

        word = readings.get(form_latin)
        if word is not None:
            return self._evidence(Level.READING, word)

        # The spelling is there but not under this reading. The letters have
        # been written; this particular word may still be new.
        others = tuple(sorted(r for r in readings if r))
        any_word = next(iter(readings.values()))
        return self._evidence(Level.SPELLING, any_word, others, unlinked=not others)

    def look_up_many(
        self, forms: list[tuple[str, str]]
    ) -> dict[tuple[str, str], Attestation]:
        """Ask about many forms at once. The only lookup generation does."""
        return {pair: self.look_up(*pair) for pair in forms}

    def _evidence(
        self,
        level: Level,
        word: WordType,
        others: tuple[str, ...] = (),
        unlinked: bool = False,
    ) -> Attestation:
        return Attestation(
            level=level,
            corpus_version=self.corpus_version,
            total_count=word.total_count,
            doc_count=word.doc_count,
            author_count=word.author_count,
            first_century=word.first_century,
            last_century=word.last_century,
            other_readings=others,
            spelling_unlinked=unlinked,
        )
