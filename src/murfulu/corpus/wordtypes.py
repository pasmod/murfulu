"""Count every distinct spelling in a corpus, and where it appears.

The counts are what let the app say *this word already exists* rather than
*this word is possible*. Four of them matter, and they say different things:

``total_count``   how often the word occurs
``doc_count``     in how many separate poems — 30 hits in one poem is a rhyme,
                  not a word
``author_count``  how many poets used it — one author means one coinage
``counts_by_century``  when it was used, and whether it survived

Corpus text has no vowels, so a word type here is a **spelling**, not a
reading. Attaching the Latin is a separate pass against the lexicon.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

from murfulu.corpus.adapter import SourceAdapter

#: A word is a run of Persian or Arabic letters, optionally joined by the
#: zero-width non-joiner, which is a letter for our purposes: می‌رود is one
#: word, not two.
_WORD = re.compile(r"[ء-يٱ-ۓ‌]+")

#: Harakat and other combining marks. Classical texts carry them unevenly, so
#: two spellings of one word would otherwise be counted apart.
_MARKS = re.compile(r"[ً-ْٰـ]")

#: Arabic letters that stand for Persian ones. Editions mix them freely.
_FOLD = str.maketrans({"ي": "ی", "ك": "ک", "ة": "ه", "أ": "ا", "إ": "ا", "ؤ": "و"})

#: How many authors to keep per word. The full list is unbounded and the app
#: shows a handful.
TOP_AUTHORS = 10


def normalise(text: str) -> str:
    """Fold the spelling variants that would otherwise split one word in two."""
    text = unicodedata.normalize("NFC", text)
    text = _MARKS.sub("", text)
    return text.translate(_FOLD)


def tokenise(text: str) -> list[str]:
    """Split a document into words, normalised."""
    return [
        stripped
        for token in _WORD.findall(normalise(text))
        # A bare ZWNJ is punctuation, not a word.
        if (stripped := token.strip("‌"))
    ]


@dataclass
class WordType:
    """One spelling, and the evidence for it."""

    spelling_fa: str
    total_count: int = 0
    documents: set[str] = field(default_factory=set)
    authors: Counter[str] = field(default_factory=Counter)
    counts_by_century: Counter[int] = field(default_factory=Counter)
    sources: set[str] = field(default_factory=set)

    @property
    def doc_count(self) -> int:
        """In how many separate documents the word occurs."""
        return len(self.documents)

    @property
    def author_count(self) -> int:
        """How many named authors used it."""
        return len(self.authors)

    @property
    def first_century(self) -> int | None:
        """The earliest century it is attested in, where dates are known."""
        return min(self.counts_by_century) if self.counts_by_century else None

    @property
    def last_century(self) -> int | None:
        """The latest century it is attested in."""
        return max(self.counts_by_century) if self.counts_by_century else None

    @property
    def top_authors(self) -> list[str]:
        """The authors who use it most, for display."""
        return [name for name, _ in self.authors.most_common(TOP_AUTHORS)]


@dataclass
class Corpus:
    """The counted corpus, and what it was built from."""

    word_types: dict[str, WordType] = field(default_factory=dict)
    document_count: int = 0
    token_count: int = 0
    #: Documents whose author or century was unknown. Reported, because both
    #: gaps weaken the evidence a word type carries.
    documents_without_author: int = 0
    documents_without_century: int = 0

    def __len__(self) -> int:
        """How many distinct spellings the corpus holds."""
        return len(self.word_types)

    def get(self, spelling: str) -> WordType | None:
        """One word type, looked up by its normalised spelling."""
        return self.word_types.get(normalise(spelling))

    def most_common(self, limit: int = 20) -> list[WordType]:
        """The most frequent spellings, for a sanity check on a new corpus."""
        return sorted(self.word_types.values(), key=lambda w: -w.total_count)[:limit]


def build(adapter: SourceAdapter) -> Corpus:
    """Count every spelling in one corpus."""
    corpus = Corpus()
    for document in adapter.documents():
        corpus.document_count += 1
        if not document.author:
            corpus.documents_without_author += 1
        if document.century is None:
            corpus.documents_without_century += 1

        # Counted per document, so one word repeated in a poem adds to
        # total_count but only once to doc_count.
        seen = Counter(tokenise(document.text_fa))
        corpus.token_count += sum(seen.values())
        for spelling, count in seen.items():
            word = corpus.word_types.get(spelling)
            if word is None:
                word = WordType(spelling_fa=spelling)
                corpus.word_types[spelling] = word
            word.total_count += count
            word.documents.add(document.document_id)
            word.sources.add(document.source_id)
            if document.author:
                word.authors[document.author] += count
            if document.century is not None:
                word.counts_by_century[document.century] += count
    return corpus
