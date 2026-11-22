/**
 * The automatic suggestion beside the most frequent unsure spellings
 * (2026-11-22): shown in the list's rows and panels and in the reading
 * screen's word panel, marked among the offered readings or offered to type,
 * and taken up only by the person's own press and save.
 *
 * Every word and line here is written for the test; no corpus text.
 */

import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Suggestion, Text, UnsureSpelling } from "../../api/texts";
import { renderApp } from "../../test/render";
import { contextOf, folded, outOf100, readHere, suggestedAmong, takeUpOf } from "./suggested";

const SUGGESTED: Suggestion = {
  latin: "del",
  as_read: "del-e",
  certainty: 92,
  right_share: 0.881,
  right_at_least: 0.846,
  band: [85, 100],
  tested_words: 1200,
  context: "یک [دل] دو",
  place: { document_id: "fixture:a:1", unit: 0, line: 0, word: 0 },
  matches: ["Del"],
  in_bank: true,
  marked: { checked: 40, fit: 30 },
};

const LISTED: UnsureSpelling = {
  rank: 1,
  spelling: "دل",
  written: "دل",
  places: 1000,
  unsure: 600,
  kind: "choice",
  known: ["Dal", "Del", "dall"],
  read_as: [["Del", 400]],
  offered: [["Dol", 100]],
  before: [["ما", 120, 80]],
  after: [["رفتند", 50, 40]],
  examples: [
    {
      document_id: "fixture:a:1",
      unit: 0,
      line: 0,
      word: 0,
      heading: "نویسنده · کتاب",
      text: "دل ما",
    },
  ],
  marked: null,
  decided: [],
  suggestion: SUGGESTED,
};

/** A text where دل stands first in its line, the model unsure of it. */
const TEXT: Text = {
  document_id: "fixture:b:1",
  source_id: "fixture",
  source_name_fa: "گنجور",
  author: "نویسنده",
  work: "کتاب",
  section: [],
  title: "حکایت",
  century: 7,
  corpus_version: "v22",
  lexicon_snapshot_id: "lexicon-fixture",
  units_total: 1,
  start: 0,
  limit: 200,
  behnevis: { sure: 0.9, mid: 0.7 },
  units: [
    {
      index: 0,
      number: 1,
      kind: "prose",
      lines: [
        {
          position: "prose",
          words: [
            {
              fa: "دل",
              s: "دل",
              auto: {
                latin: "Dal",
                confidence: 0.5,
                level: "unsure",
                source: "choice",
                candidates: [
                  ["Dal", 0.5],
                  ["Del", 0.4],
                ],
                known: [],
              },
            },
            { fa: "ما", s: "ما" },
          ],
        },
      ],
    },
  ],
  words: {
    دل: {
      readings: [
        { id: "دل:Dal", latin: "Dal", latin_variants: [], groups: [], definition_fa: null },
        { id: "دل:Del", latin: "Del", latin_variants: [], groups: [], definition_fa: null },
      ],
      total_count: 1000,
      doc_count: 500,
      function_word: null,
    },
    ما: { readings: [], total_count: 10, doc_count: 5, function_word: null },
  },
};

let listed: UnsureSpelling = LISTED;
let posted: { context: Record<string, unknown> }[] = [];

function answer(url: string): unknown {
  if (url.includes("/texts/unsure/")) return { spelling: "دل", listed, decided: [] };
  if (url.includes("/texts/unsure")) {
    return {
      meta: { corpus_version: "v22", words: 10000, unsure_words: 3300, metre: true, measured: "2026-11-21" },
      suggestions: listed.suggestion ? { made: "2026-11-22", spellings: 1, tested_words: 1200 } : null,
      total: 1,
      offset: 0,
      size: 50,
      spellings: [listed],
    };
  }
  if (url.includes("/texts/marked")) return { total: 0, offset: 0, returned: 0, marked: [] };
  return TEXT;
}

beforeEach(() => {
  listed = LISTED;
  posted = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      if (init?.method === "POST") {
        posted.push(JSON.parse(String(init.body)));
        return { ok: true, status: 201, statusText: "", json: async () => ({ id: 8 }) };
      }
      return { ok: true, status: 200, statusText: "", json: async () => answer(String(url)) };
    }),
  );
  Element.prototype.scrollIntoView = vi.fn();
});

