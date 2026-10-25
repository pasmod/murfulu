"""The read-only lexicon wrapper."""

from pathlib import Path

import pytest

from murfulu.lexicon import (
    PATH_VARIABLE,
    Lexicon,
    SnapshotMissingError,
    SnapshotNotConfiguredError,
    open_snapshot,
)


def test_a_verb_comes_back_with_both_stems(lexicon_snapshot: Path):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (entry,) = lexicon.by_spelling("رفتن")
    assert entry.latin == "raftan"
    assert entry.past_stem_latin == "raft"
    assert entry.present_stem_latin == "row"
    assert entry.past_stem_fa == "رفت"
    assert entry.present_stem_fa == "رو"
    assert entry.has_both_stems
    assert entry.is_infinitive


def test_a_letter_from_another_alphabet_is_repaired_on_the_way_out(
    lexicon_snapshot: Path,
):
    """سپردن's present stem is written `sepοr` — with a Greek omicron.

    The Behnevis alphabet is a closed set, so a character outside it is always
    a fault and never a judgement. That is why this is repaired rather than
    held as an override: an override records a value we *believe differently*,
    and nobody believes a Greek omicron.

    Measured on the real snapshot: eleven Latin fields on eleven rows, and
    because a stem is copied into everything built on it, 2,592 forms in the
    v4 index carried one. None could be typed, searched or matched, while
    looking on screen exactly like a correct form. Reported upstream as
    docs/UPSTREAM.md A5; this is the local repair until it lands there.
    """
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (entry,) = lexicon.by_spelling("سپردن")
    assert entry.present_stem_latin == "sepor"
    assert "ο" not in (entry.present_stem_latin or "")
    # The variant list repeats the fault, so it is repaired there too.
    assert all("ο" not in one for one in entry.latin_variants)


def test_repeated_senses_collapse_but_keep_every_source_row(lexicon_snapshot: Path):
    """The dictionary lists one word several times. That stays visible."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        readings = lexicon.by_spelling("پی")
    pey = next(r for r in readings if r.latin == "Pey")
    assert pey.sense_count == 3
    assert pey.source_entry_ids == (2, 3, 4)


def test_a_homograph_is_never_collapsed(lexicon_snapshot: Path):
    """مرد is two words. One record each."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        readings = lexicon.by_spelling("مرد")
    assert sorted(r.latin for r in readings) == ["mard", "mord"]
    assert all(r.sense_count == 1 for r in readings)


def test_different_readings_of_one_spelling_stay_apart(lexicon_snapshot: Path):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        readings = lexicon.by_spelling("پی")
    assert sorted(r.latin for r in readings) == ["Pay", "Pey"]


def test_deleted_rows_are_never_returned(lexicon_snapshot: Path):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        assert lexicon.by_latin("Pi") == []
        assert lexicon.count_active() == 13


def test_a_doubt_about_one_sense_flags_the_reading(lexicon_snapshot: Path):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        pey = next(r for r in lexicon.by_spelling("پی") if r.latin == "Pey")
    assert pey.needs_review


def test_lookup_by_normalized_spelling(lexicon_snapshot: Path):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (entry,) = lexicon.by_normalized_spelling("بی نام")
    assert entry.latin == "binām"


