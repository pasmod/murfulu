"""Read the Ganjoor collection of classical Persian poetry.

Source: the SQLite dump published with the Ganjoor desktop application. The
tables that matter are ``poet``, ``cat`` (the tree of books and sections),
``poem`` and ``verse``.

**One document per poem, never per verse.** A poem is the unit a citation
points at, and where a line begins differs between editions.

Century comes from a hand-written table keyed on the poet's Ganjoor slug, not
from the dump — the dump has no dates. A poet with no entry gets ``None``
rather than a guess, and :func:`poets_without_a_century` lists them so the gap
is visible.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from murfulu.corpus.adapter import SourceAdapter
from murfulu.corpus.documents import Document

#: Where the dump is. Configuration, never a literal — the file is 325 MB and
#: lives outside the repository.
PATH_VARIABLE = "MURFULU_GANJOOR_PATH"
CENTURIES_VARIABLE = "MURFULU_GANJOOR_CENTURIES"

SOURCE_ID = "ganjoor"

#: What the source is called, in Persian.
#:
#: The corpus screen headed a column سرچشمه and then wrote ``ganjoor`` under
#: it — the identifier, in Latin, on an otherwise Persian page. The identifier
#: is the right thing to *type* into ``source:ganjoor`` and the wrong thing to
#: *read*, and the two are not the same job. Same reasoning as ``LICENCE_FA``
#: below: a name is a fact about the source, not something an ingest measured,
#: so a report written before this field existed can be filled in from here
#: rather than waiting hours for a re-ingest.
NAME_FA = "گنجور"

#: The licence for the reader, in Persian.
#:
#: A module constant rather than only a property, because a stored report
#: written before 2026-08-17 carries no ``licence_fa`` and the corpus screen
#: would fall back to the English — which is the thing the field exists to stop
#: a reader seeing. `report.from_document` fills it in from here by source id,
#: and it may: the licence is a fact about **Ganjoor**, not a measurement that
#: one ingest run made, so reading it from the source is not inventing it.
#:
#: Ganjoor's own answer is in Persian — «لزوماً خیر!» to the question of whether
#: its data are free of copyright — so this is nearer the source than the
#: English beside it, not a translation away from it.
LICENCE_FA = (
    "شعر کلاسیک، گردآوردهٔ گنجور. گنجور خود می‌گوید داده‌هایش لزوماً "
    "از حق تکثیر آزاد نیست و هیچ تضمینی نمی‌دهد."
)

#: What the verse ``position`` column means in the dump.
RIGHT_HEMISTICH = 0
LEFT_HEMISTICH = 1
SINGLE_LINE = 2
PARAGRAPH = 3

# The poet's slug comes from the poet's own root category, not from the
# category the poem sits in: a poem's category is a book (…/khayyam/robaee),
# whose last path segment is the book, not the poet.
_POEM_QUERY = """
    SELECT poem.id, poem.title, poem.url, poet.name, poet_cat.url
    FROM poem
    JOIN cat ON cat.id = poem.cat_id
    JOIN poet ON poet.id = cat.poet_id
    JOIN cat AS poet_cat ON poet_cat.id = poet.cat_id
    ORDER BY poem.id
"""

_VERSE_QUERY = """
    SELECT poem_id, text FROM verse
    WHERE position != ?
    ORDER BY poem_id, vorder
"""


def _slug(url: str | None) -> str:
    """The poet's Ganjoor name, taken from the category URL."""
    if not url:
        return ""
    return url.rstrip("/").split("/")[-1]


