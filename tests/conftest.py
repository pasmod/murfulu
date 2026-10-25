"""Shared fixtures.

The lexicon fixture mirrors the real snapshot's schema but holds a handful of
handmade rows. No test reads the real lexicon: it is 28 MB, it is not in the
repository, and a test that needs it cannot run in CI.
"""

import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

SCHEMA = """
CREATE TABLE infinitives (
    id INTEGER PRIMARY KEY,
    headword TEXT NOT NULL,
    headword_normalized TEXT NOT NULL,
    vowelized TEXT NOT NULL,
    phonemic TEXT NOT NULL,
    past_stem_fa TEXT, past_stem_lat TEXT,
    present_stem_fa TEXT, present_stem_lat TEXT,
    rule_applied INTEGER, confidence REAL, needs_review INTEGER DEFAULT 0,
    file_path TEXT, notes TEXT DEFAULT '', deleted_at TEXT,
    transitivity TEXT, transitivity_source TEXT,
    transitivity_confidence REAL, transitivity_reason TEXT,
    pos TEXT, tag TEXT, bracket_raw TEXT, phonemic_variants TEXT,
    definition_preview TEXT, stem_rule INTEGER, stem_group INTEGER,
    subgroup TEXT
)
"""

FIELDS = (
    "id, headword, headword_normalized, vowelized, phonemic, "
    "past_stem_fa, past_stem_lat, present_stem_fa, present_stem_lat, "
    "confidence, needs_review, deleted_at, transitivity, pos, stem_rule, "
    "phonemic_variants"
)

# A verb with both stems; one spelling listed three times in the same reading;
# a real homograph; a soft-deleted row; a row with a null category; and a word
# the lexicon reads two ways (آبرو).
ROWS = [
    (
        1,
        "رفتن",
        "رفتن",
        "رفتن",
        "raftan",
        "رفت",
        "raft",
        "رو",
        "row",
        1.0,
        0,
        None,
        "intransitive",
        "مصدر",
        17,
        None,
    ),
    (
        2,
        "پی",
        "پی",
        "پی",
        "Pey",
        None,
        None,
        None,
        None,
        1.0,
        0,
        None,
        None,
        "اسم معنی",
        None,
        None,
    ),
    (
        3,
        "پی",
        "پی",
        "پی",
        "Pey",
        None,
        None,
        None,
        None,
        1.0,
        1,
        None,
        None,
        "اسم معنی",
        None,
        None,
    ),
    (
        4,
        "پی",
        "پی",
        "پی",
        "Pey",
        None,
        None,
        None,
        None,
        1.0,
        0,
        None,
        None,
        "اسم معنی",
        None,
        None,
    ),
    (
        5,
        "پی",
        "پی",
        "پی",
        "Pay",
        None,
        None,
        None,
        None,
        1.0,
        0,
        None,
        None,
        "اسم معنی",
        None,
        None,
    ),
    (
        6,
        "پی",
        "پی",
        "پی",
        "Pi",
        None,
        None,
        None,
        None,
        1.0,
        0,
        "2026-01-01",
        None,
        "اسم معنی",
        None,
        None,
    ),
    (
        7,
        "مرد",
        "مرد",
        "مرد",
        "mard",
        None,
        None,
        None,
        None,
        1.0,
        0,
        None,
        None,
        "اسم ذات",
        None,
        None,
    ),
    (
        8,
        "مرد",
        "مرد",
        "مرد",
        "mord",
        None,
        None,
        None,
        None,
        1.0,
        0,
        None,
        None,
        "اسم ذات",
        None,
        None,
    ),
    (
        9,
        "گفتن",
        "گفتن",
        "گفتن",
        "goftan",
        "گفت",
        "goft",
        "گو",
        "gu",
        1.0,
        0,
        None,
        "transitive",
        "مصدر",
        19,
        None,
    ),
    (
        10,
        "بی‌نام",
        "بی نام",
        "بی‌نام",
        "binām",
        None,
        None,
        None,
        None,
        0.4,
        0,
        None,
        None,
        None,
        None,
        None,
    ),
    (
        11,
        "آبرو",
        "آبرو",
        "آبرو",
        "Ābrav",
        None,
        None,
        None,
        None,
        1.0,
        0,
        None,
        None,
        "اسم مرکب",
        None,
        '["\u0101brav", "\u0101brov"]',
    ),
    # sepordan, as the snapshot really writes it: the present stem carries a
    # Greek omicron where an `o` was meant, and the variant list repeats it.
    # Eleven rows of the real snapshot hold a letter from another alphabet,
    # and this is the expensive one \u2014 a stem is copied into everything built
    # on it. See docs/UPSTREAM.md A5.
    (
        12,
        "\u0633\u067e\u0631\u062f\u0646",
        "\u0633\u067e\u0631\u062f\u0646",
        "\u0633\u067e\u0631\u062f\u0646",
        "sepordan",
        "\u0633\u067e\u0631\u062f",
        "sepord",
        "\u0633\u067e\u0631",
        "sep\u03bfr",
        1.0,
        0,
        None,
        "transitive",
        "\u0645\u0635\u062f\u0631",
        None,
        '["sep\u03bfr"]',
    ),
    # \u0628\u0644\u0646\u062f, as the real snapshot has it: the flagged
    # reading is written first and the clean one second, so row order alone
    # would open the
    # screen on the one the dictionary itself doubts. See generation.ordered.
    (
        13,
        "\u0628\u0644\u0646\u062f",
        "\u0628\u0644\u0646\u062f",
        "\u0628\u0644\u0646\u062f",
        "Baland",
        None,
        None,
        None,
        None,
        0.4,
        1,
        None,
        None,
        "\u0627\u0633\u0645 \u0630\u0627\u062a",
        None,
        None,
    ),
    (
        14,
        "\u0628\u0644\u0646\u062f",
        "\u0628\u0644\u0646\u062f",
        "\u0628\u0644\u0646\u062f",
        "boland",
        None,
        None,
        None,
        None,
        1.0,
        0,
        None,
        None,
        "\u0635\u0641\u062a",
        None,
        None,
    ),
]


