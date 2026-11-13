"""Read the Ganjoor collection of classical Persian poetry and prose.

Source: the SQLite dump published with the Ganjoor desktop application. The
tables that matter are ``poet``, ``cat`` (the tree of books and sections),
``poem`` and ``verse``.

**One document per Ganjoor page, never per verse.** A page is the unit a
citation points at, and where a line begins differs between editions. A page
is most often a poem, but not always: the preface of the Golestan is a page of
prose with a couplet in it.

**What a verse's ``position`` means is Ganjoor's, and it is read from
Ganjoor's own source code** — the ``VersePosition`` enum of the desktop
application whose dump this is (``ganjoor/desktop``, file
``DesktopGanjoorDbBrowser/Base Data Models/VersePosition.cs``, commit
``caecff0``), repeated unchanged in the web service (``ganjoor/GanjoorService``,
``RMuseum/Models/Ganjoor/VersePosition.cs``, commit ``448fb20``). Until
2026-11-13 this module guessed them, took 3 for a prose paragraph and left it
out: 3 is the second half of a band couplet, so 7,135 lines of poetry were
missing, while the 83,273 prose paragraphs (−1) and the 1,676 notes (5) were
counted as text. See FINDINGS 2026-11-13.

Century comes from a hand-written table keyed on the poet's Ganjoor slug, not
from the dump — the dump has no dates. A poet with no entry gets ``None``
rather than a guess, and :func:`poets_without_a_century` lists them so the gap
is visible.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

from murfulu.corpus.adapter import SourceAdapter
from murfulu.corpus.documents import Document, Line, Unit

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

#: What the verse ``position`` column means, as Ganjoor's ``VersePosition``
#: names it (see the module docstring for the source).
RIGHT = 0  # مصرع اول — the first half of a couplet
LEFT = 1  # مصرع دوم — the second half
CENTERED_VERSE_1 = 2  # مصرع اول یا تنهای ابیات ترجیع یا ترکیب — a band line
CENTERED_VERSE_2 = 3  # مصرع دوم ابیات ترجیع یا ترکیب — its second half
SINGLE = 4  # مصرعهای شعرهای نیمایی یا آزاد — free verse
COMMENT = 5  # پاراگرافهایی که حالت توضیحی دارند — the source's own note
PARAGRAPH = -1  # نثر — prose

#: Which positions start a couplet, and which position completes each.
_PAIRS = {RIGHT: LEFT, CENTERED_VERSE_1: CENTERED_VERSE_2}

#: Each Ganjoor position in this project's words (documents.LINE_POSITIONS).
_LINE_POSITION = {
    RIGHT: "first",
    LEFT: "second",
    CENTERED_VERSE_1: "band_first",
    CENTERED_VERSE_2: "band_second",
    SINGLE: "free",
    PARAGRAPH: "prose",
    COMMENT: "note",
}


class UnknownPositionError(ValueError):
    """Raised for a ``position`` Ganjoor's enum does not have.

    Loud on purpose: the last time a value was guessed, 7,135 lines of poetry
    went missing for three months and nothing said so.
    """


def units_of(lines: list[tuple[int, str]]) -> list[Unit]:
    """A page's lines, in order, grouped into couplets, halves, prose and notes.

    A first half followed by its second is a couplet; either one alone is a
    half — a band line standing alone is the enum's own "or the only one".
    """
    units: list[Unit] = []
    waiting: tuple[int, str] | None = None

    def flush() -> None:
        nonlocal waiting
        if waiting is not None:
            units.append(Unit("half", (_line(*waiting),)))
            waiting = None

    for position, text in lines:
        if position not in _LINE_POSITION:
            raise UnknownPositionError(
                f"Ganjoor position {position} is not in its enum"
            )
        if waiting is not None and _PAIRS[waiting[0]] == position:
            units.append(Unit("couplet", (_line(*waiting), _line(position, text))))
            waiting = None
            continue
        flush()
        if position in _PAIRS:
            waiting = (position, text)
        elif position == PARAGRAPH:
            units.append(Unit("prose", (_line(position, text),)))
        elif position == COMMENT:
            units.append(Unit("note", (_line(position, text),)))
        else:
            units.append(Unit("half", (_line(position, text),)))
    flush()
    return units


def _line(position: int, text: str) -> Line:
    return Line(text=text, position=_LINE_POSITION[position])


# The poet's slug comes from the poet's own root category, not from the
# category the poem sits in: a poem's category is a book (…/khayyam/robaee),
# whose last path segment is the book, not the poet.
_POEM_QUERY = """
    SELECT poem.id, poem.title, poem.url, poet.name, poet_cat.url, poem.cat_id
    FROM poem
    JOIN cat ON cat.id = poem.cat_id
    JOIN poet ON poet.id = cat.poet_id
    JOIN cat AS poet_cat ON poet_cat.id = poet.cat_id
    ORDER BY poem.id
