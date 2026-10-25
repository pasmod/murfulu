"""The HTTP surface.

The rule routes need nothing at all — the pack is data in the repository. The
generation routes are pointed at the fixture snapshot. The search routes need
Elasticsearch and answer 503 without it, which is itself worth testing: an
unreachable index must say so rather than look like an empty result.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from murfulu.api.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def with_fixture_lexicon(
    lexicon_snapshot: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    """A client whose lexicon is the fixture, never the real 28 MB snapshot."""
    monkeypatch.setenv("MURFULU_LEXICON_PATH", str(lexicon_snapshot))
    yield TestClient(app)


# -- the rule pack -----------------------------------------------------------


def test_the_rules_route_lists_the_whole_pack(client: TestClient):
    body = client.get("/rules").json()
    assert body["count"] == len(body["rules"]) > 100
    assert body["rule_pack_version"]


def test_rules_can_be_filtered_by_family(client: TestClient):
    body = client.get("/rules", params={"family": "V"}).json()
    assert body["count"]
    assert all(rule["id"].startswith("V-") for rule in body["rules"])


def test_rules_can_be_filtered_by_what_they_take(client: TestClient):
    body = client.get("/rules", params={"takes": "karbon_do"}).json()
    assert all("karbon_do" in rule["input_types"] for rule in body["rules"])


def test_the_flagged_rules_can_be_asked_for(client: TestClient):
    body = client.get("/rules", params={"flagged": True}).json()
    assert all(rule["needs_expert_check"] for rule in body["rules"])
    assert all(rule["notes"] for rule in body["rules"])


def test_a_rule_carries_its_farsi(client: TestClient):
    """The interface is in Farsi; a rule with no Farsi cannot be shown."""
    rule = client.get("/rules/V-010").json()
    assert rule["explanation_fa"]
    assert rule["label_fa"]
    assert rule["source"]["row"] == "10"


def test_a_retired_rule_is_still_reachable(client: TestClient):
    """A stored derivation can name a rule that no longer applies."""
    glide = client.get("/rules/G-01").json()
    assert glide["kind"] == "glide"
    assert glide["active"] is False
    assert glide["retired_reason"]


def test_a_retired_affix_rule_says_why_too(client: TestClient):
    """Only the glide branch served the reason, so an affix rule went quiet.

    Found on N-090 after it was retired: the rules screen showed it switched
    off with nothing beside it, which reads as a rule somebody disabled rather
    than one that was ruled on. The pack has carried `retired_reason` since
    G-01 and requires it whenever `active` is false; the route was dropping it
    for every rule that is not a glide.
    """
    rule = client.get("/rules/N-090").json()
    assert rule["active"] is False
    assert rule["retired_reason"]
    # Still fully readable: the source row is not withdrawn, only switched off.
    assert rule["examples"] == ["Ketābé", "u"]


def test_the_glide_family_is_served_not_empty(client: TestClient):
    """`/rules?family=G` returned nothing, so the screen's button emptied it.

    17 glide rules sit in `rules/glides.yaml` and every build result names
    them — `ow->av`, G-10, G-11 — with nowhere to look one up. They were the
    only family with a button and no members.

    They are not forced into the affix envelope: a glide has no affix, no
    input class and no semantic tag, so serving it with those fields null
    would put blanks on screen where an affix goes. It carries `kind:
    "glide"` and its own three fields, which is what /rules/{id} has always
    returned for one.
    """
    body = client.get("/rules", params={"family": "G"}).json()
    assert body["count"] == 17
    glide = next(r for r in body["rules"] if r["id"] == "G-03")
    assert glide["kind"] == "glide"
    assert (glide["left"], glide["right"], glide["result"]) == ("ā", "e", "āye")
    assert glide["explanation_fa"]
    assert "Pā + e = Pāye" in glide["examples"]
    # Retired glides are included and marked, like every other retired rule.
    retired = next(r for r in body["rules"] if r["id"] == "G-01")
    assert retired["active"] is False
    assert retired["retired_reason"]


def test_a_filter_a_glide_cannot_answer_leaves_it_out(client: TestClient):
    """A glide takes no word class and carries no tag, so it matches neither."""
    body = client.get("/rules", params={"takes": "nam"}).json()
    assert not [r for r in body["rules"] if r["kind"] == "glide"]


def test_an_unknown_rule_is_a_404(client: TestClient):
    assert client.get("/rules/V-999").status_code == 404


def test_affixes_are_grouped_by_meaning(client: TestClient):
    """The founding complaint, answered: which affixes mean *place*."""
    body = client.get("/affixes", params={"tag": "Jā"}).json()
    assert body["count"] == 1
    meaning = body["meanings"][0]
    assert meaning["tag"] == "Jā"
    assert meaning["gloss_fa"]
    assert meaning["affixes"]


def test_every_meaning_comes_back_unfiltered(client: TestClient):
    body = client.get("/affixes").json()
    assert body["count"] > 1


# -- generation --------------------------------------------------------------


def test_a_verb_generates_from_both_stems(with_fixture_lexicon: TestClient):
    """`limit=0` asks for the whole answer, which is what this is about."""
    body = with_fixture_lexicon.get(
        "/generate", params={"word": "رفتن", "limit": 0}
    ).json()
    reading = body["readings"][0]
    classes = {base["word_class"] for base in reading["built_from"]}
    assert classes == {"karbon_yek", "karbon_do"}
    forms = {form["form_latin"] for form in reading["forms"]}
    assert {"Raftār", "Raveš", "ravande", "Ravandegi"} <= forms


def test_the_build_answer_is_paged_and_says_so(with_fixture_lexicon: TestClient):
    """S1: بلند at depth 2 is 2,856 forms and 3.94 MB, and it stalled a caller.

    Nothing is hidden, only paged — so a reading states how many forms it
    holds, how many came back, from where, and whether more remain. A count
    that shrank with the page size would look exactly like a small answer.
    """
    ask = {"word": "رفتن", "limit": 5}
    reading = with_fixture_lexicon.get("/generate", params=ask).json()["readings"][0]

    assert reading["returned"] == 5
    assert len(reading["forms"]) == 5
    assert reading["count"] > 5  # the total, not the page
    assert reading["offset"] == 0
    assert reading["has_more"] is True


def test_the_pages_together_are_the_whole_answer(with_fixture_lexicon: TestClient):
    """Paging must not drop or repeat a form, which is the only thing it can break."""
    ask = {"word": "رفتن", "limit": 0}
    whole = with_fixture_lexicon.get("/generate", params=ask).json()["readings"][0]
    expected = [form["form_latin"] for form in whole["forms"]]

    collected: list[str] = []
    offset = 0
    while True:
        page = with_fixture_lexicon.get(
            "/generate", params={"word": "رفتن", "limit": 50, "offset": offset}
        ).json()["readings"][0]
        collected += [form["form_latin"] for form in page["forms"]]
        if not page["has_more"]:
            break
        offset += 50

    assert collected == expected


def test_the_last_page_says_there_is_no_more(with_fixture_lexicon: TestClient):
    reading = with_fixture_lexicon.get(
        "/generate", params={"word": "رفتن", "limit": 0}
    ).json()["readings"][0]
    total = reading["count"]

    last = with_fixture_lexicon.get(
        "/generate", params={"word": "رفتن", "limit": 10, "offset": total - 3}
    ).json()["readings"][0]

    assert last["returned"] == 3
    assert last["has_more"] is False


def test_a_lighter_answer_still_states_every_derivation(
    with_fixture_lexicon: TestClient,
):
    """`worded=false` drops the Persian, never the derivation.

    Every generated word must carry its derivation — settled after the
    *sāzāyi* incident, and output without one is a defect. What it may drop is
    the per-step label and explanation, which belong to the **rule** and are
    43% of the bytes because 8,731 steps repeat them.
    """
    ask = {"word": "رفتن", "limit": 20, "worded": False}
    reading = with_fixture_lexicon.get("/generate", params=ask).json()["readings"][0]

    for form in reading["forms"]:
        assert form["paths"]
        for path in form["paths"]:
            assert path
            for step in path:
                assert step["rule_id"]
                assert "applied_to" in step
                assert "explanation_fa" not in step


def test_a_step_says_what_its_rule_means(with_fixture_lexicon: TestClient):
    """The sense a rule carries, which is often all that tells it from its neighbours.

    وارفتنی is built four ways and all four attach the same ``vā-`` to the same
    stem by the same mechanics: V-070, V-071, V-072 and V-073 share a word for
    word identical ``explanation_fa``. What separates them is the sense —
    پس، دوباره، باز، آخشیج — and until 2026-08-18 the screen printed the same
    sentence four times with no way to see why there were four.
    """
    from murfulu.rules.pack import loaded

    pack = loaded()
    wanted = {"V-070": "پس", "V-071": "دوباره", "V-072": "باز", "V-073": "آخشیج"}
    for rule_id, gloss in wanted.items():
        rule = pack.by_id(rule_id)
        glosses = [
            found.gloss_fa
            for found in (pack.tag_for(label) for label in rule.semantic_tags)
            if found is not None
        ]
        assert gloss in glosses, f"{rule_id} lost its sense"

    body = with_fixture_lexicon.get("/generate", params={"word": "رفتن"}).json()
    for form in body["readings"][0]["forms"]:
        for path in form["paths"]:
            for step in path:
                # Present on every worded step, even where the rule is
                # untagged — an empty list is an answer, a missing key is not.
                assert isinstance(step["tags_fa"], list)


def test_the_unworded_shape_carries_no_meanings(with_fixture_lexicon: TestClient):
    """It is wording, and `worded=false` exists to drop wording."""
    ask = {"word": "رفتن", "limit": 20, "worded": False}
    reading = with_fixture_lexicon.get("/generate", params=ask).json()["readings"][0]
    for form in reading["forms"]:
        for path in form["paths"]:
            for step in path:
                assert "tags_fa" not in step


def test_every_form_states_how_it_was_built(with_fixture_lexicon: TestClient):
    """A word that cannot state its own derivation is a bug."""
    body = with_fixture_lexicon.get("/generate", params={"word": "رفتن"}).json()
    for form in body["readings"][0]["forms"]:
        assert form["paths"]
        for path in form["paths"]:
            assert path
            for step in path:
                assert step["rule_id"]
                assert step["explanation_fa"]


def test_a_reading_the_lexicon_doubts_says_so(with_fixture_lexicon: TestClient):
    """The dictionary's own doubt has to reach the reader.

    بلند has two readings in the real snapshot: *Baland*, filed as an اسم ذات
    and carrying `needs_review`, and *boland*, filed as a صفت and clean. The
    build screen showed *Baland* first, built 2,612 words from it and never
    mentioned the flag — while the same snapshot spells سربلند *sarboland*.

    31.5% of the 45,579 active rows carry the flag, so this is not one word.
    Nothing is filtered and nothing is reordered on it: the answer simply
    stops leaving the dictionary's own doubt behind.
    """
    body = with_fixture_lexicon.get("/generate", params={"word": "پی"}).json()
    doubted = next(r for r in body["readings"] if r["latin"] == "Pey")
    clean = next(r for r in body["readings"] if r["latin"] == "Pay")
    assert doubted["needs_review"] is True
    assert clean["needs_review"] is False


def test_two_readings_stay_two_results(with_fixture_lexicon: TestClient):
    """مرد is *mard* and *mord*. Merging them would invent a third word."""
    body = with_fixture_lexicon.get("/generate", params={"word": "مرد"}).json()
    assert {r["latin"] for r in body["readings"]} == {"mard", "mord"}


def test_the_snapshot_travels_with_the_answer(with_fixture_lexicon: TestClient):
    body = with_fixture_lexicon.get("/generate", params={"word": "رفتن"}).json()
    assert body["lexicon_snapshot_id"]
    assert body["rule_pack_version"]


def test_a_word_the_lexicon_does_not_have_is_a_404(with_fixture_lexicon: TestClient):
    response = with_fixture_lexicon.get("/generate", params={"word": "نیستنیست"})
    assert response.status_code == 404
    assert "snapshot" in response.json()["detail"]


def test_depth_is_bounded(with_fixture_lexicon: TestClient):
    assert (
        with_fixture_lexicon.get(
            "/generate", params={"word": "رفتن", "depth": 9}
        ).status_code
        == 422
    )


# -- explain -----------------------------------------------------------------


def test_a_chain_is_explained_step_by_step(client: TestClient):
    body = client.get("/explain", params={"chain": "V-022,V-023"}).json()
    assert [step["rule_id"] for step in body["chain"]] == ["V-022", "V-023"]
    assert all(step["explanation_fa"] for step in body["chain"])


def test_an_unknown_rule_in_a_chain_is_a_404(client: TestClient):
    assert client.get("/explain", params={"chain": "V-022,X-1"}).status_code == 404


def test_an_empty_chain_is_a_400(client: TestClient):
    assert client.get("/explain", params={"chain": " , "}).status_code == 400


def test_a_word_in_persian_script_is_refused_only_when_nothing_can_read_it(
    client: TestClient,
):
    """A spelling the dictionary does not hold is still refused, and says why.

    The route rebuilds forward and compares Latin against Latin, so a
    Persian-script word matched nothing and came back with an empty list of
    accounts — indistinguishable from *this word cannot be built*, which is a
    wrong answer given confidently. Found by handing the API to a language
    model, which passed Persian and was told nothing.

    S11 fixed that by **looking the spelling up**, never by converting it:
    reading Persian script into Behnevis without diacritics measured 5.8%
    correct, and a guess would put a wrong base under a real chain. This client
    has no lexicon, so the refusal is what is left of the old behaviour.
    """
    answer = client.get("/explain", params={"word": "\u06af\u0641\u062a\u0627\u0631"})
    assert answer.status_code == 400
    assert "Behnevis" in answer.json()["detail"]


def test_a_persian_spelling_the_lexicon_holds_is_taken_apart(
    with_fixture_lexicon: TestClient,
):
    """S11. The dictionary knows how the spelling is read, so nothing is guessed.

    `/generate` has always taken either alphabet; this route refused both, and
    among the words it refused were دانشمند and گفتگو — the rule pack's own
    examples.
    """
    answer = with_fixture_lexicon.get(
        "/explain", params={"word": "\u0631\u0641\u062a\u0646"}
    )

    assert answer.status_code == 200
    body = answer.json()
    assert body["word"] == "\u0631\u0641\u062a\u0646"
    # Which Behnevis form was taken apart, so a reader is never left to infer
    # it from a Persian spelling that may have more than one reading.
    assert "raftan" in body["analysed_as"]
    assert all(
        account["form_latin"] in body["analysed_as"] for account in body["accounts"]
    )


def test_a_word_with_a_glide_in_it_is_taken_apart_and_says_so(
    with_fixture_lexicon: TestClient,
):
    """The engine's own output, handed back in. It used to be refused.

    *guyande* is گو + -نده with a *y* between the two vowels. The decomposer
    removed the affix as a string, which left *guy*, and the route answered
    with no accounts at all — for every one of the 13 one-step forms گفتن
    builds over a glide. The step now names the glide rule, so the letter is
    not on the screen unexplained.
    """
    answer = with_fixture_lexicon.get("/explain", params={"word": "guyande"})

    assert answer.status_code == 200
    body = answer.json()
    assert body["accounts"], "the engine built this word; it must take it apart"
    assert "goftan" in {one["base"]["latin"] for one in body["accounts"]}
    assert any(step["glide_id"] for one in body["accounts"] for step in one["steps"])


def test_the_flag_says_the_letters_were_rebuilt_and_no_more(
    with_fixture_lexicon: TestClient,
):
    """S21. It was `explained`, which claimed a judgement the route cannot make.

    `/explain?word=Naxodagahi` came back true on ناخدا — a ship's captain —
    and `Hamzamani` on a base of `Zam`. Both accounts are right about the
    letters and useless about the word, and a language model reading the API
    stopped trusting the flag. Renamed rather than taught to judge meaning:
    refusing those would need a ruling this project does not make in code.
    """
    body = with_fixture_lexicon.get(
        "/explain", params={"word": "Do\u0161rafte", "depth": 2}
    ).json()

    assert body["rebuilt"] is True
    # The old name is gone, not kept beside it. See the S19 rename.
    assert "explained" not in body
    # Every account carries the base's own corpus evidence, which is the one
    # thing we already hold that separates a parse a reader would accept from
    # one that is only arithmetic. Null where the corpus was never asked —
    # this test has no Elasticsearch, and that is exactly the null case.
    assert all("attestation" in account["base"] for account in body["accounts"])


# -- search ------------------------------------------------------------------


def test_an_unreadable_query_is_a_400(client: TestClient):
    """Nine kinds of unreadable query are refused by name, not guessed at."""
    assert client.get("/search", params={"q": "nope:1"}).status_code == 400
    assert client.get("/search", params={"q": "*"}).status_code == 400


def test_search_takes_no_index(client: TestClient):
    """Every field the query language names is a ``word_types`` field.

    Offering another index would let a query that matches nothing look like a
    query that found nothing.
    """
    parameters = client.get("/openapi.json").json()["paths"]["/search"]["get"]
    assert "index" not in {p["name"] for p in parameters["parameters"]}


def test_the_total_is_counted_exactly(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    """Elasticsearch stops counting at 10,000 and calls that the total.

    Several of these searches exist to produce a count — *how many words are
    hapaxes?* — and 10,000 is not an answer, it is a ceiling.
    """
    from murfulu.api import search as route

    asked: dict[str, object] = {}

    class _Client:
        def search(self, **kwargs: object) -> dict[str, object]:
            asked.update(kwargs)
            return {"hits": {"total": {"value": 222_859}, "hits": []}}

    monkeypatch.setattr(route, "_client", lambda: _Client())
    body = client.get("/search", params={"q": "count:1"}).json()
    assert asked["track_total_hits"] is True
    assert body["total"] == 222_859


def test_a_bad_word_index_is_a_400(client: TestClient):
    assert client.get("/word/x", params={"index": "poems"}).status_code == 400


# -- the whole surface -------------------------------------------------------


def test_openapi_describes_every_route(client: TestClient):
    paths = client.get("/openapi.json").json()["paths"]
    assert {
        "/health",
        "/rules",
        "/rules/{rule_id}",
        "/affixes",
        "/generate",
        "/explain",
        "/search",
        "/word/{word_id}",
        "/corpus",
        "/feedback",
        "/me",
        "/proposals",
        "/rules/{rule_id}/proposals",
    } <= set(paths)


def test_all_eight_routes_the_plan_asks_for_are_present(client: TestClient):
    """PLAN task 6.1 names eight. None of them may quietly go missing."""
    paths = set(client.get("/openapi.json").json()["paths"])
    asked_for = {
        "/generate",
        "/search",
        "/word/{word_id}",
        "/explain",
        "/rules",
        "/affixes",
        "/corpus",
        "/feedback",
    }
    assert asked_for <= paths


def test_no_route_holds_logic():
    """``api/`` is wiring. If a rule or a score lives here, it is misplaced."""
    from pathlib import Path as FilePath

    package = FilePath(__file__).resolve().parents[1] / "src" / "murfulu" / "api"
    for module in package.glob("*.py"):
        text = module.read_text(encoding="utf-8")
        assert "def apply(" not in text
        assert "yaml" not in text


def test_every_rule_says_what_its_semantic_centre_is_made_of(client: TestClient):
    """Served from the artefact; a rule without one carries null, not a zero."""
    body = client.get("/rules", params={"family": "V"}).json()
    assert "semantic_rules" in body
    for rule in body["rules"]:
        centre = rule["semantic"]
        if centre is None:
            continue
        assert centre["bases"] > 0
        for base in centre["typical_bases"]:
            assert base["latin"] and base["fa"]


def test_every_rule_carries_the_family_the_screen_filters_on(client: TestClient):
    """It was missing, so every family button on the rules screen emptied it.

    The route filtered correctly server-side; the field the client filters on
    was never sent, and the component test's fixture supplied one — so nothing
    caught it until the real screen was opened.
    """
    body = client.get("/rules").json()
    for rule in body["rules"]:
        assert rule["family"] == rule["id"].split("-")[0]


def test_a_compounding_rule_serves_its_pattern_and_slots(client: TestClient):
    """The pack has carried both since the transcription; the route dropped them.

    A caller saw `kind: template` with an affix of `‒` and nothing to say what
    the template was — so a language model given the API hand-assembled
    compounds rather than reading the specification, which was there all
    along. V-021 is بود و نابود: the same verb's past stem, joined with `o`,
    the second one negated.
    """
    body = client.get("/rules/V-021").json()
    assert body["pattern"] == "{a} + o + na + {b}"
    assert [slot["name"] for slot in body["slots"]] == ["a", "b"]
    assert body["slots"][1]["constraint"] == "same_verb"
    assert body["slots"][1]["negated"] is True


def test_an_affix_rule_has_no_pattern_and_says_so(client: TestClient):
    """Null is the right answer for a rule that joins nothing to nothing."""
    body = client.get("/rules/N-048").json()
    assert body["pattern"] is None
    assert body["slots"] == []


def test_one_rule_carries_everything_the_whole_list_carries(client: TestClient):
    """S17: the detail route served strictly less than the list route.

    A caller asking about one rule got the pack's description and none of the
    measurement; a caller asking about all 212 and filtering got both. The
    fields were absent rather than null, and an absent measurement reads as
    *not measured* — so a rule that deliberately builds nothing looked exactly
    like one nobody had measured.

    Asserted as a subset relation rather than as a field list, so a key added
    to the list route in future cannot quietly go missing from this one.
    """
    listed = {rule["id"]: rule for rule in client.get("/rules").json()["rules"]}
    for rule_id in ("N-048", "V-021", "N-090"):
        detail = client.get(f"/rules/{rule_id}").json()

        assert set(listed[rule_id]) <= set(detail), rule_id
        for key, value in listed[rule_id].items():
            assert detail[key] == value, f"{rule_id}.{key}"


def test_one_rule_says_which_corpus_its_figures_come_from(client: TestClient):
    """A figure travels with what it is a figure about, on every route."""
    detail = client.get("/rules/N-048").json()

    assert "corpus_version" in detail
    assert (
        detail["rule_pack_version"] == client.get("/rules").json()["rule_pack_version"]
    )


def test_a_glide_is_not_given_a_productivity_it_cannot_have(client: TestClient):
    """A glide decides a letter at a join; it does not build a word.

    The keys are absent rather than null, so nothing downstream reads a
    missing measurement as a low one.
    """
    glide = client.get("/rules/G-01").json()

    assert glide["kind"] == "glide"
    assert "productivity" not in glide
    assert "semantic" not in glide


def test_a_word_that_only_differs_in_case_is_named_rather_than_denied(
    with_fixture_lexicon: TestClient,
):
    """*budmān* does not rebuild and *Budmān* does; the two are different words.

    Case is meaning in Behnevis, so they must never be merged — but an empty
    answer that is really a casing mistake looks exactly like *this word
    cannot be built*. A caller given the API recorded about ten false
    negatives before working it out.
    """
    answer = with_fixture_lexicon.get(
        "/explain", params={"word": "došrafte", "depth": 2}
    ).json()
    assert answer["rebuilt"] is False
    assert answer["built_in_another_case"] == ["Došrafte"]


def test_a_word_that_rebuilds_says_nothing_about_other_casings(
    with_fixture_lexicon: TestClient,
):
    """The note is for a dead end, not decoration on a good answer."""
    answer = with_fixture_lexicon.get(
        "/explain", params={"word": "Došrafte", "depth": 2}
    ).json()
    assert answer["rebuilt"] is True
    assert answer["built_in_another_case"] == []
