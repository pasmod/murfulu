/**
 * Every text of a spelling, under the six citations.
 *
 * What is tested is what the list promises: it is closed until asked for and
 * says its size first; it marks the word in every line and opens each line on
 * the reading screen; it pages and filters through the address; and where its
 * count and the word's count differ, or a text has the word only in a near
 * spelling, it says so instead of letting two figures disagree in silence.
 */

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Evidence, EvidenceText } from "../../api/evidence";
import type { WordDetail } from "../../api/search";
import { renderApp } from "../../test/render";

const DETAIL: WordDetail = {
  id: "روشنا:Ravšanā",
  index: "word_types",
  word: {
    id: "روشنا:Ravšanā",
    spelling_fa: "روشنا",
    latin: "Ravšanā",
    total_count: 30,
    doc_count: 21,
    author_count: 3,
    counts_by_century: {},
    corpus_version: "v1",
  },
  readings: [{ id: "روشنا:Ravšanā", spelling_fa: "روشنا", latin: "Ravšanā" }],
  citations: [],
};

function text(n: number, author: string, lines = 1): EvidenceText {
  return {
    document_id: `fixture:${n}`,
    author,
    title: `عنوان ${n}`,
    century: null,
    work: "دیوان",
    section: [],
    lines: Array.from({ length: lines }, (_, index) => ({
      unit: index,
      kind: "couplet",
      parts: ["جهان ", "روشنا", ` شد ${index}`],
    })),
    held: "counted",
  };
}

const AUTHORS = [
  { author: "الف", texts: 20 },
  { author: "ب", texts: 1 },
];

function answer(params: URLSearchParams): Evidence {
  const author = params.get("author");
  const page = Number(params.get("page") ?? "0");
  const size = Number(params.get("size") ?? "20");
  const matching = author === "ب" ? 1 : author === "الف" ? 20 : 21;
  const all = [
    ...Array.from({ length: 20 }, (_, n) => text(n, "الف", n === 0 ? 9 : 1)),
    text(20, "ب"),
  ].filter((one) => !author || one.author === author);
  return {
    spelling: "روشنا",
    corpus_version: "v1",
    total: 21,
    authors: AUTHORS,
    author,
    unnamed: false,
    matching,
    lines: params.get("count_lines") === "1" ? matching + 8 : null,
    page,
    size,
    texts: all.slice(page * size, page * size + size),
  };
}

/** A sentence whose numbers are their own elements, matched on the whole paragraph. */
function saying(pattern: RegExp) {
  return (_text: string, node: Element | null) => {
    if (!node) return false;
    const childHasIt = Array.from(node.children).some((child) =>
      pattern.test(child.textContent ?? ""),
    );
    return pattern.test(node.textContent ?? "") && !childHasIt;
  };
}

let asked: URLSearchParams[] = [];

function serve(
  change: (body: Evidence) => Evidence = (body) => body,
  refuse: (params: URLSearchParams) => boolean = () => false,
) {
  asked = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const address = new URL(url, "http://localhost");
      const listed = address.pathname.startsWith("/api/evidence");
      if (listed) asked.push(address.searchParams);
      if (listed && refuse(address.searchParams)) {
        return { ok: false, status: 503, statusText: "", json: async () => ({}) } as Response;
      }
      const body = listed ? change(answer(address.searchParams)) : DETAIL;
      return { ok: true, status: 200, statusText: "", json: async () => body } as Response;
    }),
  );
}

beforeEach(() => serve());
afterEach(() => vi.unstubAllGlobals());

const ROUTE = "/word/%D8%B1%D9%88%D8%B4%D9%86%D8%A7:Rav%C5%A1an%C4%81";

async function region() {
  return screen.findByRole("region", { name: "همهٔ شواهد" });
}

