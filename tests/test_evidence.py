"""Every text a spelling is in: the order, the paging, the lines and the counts.

Every line here is written for the test. No corpus text. The client is a
stand-in that sorts, filters, pages and aggregates the way Elasticsearch does
for the few query shapes the module sends; ``test_evidence_live.py`` sends the
same shapes to a real cluster.
"""

from typing import Any

import pytest

from murfulu.corpus.wordtypes import tokenise
from murfulu.search import evidence
from murfulu.search.evidence import (
    Summary,
    line_count,
    page,
    slices,
    summary,
    voices,
)
from murfulu.search.evidence_lines import loosen, parts, text_of


def _couplet(first: str, second: str) -> dict[str, Any]:
    return {
        "kind": "couplet",
        "lines": [
            {"text": first, "position": "first"},
            {"text": second, "position": "second"},
        ],
    }


def _text(
    document_id: str, author: str | None, order: int, *couplets: tuple[str, str]
) -> dict[str, Any]:
    units = [_couplet(*one) for one in couplets]
    return {
        "document_id": document_id,
        "author": author,
        "title": f"عنوان {order}",
        "century": None,
        "work": "دیوان",
        "section": [],
        "order": order,
        "units": units,
        "text_fa": "\n".join(line["text"] for unit in units for line in unit["lines"]),
        "corpus_version": "v-test",
    }


class _Elasticsearch:
    """Answers the searches the module sends, over texts held in memory."""

    def __init__(self, texts: list[dict[str, Any]]) -> None:
        self.texts = texts
        self.asked: list[dict[str, Any]] = []

    def _holds(self, text: dict[str, Any], query: dict[str, Any]) -> bool:
        if "match_phrase" in query:
            # The index folds as `loosen` does, which is the point of it.
            wanted = loosen(query["match_phrase"]["text_fa"])
            return wanted in {loosen(one) for one in tokenise(text["text_fa"])}
        if "term" in query:
            return bool(text.get("author") == query["term"]["author"])
        if "exists" in query:
            # Elasticsearch counts an empty string as a value; only null and
            # absent are missing.
            return text.get(query["exists"]["field"]) is not None
        if "bool" in query:
            must = query["bool"].get("must", []) + query["bool"].get("filter", [])
            never = query["bool"].get("must_not")
            should = query["bool"].get("should")
            if never is not None and self._holds(text, never):
                return False
            if should and not any(self._holds(text, one) for one in should):
                return False
            return all(self._holds(text, one) for one in must)
        raise AssertionError(f"unexpected query {query}")

    def search(self, **asked: Any) -> dict[str, Any]:
        self.asked.append(asked)
        found = sorted(
            (one for one in self.texts if self._holds(one, asked["query"])),
            key=lambda one: (one["order"], one["document_id"]),
        )
        if asked.get("search_after"):
            found = [
                one
                for one in found
                if [one["order"], one["document_id"]] > asked["search_after"]
            ]
        start = asked.get("from_", 0)
        hits = [
            {"_source": one, "sort": [one["order"], one["document_id"]]}
            for one in found[start : start + asked["size"]]
        ]
        answer: dict[str, Any] = {
            "hits": {"total": {"value": len(found)}, "hits": hits}
        }
        if "aggs" in asked:
            counts: dict[str, int] = {}
            for one in found:
                # The `missing` bucket and a stored empty name are one key.
                name = one.get("author") or ""
                counts[name] = counts.get(name, 0) + 1
            answer["aggregations"] = {
                "authors": {
                    "buckets": [
                        {"key": name, "doc_count": count}
                        for name, count in counts.items()
                    ]
                },
                "version": {"buckets": [{"key": "v-test", "doc_count": len(found)}]},
            }
        return answer


# Three authors: الف with three texts, ب with one, and a text with no author.
# الف and the unnamed text tie on nothing; ب and the unnamed tie on one each.
TEXTS = [
    _text("t:a:30", "الف", 30, ("دل ما را ببرد", "سطر دیگر")),
    _text("t:a:10", "الف", 10, ("سطر نخست", "دلِ من و دل تو")),
    _text("t:a:20", "الف", 20, ("دل", "دل")),
    _text("t:b:5", "ب", 5, ("این دل است", "آن نیست")),
    _text("t:-:1", None, 1, ("دل بی‌نام", "سطر")),
    _text("t:b:6", "ب", 6, ("بی‌ربط", "هیچ")),
]


def _summary(texts: list[dict[str, Any]] = TEXTS) -> Summary:
    return summary(_Elasticsearch(texts), "دل")  # type: ignore[arg-type]


def test_authors_come_most_texts_first_and_ties_by_name():
    found = _summary()
    assert found.total == 5
    # The unnamed text is "", which sorts before ب.
    assert found.authors == (("الف", 3), ("", 1), ("ب", 1))
    assert found.corpus_version == "v-test"


def test_a_stretch_of_the_list_is_cut_across_authors():
    authors = (("الف", 3), ("", 1), ("ب", 1))
    assert slices(authors, 0, 2) == [("الف", 0, 2)]
    assert slices(authors, 2, 2) == [("الف", 2, 1), ("", 0, 1)]
    assert slices(authors, 4, 2) == [("ب", 0, 1)]
    assert slices(authors, 5, 2) == []


def test_pages_follow_the_authors_and_then_the_source_order():
    client = _Elasticsearch(TEXTS)
    found = summary(client, "دل")  # type: ignore[arg-type]
    seen = [
        one.document_id
        for number in range(3)
        for one in page(client, "دل", found, number=number, size=2)  # type: ignore[arg-type]
    ]
    assert seen == ["t:a:10", "t:a:20", "t:a:30", "t:-:1", "t:b:5"]


