"""The unsure spellings: counted as the reading screen reads them, ranked, by kind.

Every word here is written for the test; no corpus text (NOTICE).
"""

from pathlib import Path
from typing import Any

from murfulu.behnevis import serve, unsure


def _word(
    s: str | None, latin: str | None = None, confidence: float = 0.0, **more: Any
) -> dict[str, Any]:
    word: dict[str, Any] = {"fa": s or "،", "s": s}
    if latin is not None:
        word["auto"] = {
            "latin": latin,
            "confidence": confidence,
            "level": serve.level(confidence),
            "source": more.get("source", "choice"),
            "candidates": more.get("candidates", [[latin, confidence]]),
        }
    return word


BANK = {"دل": ("Dal", "Del"), "بود": ("Bud",)}
FUNCTIONS = {"که": ("ke", "keh")}


def test_the_kind_says_what_deciding_means():
    assert unsure.kind_of("دل", BANK, FUNCTIONS) == unsure.CHOICE
    assert unsure.kind_of("بود", BANK, FUNCTIONS) == unsure.ONE
    assert unsure.kind_of("گفتم", BANK, FUNCTIONS) == unsure.MISSING
    # A function word's own readings count as held, like the bank's.
    assert unsure.kind_of("که", BANK, FUNCTIONS) == unsure.CHOICE


def _line() -> list[dict[str, Any]]:
    # «این دل ، بود دل» — a punctuation token between, not counted.
    return [
        _word("این", "in", 0.95),
        _word("دل", "Del", 0.5, candidates=[["Del", 0.5], ["Dal", 0.5]]),
        _word(None),
        _word("بود", "Bud", 0.6, source="bank"),
        _word("دل", "Dal", 0.8),
    ]


def test_a_line_is_counted_with_its_neighbours_and_the_screens_word_index():
    tally = unsure.Tally()
    where = {"document_id": "t:1", "unit": 3, "line": 0, "heading": "h"}
    tally.add_line(_line(), where)
    assert tally.words == 4  # the punctuation is not a word
    assert tally.unsure_words == 2
    assert tally.places["دل"] == 2 and tally.unsure["دل"] == 1
    # Neighbours are the counted words beside it, the punctuation skipped.
    assert tally.near[("بود", unsure.BEFORE, "دل")] == 1
    assert tally.near_unsure[("بود", unsure.AFTER, "دل")] == 1
    assert tally.near_unsure[("دل", unsure.BEFORE, "بود")] == 0  # that دل is sure
    (example,) = tally.examples["دل"]
    place = example[1]
    assert place["word"] == 1 and place["unit"] == 3 and place["line"] == 0
    assert place["text"].startswith("این دل")
    assert tally.sources[("بود", "bank")] == 1
    assert tally.offered[("دل", "Dal")] == 1


def test_the_level_the_screen_shows_decides_not_the_rounded_number():
    # 0.6996 is sent as 0.7, yet the screen shows it unsure: so is it counted.
    word = _word("دل", "Del", 0.7)
    word["auto"]["level"] = "unsure"
    tally = unsure.Tally()
    tally.add_line([word], {"document_id": "t:1", "unit": 0, "line": 0})
    assert tally.unsure["دل"] == 1


def test_a_word_without_a_reading_is_left_to_a_person():
    tally = unsure.Tally()
    tally.add_line([_word("زیک")], {"document_id": "t:1", "unit": 0, "line": 0})
    assert tally.unsure["زیک"] == 1
    assert tally.sources[("زیک", "none")] == 1


def test_only_watched_spellings_keep_their_details():
    tally = unsure.Tally(watch=frozenset({"دل"}))
    tally.add_line(_line(), {"document_id": "t:1", "unit": 0, "line": 0})
    assert tally.unsure["بود"] == 1  # still counted
    assert "بود" not in tally.examples
    assert not any(k[0] == "بود" for k in tally.near)


