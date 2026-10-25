/**
 * The corpus screen.
 *
 * What is tested here is the honesty of the screen, because the numbers
 * themselves come from the ingest and are checked on the Python side:
 *
 * - the two coverage shares stay apart and are both shown
 * - a report about another corpus version is labelled, not passed off
 * - a machine with no ingest says so instead of showing zeros
 * - what the evidence does not cover is on the screen, not in a document
 */

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { CorpusState } from "../../api/corpus";
import { renderApp } from "../../test/render";
import { LEXICON } from "../../text/lexicon";

/** The real v1 figures, so the test breaks if the shape of them changes. */
const STATE: CorpusState = {
  serving: { documents: "v1", word_types: "v1", derivations: "v1" },
  built: {
    documents: ["documents-v1"],
    word_types: ["word_types-v1"],
    derivations: ["derivations-v1"],
  },
  describes_the_served_version: true,
  report: {
    corpus_version: "v1",
    source_id: "ganjoor",
    source_name_fa: "گنجور",
    licence: "public-domain classical texts, compiled by Ganjoor (confirm terms)",
    built_at: "2026-08-12T17:54:13+00:00",
    lexicon_snapshot_id: "lexicon-20260808:45e05ff66c37",
    documents: 133148,
    tokens: 25497189,
    spellings: 409916,
    word_types: 411166,
    documents_without_author: 0,
    documents_without_century: 98627,
    spellings_linked: 16714,
    spellings_unlinked: 393202,
    tokens_linked: 11644767,
    ambiguous_spellings: 1037,
    type_share: 0.0407742,
    token_share: 0.4567078,
    poets_without_a_century: ["", "abbadi", "abdullah"],
    centuries_without_a_poet: ["ferdowsi", "roudaki"],
    biggest_gaps: [
      { spelling_fa: "و", total_count: 1109915, doc_count: 101974, author_count: 237 },
      { spelling_fa: "ز", total_count: 279353, doc_count: 76140, author_count: 230 },
    ],
  },
};

function answerWith(body: unknown, status = 200) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    statusText: "",
    json: async () => body,
  } as Response);
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("the corpus screen", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", answerWith(STATE));
  });

  it("names the source in Persian, not by its identifier", async () => {
    renderApp("/corpus");
    const block = await screen.findByRole("region", { name: "سرچشمه" });
    expect(within(block).getByText("گنجور")).toBeInTheDocument();
    // The heading says سرچشمه and this said «ganjoor» under it until
    // 2026-08-18. `source:ganjoor` is still how the query is written; that is
    // راهنمای نحو's job to teach, not this column's.
    expect(within(block).queryByText("ganjoor")).not.toBeInTheDocument();
    expect(within(block).getByText(/confirm terms/)).toBeInTheDocument();
  });

  it("falls back to the identifier for a source with no Persian name", async () => {
    vi.stubGlobal(
      "fetch",
      answerWith({
        ...STATE,
        report: { ...STATE.report, source_name_fa: "" },
      }),
    );
    renderApp("/corpus");
    const block = await screen.findByRole("region", { name: "سرچشمه" });
    expect(within(block).getByText("ganjoor")).toBeInTheDocument();
  });

  it("says which corpus version is being served", async () => {
    renderApp("/corpus");
    const block = await screen.findByRole("region", {
      name: "نسخه‌ای که به کار می‌رود",
    });
    expect(within(block).getAllByText("v1")).toHaveLength(3);
  });

  it("shows both coverage shares, because they answer different questions", async () => {
    renderApp("/corpus");
    const block = await screen.findByRole("region", {
      name: `پوشش ${LEXICON}`,
    });
    // 4.1% of the vocabulary, 45.7% of the running text. Reading the first as
    // a quality figure is exactly the mistake the pair prevents.
    expect(within(block).getByRole("img", { name: /از واژگان/ })).toHaveAttribute(
      "aria-label",
      expect.stringContaining("۴٫۱٪"),
    );
    expect(within(block).getByRole("img", { name: /از متن/ })).toHaveAttribute(
      "aria-label",
      expect.stringContaining("۴۵٫۷٪"),
    );
  });

  it("writes every count in Persian numerals", async () => {
    renderApp("/corpus");
    const block = await screen.findByRole("region", { name: "اندازه" });
    expect(within(block).getByText("۱۳۳٬۱۴۸")).toBeInTheDocument();
    expect(block.textContent).not.toMatch(/[0-9]/);
  });

  it("states what the evidence does not cover", async () => {
    renderApp("/corpus");
    const block = await screen.findByRole("region", {
      name: "آنچه شواهد نمی‌پوشاند",
    });
    // Three quarters of the poems carry no date, and the dispersion chart on
    // the word screen rests on the rest.
    expect(within(block).getByText("۷۴٫۱٪")).toBeInTheDocument();
    expect(within(block).getByText("۹۸٬۶۲۷")).toBeInTheDocument();
    // A century-table entry that matches no poet dates nothing while looking
    // exactly like one that works.
    expect(within(block).getByText("ferdowsi")).toBeInTheDocument();
  });

  it("counts the poets with no century without printing the empty slug", async () => {
    renderApp("/corpus");
    const block = await screen.findByRole("region", {
      name: "آنچه شواهد نمی‌پوشاند",
    });
    // Three entries, one of which is the empty slug: it is a real gap and
    // stays in the count, but there is nothing to print.
    const said = within(block).getByText(/سراینده در جدول سده‌ها نیست/);
    expect(said.querySelector("[data-value]")).toHaveAttribute("data-value", "2");
  });

  it("shows the unmatched pile as a deliverable, not as errors", async () => {
    renderApp("/corpus");
    const block = await screen.findByRole("region", { name: "املاهای بی‌مدخل" });
    expect(within(block).getByText("و")).toBeInTheDocument();
    expect(within(block).getByText("۱٬۱۰۹٬۹۱۵")).toBeInTheDocument();
    expect(within(block).getByText(/۳۹۳٬۲۰۲/)).toBeInTheDocument();
  });

  it("dates the ingest in the European calendar", async () => {
    // `fa-IR` on its own gives the Persian calendar and the date read
    // ۲۶ مرداد ۱۴۰۵. The project lead's call is the European one; the language
    // is unchanged, so the month is still named in Persian.
    renderApp("/corpus");
    const block = await screen.findByRole("region", { name: "سرچشمه" });
    const date = within(block).getByText(/۲۰۲۶/);
    expect(date).toBeInTheDocument();
    expect(block.textContent).not.toContain("۱۴۰۵");
  });
});

