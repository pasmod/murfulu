"""The compounding route: the first thing here that ever served a compound.

Sixteen compounding rules have been in the pack since the transcription. The
ten templates were implemented in session 2 and **nothing called them**; the
six slots were implemented in session 10 and nothing called those either. So
every rule reported zero built forms and read as unimplemented, and a language
model given the API hand-assembled compounds because no route would make one.

What is asserted here is mostly the shape of the answer rather than the
Persian, because the Persian is the engine's and is already tested against the
grammar's own examples in `test_engine_compound.py`. The shape is what was
decided: attested pairings ranked, the count of what was set aside beside
them, and inflection-shaped rows marked rather than dropped.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from murfulu.api.app import app
from murfulu.compounding import own_readings
from murfulu.lexicon.entries import Reading
from murfulu.scoring.attestation import Attestation, Level


@pytest.fixture
def client(
    lexicon_snapshot: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    """A client on the fixture snapshot, never the real 28 MB one."""
    from murfulu.api import compound

    monkeypatch.setenv("MURFULU_LEXICON_PATH", str(lexicon_snapshot))
    # The partner pool and the analyser are cached per snapshot; a test that
    # inherited another test's cache would measure the wrong lexicon.
    compound._partners.cache_clear()
    compound._analyser.cache_clear()
    yield TestClient(app)


def _reading(body: dict[str, Any]) -> dict[str, Any]:
    return body["readings"][0]


def test_a_noun_is_joined_to_every_verb_stem(client: TestClient) -> None:
    """The slot rules: the caller's word in front, any stem behind.

    مرد against the fixture's two verbs. `attested=false` because the fixture
    corpus is not the real one and this is about what the rules license.
    """
    body = client.get("/compound", params={"word": "مرد", "attested": False}).json()
    reading = _reading(body)

    made = {row["form_fa"] for row in reading["pairings"]}
    # رو is رفتن's present stem and گو is گفتن's, so both verbs were offered.
    assert "مردرو" in made
    assert "مردگو" in made
    assert reading["built"] > 0
    # Every verb in the snapshot that has both stems written, which is the
    # denominator behind every coverage figure the route reports.
    assert reading["partners_tried"] >= 2


def test_every_compound_says_what_was_joined_to_what(client: TestClient) -> None:
    """The second half is the part the caller did not choose, so it is named."""
    body = client.get("/compound", params={"word": "مرد", "attested": False}).json()

    for row in _reading(body)["pairings"]:
        assert row["front"]["fa"]
        assert row["behind"]["fa"]
        assert row["rule_id"]
        # A compound that cannot say which rule joined it is the same defect
        # as a built word with no derivation.
        assert row["explanation_fa"]
        assert row["role"] in ("front", "behind", "both")


def test_a_verb_reaches_the_templates_and_a_noun_is_told_why_it_cannot(
    client: TestClient,
) -> None:
    """A template draws both halves from one verb. That is not an empty result."""
    verb = _reading(
        client.get("/compound", params={"word": "رفتن", "attested": False}).json()
    )
    noun = _reading(
        client.get("/compound", params={"word": "مرد", "attested": False}).json()
    )

    assert "رفتورو" in {row["form_fa"] for row in verb["pairings"]}
    assert "template" not in verb["skipped"]
    assert "template" in noun["skipped"]
    assert "not a verb" in noun["skipped"]["template"]


def test_a_word_no_rule_accepts_says_which_class_it_is(client: TestClient) -> None:
    """Zero built, and nothing wrong — the screen has to be able to say why.

    پی is filed اسم معنی, which the source grammar makes a **kārnām**, and all
    six slot rules take a **nām** in front. So it is shut out of every
    compounding rule in the pack (L18; 1,949 readings are in that position) and
    the route used to report a bare zero with no reason on it.
    """
    body = client.get("/compound", params={"word": "پی", "attested": False}).json()
    reading = _reading(body)

    assert reading["built"] == 0
    assert reading["word_classes"] == ["karnam"]
    assert "nam" in reading["slot_wants"]
    assert "karnam" in reading["skipped"]["slot"]


def test_the_answer_says_what_it_set_aside(client: TestClient) -> None:
    """A list of forty means nothing without the 3,071 behind it.

    One noun makes 3,071 compounds and the corpus holds 0.5%–3.3%, so the
    counts are not decoration: they are what makes the shown list readable.
    """
    body = client.get("/compound", params={"word": "مرد"}).json()
    reading = _reading(body)

    assert reading["built"] >= reading["attested"]
    assert reading["built"] - reading["attested"] == reading["unattested"]
    assert body["showing"] == "attested"


def test_everything_built_is_one_parameter_away(client: TestClient) -> None:
    """Nothing is hidden, only ranked — so the whole list stays reachable."""
    shown = _reading(client.get("/compound", params={"word": "مرد"}).json())
    whole = _reading(
        client.get("/compound", params={"word": "مرد", "attested": False}).json()
    )

    assert whole["returned"] >= shown["returned"]
    assert whole["built"] == shown["built"]


def test_two_named_words_reach_the_rules_with_two_free_sides(
    client: TestClient,
) -> None:
    """Over the lexicon these are a product; naming the second word is the way in."""
    body = client.get(
        "/compound", params={"word": "مرد", "partner": "گفتن", "attested": False}
    ).json()

    assert body["partner"] == "گفتن"
    made = {row["form_fa"] for row in _reading(body)["pairings"]}
    assert made


def test_an_unknown_word_is_a_404(client: TestClient) -> None:
    assert client.get("/compound", params={"word": "نیستچنینچیزی"}).status_code == 404


def test_an_unknown_partner_is_a_404_too(client: TestClient) -> None:
    response = client.get(
        "/compound", params={"word": "مرد", "partner": "نیستچنینچیزی"}
    )
    assert response.status_code == 404


def test_the_limit_caps_the_rows_without_changing_the_counts(
    client: TestClient,
) -> None:
    """A count that shrank with the page would look like a small answer."""
    whole = _reading(
        client.get("/compound", params={"word": "مرد", "attested": False}).json()
    )
    capped = _reading(
        client.get(
            "/compound", params={"word": "مرد", "attested": False, "limit": 2}
        ).json()
    )

    assert capped["returned"] == 2
    assert len(capped["pairings"]) == 2
    assert capped["built"] == whole["built"]


def test_the_page_says_where_it_is_and_whether_more_remain(
    client: TestClient,
) -> None:
    """The same three fields /generate carries: offset, returned, has_more."""
    ask = {"word": "مرد", "attested": False, "limit": 2}
    reading = _reading(client.get("/compound", params=ask).json())

    assert reading["returned"] == 2
    assert reading["offset"] == 0
    assert reading["count"] > 2  # the whole list, not the page
    assert reading["has_more"] is True


def test_the_pages_together_are_the_whole_list(client: TestClient) -> None:
    """Paging must not drop or repeat a pairing, the only thing it can break.

    Written with 9.5: the route took a `limit` and no `offset`, so everything
    past the limit was unreachable by any request.
    """
    ask = {"word": "مرد", "attested": False, "limit": 0}
    whole = _reading(client.get("/compound", params=ask).json())
    expected = [p["form_latin"] for p in whole["pairings"]]

    collected: list[str] = []
    offset = 0
    while True:
        page = _reading(
            client.get(
                "/compound",
                params={
                    "word": "مرد",
                    "attested": False,
                    "limit": 25,
                    "offset": offset,
                },
            ).json()
        )
        collected += [p["form_latin"] for p in page["pairings"]]
        if not page["has_more"]:
            break
        offset += 25

    assert collected == expected


def test_the_last_page_says_there_is_no_more(client: TestClient) -> None:
    whole = _reading(
        client.get(
            "/compound", params={"word": "مرد", "attested": False, "limit": 0}
        ).json()
    )
    total = whole["count"]

    last = _reading(
        client.get(
            "/compound",
            params={
                "word": "مرد",
                "attested": False,
                "limit": 10,
                "offset": total - 3,
            },
        ).json()
    )

    assert last["returned"] == 3
    assert last["has_more"] is False


def test_a_reading_the_dictionary_doubts_still_says_so(client: TestClient) -> None:
    """The flag travels wherever a reading does, as it does on /generate."""
    body = client.get("/compound", params={"word": "مرد", "attested": False}).json()

    for reading in body["readings"]:
        assert "needs_review" in reading


def test_a_compound_the_corpus_lacks_is_not_counted_as_attested(
    client: TestClient,
) -> None:
    """The corpus answers for every spelling and says `none` where it has nothing.

    Filtering on "an attestation object came back" therefore counts every form
    as attested, and دل reported 5,223 of 5,223 before this was caught. The
    level is what says whether anyone wrote the word.
    """
    reading = _reading(
        client.get("/compound", params={"word": "مرد", "attested": False}).json()
    )

    for row in reading["pairings"]:
        found = row["attestation"]
        if found is not None:
            assert row["is_attested"] == (found["level"] != "none")
    assert reading["attested"] == sum(
        1 for row in reading["pairings"] if row["is_attested"]
    )


def test_the_same_join_by_the_same_rule_appears_once(client: TestClient) -> None:
    """Two verbs can share a stem spelling, and each produced its own row.

    Two *rules* writing the same letters is kept: V-078 and V-079 mean the
    doer and the done-to, and that is information.
    """
    reading = _reading(
        client.get("/compound", params={"word": "مرد", "attested": False}).json()
    )

    seen = [
        (row["form_fa"], row["form_latin"], row["rule_id"], row["behind"]["latin"])
        for row in reading["pairings"]
    ]
    assert len(seen) == len(set(seen))


def test_naming_the_partner_does_not_lose_the_same_verb_templates(
    client: TestClient,
) -> None:
    """`?word=رفتن` gave Raftorow and `?word=رفتن&partner=رفتن` gave nothing.

    The two words were joined as plain words, and a template needs whole
    verbs. Asking for a verb against itself is how a caller reaches the
    same-verb templates by name.
    """
    alone = _reading(
        client.get("/compound", params={"word": "رفتن", "attested": False}).json()
    )
    named = _reading(
        client.get(
            "/compound",
            params={"word": "رفتن", "partner": "رفتن", "attested": False},
        ).json()
    )

    assert "رفتورو" in {row["form_fa"] for row in alone["pairings"]}
    assert "رفتورو" in {row["form_fa"] for row in named["pairings"]}


def test_two_different_verbs_reach_the_rules_written_for_them(
    client: TestClient,
) -> None:
    """V-017, V-019, V-043 and V-047 join two *different* verbs.

    They were listed as active with examples — Zadoxord, Xordoxāb, Suzogodāz,
    Rixtopāš — and no route could fire them, because a partner was only ever
    offered as a plain word.
    """
    body = client.get(
        "/compound",
        params={"word": "رفتن", "partner": "گفتن", "attested": False},
    ).json()

    rules = {row["rule_id"] for row in _reading(body)["pairings"]}
    assert rules & {"V-017", "V-019", "V-043", "V-047"}


def test_a_template_reports_the_half_it_actually_used(client: TestClient) -> None:
    """V-021's second slot is the same verb's *past* stem, negated.

    The route reported the present stem for every template, so *Didonadid*
    was published as دید joined to بین.
    """
    body = client.get("/compound", params={"word": "رفتن", "attested": False}).json()

    negated = next(
        row for row in _reading(body)["pairings"] if row["rule_id"] == "V-021"
    )
    assert negated["front"]["latin"] == "raft"
    # The pattern is {a} + o + na + {b} over one verb, so both halves are the
    # past stem — never the present one.
    assert negated["behind"]["latin"] == "raft"
    assert negated["behind"]["latin"] in negated["form_latin"].lower()


# --- A spelling that is several entries (2026-11-21) ------------------------


def _entry(latin: str, *variants: str, spelling: str = "دل", row: int = 0) -> Reading:
    return Reading(
        spelling_fa=spelling,
        spelling_normalized=spelling,
        latin=latin,
        latin_variants=variants,
        lexicon_categories=("اسم ذات",),
        source_entry_ids=(row,) if row else (),
    )


def test_a_second_reading_that_is_another_entry_s_goes_to_that_entry() -> None:
    """دل's tree and ailment both carried *Del*, the heart's own reading.

    Built from, it filed دلبر and دلدار under the tree and the ailment as well
    as under the heart. The heart still has it; the borrowers do not.
    """
    tree, ailment, heart = own_readings(
        [_entry("Dal", "Del"), _entry("Dol", "Del"), _entry("Del")]
    )

    assert tree.all_latin == ("Dal",)
    assert ailment.all_latin == ("Dol",)
    assert heart.all_latin == ("Del",)


def test_a_second_reading_no_other_entry_has_is_kept() -> None:
    """گل's *Gol* also reads *Gal*, and no other entry is *Gal*: a real alternative."""
    flower, clay = own_readings([_entry("Gol", "Gal"), _entry("Gel")])

    assert flower.all_latin == ("Gol", "Gal")
    assert clay.all_latin == ("Gel",)


