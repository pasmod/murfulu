/**
 * Every search box suggests, and taking a suggestion does what that screen's
 * search does with it.
 *
 * One file for all seven boxes rather than a test in each screen's own file,
 * so the promise — *every search field suggests* — is checked in one place,
 * and a box that stops suggesting fails here by name. What is suggested is
 * the API's and checked on the Python side; this checks which list each box
 * asks for and where a suggestion leads.
 */

import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { TextSuggestions, WordSuggestions } from "../api/suggest";
import { renderApp } from "../test/render";

const PERSIAN: WordSuggestions = {
  q: "دل",
  script: "fa",
  suggestions: [
    { value: "دل", spellings: ["دل"], latin: ["Del", "dall", "Dol", "Dal"] },
    { value: "دلبر", spellings: ["دلبر"], latin: ["Delbar"] },
  ],
};

const LATIN: WordSuggestions = {
  q: "ravand",
  script: "latin",
  suggestions: [{ value: "Ravandegi", spellings: ["روندگی"], latin: ["Ravandegi"] }],
};

const TEXTS: TextSuggestions = {
  q: "حافظ غز",
  suggestions: [
    {
      kind: "work",
      parts: ["حافظ", "غزلیات"],
      query: "حافظ غزلیات",
      texts: 495,
      document_id: null,
    },
    {
      kind: "text",
      parts: ["حافظ", "غزلیات", "غزل شمارهٔ ۳"],
      query: "حافظ غزلیات غزل شمارهٔ ۳",
      texts: 1,
      document_id: "ganjoor:hafez:2132",
    },
  ],
};

const AUTHORS: TextSuggestions = {
  q: "فرد",
  suggestions: [
    { kind: "author", parts: ["فردوسی"], query: "فردوسی", texts: 778, document_id: null },
    { kind: "work", parts: ["فردوسی", "شاهنامه"], query: "فردوسی شاهنامه", texts: 777, document_id: null },
  ],
};

const MEANINGS = {
  rule_pack_version: "test",
  count: 2,
  meanings: [
    {
      tag: "ja",
      gloss_fa: "جا",
      gloss_en: "place",
      affixes: [
        { affix: "-gāh", affix_fa: "گاه", rule_id: "S-1", kind: "suffix", output_types: [], examples: [] },
        { affix: "-estān", affix_fa: "ستان", rule_id: "S-2", kind: "suffix", output_types: [], examples: [] },
      ],
    },
    {
      tag: "abzar",
      gloss_fa: "ابزار",
      gloss_en: "tool",
      affixes: [
        { affix: "-e", affix_fa: "ه", rule_id: "S-3", kind: "suffix", output_types: [], examples: [] },
      ],
    },
  ],
  without_a_meaning: [],
};

function answer(url: string): [number, unknown] {
  const path = decodeURIComponent(url.replace("/api", "").split("?")[0] ?? "");
  const query = new URLSearchParams(url.split("?")[1] ?? "");
  if (path === "/suggest/words") {
    return [200, /[a-z]/i.test(query.get("q") ?? "") ? LATIN : PERSIAN];
  }
  if (path === "/suggest/texts") {
    return [200, (query.get("q") ?? "").startsWith("فرد") ? AUTHORS : TEXTS];
  }
  if (path === "/affixes") return [200, MEANINGS];
  return [404, { detail: "not in this test" }];
}

