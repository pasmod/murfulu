/**
 * The search screen.
 *
 * The API is stubbed, so what is tested is the screen: that the two groups
 * stay apart, that an empty first group says so rather than disappearing, and
 * that each of the three ways a search can fail says something different and
 * useful.
 */

import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { SearchResult } from "../../api/search";
import { affixOf } from "../../api/search";
import { renderApp } from "../../test/render";

function word(id: string, spelling: string, latin: string, extra = {}) {
  return {
    id,
    spelling_fa: spelling,
    latin,
    population: ["corpus", "lexicon"],
    total_count: 12,
    doc_count: 9,
    author_count: 4,
    first_century: 11,
    last_century: 13,
    lexicon_category: "اسم ذات",
    ...extra,
  };
}

const ANSWER: SearchResult = {
  query: "*nā",
  index: "word_types",
  total: 2,
  returned: 2,
  facets: {
    population: [{ value: "corpus", count: 2 }],
    century: [{ value: 11, count: 1 }],
  },
  formed_with_affix: [word("تنکنا:Tonoknā", "تنکنا", "Tonoknā")],
  string_match_only: [word("فنا:Fanā", "فنا", "Fanā", { total_count: 4315 })],
};

/**
 * The requests that searched, leaving out the corpus's century range, which
 * the filters ask for on arrival to fill their century fields.
 */
function searches(): string[] {
  return vi
    .mocked(fetch)
    .mock.calls.map((call) => String(call[0]))
    .filter((url) => !url.includes("/corpus/centuries"));
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
  vi.stubGlobal("fetch", answerWith(ANSWER));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("running a search", () => {
  it("asks nothing until there is a query, but the corpus's range of centuries", () => {
    // The range fills the century fields before anyone touches them — the
    // project lead's request of 2026-11-20. Nothing else is asked.
    renderApp("/");
    expect(searches()).toEqual([]);
  });

  it("runs the query in the address, so a search can be linked to", async () => {
    renderApp("/?q=*n%C4%81");
    await waitFor(() => expect(searches()).not.toEqual([]));
    const url = searches()[0]!;
    expect(url).toContain("/api/search");
    expect(url).toContain("q=*n%C4%81");
  });

  it("puts what was typed into the address", async () => {
    renderApp("/");
    await userEvent.type(screen.getByRole("combobox", { name: "جست‌وجوی واژه" }), "*nā");
    await userEvent.click(screen.getByRole("button", { name: "جست‌وجو" }));
    await waitFor(() => expect(fetch).toHaveBeenCalled());
  });

  // The examples were a table behind an ⓘ until 2026-11-20; the project lead
  // asked for them to open under the box like a search engine's suggestions.
  it("shows the examples when the reader steps into the empty box", async () => {
    renderApp("/");
    await userEvent.click(screen.getByRole("combobox", { name: "جست‌وجوی واژه" }));
    const list = await screen.findByRole("listbox");
    // Each says what it finds, in Persian, beside the query.
    expect(
      within(list).getByRole("option", { name: /^\*eš، واژه‌هایی که با «ـِش» تمام می‌شوند$/ }),
    ).toBeInTheDocument();
    for (const query of ["stem1:goft", "tag:ja", "rule:V-010", "century:10-13"]) {
      expect(within(list).getByText(query)).toBeVisible();
    }
    // The examples are the screen's own; an empty box asks the API nothing.
    expect(searches()).toEqual([]);
    expect(screen.queryByRole("button", { name: "راهنمای نحو" })).toBeNull();
  });

  it("narrows the examples as the reader types", async () => {
    renderApp("/");
    await userEvent.type(screen.getByRole("combobox", { name: "جست‌وجوی واژه" }), "count");
    const list = await screen.findByRole("listbox");
    await waitFor(() =>
      expect(within(list).getAllByRole("option").map((one) => one.textContent)).toEqual([
        "count:>10بیش از ده بار در متن‌ها آمده",
        "count:1تنها یک بار در متن‌ها آمده",
      ]),
    );
  });

  it("keeps the examples when the word suggestions do not answer", async () => {
    // The examples are the screen's own; a word bank that is down must not
    // take them with it, now that they are the only list of examples.
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        String(url).includes("/suggest/")
          ? Promise.resolve({ ok: false, status: 503, statusText: "", json: async () => ({}) } as Response)
          : answerWith(ANSWER)(),
      ),
    );
    renderApp("/");
    await userEvent.type(screen.getByRole("combobox", { name: "جست‌وجوی واژه" }), "count");
    const list = await screen.findByRole("listbox");
    expect(within(list).getAllByRole("option")).toHaveLength(2);
  });

  it("shows the fitting examples without waiting for slow word suggestions", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        String(url).includes("/suggest/") ? new Promise(() => undefined) : answerWith(ANSWER)(),
      ),
    );
    renderApp("/");
    await userEvent.type(screen.getByRole("combobox", { name: "جست‌وجوی واژه" }), "count");
    const list = await screen.findByRole("listbox", {}, { timeout: 3000 });
    expect(within(list).getAllByRole("option")).toHaveLength(2);
  });

  it("runs an example when it is picked, which is how the syntax is taught", async () => {
    renderApp("/");
    await userEvent.click(screen.getByRole("combobox", { name: "جست‌وجوی واژه" }));
    await userEvent.click(await screen.findByText("type:karnam"));
    await waitFor(() => expect(searches()).not.toEqual([]));
    expect(searches()[0]).toContain("type%3Akarnam");
    expect(screen.getByRole("combobox", { name: "جست‌وجوی واژه" })).toHaveValue(
      "type:karnam",
    );
  });
});

