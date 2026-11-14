/**
 * The verses under a built word's corpus figures.
 *
 * What is tested is what the panel promises: nothing is asked for until the
 * «پیکره» field opens; then the first texts come with the word marked and a
 * way to its unit; more opens the word page's own list in place, with its
 * author filter and its pages; and a word the corpus does not have, or the
 * letters of a function word, list nothing at all.
 */

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Evidence, EvidenceText } from "../../api/evidence";
import type { Attestation, BuiltForm } from "../../api/generate";
import { renderWithRouter } from "../../test/render";
import { Signals } from "./Signals";

function found(level: Attestation["level"], texts: number, extra: Partial<Attestation> = {}) {
  return {
    level,
    corpus_version: "v1",
    total_count: texts,
    doc_count: texts,
    author_count: texts,
    first_century: null,
    last_century: null,
    other_readings: [],
    unlinked: false,
    wording: "",
    ...extra,
  };
}

function built(attestation: BuiltForm["attestation"], fa = "بسمان"): BuiltForm {
  return {
    form_latin: "Basmān",
    form_fa: fa,
    word_class: "karnam",
    depth: 2,
    semantic_tags: [],
    meaning_fa: null,
    attestation,
    paths: [],
  };
}

function text(n: number, author: string): EvidenceText {
  return {
    document_id: `fixture:${n}`,
    author,
    title: `عنوان ${n}`,
    century: null,
    work: "دیوان",
    section: [],
    lines: [{ unit: n, kind: "couplet", parts: ["", "بسمان", ` است ${n}`] }],
    held: "counted",
  };
}

/** Who wrote text n: one text by ب, every fifth by پ, the rest by الف. */
function authorOf(n: number): string {
  if (n === 0) return "ب";
  return n % 5 === 0 ? "پ" : "الف";
}

/** A list of `total` texts, its authors most texts first, as `/evidence` answers. */
function answer(params: URLSearchParams, total: number, by = authorOf): Evidence {
  const page = Number(params.get("page") ?? "0");
  const size = Number(params.get("size") ?? "20");
  const author = params.get("author");
  const every = Array.from({ length: total }, (_, n) => text(n, by(n)));
  const counts = new Map<string, number>();
  for (const one of every) counts.set(one.author!, (counts.get(one.author!) ?? 0) + 1);
  const authors = [...counts]
    .map(([name, texts]) => ({ author: name, texts }))
    .sort((a, b) => b.texts - a.texts || a.author.localeCompare(b.author));
  const listed = authors.flatMap((one) => every.filter((t) => t.author === one.author));
  const all = listed.filter((one) => !author || one.author === author);
  const texts =
    params.get("voices") === "1"
      ? authors.slice(0, size).map((one) => listed.find((t) => t.author === one.author)!)
      : all.slice(page * size, page * size + size);
  return {
    spelling: params.get("spelling") ?? "",
    corpus_version: "v1",
    total,
    authors,
    author,
    unnamed: false,
    matching: all.length,
    lines: params.get("count_lines") === "1" ? all.length : null,
    page,
    size,
    texts,
  };
}

let asked: URLSearchParams[] = [];

function serve(total: number, by = authorOf) {
  asked = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const address = new URL(url, "http://localhost");
      asked.push(address.searchParams);
      const body = answer(address.searchParams, total, by);
      return { ok: true, status: 200, statusText: "", json: async () => body } as Response;
    }),
  );
}

beforeEach(() => serve(2));
afterEach(() => vi.unstubAllGlobals());

async function openCorpus() {
  await userEvent.click(screen.getByRole("button", { name: /^پیکره/ }));
}