/** Every address asked for, as a reader would write it: «+» is a space. */
function asked(): string[] {
  return vi
    .mocked(fetch)
    .mock.calls.map(([url]) => decodeURIComponent(String(url).replace(/\+/g, " ")));
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const [status, body] = answer(String(url));
      return {
        ok: status < 400,
        status,
        statusText: "",
        json: async () => body,
      };
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

async function typeAndPick(box: HTMLElement, typed: string, option: RegExp | string) {
  await userEvent.type(box, typed);
  await userEvent.click(await screen.findByRole("option", { name: option }));
}

describe("every search box suggests", () => {
  it("the word bank: a spelling with its readings, and it asks for that word alone", async () => {
    renderApp("/bank?group=نام");
    const box = screen.getByRole("combobox", { name: "جست‌وجو در بانک واژه" });
    await userEvent.type(box, "دل");
    const first = await screen.findByRole("option", { name: /^دل،/ });
    // Three readings, then «…» for the fourth.
    expect(first).toHaveTextContent("Del، dall، Dol، …");
    await userEvent.click(first);
    await waitFor(() =>
      expect(asked().some((url) => url.includes("/bank?q=دل&exact=true"))).toBe(true),
    );
    // Picked from the whole bank, so asked for in the whole bank.
    expect(asked().at(-1)).not.toContain("group=");
  });

  it("the reading screen: a work lists its texts, a text opens", async () => {
    renderApp("/texts");
    const box = screen.getByRole("combobox", { name: "متنی را باز کنید" });
    await typeAndPick(box, "حافظ غز", "حافظ، غزلیات (کتاب، ۴۹۵ متن)");
    await waitFor(() =>
      expect(asked().some((url) => url.includes("/texts?q=حافظ غزلیات"))).toBe(true),
    );
    await userEvent.clear(box);
    await typeAndPick(box, "حافظ غز", /غزل شمارهٔ ۳/);
    await waitFor(() =>
      expect(asked().some((url) => url.includes("/texts/ganjoor:hafez:2132"))).toBe(true),
    );
    expect(box).toHaveValue("حافظ غزلیات غزل شمارهٔ ۳");
  });

  it("the word search: the last term is finished and the search runs", async () => {
    renderApp("/");
    const box = screen.getByRole("combobox", { name: "جست‌وجوی واژه" });
    await typeAndPick(box, "type:nam دل", /^دلبر/);
    await waitFor(() =>
      expect(asked().some((url) => url.includes("/search?q=type:nam دلبر"))).toBe(true),
    );
    expect(asked().filter((url) => url.includes("/suggest/words?q=دل")).length).toBe(1);
  });

  it("the word search: an author after author:", async () => {
    renderApp("/");
    const box = screen.getByRole("combobox", { name: "جست‌وجوی واژه" });
    await userEvent.type(box, "author:فرد");
    // Only the authors: a work is not something `author:` takes.
    const list = await screen.findByRole("listbox");
    expect(within(list).getAllByRole("option")).toHaveLength(1);
    await userEvent.keyboard("{ArrowDown}{Enter}");
    await waitFor(() =>
      expect(asked().some((url) => url.includes("/search?q=author:فردوسی"))).toBe(true),
    );
  });

  it("the word search: a pattern asks for nothing", async () => {
    renderApp("/");
    await userEvent.type(screen.getByRole("combobox", { name: "جست‌وجوی واژه" }), "*nā");
    await new Promise((done) => setTimeout(done, 300));
    expect(asked().some((url) => url.includes("/suggest/"))).toBe(false);
  });

  it("building: only words that build, and taking one builds", async () => {
    renderApp("/build");
    const box = screen.getByRole("combobox", { name: "واژه‌ای بنویسید" });
    await typeAndPick(box, "دل", /^دلبر/);
    expect(asked().some((url) => url.includes("/suggest/words?q=دل&builds=true"))).toBe(true);
    await waitFor(() =>
      expect(asked().some((url) => url.includes("/generate?word=دلبر"))).toBe(true),
    );
  });

  it("compounds: only words that build, and taking one joins", async () => {
    renderApp("/compound");
    const box = screen.getByRole("combobox", { name: "واژه‌ای بنویسید" });
    await typeAndPick(box, "دل", /^دل،/);
    expect(asked().some((url) => url.includes("/suggest/words?q=دل&builds=true"))).toBe(true);
    await waitFor(() =>
      expect(asked().some((url) => url.includes("/compound?word=دل"))).toBe(true),
    );
  });

  it("taking apart: a Latin reading with its spelling, and taking it takes it apart", async () => {
    renderApp("/explain");
    const box = screen.getByRole("combobox", { name: "واژه‌ای به بهنویس بنویسید" });
    await userEvent.type(box, "ravand");
    const option = await screen.findByRole("option", { name: /Ravandegi/ });
    expect(option).toHaveTextContent("روندگی");
    await userEvent.click(option);
    await waitFor(() =>
      expect(asked().some((url) => url.includes("/explain?word=Ravandegi"))).toBe(true),
    );
  });

  it("meanings: from the list the screen already has, with how many affixes each", async () => {
    renderApp("/affixes");
    const box = await screen.findByRole("combobox", { name: "میان معناها بگردید" });
    await userEvent.type(box, "ا");
    const option = await screen.findByRole("option", { name: /ابزار/ });
    expect(option).toHaveTextContent("۱ وند");
    await userEvent.click(option);
    expect(box).toHaveValue("ابزار");
    expect(asked().some((url) => url.includes("/suggest/"))).toBe(false);
    expect(screen.getByRole("status")).toHaveTextContent("۱ معنا از ۲");
  });
});
