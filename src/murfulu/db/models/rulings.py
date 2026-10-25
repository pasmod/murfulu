"""Questions for the linguist, and the rulings that answer them.

**This table is the record.** Until 2026-08-15 the questions lived in
``docs/FOR_THE_LINGUIST.md`` and were answered in one conversation at the end
of a session, then written back into the file by hand. That works for us and
asks the wrong thing of him: he works in Persian, and the file is English
Markdown in a repository, in a language he does not work in.

**So the store holds the question and the ruling, and the document becomes an
export of it** — the project lead's decision, 2026-08-15. That is the reverse
of :mod:`murfulu.db.models.proposals`, where the YAML in git stays the source
of truth and the store only proposes. The difference is what the two hold: a
proposal is a change to something that already exists and can be reviewed as a
diff, while a ruling is **new information that exists nowhere until he gives
it**, exactly like the expert feedback table.

**A separate flow from expert review, but not a separate role.** The flow is
separate because the two hold different things: a graded verdict is one opinion
about one built word and dozens are aggregated, while a ruling settles a
question about the grammar once. **A third role was tried for that and taken
out again** on 2026-08-16 — in practice the expert *is* the linguist, and a
concept naming the same person twice earns nothing. So an expert rules, as an
expert grades and proposes.

**Append-only in the same way and for the same reason.** A ruling is work no
job can recreate. A question can be superseded or withdrawn, and a ruling can
be *replaced* by a later one that says so — but nothing is edited in place and
nothing is deleted.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from murfulu.db.base import Base, Json, created_at_column, one_of

#: Where a question came from, so an export can be checked against its source.
#: ``document`` means it was imported from FOR_THE_LINGUIST.md on the way in;
#: ``app`` means it was asked here and has never lived anywhere else.
ORIGINS = ("document", "app")

#: What a question is waiting on. **`blocked` is not the same as `open`**: a
#: question nothing depends on can wait, and one that stops work should be
#: visible as such. `withdrawn` is for a question that stopped mattering —
#: kept, because "we asked and then stopped caring" is worth knowing.
STATES = ("open", "blocked", "answered", "withdrawn")

#: **Where a question keeps its answer options**: ``context["choices"]``, a
#: list of ``{"id", "text_fa", "suggested", "settles"}``. Added 2026-10-18,
#: when the project lead asked for the questions screen to become a
#: multiple-choice form: one radio per option, and always a free-text box
#: beside them.
#:
#: * ``id`` — short, ASCII, stable. A ruling records it, so it never changes
#:   meaning once a question has been answered.
#: * ``text_fa`` — the option as a full Persian sentence saying what follows.
#: * ``suggested`` — true only where the documents state a proposed default;
#:   the screen marks it «پیشنهاد ما».
#: * ``settles`` — false for «نمی‌دانم / باید بیشتر بررسی کنم»: recorded
#:   like any ruling, but the question stays waiting.
#:
#: **In `context` and not a table of its own**, because the options are part
#: of how a question is worded — written beside it in
#: ``rules/questions_fa.yaml`` and loaded by ``tools/load_questions.py`` — and
#: a ruling keeps its own copy of the option it chose, so rewording a question
#: later can never change what an earlier answer said.
CHOICES_KEY = "choices"


class LinguistQuestion(Base):
    """One question only the linguist can settle."""

    __tablename__ = "linguist_questions"
    __table_args__ = (
        CheckConstraint(one_of("origin", ORIGINS), name="origin"),
        CheckConstraint(one_of("state", STATES), name="state"),
        # A question nobody can read is not a question. The Persian is what he
        # actually reads, so it is required and the English is the gloss.
        CheckConstraint("length(trim(question_fa)) > 0", name="a_question_is_asked"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    #: The handle the document gives it — L13, S11, Q2. Kept so a question can
    #: be followed between the app, the docs and a git history that already
    #: refers to it by that name. Unique, because two questions under one
    #: handle would make every past reference ambiguous.
    reference: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)

    #: **What he reads.** He works in Persian; an English-only question is one
    #: he has to translate before he can answer it.
    question_fa: Mapped[str] = mapped_column(Text, nullable=False)

    #: **The same question in Behnevis.** Murfulu operates on Behnevis and
    #: never on raw Arabic script, and he is the authority on that script — so
    #: a question whose examples are all Behnevis (*šāhvār* against *šāhevār*)
    #: should be readable in it too. Nullable: absent is better than invented.
    question_latin: Mapped[str | None] = mapped_column(Text)

    #: The English statement, for the repository and for us. A gloss of the
    #: Persian, never the other way round.
    question_en: Mapped[str | None] = mapped_column(Text)

    #: The evidence: what was measured, the examples, the list. Free-shaped
    #: because a question about 21 words and a question about one verb do not
    #: carry the same thing.
    context: Mapped[Any] = mapped_column(Json)

    origin: Mapped[str] = mapped_column(String(16), nullable=False, default="document")
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="open")

    #: True when work is stopped until this is settled. Separate from `state`
    #: so a question can be answered *and* have been blocking, which is what
    #: makes it worth knowing how long it blocked for.
    blocks_work: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = created_at_column()


class LinguistRuling(Base):
    """One answer, from the linguist, to one question.

    Several may point at one question. The latest is the ruling that stands,
    and the ones before it are how it got there — a reversal is a fact about
    the grammar and deleting it would hide that anything changed.
    """

    __tablename__ = "linguist_rulings"
    __table_args__ = (
        CheckConstraint("length(trim(ruling_fa)) > 0", name="a_ruling_says_something"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    question_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("linguist_questions.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    #: The account that gave it. RESTRICT, not CASCADE: an account is disabled
    #: rather than deleted precisely so a ruling keeps pointing at its author.
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    #: **The ruling, in his own words and his own language.** Never translated
    #: on the way in; a translation is a reading of an answer, and the answer
    #: is the record.
    ruling_fa: Mapped[str] = mapped_column(Text, nullable=False)

    #: The same ruling in Behnevis, if he gives one. His, like the Persian.
    ruling_latin: Mapped[str | None] = mapped_column(Text)

    #: Our English rendering, written afterwards and clearly ours. Nullable,
    #: because a ruling is complete without it.
    ruling_en: Mapped[str | None] = mapped_column(Text)

    #: **The option he chose**, when the question offers options — its id in
    #: ``context["choices"]``. Null for a ruling written as free text alone,
    #: and for every ruling given before options existed.
    choice_id: Mapped[str | None] = mapped_column(String(32))

    #: **The option's Persian, copied at the moment of ruling.** The question's
    #: wording can be revised while it waits; the answer cannot, so it keeps
    #: the sentence that was actually chosen. When he chooses an option and
    #: writes nothing, ``ruling_fa`` is this same sentence — a ruling always
    #: says something in Persian.
    choice_fa: Mapped[str | None] = mapped_column(Text)

    #: What changes here as a result — a rule id, a decisions.yaml key. Held so
    #: an answer can be traced to what it altered instead of being read twice.
    affects: Mapped[Any] = mapped_column(Json)

    #: True when this replaces the previous ruling on the same question rather
    #: than adding to it. Set by the author, so a reversal says it is one.
    supersedes_earlier: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    created_at: Mapped[datetime] = created_at_column()


class LinguistQuestionFile(Base):
    """A file attached to a question, held as bytes rather than as a path.

    **A question that names a document is not answerable without it.** L1 turns
    on what the grammar document says about three verbs; L13 on a list of
    twenty-one words. Sending the reader to a shared drive to find those is the
    thing this store exists to stop.

    **The bytes are here and not a path**, because a path is a promise about
    one machine: it breaks when the file moves, when the container is rebuilt,
    or when the drive is not mounted — and it breaks silently, at the moment
    somebody is trying to answer. Everything attached today is under a megabyte.
    """

    __tablename__ = "linguist_question_files"
    __table_args__ = (
        CheckConstraint("length(trim(filename)) > 0", name="a_file_is_named"),
        CheckConstraint(
            "length(trim(description_fa)) > 0", name="a_file_says_what_it_is"
        ),
        UniqueConstraint("question_id", "filename", name="one_name_per_question"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    question_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("linguist_questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    #: What it is called when it lands in his downloads folder.
    filename: Mapped[str] = mapped_column(String(200), nullable=False)
    media_type: Mapped[str] = mapped_column(String(100), nullable=False)

    #: **In Persian**, because it is read beside the question and the question
    #: is in Persian. A file nobody can tell the purpose of is one nobody opens.
    description_fa: Mapped[str] = mapped_column(Text, nullable=False)

    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = created_at_column()
