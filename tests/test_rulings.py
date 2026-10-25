"""Questions for the linguist, answered in the app.

**The store is the record.** The project lead settled that on 2026-08-15: the
questions used to live in `docs/FOR_THE_LINGUIST.md` and be answered in one
conversation at the end of a session, which asks someone who works in Persian
to read English Markdown in a repository. The document becomes an export.

**The expert is the linguist.** A third role was tried and taken out again on
2026-08-16: the flow is separate from expert review, the role is not.

Most of what is asserted here is who may **not** rule, and what may **not** be
edited — because a store that quietly loses or rewrites an answer is worse than
the Markdown file it replaced.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from murfulu.api.app import app
from murfulu.db import rulings as store
from murfulu.db.models import Base
from murfulu.db.site import SITE_USERNAME


@pytest.fixture
def accounts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[dict]:
    """A store holding two questions.

    No accounts: there is one and it makes itself on first use — see
    murfulu.db.site.
    """
    url = f"sqlite:///{tmp_path / 'authored.sqlite'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        store.ask(
            session,
            reference="L13",
            question_fa="آیا میان دو همخوان مصوت e می‌آید؟",
            question_latin="āyā miyān-e do hamxān mosavvat-e e miāyad?",
            question_en="Does an e go in between two consonants?",
            context={"words": ["šāhvār", "Kuhsār"], "count": 21},
            origin="document",
        )
        store.ask(
            session,
            reference="L15",
            question_fa="آیا V-052 پیشوند است؟",
            question_en="Is V-052 a prefix?",
            blocks_work=True,
        )
        session.commit()
    engine.dispose()
    monkeypatch.setenv("MURFULU_DATABASE_URL", url)
    yield {}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _as(_who: str = "") -> dict[str, str]:
    """No credential at all. Kept so call sites read unchanged.

    Every route behind the password wall is open as of 2026-08-17 —
    there is one account and no roles. See murfulu.db.site.
    """
    return {}


RULING = {
    "ruling_fa": "بله، میان دو همخوان e می‌آید.",
    "ruling_latin": "bale, miyān-e do hamxān e miāyad.",
    "ruling_en": "Yes, an e goes in between two consonants.",
    "affects": {"rules": ["N-075", "N-079"]},
}


# -- who may rule ------------------------------------------------------------


def test_an_expert_may_settle_a_question(client: TestClient, accounts: dict):
    made = client.post("/questions/L13/ruling", json=RULING, headers=_as())
    assert made.status_code == 201, made.text
    body = made.json()
    assert body["state"] == "answered"
    assert body["ruling"]["ruling_fa"] == RULING["ruling_fa"]
    assert body["ruling"]["affects"] == {"rules": ["N-075", "N-079"]}


def test_anyone_signed_in_may_read_the_questions(client: TestClient, accounts: dict):
    """What the project does not yet know is not a secret.

    A reviewer who can see the open questions is a reviewer who will not report
    one of them as a bug.
    """
    seen = client.get("/questions", headers=_as())
    assert seen.status_code == 200
    body = seen.json()
    assert body["count"] == 2
    assert {q["reference"] for q in body["questions"]} == {"L13", "L15"}


def test_the_reader_is_told_they_are_the_one_answering(
    client: TestClient, accounts: dict
):
    """Everyone behind the wall is told they may answer.

    It used to be null for anyone without the expert role, so a reader learned
    they could not answer before writing a ruling rather than after. There are
    no roles now.
    """
    body = client.get("/questions", headers=_as()).json()
    assert body["answering_as"] == SITE_USERNAME


def test_a_blocking_question_comes_first(client: TestClient, accounts: dict):
    """The point of the flag is that somebody is waiting."""
    body = client.get("/questions", headers=_as()).json()
    assert body["questions"][0]["reference"] == "L15"
    assert body["questions"][0]["blocks_work"] is True


def test_only_the_blocking_ones_can_be_asked_for(client: TestClient, accounts: dict):
    body = client.get("/questions", params={"blocking": True}, headers=_as()).json()
    assert [q["reference"] for q in body["questions"]] == ["L15"]


class TestTheEvidenceIsAttached:
    """A question that names a document is not answerable without it.

    L1 turns on what the grammar document says about three verbs; L13 on a list
    of twenty-one words. Sending the reader to a shared drive to find those is
    the thing this store was built to stop.
    """

    def _attach(self, tmp_path: Path, name: str, body: bytes) -> None:
        engine = create_engine(f"sqlite:///{tmp_path / 'authored.sqlite'}")
        with Session(engine) as session:
            store.attach(
                session,
                question=store.by_reference(session, "L13"),
                filename=name,
                content=body,
                description_fa="فهرست بیست‌ویک واژه.",
                media_type="text/csv",
            )
            session.commit()
        engine.dispose()

    def test_a_question_lists_what_is_attached_to_it(
        self, client: TestClient, accounts: dict, tmp_path: Path
    ) -> None:
        self._attach(tmp_path, "واژه‌ها.csv", b"a,b\n")
        body = client.get("/questions/L13", headers=_as()).json()

        (file,) = body["files"]
        assert file["filename"] == "واژه‌ها.csv"
        assert file["description_fa"], "a file nobody can name is one nobody opens"
        assert file["href"] == "/questions/L13/files/واژه‌ها.csv"

    def test_the_bytes_come_back(
        self, client: TestClient, accounts: dict, tmp_path: Path
    ) -> None:
        self._attach(tmp_path, "واژه‌ها.csv", b"rule,spelling\nN-075,shahvar\n")
        got = client.get("/questions/L13/files/واژه‌ها.csv", headers=_as())
        assert got.status_code == 200
        assert got.content == b"rule,spelling\nN-075,shahvar\n"

    def test_a_persian_filename_does_not_break_the_header(
        self, client: TestClient, accounts: dict, tmp_path: Path
    ) -> None:
        """An HTTP header is latin-1, and these filenames are Persian.

        Putting the name in raw is a 500 at download time — the worst place to
        find it. RFC 5987's `filename*` carries it percent-encoded.
        """
        self._attach(tmp_path, "واژه‌ها.csv", b"x")
        got = client.get("/questions/L13/files/واژه‌ها.csv", headers=_as())
        assert got.status_code == 200
        disposition = got.headers["content-disposition"]
        assert "filename*=UTF-8''" in disposition
        assert disposition.startswith("attachment;")

    def test_an_unknown_attachment_is_a_404(
        self, client: TestClient, accounts: dict
    ) -> None:
        got = client.get("/questions/L13/files/nothing.csv", headers=_as())
        assert got.status_code == 404

    def test_attaching_the_same_name_replaces_it(
        self, client: TestClient, accounts: dict, tmp_path: Path
    ) -> None:
        """The attachments are regenerated whenever the measurement is re-run."""
        self._attach(tmp_path, "واژه‌ها.csv", b"old")
        self._attach(tmp_path, "واژه‌ها.csv", b"new")
        body = client.get("/questions/L13", headers=_as()).json()
        assert len(body["files"]) == 1
        got = client.get("/questions/L13/files/واژه‌ها.csv", headers=_as())
        assert got.content == b"new"


def test_a_question_is_carried_in_behnevis_too(client: TestClient, accounts: dict):
    """Murfulu works in Behnevis and never in raw Arabic script.

    A question about *šāhvār* against *šāhevār* whose examples are all Behnevis
    should be readable in it, not only in Persian.
    """
    body = client.get("/questions/L13", headers=_as()).json()
    assert body["question_latin"] == "āyā miyān-e do hamxān mosavvat-e e miāyad?"


def test_a_ruling_is_carried_in_behnevis_too(client: TestClient, accounts: dict):
    made = client.post("/questions/L13/ruling", json=RULING, headers=_as())
    assert made.json()["ruling"]["ruling_latin"] == RULING["ruling_latin"]


def test_the_question_carries_its_evidence(client: TestClient, accounts: dict):
    """A question with no evidence behind it cannot be answered in the app.

    The 21 words are the question; asking it without them would send him back
    to the repository, which is the thing this replaces.
    """
    body = client.get("/questions/L13", headers=_as()).json()
    assert body["context"]["count"] == 21
    assert "šāhvār" in body["context"]["words"]
    assert body["question_fa"], "the Persian is what he reads"


def test_an_unknown_question_is_a_404(client: TestClient, accounts: dict):
    seen = client.get("/questions/L99", headers=_as())
    assert seen.status_code == 404


def test_a_bad_state_is_refused(client: TestClient, accounts: dict):
    refused = client.get("/questions", params={"state": "maybe"}, headers=_as())
    assert refused.status_code == 400


# -- the record --------------------------------------------------------------


def test_answering_moves_the_question_out_of_the_open_list(
    client: TestClient, accounts: dict
):
    client.post("/questions/L13/ruling", json=RULING, headers=_as())
    open_now = client.get("/questions", params={"state": "open"}, headers=_as()).json()
    assert "L13" not in {q["reference"] for q in open_now["questions"]}


def test_a_second_ruling_does_not_erase_the_first(client: TestClient, accounts: dict):
    """A reversal is a fact about the grammar.

    Deleting the earlier answer would hide that the ruling ever changed, and
    the code written against the first would look as though it never had a
    reason.
    """
    head = _as()
    client.post("/questions/L13/ruling", json=RULING, headers=head)
    client.post(
        "/questions/L13/ruling",
        json={"ruling_fa": "پس از بررسی، خیر.", "supersedes_earlier": True},
        headers=head,
    )

    body = client.get("/questions/L13", headers=head).json()
    assert body["rulings"] == 2
    assert len(body["history"]) == 2
    assert body["history"][0]["ruling_fa"] == RULING["ruling_fa"]
    # The one that stands is the latest, and it says it is a reversal.
    assert body["ruling"]["ruling_fa"] == "پس از بررسی، خیر."
    assert body["ruling"]["supersedes_earlier"] is True


def test_an_empty_ruling_is_refused(client: TestClient, accounts: dict):
    refused = client.post(
        "/questions/L13/ruling",
        json={"ruling_fa": "   "},
        headers=_as(),
    )
    assert refused.status_code == 400


def test_a_withdrawn_question_is_not_answered(
    client: TestClient, accounts: dict, tmp_path: Path
):
    """Question L was withdrawn because a measurement answered it instead."""
    engine = create_engine(f"sqlite:///{tmp_path / 'authored.sqlite'}")
    with Session(engine) as session:
        question = store.by_reference(session, "L15")
        store.withdraw(session, question, why="answered by measurement instead")
        session.commit()
    engine.dispose()

    refused = client.post("/questions/L15/ruling", json=RULING, headers=_as())
    assert refused.status_code == 400
    assert "withdrawn" in refused.json()["detail"]


def test_withdrawing_keeps_the_question_and_says_why(
    client: TestClient, accounts: dict, tmp_path: Path
):
    """*We asked and then stopped caring* is worth knowing."""
    engine = create_engine(f"sqlite:///{tmp_path / 'authored.sqlite'}")
    with Session(engine) as session:
        question = store.by_reference(session, "L15")
        store.withdraw(session, question, why="answered by measurement instead")
        session.commit()
    engine.dispose()

    body = client.get("/questions/L15", headers=_as()).json()
    assert body["state"] == "withdrawn"
    assert body["context"]["withdrawn_because"] == "answered by measurement instead"


# -- options: a multiple-choice answer ---------------------------------------
#
# Asked for by the project lead on 2026-10-18: each question offers options as
# full Persian sentences, and a free-text box is always beside them. A ruling is
# an option, free text, or both — never neither — and `ruling_fa` is never
# empty, because an option chosen with nothing written is stored in its own
# Persian.

CHOICES = [
    {"id": "yes", "text_fa": "آری؛ میان دو همخوان e می‌آید."},
    {"id": "no", "text_fa": "نه؛ e نمی‌آید.", "suggested": True},
    {"id": "unsure", "text_fa": "نمی‌دانم و باید بیشتر بررسی کنم.", "settles": False},
]


@pytest.fixture
def with_choices(accounts: dict, tmp_path: Path) -> dict:
    """L13 offering three options; L15 left as a free-text question."""
    engine = create_engine(f"sqlite:///{tmp_path / 'authored.sqlite'}")
    with Session(engine) as session:
        store.reword(
            session,
            store.by_reference(session, "L13"),
            question_fa="آیا میان دو همخوان مصوت e می‌آید؟",
            choices=CHOICES,
        )
        session.commit()
    engine.dispose()
    return accounts


class TestAnsweringWithOptions:
    def test_the_options_are_served_with_the_question(
        self, client: TestClient, with_choices: dict
    ) -> None:
        body = client.get("/questions/L13", headers=_as()).json()
        assert [one["id"] for one in body["choices"]] == ["yes", "no", "unsure"]
        assert body["choices"][1]["suggested"] is True
        assert body["choices"][2]["settles"] is False
        # A question without options says so, rather than leaving the key out.
        assert client.get("/questions/L15", headers=_as()).json()["choices"] == []

    def test_a_choice_alone_is_stored_in_its_own_persian(
        self, client: TestClient, with_choices: dict
    ) -> None:
        made = client.post(
            "/questions/L13/ruling", json={"choice_id": "no"}, headers=_as()
        )
        assert made.status_code == 201, made.text
        ruling = made.json()["ruling"]
        assert ruling["choice_id"] == "no"
        assert ruling["choice_fa"] == "نه؛ e نمی‌آید."
        assert ruling["ruling_fa"] == "نه؛ e نمی‌آید.", "a ruling always says something"
        assert made.json()["state"] == "answered"

    def test_text_alone_is_a_ruling(
        self, client: TestClient, with_choices: dict
    ) -> None:
        made = client.post(
            "/questions/L13/ruling",
            json={"ruling_fa": "بستگی به واژه دارد."},
            headers=_as(),
        )
        assert made.status_code == 201, made.text
        ruling = made.json()["ruling"]
        assert ruling["ruling_fa"] == "بستگی به واژه دارد."
        assert ruling["choice_id"] is None
        assert ruling["choice_fa"] is None

    def test_both_keep_his_words_and_the_option_beside_them(
        self, client: TestClient, with_choices: dict
    ) -> None:
        made = client.post(
            "/questions/L13/ruling",
            json={"choice_id": "yes", "ruling_fa": "جز در talxvaš."},
            headers=_as(),
        )
        assert made.status_code == 201, made.text
        ruling = made.json()["ruling"]
        assert ruling["ruling_fa"] == "جز در talxvaš."
        assert ruling["choice_id"] == "yes"
        assert ruling["choice_fa"] == "آری؛ میان دو همخوان e می‌آید."

    def test_neither_is_refused(self, client: TestClient, with_choices: dict) -> None:
        refused = client.post(
            "/questions/L13/ruling",
            json={"ruling_fa": "   ", "choice_id": None},
            headers=_as(),
        )
        assert refused.status_code == 400
        assert client.get("/questions/L13", headers=_as()).json()["rulings"] == 0

    def test_an_option_the_question_does_not_offer_is_refused(
        self, client: TestClient, with_choices: dict
    ) -> None:
        refused = client.post(
            "/questions/L13/ruling", json={"choice_id": "maybe"}, headers=_as()
        )
        assert refused.status_code == 400
        # And on a question with no options at all.
        refused = client.post(
            "/questions/L15/ruling", json={"choice_id": "yes"}, headers=_as()
        )
        assert refused.status_code == 400

    def test_i_do_not_know_is_recorded_and_the_question_keeps_waiting(
        self, client: TestClient, with_choices: dict
    ) -> None:
        made = client.post(
            "/questions/L13/ruling", json={"choice_id": "unsure"}, headers=_as()
        )
        assert made.status_code == 201, made.text
        assert made.json()["state"] == "open"
        body = client.get("/questions/L13", headers=_as()).json()
        assert body["rulings"] == 1
        assert body["ruling"]["choice_id"] == "unsure"

    def test_the_chosen_sentence_survives_a_rewording(
        self, client: TestClient, with_choices: dict, tmp_path: Path
    ) -> None:
        """The answer keeps the sentence that was chosen, not today's wording."""
        client.post(
            "/questions/L13/ruling", json={"choice_id": "unsure"}, headers=_as()
        )
        engine = create_engine(f"sqlite:///{tmp_path / 'authored.sqlite'}")
        with Session(engine) as session:
            question = store.by_reference(session, "L13")
            with pytest.raises(store.RulingRefusedError, match="answered"):
                store.reword(session, question, question_fa="پرسش دیگر", choices=[])
        engine.dispose()
        body = client.get("/questions/L13", headers=_as()).json()
        assert body["ruling"]["choice_fa"] == "نمی‌دانم و باید بیشتر بررسی کنم."