"""

# Every position is read: what to leave out of the counted text is decided by
# the unit's kind (a note is kept for the reader and not counted), not here.
_VERSE_QUERY = """
    SELECT poem_id, position, text FROM verse
    ORDER BY poem_id, vorder
"""

_CAT_QUERY = "SELECT id, parent_id, text FROM cat"


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
        #: Units by kind, over the last full pass. For the report.
        self._units: Counter[str] = Counter()

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

    def units_by_kind(self) -> dict[str, int]:
        """How many couplets, halves, prose paragraphs and notes the last pass held."""
        return dict(sorted(self._units.items()))

    def documents(self) -> Iterator[Document]:
        """Yield one document per page, in id order so two passes agree."""
        connection = sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)
        self._units = Counter()
        try:
            lines = self._lines_by_poem(connection)
            places = _Places(connection)
            for poem_id, title, url, poet, cat_url, cat_id in connection.execute(
                _POEM_QUERY
            ):
                units = units_of(lines.get(poem_id, []))
                if not any(unit.counted for unit in units):
                    # A page with no verses, or only notes, is metadata, not a
                    # document: there is nothing in it to count.
                    continue
                self._units.update(unit.kind for unit in units)
                work, section = places.of(cat_id)
                slug = _slug(cat_url)
                self._seen_slugs.add(slug)
                century = self.centuries.get(slug)
                if century is None:
                    self._missing.add(slug)
                yield Document.from_units(
                    source_id=SOURCE_ID,
                    document_id=f"{SOURCE_ID}:{slug or 'unknown'}:{poem_id}",
                    units=units,
                    title=title or None,
                    author=poet or None,
                    century=century,
                    extra={"url": url or "", "poet_slug": slug},
                    work=work,
                    section=section,
                    order=poem_id,
                )
        finally:
            connection.close()

    def _lines_by_poem(
        self, connection: sqlite3.Connection
    ) -> dict[int, list[tuple[int, str]]]:
        lines: dict[int, list[tuple[int, str]]] = {}
        for poem_id, position, text in connection.execute(_VERSE_QUERY):
            if text and text.strip():
                lines.setdefault(poem_id, []).append((position, text.strip()))
        return lines


class _Places:
    """Where a page sits: its work and the sections between, from ``cat``.

    The tree is poet → work → section … → page. The poet's own category is the
    root (``parent_id`` 0); its child is the work; anything below that is a
    section. A page filed straight under its poet has no work.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._cats = {
            cat_id: (parent_id, text or "")
            for cat_id, parent_id, text in connection.execute(_CAT_QUERY)
        }
        self._known: dict[int, tuple[str | None, tuple[str, ...]]] = {}

    def of(self, cat_id: int) -> tuple[str | None, tuple[str, ...]]:
        """The work and the sections of a page in this category."""
        if cat_id not in self._known:
            path: list[str] = []
            current: int | None = cat_id
            seen: set[int] = set()
            while current and current in self._cats and current not in seen:
                seen.add(current)
                parent, text = self._cats[current]
                path.append(text)
                current = parent
            path.reverse()  # the poet's own category first
            below_poet = path[1:]
            self._known[cat_id] = (
                (below_poet[0] or None, tuple(below_poet[1:]))
                if below_poet
                else (None, ())
            )
        return self._known[cat_id]


def _load_centuries() -> dict[str, int]:
    configured = os.environ.get(CENTURIES_VARIABLE)
    if not configured:
        return {}
    document = json.loads(Path(configured).expanduser().read_text(encoding="utf-8"))
    return {k: v for k, v in document.items() if not k.startswith("_")}
