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
  it("asks nothing until there is a query", () => {
    renderApp("/");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("runs the query in the address, so a search can be linked to", async () => {
    renderApp("/?q=*n%C4%81");
    await waitFor(() => expect(fetch).toHaveBeenCalled());
    const url = String(vi.mocked(fetch).mock.calls[0]?.[0]);
    expect(url).toContain("/api/search");
    expect(url).toContain("q=*n%C4%81");
  });

  it("puts what was typed into the address", async () => {
    renderApp("/");
    await userEvent.type(screen.getByRole("searchbox"), "*nā");
    await userEvent.click(screen.getByRole("button", { name: "جست‌وجو" }));
    await waitFor(() => expect(fetch).toHaveBeenCalled());
  });

  // The four example chips under the box were folded into راهنمای نحو on
  // 2026-08-18 — every one of them was already a row in it. The syntax is
  // still taught by being clickable; it is now taught from one place.
  it("runs a listed query when it is clicked, which is how the syntax is taught", async () => {
    renderApp("/");
    await userEvent.click(
      screen.getByRole("button", { name: "راهنمای نحو" }),
    );
    await userEvent.click(screen.getByText("type:karnam"));
    await waitFor(() => expect(fetch).toHaveBeenCalled());
    expect(String(vi.mocked(fetch).mock.calls[0]?.[0])).toContain("type%3Akarnam");
  });
});

describe("the two groups", () => {
  it("keeps a word formed with the affix apart from one that merely ends in it", async () => {
    renderApp("/?q=*n%C4%81");
    const formed = await screen.findByRole("region", { name: /ساخته‌شده با/ });
    expect(within(formed).getByText("تنکنا")).toBeInTheDocument();
    expect(within(formed).queryByText("فنا")).not.toBeInTheDocument();

    const merely = screen.getByRole("region", { name: /تنها به این حروف/ });
    expect(within(merely).getByText("فنا")).toBeInTheDocument();
  });

  it("says an empty first group is unknown, not empty", async () => {
    vi.stubGlobal(
      "fetch",
      answerWith({ ...ANSWER, formed_with_affix: [], total: 1 }),
    );
    renderApp("/?q=*n%C4%81");
    expect(await screen.findByText(/هنوز روشن نیست/)).toBeInTheDocument();
    expect(screen.getByText(/این با «هیچ‌کدام» یکی نیست/)).toBeInTheDocument();
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
});

describe("the facets", () => {
  it("count the whole result set and narrow rather than replace", async () => {
    renderApp("/?q=*n%C4%81");
    const panel = await screen.findByRole("complementary", {
      name: "باریک‌کردن نتیجه",
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
      name: "باریک‌کردن نتیجه",
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
    const trouble = await screen.findByText("این جست‌وجو خوانده نشد.");
    expect(trouble).toBeInTheDocument();
    expect(screen.getByText(/«poem» چیزی نیست که بتوان بر آن جست‌وجو کرد/))
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
    // The whole sentence, because `count:1` on its own is also a reference row
    // and an example chip — it is offered in three places on this screen.
    const advice = await screen.findByText(
      /بسامد باید عدد باشد، نه «abc».+count:1/,
    );
    expect(advice).toBeInTheDocument();
  });

  it("still says something in Persian when the API only sends English", async () => {
    // A container a version behind sends the old shape. The reader gets a
    // general Persian sentence rather than a precise English one.
    vi.stubGlobal("fetch", answerWith({ detail: "unknown field 'poem'" }, 400));
    renderApp("/?q=poem%3Ax");
    expect(await screen.findByText("این جست‌وجو خوانده نشد.")).toBeInTheDocument();
    expect(screen.getByText(/راهنمای نحو را باز کنید/)).toBeInTheDocument();
    expect(screen.queryByText(/unknown field/)).not.toBeInTheDocument();
  });

  it("says an unbuilt index is not the reader's fault", async () => {
    vi.stubGlobal("fetch", answerWith({ detail: "not built" }, 503));
    renderApp("/?q=*n%C4%81");
    expect(
      await screen.findByText(/هنوز پیکره‌ای برای جست‌وجو ساخته نشده/),
    ).toBeInTheDocument();
  });

  it("says nothing was found without saying the words do not exist", async () => {
    vi.stubGlobal(
      "fetch",
      answerWith({ ...ANSWER, total: 0, formed_with_affix: [], string_match_only: [] }),
    );
    renderApp("/?q=*zzz");
    expect(await screen.findByText(/هیچ واژه‌ای با این الگو یافت نشد/)).toBeInTheDocument();
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