describe("the words the screen uses for itself", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", answerWith(STATE));
  });

  it("says what each of the three stores holds", async () => {
    // Three cards with the same version under each and nothing saying which is
    // which. The project lead's finding: the names do not say what they do.
    renderApp("/corpus");
    const block = await screen.findByRole("region", {
      name: "نسخه‌ای که به کار می‌رود",
    });
    for (const name of ["سروده‌ها", "واژه‌گونه‌ها", "ساخته‌ها"]) {
      expect(
        within(block).getByRole("button", { name: `${name} چیست؟` }),
      ).toBeInTheDocument();
    }
  });

  it("explains a store in plain words when the mark is opened", async () => {
    renderApp("/corpus");
    const block = await screen.findByRole("region", {
      name: "نسخه‌ای که به کار می‌رود",
    });
    await userEvent.click(
      within(block).getByRole("button", { name: "ساخته‌ها چیست؟" }),
    );
    expect(screen.getByRole("tooltip")).toHaveTextContent(
      /ما با دستورهای واژه‌سازی ساخته‌ایم/,
    );
  });

  it("explains the difference between the two counts that look alike", async () => {
    // ۴۰۹٬۹۱۶ spellings beside ۴۱۱٬۱۶۷ word types: a thousand apart, and
    // nothing beside either number said why.
    renderApp("/corpus");
    const block = await screen.findByRole("region", { name: "اندازه" });
    await userEvent.click(
      within(block).getByRole("button", { name: "املای جداگانه چیست؟" }),
    );
    expect(screen.getByRole("tooltip")).toHaveTextContent(/نوشته/);

    await userEvent.click(
      within(block).getByRole("button", { name: "واژه‌گونه چیست؟" }),
    );
    expect(screen.getByRole("tooltip")).toHaveTextContent(/خوانده/);
  });
});

describe("when the report is about another corpus version", () => {
  it("says so rather than passing it off as current", async () => {
    vi.stubGlobal(
      "fetch",
      answerWith({
        ...STATE,
        serving: { ...STATE.serving, word_types: "v2" },
        describes_the_served_version: false,
      }),
    );
    renderApp("/corpus");
    expect(
      await screen.findByText(/تنها برای نسخهٔ خودش درست است/),
    ).toBeInTheDocument();
  });
});

describe("when no ingest has been reported", () => {
  it("says so rather than showing zeros", async () => {
    vi.stubGlobal(
      "fetch",
      answerWith({ ...STATE, report: null, describes_the_served_version: false }),
    );
    renderApp("/corpus");
    expect(
      await screen.findByText(/عددِ ساختگی بدتر از نبودِ عدد است/),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("region", { name: `پوشش ${LEXICON}` }),
    ).toBeNull();
  });
});

describe("when the search index is not there", () => {
  it("explains what to do rather than only what failed", async () => {
    vi.stubGlobal("fetch", answerWith({ detail: "not built" }, 503));
    renderApp("/corpus");
    expect(
      await screen.findByText(/پس از نخستین درون‌ریزی اینجا پر می‌شود/),
    ).toBeInTheDocument();
  });
});