def test_lookup_by_latin_does_not_fold_case(lexicon_snapshot: Path):
    """Gofte and gofte are different words. Case is meaning here."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        assert [r.spelling_fa for r in lexicon.by_latin("Pey")] == ["پی"]
        assert lexicon.by_latin("pey") == []


class TestLookingAWordUpByItsSecondReading:
    """آبرو is *Ābrav* **or** *Ābrov*, and both are the dictionary's answer.

    Question P settled that generation builds from every reading. **Lookup was
    never given the same treatment**, so 7,106 of the 7,181 second readings in
    the real snapshot could not be found at all and a caller typing a reading
    karbon itself records got a 404. Approved and fixed 2026-08-15; the risk
    was measured first — only 8 second readings collide with another word's
    primary, and all eight are the same word spelled two ways.
    """

    def test_the_second_reading_finds_the_word(self, lexicon_snapshot: Path):
        with Lexicon.open(lexicon_snapshot) as lexicon:
            (entry,) = lexicon.by_latin("Ābrov")
            assert entry.spelling_fa == "آبرو"
            assert entry.latin == "Ābrav", "the primary reading is still primary"

    def test_the_primary_reading_still_finds_it(self, lexicon_snapshot: Path):
        with Lexicon.open(lexicon_snapshot) as lexicon:
            (entry,) = lexicon.by_latin("Ābrav")
            assert entry.spelling_fa == "آبرو"

    def test_the_word_comes_back_once_not_twice(self, lexicon_snapshot: Path):
        """Both readings name one entry, so neither route may double it."""
        with Lexicon.open(lexicon_snapshot) as lexicon:
            assert len(lexicon.by_latin("Ābrav")) == 1
            assert len(lexicon.by_latin("Ābrov")) == 1

    def test_case_is_still_meaning(self, lexicon_snapshot: Path):
        """The variants are stored lower-case; the cased reading is the answer.

        So the filter is on `all_latin`, which carries the primary's
        capitalisation — not on the raw column, which would match anything.
        """
        with Lexicon.open(lexicon_snapshot) as lexicon:
            assert lexicon.by_latin("ābrov") == []
            assert lexicon.by_latin("Ābrov")

    def test_a_long_vowel_is_matched_too(self, lexicon_snapshot: Path):
        """SQLite's own `lower()` is ASCII only and leaves Ā alone.

        Matching case-blind in SQL therefore missed every reading beginning
        with a long vowel — *Ābrov* among them. Found by testing this fix, so
        the lower-casing is Python's.
        """
        with Lexicon.open(lexicon_snapshot) as lexicon:
            assert lexicon.by_latin("Ābrov"), "the Ā must not stop the match"


def test_a_null_category_is_kept_not_dropped(lexicon_snapshot: Path):
    """11 rows in the real snapshot have no category. They must not vanish."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (entry,) = lexicon.by_latin("binām")
    assert entry.lexicon_category is None
    assert entry.lexicon_categories == (None,)


def test_every_reading_carries_the_snapshot_id(lexicon_snapshot: Path):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (entry,) = lexicon.by_spelling("رفتن")
        assert entry.snapshot_id == lexicon.snapshot_id
    assert entry.snapshot_id.startswith("lexicon-fixture:")


def test_the_infinitives_are_the_verbs(lexicon_snapshot: Path):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        verbs = list(lexicon.infinitives())
    assert sorted(v.latin for v in verbs) == ["goftan", "raftan", "sepordan"]
    assert all(v.has_both_stems for v in verbs)


def test_karbon_stem_rule_is_carried_but_labelled(lexicon_snapshot: Path):
    """The karbon numbering is not the source grammar's. Stored, never used."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (entry,) = lexicon.by_spelling("رفتن")
    assert entry.karbon_stem_rule == 17


def test_another_snapshot_needs_no_code_change(
    lexicon_snapshot: Path, second_snapshot: Path
):
    with (
        Lexicon.open(lexicon_snapshot) as first,
        Lexicon.open(second_snapshot) as other,
    ):
        assert first.by_spelling("رفتن")[0].latin == "raftan"
        assert other.by_spelling("رفتن")[0].latin == "raftan"
        assert first.snapshot_id != other.snapshot_id


def test_the_path_comes_from_the_environment(
    lexicon_snapshot: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv(PATH_VARIABLE, str(lexicon_snapshot))
    with Lexicon.open() as lexicon:
        assert lexicon.by_spelling("گفتن")[0].present_stem_latin == "gu"


def test_an_unconfigured_path_fails_loudly(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(PATH_VARIABLE, raising=False)
    with pytest.raises(SnapshotNotConfiguredError):
        open_snapshot()


def test_a_missing_snapshot_fails_loudly(tmp_path: Path):
    with pytest.raises(SnapshotMissingError):
        open_snapshot(tmp_path / "nope.sqlite")


def test_the_snapshot_is_opened_read_only(lexicon_snapshot: Path):
    import sqlite3

    with (
        Lexicon.open(lexicon_snapshot) as lexicon,
        pytest.raises(sqlite3.OperationalError),
    ):
        lexicon._connection.execute("DELETE FROM infinitives")  # noqa: SLF001


def test_the_same_file_under_another_name_hashes_the_same(
    lexicon_snapshot: Path, second_snapshot: Path
):
    """The id is content plus name, so figures compare across machines."""
    first = open_snapshot(lexicon_snapshot).snapshot_id.split(":")[1]
    other = open_snapshot(second_snapshot).snapshot_id.split(":")[1]
    assert first == other


# -- words the lexicon reads more than one way -------------------------------


def test_a_second_reading_is_kept_not_dropped(lexicon_snapshot: Path):
    """7,212 rows in the real snapshot carry one. آبرو is Ābrav or Ābrov."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (entry,) = lexicon.by_spelling("آبرو")
    assert entry.latin == "Ābrav"
    assert entry.latin_variants == ("Ābrov",)
    assert entry.all_latin == ("Ābrav", "Ābrov")