class TestRewording:
    def _session(self, tmp_path: Path) -> Session:
        return Session(create_engine(f"sqlite:///{tmp_path / 'authored.sqlite'}"))

    def test_the_earlier_persian_is_kept(self, accounts: dict, tmp_path: Path) -> None:
        with self._session(tmp_path) as session:
            question = store.by_reference(session, "L13")
            old = question.question_fa
            assert store.reword(session, question, question_fa="پرسش تازه")
            assert question.question_fa == "پرسش تازه"
            assert question.context["reworded"][0]["question_fa"] == old
            # The evidence already there is not lost.
            assert question.context["count"] == 21

    def test_rewording_to_the_same_text_changes_nothing(
        self, accounts: dict, tmp_path: Path
    ) -> None:
        with self._session(tmp_path) as session:
            question = store.by_reference(session, "L15")
            same = question.question_fa
            assert not store.reword(
                session, question, question_fa=same, blocks_work=True
            )

    def test_bad_options_are_refused(self, accounts: dict, tmp_path: Path) -> None:
        with self._session(tmp_path) as session:
            question = store.by_reference(session, "L13")
            for bad in (
                [{"id": "a", "text_fa": "یک"}, {"id": "a", "text_fa": "دو"}],
                [{"id": "Not ASCII!", "text_fa": "یک"}],
                [{"id": "a", "text_fa": "  "}],
            ):
                with pytest.raises(store.RulingRefusedError):
                    store.reword(session, question, question_fa="پرسش", choices=bad)


def test_a_part_of_a_question_sorts_beside_it():
    """L17b is a part of L17: after it, and before L18 — and L2 before L10."""
    handles = ["L18", "L17b", "L10", "L2", "L17", "L10c", "L17d", "S3"]
    ordered = sorted(handles, key=store._handle)
    assert ordered == ["L2", "L10", "L10c", "L17", "L17b", "L17d", "L18", "S3"]