describe("the two groups", () => {
  it("keeps a word formed with the affix apart from one that merely ends in it", async () => {
    renderApp("/?q=*n%C4%81");
    const formed = await screen.findByRole("region", { name: /ساخته‌شده با/ });
    expect(within(formed).getByText("تنکنا")).toBeInTheDocument();
    expect(within(formed).queryByText("فنا")).not.toBeInTheDocument();

    const merely = screen.getByRole("region", { name: /فقط با همین حروف/ });
    expect(within(merely).getByText("فنا")).toBeInTheDocument();
  });

  it("says an empty first group is unknown, not empty", async () => {
    vi.stubGlobal(
      "fetch",
      answerWith({ ...ANSWER, formed_with_affix: [], total: 1 }),
    );
    renderApp("/?q=*n%C4%81");
    expect(await screen.findByText(/هنوز نمی‌دانیم کدام‌یک/)).toBeInTheDocument();
    expect(screen.getByText(/این یعنی «نمی‌دانیم»، نه «هیچ‌کدام»/)).toBeInTheDocument();
  });

  it("does not split at all when the query asks about no affix", async () => {
    renderApp("/?q=type%3Akarnam");
    await screen.findByRole("region", { name: /نتیجه‌ها/ });
    expect(
      screen.queryByRole("region", { name: /ساخته‌شده با/ }),
    ).not.toBeInTheDocument();
  });
});

describe("what a hit shows", () => {
  it("shows both scripts, because the Latin is the point", async () => {
    renderApp("/?q=*n%C4%81");
    expect(await screen.findByText("تنکنا")).toBeInTheDocument();
    expect(screen.getByText("Tonoknā")).toHaveAttribute("dir", "ltr");
  });

  it("writes every count in Persian numerals", async () => {
    renderApp("/?q=*n%C4%81");
    expect(await screen.findByText("۴٬۳۱۵")).toBeInTheDocument();
  });

  it("links to the word, not to nowhere", async () => {
    renderApp("/?q=*n%C4%81");
    const link = await screen.findByRole("link", { name: /تنکنا/ });
    expect(link).toHaveAttribute("href", expect.stringContaining("/word/"));
  });

  it("shows the short vowels where the API sends them, and links on the plain spelling", async () => {
    vi.stubGlobal(
      "fetch",
      answerWith({
        ...ANSWER,
        formed_with_affix: [
          word("تنکنا:Tonoknā", "تنکنا", "Tonoknā", { spelling_fa_marked: "تُنُکنا" }),
        ],
      }),
    );
    renderApp("/?q=*n%C4%81");
    expect(await screen.findByText("تُنُکنا")).toBeInTheDocument();
    expect(screen.queryByText("تنکنا")).not.toBeInTheDocument();
    const link = screen.getByRole("link", { name: /تُنُکنا/ });
    expect(link).toHaveAttribute("href", `/word/${encodeURIComponent("تنکنا:Tonoknā")}`);
    // A hit the API sent no marks for stays as it is written.
    expect(screen.getByText("فنا")).toBeInTheDocument();
  });
});

