/**
 * The word bank screen.
 *
 * The order, counts and search are the API's and checked on the Python side.
 * What is checked here is what the reader sees: the linguist's group names on
 * the buttons, both stems under a verb by their new names, a loanword listed
 * and marked as building nothing, and the address carrying the choice.
 */

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { BankGroups, BankPage } from "../../api/bank";
import { renderApp } from "../../test/render";

const GROUPS: BankGroups = {
  lexicon_snapshot_id: "lexicon-20261111:e300dbc27083",
  has_bank: true,
  total: 3,
  stem_labels: { past: "پیشین‌کاربن", present: "کنون‌کاربن" },
  groups: [
    { key: "نابسودکارواژه", label_fa: "نابسودکارواژه", words: 1, word_classes: ["nabesudkarvaze"], in_word_formation: true },
    { key: "نام", label_fa: "نام", words: 1, word_classes: ["nam"], in_word_formation: true },
    { key: "وام‌واژه", label_fa: "وام‌واژه", words: 1, word_classes: [], in_word_formation: false },
  ],
};

const WORDS: BankPage["words"] = [
  {
    spelling_fa: "رفتن",
    latin: "raftan",
    latin_variants: [],
    groups: [{ key: "نابسودکارواژه", label_fa: "نابسودکارواژه" }],
    lexicon_category: "مصدر",
    in_word_formation: true,
    needs_review: false,
    definition_fa: null,
    definition_truncated: null,
    past_stem_fa: "رفت",
    past_stem_latin: "raft",
    present_stem_fa: "رو",
    present_stem_latin: "row",
    sense_count: 1,
  },
  {
    spelling_fa: "آبجو",
    latin: "ābjow",
    latin_variants: [],
    groups: [{ key: "وام‌واژه", label_fa: "وام‌واژه" }],
    lexicon_category: "وام‌واژه",
    in_word_formation: false,
    needs_review: false,
    definition_fa: "نوشابه‌ای از جو",
    definition_truncated: true,
    past_stem_fa: null,
    past_stem_latin: null,
    present_stem_fa: null,
    present_stem_latin: null,
    sense_count: 1,
  },
];

function answer(url: string): unknown {
  if (url.includes("/bank/groups")) return GROUPS;
  return {
    lexicon_snapshot_id: GROUPS.lexicon_snapshot_id,
    group: null,
    q: null,
    total: WORDS.length,
    offset: 0,
    limit: 50,
    words: WORDS,
  } satisfies BankPage;
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => ({
      ok: true,
      status: 200,
      statusText: "",
      json: async () => answer(String(url)),
    })),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("the word bank screen", () => {
  it("offers the linguist's groups by his names", async () => {
    renderApp("/bank");
    const groups = await screen.findByRole("navigation", { name: "گروه‌های بانک واژه" });
    expect(within(groups).getByRole("button", { name: /^نام/ })).toBeInTheDocument();
    expect(within(groups).getByRole("button", { name: /وام‌واژه/ })).toBeInTheDocument();
  });

  it("shows both stems of a verb under their new names", async () => {
    renderApp("/bank");
    const verb = (await screen.findByText("رفتن")).closest("li")!;
    expect(within(verb).getByText("پیشین‌کاربن")).toBeInTheDocument();
    expect(within(verb).getByText("کنون‌کاربن")).toBeInTheDocument();
    expect(within(verb).getByText("raft")).toBeInTheDocument();
    expect(within(verb).getByText("row")).toBeInTheDocument();
    expect(within(verb).queryByText(/کاربن یک|کاربن دو/)).not.toBeInTheDocument();
  });

  it("lists a loanword and says it builds nothing", async () => {
    renderApp("/bank");
    const loan = (await screen.findByText("آبجو")).closest("li")!;
    expect(within(loan).getByText("در واژه‌سازی به کار نمی‌رود")).toBeInTheDocument();
    expect(within(loan).queryByRole("link", { name: "ساختن از این واژه" })).not.toBeInTheDocument();
    expect(within(loan).getByText("نوشابه‌ای از جو…")).toBeInTheDocument();
  });

  it("puts the chosen group in the address", async () => {
    renderApp("/bank");
    const groups = await screen.findByRole("navigation", { name: "گروه‌های بانک واژه" });
    await userEvent.click(within(groups).getByRole("button", { name: /^نام/ }));
    const calls = vi.mocked(fetch).mock.calls.map(([url]) => decodeURIComponent(String(url)));
    expect(calls.some((url) => url.includes("/bank?group=نام"))).toBe(true);
  });
});

describe("the word bank's address", () => {
  it("reads a page number that is not a whole number as the first page", async () => {
    renderApp("/bank?page=2.5");
    await screen.findByText("رفتن");
    const calls = vi.mocked(fetch).mock.calls.map(([url]) => String(url));
    expect(calls.some((url) => url.includes("/bank?") && url.includes("offset=0"))).toBe(true);
  });

  it("moves a page past the end back to the last page", async () => {
    renderApp("/bank?page=999");
    await screen.findByText("رفتن");
    await vi.waitFor(() => {
      const calls = vi.mocked(fetch).mock.calls.map(([url]) => String(url));
      expect(calls.filter((url) => url.includes("/bank?")).at(-1)).toContain("offset=0");
    });
  });
});