def test_one_author_is_paged_from_the_start_of_their_own_texts():
    client = _Elasticsearch(TEXTS)
    found = summary(client, "دل")  # type: ignore[arg-type]
    second = page(client, "دل", found, author="الف", number=1, size=2)  # type: ignore[arg-type]
    assert [one.document_id for one in second] == ["t:a:30"]
    unnamed = page(client, "دل", found, author="", size=5)  # type: ignore[arg-type]
    assert [one.document_id for one in unnamed] == ["t:-:1"]


def test_a_text_stored_with_an_empty_author_is_one_with_none():
    texts = [*TEXTS, {**_text("t:-:2", None, 2, ("دل", "سطر")), "author": ""}]
    client = _Elasticsearch(texts)
    found = summary(client, "دل")  # type: ignore[arg-type]
    assert ("", 2) in found.authors
    assert found.texts("") == 2
    unnamed = page(client, "دل", found, author="", size=5)  # type: ignore[arg-type]
    assert [one.document_id for one in unnamed] == ["t:-:1", "t:-:2"]
    assert unnamed[1].author is None


def test_an_author_longer_than_the_window_is_walked_past_it():
    """The window is 10,000 in Elasticsearch; three here, so the walk is used."""
    many = [_text(f"t:c:{n:02}", "ج", n, ("دل", "سطر")) for n in range(10)]
    client = _Elasticsearch(many)
    found = summary(client, "دل")  # type: ignore[arg-type]
    shown = page(client, "دل", found, number=3, size=2, window=3)  # type: ignore[arg-type]
    assert [one.document_id for one in shown] == ["t:c:06", "t:c:07"]
    walked = [asked for asked in client.asked if "search_after" in asked]
    assert walked, "the page past the window was read with from/size"
    assert all(asked.get("from_", 0) + asked["size"] <= 3 for asked in client.asked)


def test_every_line_holding_the_word_is_given_with_its_unit():
    shown = text_of(TEXTS[1], "دل")
    assert shown.held == "counted"
    assert [(one.unit, one.kind) for one in shown.lines] == [(0, "couplet")]
    assert shown.lines[0].parts == ("", "دلِ", " من و ", "دل", " تو")
    both = text_of(TEXTS[2], "دل")
    assert len(both.lines) == 2


def test_a_text_with_the_word_only_in_a_near_spelling_says_so():
    """The index found امد for آمد; the counting keeps the two apart."""
    source = _text("t:d:1", "د", 1, ("بهار امد", "سطری دیگر"))
    shown = text_of(source, "آمد")
    assert shown.held == "near"
    assert shown.lines[0].parts == ("بهار ", "امد", "")
    # The reading screen is opened at the spelling the line really holds.
    assert shown.lines[0].word == "امد"
    assert shown.lines[0].as_dict()["word"] == "امد"
    assert "word" not in text_of(TEXTS[1], "دل").lines[0].as_dict()
    assert loosen("خانۀ") == loosen("خانه")
    assert loosen("على") == loosen("علی")


def test_a_text_the_index_found_with_no_line_the_counting_credits_says_none():
    """The index joins a word and a trailing ZWNJ, say, where the counting splits."""
    shown = text_of(_text("t:f:1", "و", 1, ("سطری بی آن", "و دیگری")), "دل")
    assert shown.held == "none"
    assert shown.lines == ()


def test_a_stored_line_break_makes_two_lines():
    source = _text("t:g:1", "ز", 1, ("دل یکم\nدل دوم", "سطر"))
    shown = text_of(source, "دل")
    assert [one.parts for one in shown.lines] == [
        ("", "دل", " یکم"),
        ("", "دل", " دوم"),
    ]
    assert line_count(_Elasticsearch([source]), "دل", 1) == 2  # type: ignore[arg-type]


def test_a_note_is_never_quoted():
    source = _text("t:e:1", "ه", 1, ("سطر", "سطر"))
    source["units"].insert(
        0, {"kind": "note", "lines": [{"text": "یادداشت با دل", "position": "note"}]}
    )
    assert text_of(source, "دل").lines == ()


def test_the_marks_of_a_word_stay_with_it_and_every_occurrence_is_marked():
    assert parts("دلِ ما و دلِ تو", "دل") == ("", "دلِ", " ما و ", "دلِ", " تو")
    assert parts("هیچ", "دل") == ("هیچ",)
    # A longer word holding the letters is another word.
    assert parts("دلبر آمد", "دل") == ("دلبر آمد",)


def test_the_lines_are_counted_for_a_short_list_and_not_for_a_long_one(
    monkeypatch: pytest.MonkeyPatch,
):
    client = _Elasticsearch(TEXTS)
    # t:a:10 has one line, t:a:20 two, t:a:30 one, t:b:5 one, t:-:1 one.
    assert line_count(client, "دل", 5) == 6  # type: ignore[arg-type]
    assert line_count(client, "دل", 3, author="الف") == 4  # type: ignore[arg-type]
    monkeypatch.setattr(evidence, "LINE_COUNT_LIMIT", 4)
    assert line_count(client, "دل", 5) is None  # type: ignore[arg-type]


def test_a_preview_takes_one_text_from_each_of_the_first_authors():
    """One voice each, as the six citations: الف has three texts and gives one."""
    client = _Elasticsearch(TEXTS)
    found = summary(client, "دل")  # type: ignore[arg-type]
    shown = voices(client, "دل", found, count=2)  # type: ignore[arg-type]
    assert [one.document_id for one in shown] == ["t:a:10", "t:-:1"]
    every = voices(client, "دل", found, count=5)  # type: ignore[arg-type]
    # Three authors, so three texts however many are asked for.
    assert [one.author for one in every] == ["الف", None, "ب"]
