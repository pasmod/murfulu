/**
 * Which readings are the bank's, and the list of those it lacks (2026-11-22).
 *
 * Which readings the bank holds and which rows the list has are the API's,
 * checked on the Python side. What is checked here is what a reader sees: a
 * star on a reading the bank does not hold and none on one it holds, the
 * line sent with a saved reading, and the list for karbon — two groups, a
 * row's line with its word marked, and the linguist's confirmation given and
 * taken back through the feedback store.
 *
 * Every line here is written for the test; no corpus text.
 */

import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { KarbonPage, KarbonRow } from "../../api/karbon";
import type { Text } from "../../api/texts";
import { renderApp, renderWithRouter } from "../../test/render";
import { Line } from "./ForKarbon";
import { lineText } from "./lines";

const reading = (id: string, latin: string) => ({
  id,
  latin,
  latin_variants: [],
  groups: [],
  definition_fa: null,
});

/** «دل و کنم»: the bank's reading, a function word's, and a guess. */
const TEXT: Text = {
  document_id: "fixture:k:1",
  source_id: "fixture",
  source_name_fa: "گنجور",
  author: "نویسنده",
  work: "کتاب",
  section: [],
  title: "حکایت",
  century: 7,
  corpus_version: "v22",
  lexicon_snapshot_id: "lexicon-20261111:e300dbc27083",
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
                latin: "Del",
                confidence: 0.96,
                level: "sure",
                source: "choice",
                candidates: [
                  ["Del", 0.96],
                  ["Dal", 0.04],
                ],
                known: ["Del", "Dal"],
                bank: ["Del", "Dal"],
              },
            },
            {
              fa: "و",
              s: "و",
              auto: {
                latin: "va",
                confidence: 0.9,
                level: "sure",
                source: "function",
                candidates: [["va", 0.9]],
                known: ["va", "o"],
                bank: [],
              },
            },
            {
              fa: "کنم",
              s: "کنم",
              after: ".",
              auto: {
                latin: "konam",
                confidence: 0.4,
                level: "unsure",
                source: "inflected",
                candidates: [["konam", 0.4]],
                known: [],
                bank: [],
              },
            },
            {
              // An API from before 2026-11-22 does not say what the bank holds.
              fa: "ما",
              s: "ما",
              auto: {
                latin: "mā",
                confidence: 0.9,
                level: "sure",
                source: "function",
                candidates: [["mā", 0.9]],
              },
            },
          ],
        },
      ],
    },
  ],
  words: {
    دل: {
      readings: [reading("دل:Dal", "Dal"), reading("دل:Del", "Del")],
      total_count: 100,
      doc_count: 50,
      function_word: null,
    },
    و: { readings: [], total_count: 900, doc_count: 90, function_word: "و" },
    کنم: { readings: [], total_count: 40, doc_count: 30, function_word: null },
    ما: { readings: [reading("ما:mā", "mā")], total_count: 70, doc_count: 60, function_word: null },
  },
};

const ARAD: KarbonRow = {
  spelling: "آرد",
  spelling_fa: "آرد",
  spelling_fa_marked: "آرَد",
  latin: "ārad",
  kind: "reading",
  bank: ["Ārd"],
  origin: "reader",
  times: 2,
  model: "Ārd",
  decided: [{ scope: "after_word", word: "دست" }],
  places: [
    {
      document_id: "fixture:a:1",
      unit: 4,
      line: 0,
      word: 2,
      heading: "نویسنده · کتاب",
      written: "آرد",
      before: "دست",
      after: "دل",
      text: "به دست آرد دل ما را",
    },
  ],
  examples: [],
  confirmed: null,
};

const KONAM: KarbonRow = {
  spelling: "کنم",
  spelling_fa: "کنم",
  latin: "konam",
  kind: "missing",
  bank: [],
  origin: "reader",
  times: 1,
  model: null,
  decided: [],
  // Saved before lines were sent: only the word and its neighbours.
  places: [
    {
      document_id: "fixture:a:2",
      unit: 0,
      line: 0,
      word: 1,
      heading: "نویسنده · دیوان",
      written: "کنم",
      before: "چه",
      after: "که",
      text: null,
    },
  ],
  examples: [],
  confirmed: null,
};

