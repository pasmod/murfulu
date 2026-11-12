"""The word bank screen's API: `/bank/groups` and `/bank`.

Read straight from the lexicon snapshot, so these run on a handmade one with
the 1.3.x tables. What matters: the linguist's groups and names come back in
his order, the list is in Persian alphabetical order (پ after ب, not after ی),
a verb carries both stems, a loanword is listed and says it builds nothing,
and a search finds Persian letters and Latin readings alike.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from murfulu.api import bank as bank_api
from murfulu.api.app import app

from .conftest import FIELDS, SCHEMA


def _row(row_id: int, spelling: str, latin: str, pos: str, **stems: str) -> tuple:
    return (
        row_id, spelling, spelling, spelling, latin,
        stems.get("past_fa"), stems.get("past"),
        stems.get("present_fa"), stems.get("present"),
        1.0, 0, None, None, pos, None, None,
    )  # fmt: skip


ROWS = [
    _row(1, "یار", "Yār", "اسم ذات"),
    _row(2, "پدر", "Pedar", "اسم ذات"),
    _row(3, "باغ", "Bāq", "اسم ذات"),
    _row(4, "رفتن", "raftan", "مصدر",
         past_fa="رفت", past="raft", present_fa="رو", present="row"),
    _row(5, "آبجو", "ābjow", "وام‌واژه"),
    _row(6, "هوش", "Huš", "اسم معنی"),
]  # fmt: skip

GROUPS = {
    1: ["نام"],
    2: ["نام"],
    3: ["نام"],
    4: ["نابسودکارواژه"],
    5: ["وام‌واژه"],
    6: ["کارنام"],
}

LABELS = [
    ("past_stem", "پیشین‌کاربن"),
    ("present_stem", "کنون‌کاربن"),
    ("نابسودکارواژه", "نابسودکارواژه"),
    ("نام", "نام"),
    ("کارنام", "کارنام"),
    ("وام‌واژه", "وام‌واژه"),
]


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    # A name no overrides table lists, so the shipped table stays out of it.
    path = tmp_path / "lexicon-20991231.sqlite"
    connection = sqlite3.connect(path)
    connection.execute(SCHEMA)
    connection.executemany(
        f"INSERT INTO infinitives ({FIELDS}) VALUES ({', '.join('?' * 16)})", ROWS
    )
    connection.execute(
        "UPDATE infinitives SET definition_preview = 'رونده.' WHERE id = 4"
    )
    connection.execute("CREATE TABLE bank_group (word_id INTEGER, bank_group TEXT)")
    connection.executemany(
        "INSERT INTO bank_group VALUES (?, ?)",
        [(row, group) for row, names in GROUPS.items() for group in names],
    )
    connection.execute("CREATE TABLE bank_labels (key TEXT PRIMARY KEY, label_fa TEXT)")
    connection.executemany("INSERT INTO bank_labels VALUES (?, ?)", LABELS)
    connection.commit()
    connection.close()
    monkeypatch.setenv("MURFULU_LEXICON_PATH", str(path))
    bank_api._shelf.cache_clear()
    yield TestClient(app)
    bank_api._shelf.cache_clear()


def test_the_groups_come_in_the_linguists_order_with_counts(client: TestClient) -> None:
    answer = client.get("/bank/groups").json()
    assert answer["has_bank"] is True
    assert answer["stem_labels"] == {"past": "پیشین‌کاربن", "present": "کنون‌کاربن"}
    keys = [one["key"] for one in answer["groups"]]
    assert keys == ["نابسودکارواژه", "نام", "کارنام", "وام‌واژه"]
    loan = next(one for one in answer["groups"] if one["key"] == "وام‌واژه")
    assert loan["in_word_formation"] is False and loan["word_classes"] == []
    assert answer["total"] == len(ROWS)
    assert {one["key"]: one["words"] for one in answer["groups"]}["نام"] == 3


def test_the_list_is_in_persian_alphabetical_order(client: TestClient) -> None:
    words = client.get("/bank", params={"group": "نام"}).json()["words"]
    # By code point پ (U+067E) would come after ی; in Persian it follows ب.
    assert [one["spelling_fa"] for one in words] == ["باغ", "پدر", "یار"]


def test_a_verb_carries_both_stems(client: TestClient) -> None:
    (verb,) = client.get("/bank", params={"group": "نابسودکارواژه"}).json()["words"]
    assert (verb["past_stem_fa"], verb["past_stem_latin"]) == ("رفت", "raft")
    assert (verb["present_stem_fa"], verb["present_stem_latin"]) == ("رو", "row")
    assert verb["definition_fa"] == "رونده."


def test_a_loanword_is_listed_and_builds_nothing(client: TestClient) -> None:
    (loan,) = client.get("/bank", params={"group": "وام‌واژه"}).json()["words"]
    assert loan["spelling_fa"] == "آبجو"
    assert loan["in_word_formation"] is False
    assert loan["groups"] == [{"key": "وام‌واژه", "label_fa": "وام‌واژه"}]


def test_search_finds_persian_letters_and_latin_readings(client: TestClient) -> None:
    by_letters = client.get("/bank", params={"q": "هو"}).json()
    assert [one["latin"] for one in by_letters["words"]] == ["Huš"]
    by_latin = client.get("/bank", params={"q": "ROW"}).json()
    assert [one["spelling_fa"] for one in by_latin["words"]] == ["رفتن"]


def test_pages_are_counted_and_an_unknown_group_is_refused(client: TestClient) -> None:
    page = client.get("/bank", params={"offset": 2, "limit": 2}).json()
    assert page["total"] == len(ROWS) and len(page["words"]) == 2
    assert client.get("/bank", params={"group": "ناگروه"}).status_code == 400


def test_a_hamza_mark_and_a_decomposed_letter_do_not_hide_a_word() -> None:
    """خامهٔ افشان is found as خامه افشان; *huš* typed as u + combining caron too."""
    import unicodedata

    assert bank_api._plain("خامهٔ افشان") == bank_api._plain("خامه افشان")
    assert bank_api.sort_key("خامهٔ افشان")[0] == bank_api.sort_key("خامه افشان")[0]
    decomposed = unicodedata.normalize("NFD", "huš")
    assert decomposed != "huš"
    assert bank_api._latin(decomposed) == "huš"


def test_a_loanword_on_a_snapshot_before_the_bank_builds_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "lexicon-20991230.sqlite"
    connection = sqlite3.connect(path)
    connection.execute(SCHEMA)
    connection.executemany(
        f"INSERT INTO infinitives ({FIELDS}) VALUES ({', '.join('?' * 16)})",
        [
            _row(1, "آب در خصیه", "ābdarxosye", "وام‌واژه"),
            _row(2, "باغ", "Bāq", "اسم ذات"),
        ],
    )
    connection.commit()
    connection.close()
    monkeypatch.setenv("MURFULU_LEXICON_PATH", str(path))
    bank_api._shelf.cache_clear()
    words = TestClient(app).get("/bank").json()["words"]
    bank_api._shelf.cache_clear()
    flags = {one["spelling_fa"]: one["in_word_formation"] for one in words}
    assert flags == {"آب در خصیه": False, "باغ": True}