describe("the facets", () => {
  it("count the whole result set and narrow rather than replace", async () => {
    renderApp("/?q=*n%C4%81");
    const panel = await screen.findByRole("complementary", {
      name: "محدود کردن نتیجه‌ها",
    });
    await userEvent.click(within(panel).getByRole("button", { name: /پیکره/ }));
    await waitFor(() => {
      const last = vi.mocked(fetch).mock.calls.at(-1);
      expect(String(last?.[0])).toContain("in%3Acorpus");
    });
    expect(String(vi.mocked(fetch).mock.calls.at(-1)?.[0])).toContain("*n%C4%81");
  });

  it("writes the narrowed query into the box, which is the point of them", async () => {
    // Facets.tsx says why: a facet writes the query it stands for and the box
    // shows it, so the reader learns the syntax by using the interface. The
    // box seeded its draft from the query once and never again, so the URL
    // and the results narrowed and the box went on showing the old query —
    // the reader was never shown the syntax the facet had just written.
    renderApp("/?q=*n%C4%81");
    const panel = await screen.findByRole("complementary", {
      name: "محدود کردن نتیجه‌ها",
    });
    await userEvent.click(within(panel).getByRole("button", { name: /پیکره/ }));
    await waitFor(() => {
      expect(screen.getByLabelText("جست‌وجوی واژه")).toHaveValue("*nā in:corpus");
    });
  });
});

describe("when it goes wrong", () => {
  it("says why the query was not read, in Persian and not in English", async () => {
    // This test used to assert the opposite — that the parser's English was
    // repeated to the reader, which is what it did. The project lead asked on
    // 2026-08-17 why there is still English in the app, and this was most of
    // the answer. The API names the fault now and the screen writes the
    // sentence; see UNREADABLE in Search.tsx.
    vi.stubGlobal(
      "fetch",
      answerWith(
        {
          detail: {
            code: "unknown-field",
            facts: { name: "poem" },
            said: "poem: is not a searchable field",
          },
        },
        400,
      ),
    );
    renderApp("/?q=poem%3Ax");
    const trouble = await screen.findByText("این جست‌وجو را نفهمیدیم.");
    expect(trouble).toBeInTheDocument();
    expect(screen.getByText(/با «poem» نمی‌شود جست‌وجو کرد/))
      .toBeInTheDocument();
    expect(screen.queryByText(/is not a searchable field/)).not.toBeInTheDocument();
  });

  it("names the part of the query that is wrong, so it can be found and fixed", async () => {
    vi.stubGlobal(
      "fetch",
      answerWith(
        {
          detail: {
            code: "bad-count",
            facts: { value: "abc" },
            said: "count: 'abc' is not a number or a band",
          },
        },
        400,
      ),
    );
    renderApp("/?q=count%3Aabc");
    // The whole sentence, because `count:1` on its own is also one of the
    // box's examples.
    const advice = await screen.findByText(
      /شمار کاربرد را با عدد بنویسید، نه «abc».+count:1/,
    );
    expect(advice).toBeInTheDocument();
  });

  it("still says something in Persian when the API only sends English", async () => {
    // A container a version behind sends the old shape. The reader gets a
    // general Persian sentence rather than a precise English one.
    vi.stubGlobal("fetch", answerWith({ detail: "unknown field 'poem'" }, 400));
    renderApp("/?q=poem%3Ax");
    expect(await screen.findByText("این جست‌وجو را نفهمیدیم.")).toBeInTheDocument();
    expect(screen.getByText(/کادر جست‌وجو را خالی کنید و رویش بزنید/)).toBeInTheDocument();
    expect(screen.queryByText(/unknown field/)).not.toBeInTheDocument();
  });

  it("says an unbuilt index is not the reader's fault", async () => {
    vi.stubGlobal("fetch", answerWith({ detail: "not built" }, 503));
    renderApp("/?q=*n%C4%81");
    expect(
      await screen.findByText(/پیکره هنوز برای جست‌وجو آماده نیست/),
    ).toBeInTheDocument();
  });

  it("says nothing was found without saying the words do not exist", async () => {
    vi.stubGlobal(
      "fetch",
      answerWith({ ...ANSWER, total: 0, formed_with_affix: [], string_match_only: [] }),
    );
    renderApp("/?q=*zzz");
    expect(await screen.findByText(/هیچ واژه‌ای با این الگو جور درنیامد/)).toBeInTheDocument();
  });
});

describe("the affix a query asks about", () => {
  it("reads a suffix, a prefix, and nothing from anything else", () => {
    expect(affixOf("*nā")).toBe("-nā");
    expect(affixOf("bar*")).toBe("bar-");
    expect(affixOf("*raft*")).toBeUndefined();
    expect(affixOf("type:karnam")).toBeUndefined();
    expect(affixOf("*nā type:nam")).toBe("-nā");
  });
});