const VA: KarbonRow = {
  spelling: "و",
  spelling_fa: "و",
  latin: "va",
  kind: "missing",
  bank: [],
  origin: "function",
  times: 0,
  model: null,
  decided: [],
  places: [],
  examples: [
    {
      document_id: "fixture:b:1",
      unit: 1,
      line: 0,
      word: 1,
      heading: "نویسنده · گلستان",
      text: "این و آن",
    },
  ],
  confirmed: { id: 40, created_at: "2026-11-22T10:00:00+00:00" },
};

let rows: KarbonRow[] = [];
let posted: { verdict: string; target_id: string; context: Record<string, unknown> }[] = [];
let asked: string[] = [];
let noBank = false;

function page(url: string): KarbonPage {
  const state = url.includes("state=confirmed")
    ? "confirmed"
    : url.includes("state=open")
      ? "open"
      : "all";
  const chosen = rows.filter(
    (one) => state === "all" || (one.confirmed !== null) === (state === "confirmed"),
  );
  return {
    total: rows.length,
    confirmed: rows.filter((one) => one.confirmed).length,
    missing: rows.filter((one) => one.kind === "missing").length,
    state,
    matching: chosen.length,
    offset: 0,
    size: 50,
    rows: chosen,
  };
}

beforeEach(() => {
  rows = [ARAD, KONAM, VA];
  posted = [];
  asked = [];
  noBank = false;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      if (init?.method === "POST") {
        posted.push(JSON.parse(String(init.body)));
        return {
          ok: true,
          status: 201,
          statusText: "",
          json: async () => ({ id: 50 + posted.length, created_at: "2026-11-22T12:00:00+00:00" }),
        };
      }
      asked.push(String(url));
      if (String(url).includes("/texts/karbon")) {
        if (noBank) {
          return {
            ok: false,
            status: 503,
            statusText: "",
            json: async () => ({ detail: "the word bank is not available" }),
          };
        }
        return { ok: true, status: 200, statusText: "", json: async () => page(String(url)) };
      }
      if (String(url).includes("/texts/marked")) {
        return {
          ok: true,
          status: 200,
          statusText: "",
          json: async () => ({ total: 0, offset: 0, returned: 0, marked: [] }),
        };
      }
      if (String(url).includes("/texts/unsure/")) {
        return {
          ok: true,
          status: 200,
          statusText: "",
          json: async () => ({ spelling: "کنم", listed: null, decided: [] }),
        };
      }
      return { ok: true, status: 200, statusText: "", json: async () => TEXT };
    }),
  );
  Element.prototype.scrollIntoView = vi.fn();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("which readings are the bank's", () => {
  it("stars a reading the bank does not hold, and no other", async () => {
    renderApp("/texts?text=fixture%3Ak%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · حکایت" });
    const held = within(text).getByRole("button", { name: /^دل:/ });
    expect(held).not.toHaveAttribute("data-held");
    expect(held).not.toHaveTextContent("*");
    expect(held).toHaveAccessibleName("دل: Del، مطمئن (۹۶٪)");

    // A function word's own reading is this project's, not the bank's.
    const va = within(text).getByRole("button", { name: /^و:/ });
    expect(va).toHaveAttribute("data-held", "no");
    expect(va).toHaveTextContent("va*");
    expect(va).toHaveAccessibleName("و: va، مطمئن (۹۰٪)، در بانک واژه نیست");

    // A guess, whatever its level.
    const guess = within(text).getByRole("button", { name: /^کنم:/ });
    expect(guess).toHaveTextContent("konam*");

    // Where the API does not say what the bank holds, nothing is starred.
    expect(within(text).getByRole("button", { name: /^ما:/ })).not.toHaveTextContent("*");
  });

  it("says what the star means, with the way to the list", async () => {
    renderApp("/texts?text=fixture%3Ak%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · حکایت" });
    const legend = within(text).getByText(/ستاره یعنی این خوانش در بانک واژه/);
    expect(legend).toHaveTextContent("خوانشِ بی‌ستاره در بانک واژه هست.");
    expect(within(legend).getByRole("link")).toHaveAttribute("href", "/texts?view=karbon");
  });

  it("says it in the word's panel too, and sends the line with a saved reading", async () => {
    renderApp("/texts?text=fixture%3Ak%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · حکایت" });
    await userEvent.click(within(text).getByRole("button", { name: /^دل:/ }));
    expect(
      within(screen.getByRole("region", { name: "خوانش‌های دل" })).queryByText(/ثبت\s+نشده است/),
    ).toBeNull();

    await userEvent.click(within(text).getByRole("button", { name: /^کنم:/ }));
    const panel = screen.getByRole("region", { name: "خوانش‌های کنم" });
    expect(within(panel).getByText(/ثبت\s+نشده است/)).toHaveTextContent(
      /خوانشِ konam در بانک واژه \(کاربن\) ثبت\s+نشده است؛ برنامه آن را خودش ساخته است\./,
    );
    await userEvent.type(within(panel).getByRole("textbox"), "konom");
    await userEvent.click(within(panel).getByRole("button", { name: /^ثبت/ }));
    await waitFor(() => expect(posted).toHaveLength(1));
    expect(posted[0]!.context).toMatchObject({
      kind: "reading_here",
      latin: "konom",
      line_text: "دل و کنم. ما",
      line: 0,
      word: 2,
    });
  });

  it("joins a line's words as the screen counts them", () => {
    expect(lineText([{ fa: "«", s: null }, { fa: "دل", s: "دل", after: "»" }])).toBe("« دل»");
    expect(lineText([])).toBe("");
  });
});