describe("matching a suggestion to the offered readings", () => {
  it("compares without ezafe, case, accents or the mark for ع", () => {
    expect(folded("sar-e")).toBe("sar");
    expect(folded("xāne-ye")).toBe("xāne");
    expect(folded("Bahré")).toBe("bahre");
    expect(folded("ˈElm")).toBe("elm");
  });

  it("marks every offered reading that is the suggestion, in the panel's order", () => {
    const xod = { ...SUGGESTED, latin: "xod", matches: [] };
    expect(suggestedAmong(xod, ["Xod", "xvad", "xod"])).toEqual(["Xod", "xod"]);
    expect(suggestedAmong(SUGGESTED, ["Dal", "Del"])).toEqual(["Del"]);
  });

  it("picks the one offered reading, types the bank's spelling or the suggestion, else leaves it", () => {
    expect(takeUpOf(SUGGESTED, ["Dal", "Del"])).toEqual({ latin: "Del", how: "pick" });
    // Not among this line's readings, but the bank holds it: typed as the bank writes it.
    expect(takeUpOf(SUGGESTED, ["Dal"])).toEqual({ latin: "Del", how: "type" });
    const missing = { ...SUGGESTED, latin: "delam", matches: [], in_bank: false };
    expect(takeUpOf(missing, ["Dalam"])).toEqual({ latin: "delam", how: "type" });
    // Several are the suggestion: the person picks.
    expect(takeUpOf({ ...SUGGESTED, matches: ["Del", "del"] }, ["Del", "del"])).toBeNull();
  });

  it("reads its context and its place", () => {
    expect(contextOf("یک [دل] دو")).toEqual({ before: "یک", word: "دل", after: "دو" });
    expect(contextOf("[دل]")).toEqual({ before: "", word: "دل", after: "" });
    expect(contextOf("دل")).toBeNull();
    expect(outOf100(0.881)).toBe(88);
    expect(readHere(SUGGESTED, { document_id: "fixture:a:1", unit: 0, line: 0, word: 0 })).toBe(true);
    expect(readHere(SUGGESTED, { document_id: "fixture:a:1", unit: 0, line: 1, word: 0 })).toBe(false);
  });
});

async function openRow() {
  renderApp("/texts?view=unsure");
  const list = await screen.findByRole("region", { name: "پرتکرارترین واژه‌های نامطمئن" });
  const row = await within(list).findByRole("button", { name: /دل/ });
  return { list, row };
}