class GanjoorCorpus(SourceAdapter):
    """The Ganjoor dump, as documents."""

    def __init__(
        self,
        path: str | Path | None = None,
        centuries: dict[str, int] | None = None,
    ) -> None:
        configured = path or os.environ.get(PATH_VARIABLE)
        if not configured:
            raise ValueError(f"no Ganjoor dump given and {PATH_VARIABLE} is not set")
        self.path = Path(configured).expanduser()
        if not self.path.is_file():
            raise FileNotFoundError(f"Ganjoor dump not found: {self.path}")
        self.centuries = centuries if centuries is not None else _load_centuries()
        #: Every poet slug this corpus actually uses, filled as it is read.
        self._seen_slugs: set[str] = set()
        self._missing: set[str] = set()

    @property
    def source_id(self) -> str:
        """The stable identifier that prefixes every document id."""
        return SOURCE_ID

    @property
    def licence(self) -> str:
        """What the material may be used for, in Ganjoor's own answer.

        **This said "public-domain classical texts … (confirm terms)" until
        2026-08-17, and the first half was ours rather than theirs.** The
        parenthesis was honest about not knowing; the words in front of it were
        not, because they asserted the thing nobody had checked.

        Asked, Ganjoor's FAQ answers whether its data are free of copyright
        with **«لزوماً خیر!»** — *not necessarily*. It states that no legal
        review has been made; that most of the content was typed from published
        books whose own status was never established; that editing and
        compilation can attract rights of their own; and that free access must
        not be read as a licence, the responsibility being the reader's.

        The poems are classical and their *authors* are centuries dead, which
        is what made the old wording feel safe. It is not the same question as
        whether this compilation of them may be redistributed. See NOTICE.
        """
        return (
            "classical poetry compiled by Ganjoor; Ganjoor states its data are "
            "not necessarily free of copyright and warrants nothing"
        )

    @property
    def licence_fa(self) -> str:
        """The same, for the reader. The text is :data:`LICENCE_FA`."""
        return LICENCE_FA

    def poets_without_a_century(self) -> list[str]:
        """Poet slugs the century table does not cover, after a full pass."""
        return sorted(self._missing)

    def centuries_without_a_poet(self) -> list[str]:
        """Century-table keys that match no poet in this corpus.

        The other half of the same gap, and the half nothing was reporting.
        A table entry that names a slug the corpus does not use dates nothing
        and looks exactly like one that works — which is how **فردوسی** came
        to be undated: the table writes ``ferdowsi`` and Ganjoor's own slug is
        ``ferdousi``.

        Only meaningful after a full pass, since the slugs are collected as
        the documents are read.
        """
        return sorted(set(self.centuries) - self._seen_slugs)

    def documents(self) -> Iterator[Document]:
        """Yield one document per poem, in id order so two passes agree."""
        connection = sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)
        try:
            # Verses are read in one ordered pass and attached as they go, so
            # three million rows never sit in memory at once.
            lines = self._lines_by_poem(connection)
            for poem_id, title, url, poet, cat_url in connection.execute(_POEM_QUERY):
                text = "\n".join(lines.get(poem_id, ()))
                if not text.strip():
                    # A poem with no verses is metadata, not a document.
                    continue
                slug = _slug(cat_url)
                self._seen_slugs.add(slug)
                century = self.centuries.get(slug)
                if century is None:
                    self._missing.add(slug)
                yield Document(
                    source_id=SOURCE_ID,
                    document_id=f"{SOURCE_ID}:{slug or 'unknown'}:{poem_id}",
                    text_fa=text,
                    title=title or None,
                    author=poet or None,
                    century=century,
                    extra={"url": url or "", "poet_slug": slug},
                )
        finally:
            connection.close()

    def _lines_by_poem(self, connection: sqlite3.Connection) -> dict[int, list[str]]:
        lines: dict[int, list[str]] = {}
        for poem_id, text in connection.execute(_VERSE_QUERY, (PARAGRAPH,)):
            if text and text.strip():
                lines.setdefault(poem_id, []).append(text.strip())
        return lines


def _load_centuries() -> dict[str, int]:
    configured = os.environ.get(CENTURIES_VARIABLE)
    if not configured:
        return {}
    document = json.loads(Path(configured).expanduser().read_text(encoding="utf-8"))
    return {k: v for k, v in document.items() if not k.startswith("_")}
