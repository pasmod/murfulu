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