def test_another_entry_s_reading_is_recognised_whatever_its_case() -> None:
    """گرد's *Gerd* carried *Gard*, and *gard* (dust) is its own entry.

    A capital is a word class showing, not another word — the rule the corpus
    check follows — so the two are the same reading.
    """
    around, dust = own_readings([_entry("Gerd", "Gard"), _entry("gard")])

    assert around.all_latin == ("Gerd",)
    assert dust.all_latin == ("gard",)


def test_a_lookup_by_latin_is_cleaned_against_every_entry_with_those_letters() -> None:
    """Asked for *Dal* by its Latin, the lexicon returns the tree alone.

    The heart that owns *Del* is not among what came back, so it has to be
    looked up by the spelling to be seen — or the tree keeps the heart's words.
    """
    tree = _entry("Dal", "Del", row=11452)
    heart = _entry("Del", row=11456)

    (cleaned,) = own_readings([tree], {"دل": [tree, heart]})

    assert cleaned.all_latin == ("Dal",)


def test_entries_with_other_letters_are_not_compared() -> None:
    """*Čoquk* is چغوک, and چقوک's *Čaquk* lists *Čoquk*: that is چقوک's own.

    A lookup by Latin returned both, and comparing across spellings took the
    variant away and halved چقوک's words (10,572 to 5,286).
    """
    sparrow = _entry("Čoquk", spelling="چغوک", row=1)
    other = _entry("Čaquk", "Čoquk", spelling="چقوک", row=2)

    kept = own_readings([sparrow, other])

    assert kept[1].all_latin == ("Čaquk", "Čoquk")