describe("the suggestion on the list", () => {
  it("shows the reading and its measured share in the row, and says what it is above the list", async () => {
    const { list, row } = await openRow();
    expect(row).toHaveTextContent("پیشنهاد خودکار: del (۸۸ از ۱۰۰)");
    expect(within(list).getByText(/کنار هر املا یک «پیشنهاد خودکار» هم آمده است/)).toBeInTheDocument();
  });

  it("marks the offered reading, picks it on a press, and saves only on the person's own press", async () => {
    const { list, row } = await openRow();
    await userEvent.click(row);
    const panel = within(list).getByRole("region", { name: "تصمیم دربارهٔ دل" });
    const box = within(panel).getByRole("region", { name: "پیشنهاد خودکار" });
    expect(box).toHaveTextContent("در آزمون، از هر ۱۰۰ پیشنهاد با این اطمینان ۸۸ تا درست بود.");
    expect(box).toHaveTextContent("این پیشنهاد از یک سطر آمده است: «یک دل دو».");
    expect(box).toHaveTextContent("در ۴۰ جا اعراب گذاشته‌اند و اعرابِ ۳۰ جا با این پیشنهاد جور است.");
    expect(within(box).getByText(/از کجا آمده/).closest("details")).toHaveTextContent(
      /روی ۱٬۲۰۰ واژهٔ اعراب‌دار/,
    );
    const del = within(panel).getByRole("radio", { name: /^Del/ });
    expect(del.closest("label")).toHaveTextContent("پیشنهاد خودکار");
    expect(within(panel).getByRole("radio", { name: "Dal" }).closest("label")).not.toHaveTextContent(
      "پیشنهاد خودکار",
    );
    // Nothing is chosen, let alone saved, before the person presses.
    expect(del).not.toBeChecked();
    expect(within(panel).getByText(/از این سطر است/)).toBeInTheDocument();
    await userEvent.click(within(box).getByRole("button", { name: "«Del» را برگزین" }));
    expect(del).toBeChecked();
    expect(posted).toHaveLength(0);
    await userEvent.click(within(panel).getByRole("button", { name: "ثبت «Del» برای همه‌جا" }));
    await within(panel).findByText(/برای همه‌جا ثبت شد/);
    expect(posted).toHaveLength(1);
    expect(posted[0]!.context).toEqual(
      expect.objectContaining({ kind: "reading_decided", latin: "Del", in_bank: true, scope: "everywhere" }),
    );
  });

  it("offers a reading no option holds to type, and it goes to karbon's list", async () => {
    listed = {
      ...LISTED,
      kind: "one",
      known: ["Dal"],
      read_as: [],
      offered: [],
      suggestion: { ...SUGGESTED, latin: "dol", matches: [], in_bank: false, marked: { checked: 9, fit: 2 } },
    };
    const { list, row } = await openRow();
    await userEvent.click(row);
    const panel = within(list).getByRole("region", { name: "تصمیم دربارهٔ دل" });
    const box = within(panel).getByRole("region", { name: "پیشنهاد خودکار" });
    expect(box).toHaveTextContent("با تنها خوانشِ بانک واژه (Dal) یکی نیست");
    expect(box).toHaveTextContent(/حرف نخستش را بزرگ کنید/);
    // The editions' signs fit it in fewer than half their places: said so.
    expect(within(box).getByText(/جور دیگری خوانده می‌شود/)).toHaveAttribute("data-weak", "true");
    await userEvent.click(within(box).getByRole("button", { name: "«dol» را در جای نوشتن بگذار" }));
    expect(within(panel).getByRole("textbox")).toHaveValue("dol");
    expect(posted).toHaveLength(0);
    await userEvent.click(within(panel).getByRole("button", { name: "ثبت «dol» برای همه‌جا" }));
    await waitFor(() => expect(posted).toHaveLength(1));
    expect(posted[0]!.context).toEqual(expect.objectContaining({ latin: "dol", in_bank: false }));
  });

  it("leaves the choice to the person where the suggestion cannot tell a capital", async () => {
    listed = { ...LISTED, known: ["Del", "del"], suggestion: { ...SUGGESTED, matches: ["Del", "del"] } };
    const { list, row } = await openRow();
    await userEvent.click(row);
    const box = within(list).getByRole("region", { name: "پیشنهاد خودکار" });
    expect(box).toHaveTextContent("میان Del و del فرق نمی‌گذارد");
    expect(within(box).queryByRole("button", { name: /برگزین|بگذار/ })).not.toBeInTheDocument();
  });

  it("does not repeat the marks where the panel already gives them for this reading", async () => {
    listed = { ...LISTED, marked: { fitted: 40, best: 30, none: 0, reading: "Del" } };
    const { list, row } = await openRow();
    await userEvent.click(row);
    const box = within(list).getByRole("region", { name: "پیشنهاد خودکار" });
    expect(box).not.toHaveTextContent("اعراب گذاشته‌اند");
    expect(within(list).getByText(/جایی که ویراستاران/)).toHaveTextContent("در ۴۰ جایی");
  });

  it("shows nothing where no suggestion was made", async () => {
    listed = { ...LISTED, suggestion: null };
    const { list, row } = await openRow();
    expect(row).not.toHaveTextContent("پیشنهاد خودکار");
    expect(within(list).queryByText(/کنار هر املا/)).not.toBeInTheDocument();
    await userEvent.click(row);
    expect(within(list).queryByRole("region", { name: "پیشنهاد خودکار" })).not.toBeInTheDocument();
  });
});

describe("the suggestion in the reading screen's word panel", () => {
  async function here() {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · حکایت" });
    await userEvent.click(within(text).getByRole("button", { name: /^دل:/ }));
    return within(text).getByRole("region", { name: "خوانش در این سطر" });
  }

  it("says it was read in another line, and is saved for this line only unless the reader says otherwise", async () => {
    const panel = await here();
    const box = await within(panel).findByRole("region", { name: "پیشنهاد خودکار" });
    expect(box).toHaveTextContent("این پیشنهاد برای سطر دیگری است: «یک دل دو». ببینید اینجا هم درست است یا نه.");
    expect(within(panel).getByRole("radio", { name: /^Del/ }).closest("label")).toHaveTextContent(
      "پیشنهاد خودکار",
    );
    await userEvent.click(within(box).getByRole("button", { name: "«Del» را برگزین" }));
    expect(within(panel).getByRole("radio", { name: /^Del/ })).toBeChecked();
    expect(within(panel).getByRole("radio", { name: "فقط همین‌جا" })).toBeChecked();
    expect(posted).toHaveLength(0);
  });

  it("says so where this is the line it was read in", async () => {
    listed = { ...LISTED, suggestion: { ...SUGGESTED, place: { document_id: "fixture:b:1", unit: 0, line: 0, word: 0 } } };
    const panel = await here();
    const box = await within(panel).findByRole("region", { name: "پیشنهاد خودکار" });
    expect(box).toHaveTextContent("این پیشنهاد برای همین سطر است");
  });
});