#: The dictionary's own definition, set by headword after the insert so the
#: row tuples stay readable. **رفتن and گفتن deliberately have none**: karbon
#: gives every word class a definition for 100% of its rows except مصدر, which
#: has none at all, and a verb is what the build screen mostly starts from.
DEFINITIONS = {
    "بلند": "دراز. مرتفع. آنچه از زمین بالا رفته باشد",
    "مرد": "آدمی نرینه. مقابل زن",
}


def _write(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute(SCHEMA)
    placeholders = ", ".join("?" * len(ROWS[0]))
    connection.executemany(
        f"INSERT INTO infinitives ({FIELDS}) VALUES ({placeholders})", ROWS
    )
    connection.executemany(
        "UPDATE infinitives SET definition_preview = ? WHERE headword = ?",
        [(text, headword) for headword, text in DEFINITIONS.items()],
    )
    connection.commit()
    connection.close()


@pytest.fixture(scope="session")
def lexicon_snapshot(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build a small lexicon snapshot with the real schema."""
    path = tmp_path_factory.mktemp("lexicon") / "lexicon-fixture.sqlite"
    _write(path)
    return path


@pytest.fixture(scope="session")
def second_snapshot(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the same content under another name: the path must be configurable."""
    path = tmp_path_factory.mktemp("lexicon2") / "lexicon-20990101.sqlite"
    _write(path)
    return path


GANJOOR_SCHEMA = """
CREATE TABLE poet (id INTEGER PRIMARY KEY, name TEXT, cat_id INTEGER, description TEXT);
CREATE TABLE cat (id INTEGER PRIMARY KEY, poet_id INTEGER, text TEXT,
                  parent_id INTEGER, url TEXT);
CREATE TABLE poem (id INTEGER PRIMARY KEY, cat_id INTEGER, title TEXT, url TEXT);
CREATE TABLE verse (poem_id INTEGER, vorder INTEGER, position INTEGER, text TEXT);
"""

# Two poets, one with a century in the table and one without; a poem whose
# verses are prose paragraphs, and a poem with no verses at all.
GANJOOR_ROWS = {
    "poet": [(2, "حافظ", 9, ""), (3, "خیام", 30, "")],
    "cat": [
        (9, 2, "حافظ", 0, "https://ganjoor.net/hafez"),
        (24, 2, "غزلیات", 9, "https://ganjoor.net/hafez/ghazal"),
        (30, 3, "خیام", 0, "https://ganjoor.net/khayyam"),
        (31, 3, "رباعیات", 30, "https://ganjoor.net/khayyam/robaee"),
    ],
    "poem": [
        (100, 24, "غزل شمارهٔ ۱", "https://ganjoor.net/hafez/ghazal/sh1"),
        (101, 31, "رباعی شمارهٔ ۱", "https://ganjoor.net/khayyam/robaee/sh1"),
        (102, 24, "بی‌بیت", "https://ganjoor.net/hafez/ghazal/sh2"),
    ],
    "verse": [
        (100, 1, 0, "الا یا ایها الساقی ادر کاسا و ناولها"),
        (100, 2, 1, "که عشق آسان نمود اول ولی افتاد مشکل‌ها"),
        (101, 1, 0, "برخیز بتا بیا ز بهر دل ما"),
        (101, 2, 3, "این یک بند نثر است و باید کنار گذاشته شود"),
    ],
}


@pytest.fixture(scope="session")
def ganjoor_snapshot(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A tiny corpus with the real Ganjoor schema."""
    path = tmp_path_factory.mktemp("ganjoor") / "ganjoor-fixture.db"
    connection = sqlite3.connect(path)
    connection.executescript(GANJOOR_SCHEMA)
    for table, rows in GANJOOR_ROWS.items():
        placeholders = ", ".join("?" * len(rows[0]))
        connection.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
    connection.commit()
    connection.close()
    return path


# -- Elasticsearch: leaving the machine as we found it -----------------------
#
# The live tests move the aliases the app serves from, which is the point —
# they test the real route against the real alias. What they must not do is
# leave them moved. On a machine with an ingested corpus, a test that released
# `word_types` onto its own fixture index and then deleted that index left the
# alias pointing at nothing: `/search` answered "index has not been built"
# while 411,166 word types sat in the cluster untouched.
#
# So an alias is saved before and put back afterwards, whatever the test did.


@contextmanager
def aliases_restored(client: Any, names: Iterable[str]) -> Iterator[None]:
    """Put the aliases back where they were, however the test leaves them."""
    wanted = list(names)

    def behind(alias: str) -> list[str]:
        if not client.indices.exists_alias(name=alias):
            return []
        return sorted(client.indices.get_alias(name=alias).body)

    before = {alias: behind(alias) for alias in wanted}
    try:
        yield
    finally:
        actions: list[dict[str, Any]] = []
        for alias in wanted:
            for now in behind(alias):
                actions.append({"remove": {"index": now, "alias": alias}})
            for original in before[alias]:
                # An index the test deleted cannot be restored to, and saying
                # so beats failing the teardown of an otherwise good test.
                if client.indices.exists(index=original):
                    actions.append({"add": {"index": original, "alias": alias}})
        if actions:
            client.indices.update_aliases(actions=actions)