def test_slices_merge_and_the_examples_stay_the_lowest_ranked_three():
    one, two = unsure.Tally(), unsure.Tally()
    for i in range(4):
        one.add_line(_line(), {"document_id": f"a:{i}", "unit": 0, "line": 0})
        two.add_line(_line(), {"document_id": f"b:{i}", "unit": 0, "line": 0})
    whole = unsure.Tally()
    for i in range(4):
        for doc in (f"a:{i}", f"b:{i}"):
            whole.add_line(_line(), {"document_id": doc, "unit": 0, "line": 0})
    one.merge(two)
    assert one.words == whole.words == 32
    assert one.unsure == whole.unsure
    assert one.examples["دل"] == whole.examples["دل"]
    assert len(one.examples["دل"]) == unsure.EXAMPLES


def test_the_list_ranks_by_places_left_and_names_the_kind():
    tally = unsure.Tally()
    for i in range(3):
        tally.add_line(_line(), {"document_id": f"t:{i}", "unit": 0, "line": 0})
    alone = [_word("دل", "Del", 0.4)]
    tally.add_line(alone, {"document_id": "x", "unit": 0, "line": 0})
    listed = unsure.entries(tally, BANK, FUNCTIONS, top=10)
    assert [one["spelling"] for one in listed] == ["دل", "بود"]
    first = listed[0]
    assert first["rank"] == 1 and first["unsure"] == 4 and first["places"] == 7
    assert first["kind"] == unsure.CHOICE
    assert first["known"] == ["Dal", "Del"]
    assert first["read_as"][0] == ["Del", 4]
    # The neighbour that holds the most unsure places comes first.
    assert first[unsure.BEFORE][0][0] == "این"
    assert listed[1]["kind"] == unsure.ONE


def test_coverage_counts_the_top_spellings_places_by_kind():
    tally = unsure.Tally()
    for i in range(3):
        tally.add_line(_line(), {"document_id": f"t:{i}", "unit": 0, "line": 0})
    (top1, top2) = unsure.coverage(tally, BANK, FUNCTIONS, [1, 2])
    assert top1.unsure == 3 and top1.by_kind[unsure.CHOICE] == 3
    assert top2.unsure == 6 and top2.by_kind[unsure.ONE] == 3
    assert top2.by_kind[unsure.MISSING] == 0


def test_one_reading_per_spelling_is_read_against_the_marked_places():
    listed = [
        {
            "spelling": "دل",
            "known": ["Dal", "Del"],
            "read_as": [["Del", 3]],
            "offered": [["Dal", 2]],
        }
    ]
    marked = [
        {"spelling": "دل", "written": "دِل"},
        {"spelling": "دل", "written": "دِل"},
        {"spelling": "دل", "written": "دَل"},
        {"spelling": "دل", "written": "دُل"},  # fits neither
        {"spelling": "بود", "written": "بُوَد"},  # not listed
    ]
    fit = unsure.single_reading_fit(listed, marked)["دل"]
    assert (fit.fitted, fit.best, fit.none, fit.reading) == (3, 2, 1, "Del")


def test_the_list_lives_beside_its_model(tmp_path: Path):
    model = tmp_path / "behnevis-v22.json"
    assert unsure.path_beside(model).name == "behnevis-unsure-v22.json"
    # A model named otherwise is never overwritten by its list.
    other = tmp_path / "model.json"
    assert unsure.path_beside(other).name == "model.unsure.json"
    unsure.write(unsure.path_beside(model), {"words": 1}, [{"spelling": "دل"}])
    back = unsure.read(unsure.path_beside(model))
    assert back == ({"words": 1}, [{"spelling": "دل"}])


def test_a_one_spelling_the_editions_mark_otherwise_waits_for_karbon():
    bud = {
        "kind": unsure.ONE,
        "known": ["Bud"],
        "marked": {"fitted": 1464, "best": 1463, "none": 0, "reading": "bovad"},
    }
    assert unsure.marks_another(bud)
    # Too few marks say nothing; marks for the bank's own reading confirm it.
    assert not unsure.marks_another({**bud, "marked": {**bud["marked"], "fitted": 4}})
    assert not unsure.marks_another(
        {**bud, "marked": {**bud["marked"], "reading": "Bud"}}
    )
    assert not unsure.marks_another({**bud, "kind": unsure.CHOICE})
    assert not unsure.marks_another({**bud, "marked": None})