class _Corpus:
    """A corpus that confirms every form built on *mord* and has nothing else."""

    def look_up(self, form_fa: str, form_latin: str) -> Attestation:
        if form_latin.startswith("mord"):
            return Attestation(
                level=Level.READING, corpus_version="test", total_count=3, doc_count=2
            )
        return Attestation(level=Level.NONE, corpus_version="test")


def test_the_reading_whose_words_are_confirmed_comes_first(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fixture lists مرد as *mard* then *mord*; the evidence says *mord*.

    دل opened on *Dal*, a tree in a dialect, because karbon lists it first. The
    words built on a reading that the dictionary holds under exactly that
    reading and the corpus has are the evidence for which entry leads.
    """
    from murfulu.api import compound

    monkeypatch.setattr(compound, "_asked", lambda pairings: _Corpus())
    body = client.get("/compound", params={"word": "مرد"}).json()

    assert [one["latin"] for one in body["readings"]] == ["mord", "mard"]
    first, second = body["readings"]
    assert second["confirmed"] == 0
    # Per form, not per row: V-078 and V-079 writing the same letters with the
    # same Latin are one word, however many rows they make.
    forms = {
        (row["form_fa"], row["form_latin"])
        for row in first["pairings"]
        if row["attestation"]["level"] == "reading"
    }
    assert first["confirmed"] == len(forms) > 0
    assert len(first["pairings"]) > first["confirmed"]


def test_a_corpus_that_does_not_answer_is_not_a_measured_zero(
    client: TestClient,
) -> None:
    """No corpus in the tests: nothing moves, and nothing claims it was measured.

    A zero here would let the screen say the corpus cannot tell the entries
    apart, when nobody asked it.
    """
    body = client.get("/compound", params={"word": "مرد", "attested": False}).json()

    assert [one["latin"] for one in body["readings"]] == ["mard", "mord"]
    assert {one["confirmed"] for one in body["readings"]} == {None}


def test_the_ranking_does_not_depend_on_the_page(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Counted on every row built, before the list is filtered and paged."""
    from murfulu.api import compound

    monkeypatch.setattr(compound, "_asked", lambda pairings: _Corpus())
    whole = client.get("/compound", params={"word": "مرد", "limit": 0}).json()
    one_row = client.get("/compound", params={"word": "مرد", "limit": 1}).json()

    assert [r["confirmed"] for r in one_row["readings"]] == [
        r["confirmed"] for r in whole["readings"]
    ]
    assert [r["latin"] for r in one_row["readings"]] == ["mord", "mard"]


def test_each_entry_is_named_by_its_dictionary_row(client: TestClient) -> None:
    """The Latin cannot name an entry: *Allākolang* is two words."""
    body = client.get("/compound", params={"word": "مرد", "attested": False}).json()

    assert [one["entry"] for one in body["readings"]] == [7, 8]


def test_each_entry_says_what_it_means(client: TestClient) -> None:
    """With two entries a tap apart, the definition is what tells them apart."""
    body = client.get("/compound", params={"word": "مرد", "attested": False}).json()

    assert _reading(body)["definition_fa"] == "آدمی نرینه. مقابل زن"
