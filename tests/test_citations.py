"""Citations: one per author, as long as a line of verse, and where they sit.

Every line here is written for the test. No corpus text.
"""

from typing import Any

from murfulu.search.citations import MAX_WORDS, excerpt, find, locate

PROSE = (
    "این جمله نخست است و چیزی در آن نیست. "
    + " ".join(["واژه"] * 30)
    + " دل "
    + " ".join(["واژه"] * 30)
    + ". جملهٔ پایانی کوتاه است."
)


def test_a_short_line_is_quoted_whole():
    assert excerpt("دل ما با رفتار تو آرام گرفت", "دل") == "دل ما با رفتار تو آرام گرفت"


def test_a_long_paragraph_is_cut_to_the_sentence_that_holds_the_word():
    short = "نخست جمله‌ای بی‌ربط است. " + " ".join(["پر"] * 30) + ". اینجا دل هست."
    assert excerpt(short, "دل") == "اینجا دل هست."


def test_a_long_sentence_is_cut_around_the_word_and_says_so():
    quoted = excerpt(PROSE, "دل")
    words = quoted.split()
    assert "دل" in words
    assert words[0] == "…" and words[-1] == "…"
    assert len(words) <= MAX_WORDS


def test_the_word_is_found_however_it_is_written():
    """Harakat and Arabic letters fold, as they did when the corpus was counted."""
    assert excerpt(PROSE.replace(" دل ", " دِل، "), "دل").split()[11] == "دِل،"


def _stored(units: list[dict[str, Any]]) -> dict[str, Any]:
    return {"units": units, "text_fa": "ignored when there are units"}


def test_the_unit_is_named_and_a_note_is_never_quoted():
    source = _stored(
        [
            {"kind": "note", "lines": [{"text": "یادداشتی با دل", "position": "note"}]},
            {
                "kind": "couplet",
                "lines": [
                    {"text": "سطر نخست", "position": "first"},
                    {"text": "دلِ ما سطر دوم", "position": "second"},
                ],
            },
        ]
    )
    assert locate(source, "دل") == (1, "couplet", "دلِ ما سطر دوم")


def test_a_text_stored_before_units_still_gives_its_line():
    assert locate({"text_fa": "سطر یکم\nسطر دل دوم"}, "دل") == (
        None,
        None,
        "سطر دل دوم",
    )


class _Client:
    """Stands in for Elasticsearch: one hit, and the query it was sent."""

    def __init__(self, source: dict[str, Any]) -> None:
        self.source = source
        self.asked: dict[str, Any] = {}

    def search(self, **asked: Any) -> dict[str, Any]:
        self.asked = asked
        return {"hits": {"hits": [{"_source": self.source}]}}


def test_find_collapses_on_the_author_and_names_work_section_and_unit():
    client = _Client(
        {
            "document_id": "fixture:a:1",
            "author": "نویسنده",
            "title": "عنوان",
            "century": 7,
            "work": "کتاب",
            "section": ["باب نخست"],
            "units": [
                {"kind": "prose", "lines": [{"text": PROSE, "position": "prose"}]}
            ],
        }
    )
    [one] = find(client, "دل")  # type: ignore[arg-type]
    assert client.asked["collapse"] == {"field": "author"}
    assert one.as_dict()["unit"] == 0
    assert one.kind == "prose"
    assert one.work == "کتاب" and one.section == ("باب نخست",)
    assert len(one.line.split()) <= MAX_WORDS