describe("the list of readings the bank lacks", () => {
  it("is reached from the reading screen's first page", async () => {
    renderApp("/texts");
    expect(
      await screen.findByRole("link", { name: /خوانش‌هایی که کاربن ندارد را ببینید/ }),
    ).toHaveAttribute("href", "/texts?view=karbon");
  });

  it("groups the readings by what the bank lacks, each with its line", async () => {
    renderApp("/texts?view=karbon");
    const list = await screen.findByRole("region", { name: "خوانش‌هایی که کاربن ندارد" });
    expect(await within(list).findByText(/تای آن تأیید شده/)).toHaveTextContent(
      "۳ خوانش؛ ۱ تای آن تأیید شده است.",
    );
    const missing = within(list).getByRole("region", { name: /^املا در بانک واژه نیست/ });
    expect(within(missing).getAllByRole("listitem")).not.toHaveLength(0);
    expect(missing).toHaveTextContent("konam");
    expect(missing).toHaveTextContent("واژهٔ دستوری");

    const held = within(list).getByRole("region", { name: /^املا هست، این خوانش نیست/ });
    // The word with its short vowels, what the bank has, and the line.
    expect(held).toHaveTextContent("آرَد");
    expect(held).toHaveTextContent("۲ بار ثبت شده");
    expect(within(held).getByText(/بانک واژه برای این املا دارد/)).toHaveTextContent("Ārd");
    expect(held).toHaveTextContent("هر جا پس از «دست»");
    expect(within(held).getByText("آرد").tagName).toBe("MARK");
    expect(within(held).getByRole("link", { name: "در متن ←" })).toHaveAttribute(
      "href",
      "/texts?text=fixture%3Aa%3A1&unit=4&word=%D8%A2%D8%B1%D8%AF",
    );
    // Without its line, the word between its neighbours, cut on both sides.
    const marked = (text: string) =>
      within(missing)
        .getAllByText(text)
        .find((one) => one.tagName === "MARK");
    expect(marked("کنم")?.parentElement).toHaveTextContent("… چه کنم که …");
    // A row with no place of its own borrows a line from the corpus.
    expect(within(missing).getByText(/چند جا از پیکره/)).toBeInTheDocument();
    expect(marked("و")?.parentElement).toHaveTextContent("این و آن");
  });

  it("records the linguist's confirmation, and takes one back", async () => {
    renderApp("/texts?view=karbon");
    const list = await screen.findByRole("region", { name: "خوانش‌هایی که کاربن ندارد" });
    await userEvent.click(
      await within(list).findByRole("button", { name: "زبان‌شناس آرد ārad را تأیید می‌کند" }),
    );
    await waitFor(() => expect(posted).toHaveLength(1));
    expect(posted[0]).toMatchObject({
      verdict: "good",
      target_id: "آرد:ārad",
      context: {
        screen: "texts",
        kind: "reading_confirmed",
        spelling_fa: "آرد",
        latin: "ārad",
        withdrawn: false,
        gap: "reading",
        bank: ["Ārd"],
      },
    });
    await waitFor(() =>
      expect(within(list).getByText(/تای آن تأیید شده/)).toHaveTextContent("۲ تای آن"),
    );
    // The new confirmation names itself when it is taken back.
    await userEvent.click(
      within(list).getByRole("button", { name: "برداشتن تأیید آرد ārad" }),
    );
    await waitFor(() => expect(posted).toHaveLength(2));
    expect(posted[1]).toMatchObject({
      verdict: "unsure",
      context: { kind: "reading_confirmed", withdrawn: true, replaces: 51 },
    });
    await waitFor(() =>
      expect(within(list).getByText(/تای آن تأیید شده/)).toHaveTextContent("۱ تای آن"),
    );

    // One confirmed before this visit says when, and can be taken back too.
    expect(within(list).getByText(/زبان‌شناس تأیید کرده است/)).toHaveTextContent("۱۴۰۵");
    await userEvent.click(within(list).getByRole("button", { name: "برداشتن تأیید و va" }));
    await waitFor(() => expect(posted).toHaveLength(3));
    expect(posted[2]!.context).toMatchObject({ withdrawn: true, replaces: 40 });
  });

  it("filters by what is confirmed", async () => {
    renderApp("/texts?view=karbon");
    const list = await screen.findByRole("region", { name: "خوانش‌هایی که کاربن ندارد" });
    await userEvent.click(await within(list).findByRole("button", { name: "تأییدشده" }));
    await waitFor(() => expect(asked.some((url) => url.includes("state=confirmed"))).toBe(true));
    await waitFor(() => expect(within(list).queryByText("konam")).toBeNull());
    expect(within(list).getByText("va")).toBeInTheDocument();
    rows = [ARAD];
    await userEvent.click(within(list).getByRole("button", { name: "همه" }));
    await userEvent.click(within(list).getByRole("button", { name: "تأییدشده" }));
    expect(await within(list).findByText("هنوز هیچ خوانشی تأیید نشده است.")).toBeInTheDocument();
  });

  it("says so when the bank cannot be read", async () => {
    noBank = true;
    renderApp("/texts?view=karbon");
    expect(await screen.findByRole("status")).toHaveTextContent("بانک واژه در دسترس نیست");
  });

  it("marks the word in a line by its place, and leaves a line it cannot find it in", () => {
    renderWithRouter(<Line text="یک دلِ دو دل" at={3} target="دل" />);
    expect(screen.getByText("دل").tagName).toBe("MARK");
    expect(screen.getByText("دل").parentElement).toHaveTextContent("یک دلِ دو دل");
    // Without a place, the first word that matches; punctuation and marks aside.
    renderWithRouter(<Line text="«آرَد» را" at={null} target="آرد" />);
    expect(screen.getByText("«آرَد»").tagName).toBe("MARK");
    // A longer word that holds its letters is not it.
    renderWithRouter(<Line text="این دلداده است" at={1} target="دل" />);
    expect(screen.getByText("این دلداده است").querySelector("mark")).toBeNull();
  });
});