describe("every text of the spelling", () => {
  it("is closed until asked for, and says its size and what it is evidence for", async () => {
    renderApp(ROUTE);
    const block = await region();
    expect(
      await within(block).findByText(saying(/در .* متن از .* نویسنده آمده است/)),
    ).toHaveTextContent("املای «روشنا» در ۲۱ متن از ۲ نویسنده آمده است، در ۲۹ سطر.");
    expect(within(block).getByText(/نه یکی از خوانش‌های آن/)).toBeInTheDocument();
    const toggle = within(block).getByRole("button", { name: "نشان دادن همهٔ شواهد" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(within(block).queryByRole("list")).not.toBeInTheDocument();
  });

  it("opens to a page of texts, each line with the word marked and a way to its unit", async () => {
    renderApp(ROUTE);
    const block = await region();
    await userEvent.click(
      await within(block).findByRole("button", { name: "نشان دادن همهٔ شواهد" }),
    );
    expect(await within(block).findByText(saying(/۱–۲۰ از ۲۱ متن/))).toBeInTheDocument();
    const texts = await within(block).findAllByText(/^الف — دیوان — عنوان/);
    expect(texts).toHaveLength(20);
    const marked = block.querySelectorAll("mark");
    expect(marked[0]).toHaveTextContent("روشنا");
    const link = within(block).getAllByRole("link", { name: "در متن ←" })[0]!;
    expect(link).toHaveAttribute(
      "href",
      `/texts?text=fixture%3A0&unit=0&word=${encodeURIComponent("روشنا")}`,
    );
  });

  it("shows a long text's first lines and the rest on a press", async () => {
    renderApp(`${ROUTE}?all=1`);
    const block = await region();
    const more = await within(block).findByRole("button", { name: "همهٔ ۹ سطر" });
    const first = more.closest("li")!;
    expect(within(first).getAllByRole("link", { name: "در متن ←" })).toHaveLength(6);
    await userEvent.click(more);
    expect(within(first).getAllByRole("link", { name: "در متن ←" })).toHaveLength(9);
  });

  it("pages through the address and asks for the next page by number", async () => {
    renderApp(`${ROUTE}?all=1`);
    const block = await region();
    await userEvent.click(await within(block).findByRole("button", { name: "صفحهٔ پسین" }));
    expect(await within(block).findByText(saying(/۲۱–۲۱ از ۲۱ متن/))).toBeInTheDocument();
    expect(await within(block).findByText(/^ب — دیوان/)).toBeInTheDocument();
    expect(asked.some((one) => one.get("page") === "1")).toBe(true);
    expect(within(block).getByRole("button", { name: "صفحهٔ پسین" })).toBeDisabled();
  });

  it("filters by author, most texts first, and counts that author's lines", async () => {
    renderApp(`${ROUTE}?all=1`);
    const block = await region();
    const filter = await within(block).findByRole("combobox", { name: "نویسنده" });
    const options = within(filter)
      .getAllByRole("option")
      .map((one) => one.textContent);
    expect(options).toEqual(["همهٔ نویسندگان (۲۱ متن)", "الف (۲۰)", "ب (۱)"]);
    await userEvent.selectOptions(filter, "ب");
    expect(await within(block).findByText(saying(/۱–۱ از ۱ متن، در ۹ سطر/))).toBeInTheDocument();
    expect(asked.some((one) => one.get("author") === "ب")).toBe(true);
  });

  it("is silent about the count when it agrees with the word's", async () => {
    renderApp(`${ROUTE}?all=1`);
    const block = await region();
    expect(await within(block).findByText(saying(/۱–۲۰ از ۲۱ متن/))).toBeInTheDocument();
    expect(within(block).queryByText(saying(/شمارش بالا/))).not.toBeInTheDocument();
  });

  it("says in one sentence why its count differs from the word's", async () => {
    serve((body) => ({ ...body, total: 23 }));
    renderApp(`${ROUTE}?all=1`);
    const block = await region();
    expect(await within(block).findByText(saying(/شمارش بالا/))).toHaveTextContent(
      /این فهرست ۲۳ متن دارد و شمارش بالا ۲۱، چون/,
    );
  });

  it("marks a text that has the word only in a near spelling, and links to that spelling", async () => {
    serve((body) => ({
      ...body,
      texts: [
        {
          ...text(0, "الف"),
          held: "near",
          lines: [{ unit: 3, kind: "couplet", parts: ["جهان ", "روشنی", ""], word: "روشنی" }],
        },
      ],
    }));
    renderApp(`${ROUTE}?all=1`);
    const block = await region();
    expect(await within(block).findByText(/تنها با املایی نزدیک/)).toBeInTheDocument();
    expect(within(block).getByRole("link", { name: "در متن ←" })).toHaveAttribute(
      "href",
      `/texts?text=fixture%3A0&unit=3&word=${encodeURIComponent("روشنی")}`,
    );
  });

  it("says when its counts did not come, instead of waiting for ever", async () => {
    serve(undefined, () => true);
    renderApp(`${ROUTE}?all=1`);
    const block = await region();
    expect(await within(block).findByText(/شمار متن‌ها نرسید/)).toBeInTheDocument();
  });

  it("says when a page did not come, and keeps the counts", async () => {
    serve(undefined, (params) => params.get("size") !== "0");
    renderApp(`${ROUTE}?all=1`);
    const block = await region();
    expect(await within(block).findByText(/این صفحه نرسید/)).toBeInTheDocument();
    expect(within(block).getByText(saying(/۱–۲۰ از ۲۱ متن/))).toBeInTheDocument();
  });

  it("counts named authors only, as the word's own count does, and says the version", async () => {
    serve((body) => ({ ...body, authors: [...AUTHORS, { author: null, texts: 2 }] }));
    renderApp(ROUTE);
    const block = await region();
    expect(
      await within(block).findByText(saying(/در .* متن از .* نویسنده آمده است/)),
    ).toHaveTextContent("در نسخهٔ v1 پیکره، املای «روشنا» در ۲۱ متن از ۲ نویسنده");
  });

  it("shows an author from the address the list does not have as chosen, with nothing", async () => {
    renderApp(`${ROUTE}?all=1&author=${encodeURIComponent("ناشناس")}`);
    const block = await region();
    const filter = await within(block).findByRole("combobox", { name: "نویسنده" });
    expect(filter).toHaveValue("ناشناس");
    expect(within(filter).getByRole("option", { name: "ناشناس (۰)" })).toBeInTheDocument();
  });
});
