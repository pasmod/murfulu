/**
 * The word screen, and the chart that is the point of it.
 *
 * What is tested here is what the project keeps insisting on: readings are
 * not merged, a count says which corpus version it belongs to, and what the
 * evidence does **not** cover is stated rather than dropped.
 */

import { screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { WordDetail } from "../../api/search";
import { renderApp } from "../../test/render";

const DETAIL: WordDetail = {
  id: "روشنا:Ravšanā",
  index: "word_types",
  word: {
    id: "روشنا:Ravšanā",
    spelling_fa: "روشنا",
    latin: "Ravšanā",
    lexicon_category: "اسم معنی",
    total_count: 22,
    doc_count: 21,
    author_count: 14,
    first_century: 12,
    last_century: 13,
    counts_by_century: { "12": 1, "13": 1 },
    corpus_version: "v1",
  },
  readings: [
    { id: "روشنا:Ravšanā", spelling_fa: "روشنا", latin: "Ravšanā" },
    { id: "روشنا:rowšanā", spelling_fa: "روشنا", latin: "rowšanā" },
  ],
  citations: [
    {
      document_id: "ganjoor:ferdousi:1",
      author: "فردوسی",
      title: "شاهنامه",
      century: null,
      line: "شود تیره گیتی بدو روشنا",
    },
  ],
};

/**
 * A sentence built from a number component and plain text is split across
 * elements, so it has to be matched on the whole paragraph rather than on a
 * text node. Every count on this screen is written that way.
 */
function saying(pattern: RegExp) {
  return (_text: string, node: Element | null) => {
    if (!node) return false;
    const own = node.textContent ?? "";
    const childHasIt = Array.from(node.children).some((child) =>
      pattern.test(child.textContent ?? ""),
    );
    return pattern.test(own) && !childHasIt;
  };
}

function answerWith(body: unknown, status = 200) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    statusText: "",
    json: async () => body,
  } as Response);
}

beforeEach(() => {
  vi.stubGlobal("fetch", answerWith(DETAIL));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const ROUTE = "/word/%D8%B1%D9%88%D8%B4%D9%86%D8%A7:Rav%C5%A1an%C4%81";

describe("the word screen", () => {
  it("shows both scripts", async () => {
    renderApp(ROUTE);
    const heading = await screen.findByRole("heading", {
      level: 1,
      name: "روشنا",
    });
    expect(heading).toBeInTheDocument();
    expect(screen.getByText("Ravšanā")).toHaveAttribute("dir", "ltr");
  });

  it("never merges two readings of one spelling", async () => {
    renderApp(ROUTE);
    const others = await screen.findByRole("region", {
      name: /خوانش‌های دیگر/,
    });
    expect(within(others).getByText("rowšanā")).toBeInTheDocument();
    // The reading being read is not listed again as an "other".
    expect(within(others).queryByText("Ravšanā")).not.toBeInTheDocument();
  });

  it("says which corpus version the counts belong to", async () => {
    renderApp(ROUTE);
    expect(await screen.findByText(/نسخهٔ/)).toBeInTheDocument();
    expect(screen.getByText("v1")).toBeInTheDocument();
  });

  it("quotes real lines with who wrote them", async () => {
    renderApp(ROUTE);
    expect(await screen.findByText("شود تیره گیتی بدو روشنا")).toBeInTheDocument();
    expect(screen.getByText(/فردوسی/)).toBeInTheDocument();
  });
});

describe("the dispersion chart", () => {
  it("says how much of the evidence it cannot show", async () => {
    // 22 occurrences, 2 of them dated. A chart drawn over 2 and presented as
    // the whole picture would be a lie about the evidence.
    renderApp(ROUTE);
    expect(await screen.findByText(saying(/۲۰ کاربرد دیگر تاریخ ندارد/))).toBeInTheDocument();
  });

  it("keeps an empty century inside the span, because the hole is evidence", async () => {
    vi.stubGlobal(
      "fetch",
      answerWith({
        ...DETAIL,
        word: { ...DETAIL.word, counts_by_century: { "10": 4, "13": 2 }, total_count: 6 },
      }),
    );
    renderApp(ROUTE);
    const rows = await screen.findAllByRole("row");
    // Two centuries are reported in the table…
    expect(rows).toHaveLength(2);
    // …but the bars span 10 to 13, so the two silent centuries are drawn.
    expect(screen.getByText("۱۱")).toBeInTheDocument();
    expect(screen.getByText("۱۲")).toBeInTheDocument();
  });

  it("draws nothing and says why when nothing is dated", async () => {
    vi.stubGlobal(
      "fetch",
      answerWith({
        ...DETAIL,
        word: { ...DETAIL.word, counts_by_century: {}, total_count: 9 },
      }),
    );
    renderApp(ROUTE);
    expect(
      await screen.findByText(saying(/هیچ‌یک از .* کاربرد این واژه تاریخ‌دار نیست/)),
    ).toBeInTheDocument();
  });
});

describe("when the word is not there", () => {
  it("says so without saying the word does not exist", async () => {
    vi.stubGlobal("fetch", answerWith({ detail: "no word" }, 404));
    renderApp(ROUTE);
    expect(
      await screen.findByText("این واژه در پیکرهٔ کنونی نیست."),
    ).toBeInTheDocument();
  });
});