describe("the verses under a built word's figures", () => {
  it("asks for nothing until the field opens, then shows the texts with the word marked", async () => {
    renderWithRouter(<Signals form={built(found("reading", 2))} corpusVersion="v1" />);
    expect(asked).toHaveLength(0);
    await openCorpus();
    expect(await screen.findByText(/نه یکی از خوانش‌های آن/)).toBeInTheDocument();
    const links = await screen.findAllByRole("link", { name: "در متن ←" });
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute(
      "href",
      // الف and ب tie on one text each, so الف comes first, by name.
      `/texts?text=fixture%3A1&unit=1&word=${encodeURIComponent("بسمان")}`,
    );
    expect(document.querySelector("mark")).toHaveTextContent("بسمان");
    expect(asked).toHaveLength(1);
    expect(asked[0]!.get("size")).toBe("3");
    expect(asked[0]!.get("voices")).toBe("1");
    expect(asked[0]!.get("count_lines")).toBe("0");
    // Two texts are all there is: nothing more to open.
    expect(screen.queryByRole("button", { name: "نشان دادن همهٔ شواهد" })).not.toBeInTheDocument();
  });

  it("opens the whole list in place, with its authors and its pages", async () => {
    serve(25);
    renderWithRouter(<Signals form={built(found("reading", 25))} corpusVersion="v1" />);
    await openCorpus();
    // One text by each of three authors, never three by the one with most.
    expect(await screen.findAllByRole("link", { name: "در متن ←" })).toHaveLength(3);
    expect(
      screen.getAllByText(/ — دیوان — /).map((one) => one.textContent?.split(" — ")[0]),
    ).toEqual(["الف", "پ", "ب"]);
    // No number on the button: the figures above are the counting's.
    const more = screen.getByRole("button", { name: "نشان دادن همهٔ شواهد" });
    expect(more).toHaveAttribute("aria-expanded", "false");
    await userEvent.click(more);

    const filter = await screen.findByRole("combobox", { name: "نویسنده" });
    expect(
      within(filter)
        .getAllByRole("option")
        .map((one) => one.textContent),
    ).toEqual(["همهٔ نویسندگان (۲۵ متن)", "الف (۲۰)", "پ (۴)", "ب (۱)"]);
    // Ten to a page in a panel.
    expect(await screen.findAllByRole("link", { name: "در متن ←" })).toHaveLength(10);
    await userEvent.click(screen.getByRole("button", { name: "صفحهٔ پسین" }));
    expect(asked.some((one) => one.get("page") === "1" && one.get("size") === "10")).toBe(true);

    await userEvent.selectOptions(filter, "ب");
    expect(await screen.findAllByRole("link", { name: "در متن ←" })).toHaveLength(1);
    expect(asked.some((one) => one.get("author") === "ب")).toBe(true);

    await userEvent.click(screen.getByRole("button", { name: "بستن همهٔ شواهد" }));
    expect(await screen.findAllByRole("link", { name: "در متن ←" })).toHaveLength(3);
  });

  it("lists nothing for a word the corpus does not have, and keeps its sentence", async () => {
    renderWithRouter(<Signals form={built(found("none", 0))} corpusVersion="v1" />);
    await openCorpus();
    expect(screen.getByText(/نیامده است/)).toBeInTheDocument();
    expect(screen.queryByText(/نه یکی از خوانش‌های آن/)).not.toBeInTheDocument();
    expect(asked).toHaveLength(0);
  });

  it("lists nothing for the letters of a function word, whose uses are not this word's", async () => {
    renderWithRouter(
      <Signals
        form={built(found("spelling", 0, { function_word: "حرف اضافه" }))}
        corpusVersion="v1"
      />,
    );
    await openCorpus();
    expect(asked).toHaveLength(0);
  });

  it("keeps the reader's focus on the one button as the list opens and closes", async () => {
    serve(25);
    renderWithRouter(<Signals form={built(found("reading", 25))} corpusVersion="v1" />);
    await openCorpus();
    const more = await screen.findByRole("button", { name: "نشان دادن همهٔ شواهد" });
    await userEvent.click(more);
    expect(more).toHaveFocus();
    expect(more).toHaveAttribute("aria-expanded", "true");
    expect(document.getElementById(more.getAttribute("aria-controls")!)).not.toBeNull();
    await userEvent.click(more);
    expect(more).toHaveFocus();
  });

  it("starts afresh when the row comes to hold another word", async () => {
    serve(25);
    const { rerender } = renderWithRouter(
      <Signals form={built(found("reading", 25))} corpusVersion="v1" />,
    );
    await openCorpus();
    await userEvent.click(await screen.findByRole("button", { name: "نشان دادن همهٔ شواهد" }));
    await userEvent.selectOptions(await screen.findByRole("combobox", { name: "نویسنده" }), "ب");
    rerender(
      <MemoryRouter>
        <Signals form={built(found("reading", 25), "بستگاه")} corpusVersion="v1" />
      </MemoryRouter>,
    );
    expect(await screen.findByText(/شاهد املای «بستگاه»/)).toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "نویسنده" })).not.toBeInTheDocument();
    expect(await screen.findAllByRole("link", { name: "در متن ←" })).toHaveLength(3);
  });

  it("shows what voices there are, and the open list says why its count is not the figures'", async () => {
    // Six texts, all by one author; the counting found five.
    serve(6, () => "الف");
    renderWithRouter(<Signals form={built(found("reading", 5))} corpusVersion="v1" />);
    await openCorpus();
    expect(await screen.findAllByRole("link", { name: "در متن ←" })).toHaveLength(1);
    const more = screen.getByRole("button", { name: "نشان دادن همهٔ شواهد" });
    // The button says no number; the figures above say five.
    expect(more.textContent).not.toMatch(/[۰-۹]/);
    await userEvent.click(more);
    expect(
      await screen.findByText((_text, node) =>
        Boolean(
          node?.matches("p") &&
          /این فهرست ۶ متن دارد و شمارش بالا ۵، چون/.test(node.textContent ?? ""),
        ),
      ),
    ).toBeInTheDocument();
  });
});