def test_a_variant_takes_the_primary_capitalisation(lexicon_snapshot: Path):
    """Case is meaning in Behnevis, and a variant is the same class of word."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (entry,) = lexicon.by_spelling("آبرو")
    assert entry.latin_variants[0][0].isupper()


def test_a_variant_that_only_repeats_the_primary_is_not_a_variant(
    lexicon_snapshot: Path,
):
    """The stored list always includes the primary. That is not an alternative."""
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (entry,) = lexicon.by_spelling("آبرو")
    assert "Ābrav" not in entry.latin_variants
    assert len(entry.latin_variants) == 1


def test_a_word_with_one_reading_has_no_variants(lexicon_snapshot: Path):
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (entry,) = lexicon.by_spelling("رفتن")
    assert entry.latin_variants == ()
    assert entry.all_latin == ("raftan",)


def test_the_dictionary_definition_is_carried(lexicon_snapshot: Path):
    """96.1% of karbon's rows hold one and nothing of ours read it.

    Found by listing every column of the snapshot against the code that
    consumes it — the same audit that found برنا's second pronunciation.
    See tools/audit_lexicon_use.py and UPSTREAM B5.
    """
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (reading,) = lexicon.by_spelling("بلند")[:1]
    assert reading.definition_fa is not None
    assert "مرتفع" in reading.definition_fa


def test_a_verb_has_no_definition_and_that_is_the_data(lexicon_snapshot: Path):
    """Every class is 100% covered except مصدر, which is 0 of 1,752.

    So the build screen, which mostly starts from a verb, still cannot say
    what the word it is building from means. Asserted rather than left to be
    discovered on a screen.
    """
    with Lexicon.open(lexicon_snapshot) as lexicon:
        (reading,) = lexicon.by_spelling("رفتن")
    assert reading.definition_fa is None


def test_the_snapshot_is_opened_immutable_when_nothing_is_pending(
    lexicon_snapshot: Path,
) -> None:
    """S9: a WAL reader on a read-only mount cannot make the -shm it needs.

    `immutable=1` is the flag for exactly that, and it is what lets the
    container open a snapshot on a read-only mount at all.
    """
    from murfulu.lexicon.store import _open_mode

    assert _open_mode(lexicon_snapshot) == "immutable=1"


def test_a_pending_write_ahead_log_falls_back_to_read_only(
    lexicon_snapshot: Path, tmp_path: Path
) -> None:
    """`immutable=1` ignores the WAL entirely, so it must not be promised falsely.

    A snapshot with pending transactions would be read as though they had
    never happened — silently, and wrongly. A non-empty `-wal` beside the file
    is the evidence that somebody has written to it.
    """
    from murfulu.lexicon.store import _open_mode

    copied = tmp_path / lexicon_snapshot.name
    copied.write_bytes(lexicon_snapshot.read_bytes())
    journal = copied.with_name(copied.name + "-wal")

    journal.write_bytes(b"")
    assert _open_mode(copied) == "immutable=1", "an empty log is not a pending write"

    journal.write_bytes(b"not empty")
    assert _open_mode(copied) == "mode=ro"


def test_the_lexicon_still_reads_with_a_pending_log(
    lexicon_snapshot: Path, tmp_path: Path
) -> None:
    """The fallback has to work, not merely be chosen."""
    copied = tmp_path / lexicon_snapshot.name
    copied.write_bytes(lexicon_snapshot.read_bytes())
    copied.with_name(copied.name + "-wal").write_bytes(b"not empty")

    with Lexicon.open(copied) as lexicon:
        assert lexicon.count_active() > 0
