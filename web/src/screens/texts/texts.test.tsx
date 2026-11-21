/**
 * The reading screen.
 *
 * Which words a line holds, and what the bank says of each, is the API's and
 * checked on the Python side. What is checked here is what the reader sees:
 * every reading under its word with none proposed, «؟» and never "not a
 * word", the panel's count and its way into the bank, a citation opening the
 * text at its line, and a reading marked wrong through the feedback store.
 *
 * Every line here is written for the test; no corpus text.
 */

import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Decision, Marked, Text, TextFound, UnsureSpelling } from "../../api/texts";
import { renderApp, renderWithRouter } from "../../test/render";
import { markedFor } from "./levels";
import { newest, placeSaved } from "./Reader";
import { ExampleLine } from "./Unsure";

const TEXT: Text = {
  document_id: "fixture:a:1",
  source_id: "fixture",
  source_name_fa: "گنجور",
  author: "نویسنده",
  work: "کتاب",
  section: ["باب نخست"],
  title: "حکایت یکم",
  century: 7,
  corpus_version: "v17",
  lexicon_snapshot_id: "lexicon-20261111:e300dbc27083",
  units_total: 4,
  start: 0,
  limit: 200,
  units: [
    {
      index: 0,
      number: 1,
      kind: "couplet",
      lines: [
        { position: "first", words: [{ fa: "دلِ", s: "دل" }, { fa: "ما", s: "ما" }] },
        { position: "second", words: [{ fa: "رفتند", s: "رفتند", after: "،" }] },
      ],
    },
    { index: 1, number: null, kind: "note", lines: [{ position: "note", text: "یادداشت گردآورنده" }] },
    {
      index: 2,
      number: 2,
      kind: "prose",
      lines: [{ position: "prose", words: [{ fa: "«", s: null }, { fa: "دل", s: "دل", after: "»" }] }],
    },
    {
      index: 3,
      number: 3,
      kind: "half",
      lines: [
        {
          position: "free",
          words: [
            { fa: "ما", s: "ما" },
            // A kasra on the first letter: Dal and dall are ruled out.
            { fa: "دِل", s: "دل", against: ["دل:Dal", "دل:dall"] },
          ],
        },
      ],
    },
  ],
  words: {
    دل: {
      readings: [
        { id: "دل:Dal", latin: "Dal", latin_variants: [], groups: ["نام"], definition_fa: null },
        { id: "دل:dall", latin: "dall", latin_variants: [], groups: ["برنام"], definition_fa: null },
        { id: "دل:Del", latin: "Del", latin_variants: [], groups: ["نام"], definition_fa: "قلب." },
      ],
      total_count: 148697,
      doc_count: 65807,
      function_word: null,
    },
    ما: {
      readings: [{ id: "ما:mā", latin: "mā", latin_variants: [], groups: [], definition_fa: null }],
      total_count: 115948,
      doc_count: 40000,
      function_word: null,
    },
    رفتند: { readings: [], total_count: 5000, doc_count: 3000, function_word: null },
  },
};

const FOUND: TextFound = {
  q: "کتاب",
  total: 1,
  offset: 0,
  size: 20,
  corpus_version: "v17",
  texts: [
    {
      document_id: "fixture:a:1",
      author: "نویسنده",
      work: "کتاب",
      section: ["باب نخست"],
      title: "حکایت یکم",
      century: 7,
    },
  ],
};

const MARKED: Marked = {
  id: 7,
  target_id: "دل:Dol",
  spelling_fa: "دل",
  latin: "Dol",
  written: "دلِ",
  document_id: "fixture:a:1",
  unit: 0,
  heading: "نویسنده · کتاب · حکایت یکم",
  note: "در این بیت دل است",
  corpus_version: "v17",
  created_at: "2026-11-13T12:00:00+00:00",
};

let posted: unknown[] = [];

/** Marked before this visit: Del, on دل — the panel asks for it by spelling. */
const EARLIER: Marked = { ...MARKED, id: 3, target_id: "دل:Del", latin: "Del", note: null };

/** The same text with the automatic Behnevis on (direction A, 2026-11-14). */
const AUTO: Text = {
  ...TEXT,
  document_id: "fixture:b:1",
  words: {
    ...TEXT.words,
    دل: {
      ...TEXT.words["دل"]!,
      readings: TEXT.words["دل"]!.readings.map((one) =>
        one.latin === "Del" ? { ...one, latin_variants: ["Dil"] } : one,
      ),
    },
  },
  behnevis: { sure: 0.9, mid: 0.7 },
  units: [
    {
      index: 0,
      number: 1,
      kind: "couplet",
      lines: [
        {
          position: "first",
          words: [
            {
              fa: "دلِ",
              s: "دل",
              auto: {
                latin: "Del",
                fa_marked: "دِلِ",
                confidence: 0.96,
                level: "sure",
                source: "choice",
                candidates: [
                  ["Del", 0.96],
                  ["Dal", 0.03],
                  ["Dil", 0.01],
                ],
              },
            },
            {
              fa: "رفتند",
              s: "رفتند",
              auto: {
                latin: "raftand",
                confidence: 0.4,
                level: "unsure",
                source: "inflected",
                candidates: [
                  ["raftand", 0.4],
                  ["roftand", null],
                ],
                known: [],
              },
            },
          ],
        },
        {
          position: "second",
          words: [
            {
              fa: "و",
              s: "و",
              auto: {
                latin: "o",
                confidence: 0.8,
                level: "mid",
                source: "function",
                candidates: [
                  ["o", 0.8],
                  ["va", 0.2],
                ],
                // The function-word list holds both: the bank has neither.
                known: ["va", "o"],
              },
            },
          ],
        },
      ],
    },
  ],
};

/** Readings saved for this text before the visit, newest first. */
let saved: Marked[] = [];

/** The review list of readings marked wrong. */
let review: Marked[] = [MARKED];

/**
 * A text with the automatic Behnevis off, where the bank reads نثر one way
 * only and دل three ways: only نثر is given its short vowels (2026-11-21).
 */
const VOWELS: Text = {
  ...TEXT,
  document_id: "fixture:c:1",
  units: [
    {
      index: 0,
      number: 1,
      kind: "prose",
      lines: [
        {
          position: "prose",
          words: [
            { fa: "نثر", s: "نثر", fa_marked: "نَثر" },
            { fa: "دل", s: "دل" },
          ],
        },
      ],
    },
  ],
  words: {
    ...TEXT.words,
    نثر: {
      readings: [{ id: "نثر:nasr", latin: "nasr", latin_variants: [], groups: [], definition_fa: null }],
      total_count: 30,
      doc_count: 20,
      function_word: null,
    },
  },
};

/** The measured list of unsure spellings, and what was decided for دل (2026-11-21). */
const UNSURE: UnsureSpelling = {
  rank: 1,
  spelling: "دل",
  written: "دل",
  places: 1000,
  unsure: 600,
  kind: "choice",
  known: ["Dal", "Del", "dall"],
  read_as: [
    ["Del", 400],
    ["Dal", 200],
  ],
  offered: [
    ["Del", 600],
    ["Dal", 600],
    ["Dol", 100],
  ],
  before: [["ما", 120, 80]],
  after: [
    ["رفتند", 50, 40],
    ["ما", 30, 10],
  ],
  examples: [
    {
      document_id: "fixture:a:1",
      unit: 0,
      line: 0,
      word: 0,
      heading: "نویسنده · کتاب · حکایت یکم",
      text: "دلِ ما",
    },
  ],
  marked: { fitted: 40, best: 24, none: 2, reading: "Del" },
  decided: [],
};

let decided: Decision[] = [];
let listGone = false;

function answer(url: string): unknown {
  if (url.includes("/texts/unsure/")) {
    return { spelling: "دل", listed: url.includes("%D8%AF%D9%84") ? UNSURE : null, decided };
  }
  if (url.includes("/texts/unsure")) {
    const missing = url.includes("kind=missing");
    const rows = missing ? [] : [{ ...UNSURE, decided }];
    return {
      meta: { corpus_version: "v22", words: 10000, unsure_words: 3300, metre: true, measured: "2026-11-21" },
      total: rows.length,
      offset: 0,
      size: 50,
      spellings: rows,
    };
  }
  if (url.includes("/texts/marked") && url.includes("kind=proposed")) {
    return { total: saved.length, offset: 0, returned: saved.length, marked: saved };
  }
  if (url.includes("/texts/marked") && url.includes("spelling=")) {
    return { total: 1, offset: 0, returned: 1, marked: [EARLIER] };
  }
  if (url.includes("/texts/marked")) {
    return { total: review.length, offset: 0, returned: review.length, marked: review };
  }
  if (url.includes("fixture%3Ab%3A1") || url.includes("fixture:b:1")) return AUTO;
  if (url.includes("fixture%3Ac%3A1") || url.includes("fixture:c:1")) return VOWELS;
  if (url.includes("/texts/")) return TEXT;
  return FOUND;
}

beforeEach(() => {
  posted = [];
  saved = [];
  review = [MARKED];
  decided = [];
  listGone = false;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      if (init?.method === "POST") {
        posted.push(JSON.parse(String(init.body)));
        return { ok: true, status: 201, statusText: "", json: async () => ({ id: 8 }) };
      }
      if (listGone && String(url).includes("/texts/unsure?")) {
        return {
          ok: false,
          status: 503,
          statusText: "",
          json: async () => ({ detail: "the list of unsure spellings has not been measured" }),
        };
      }
      return { ok: true, status: 200, statusText: "", json: async () => answer(String(url)) };
    }),
  );
  Element.prototype.scrollIntoView = vi.fn();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

async function openText(route = "/texts?text=fixture%3Aa%3A1") {
  renderApp(route);
  return screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
}

describe("the reading screen", () => {
  it("says where the text is from, with the corpus version", async () => {
    const text = await openText();
    expect(within(text).getByRole("link", { name: "نویسنده" })).toHaveAttribute(
      "href",
      "/texts?q=%D9%86%D9%88%DB%8C%D8%B3%D9%86%D8%AF%D9%87",
    );
    expect(within(text).getByText("v17")).toBeInTheDocument();
    expect(within(text).getByText(/از گنجور/)).toBeInTheDocument();
  });

  it("puts every reading under its word, all alike, and proposes none", async () => {
    const text = await openText();
    const word = within(text).getAllByRole("button", { name: /^دلِ:/ })[0]!;
    expect(word).toHaveAttribute("data-state", "several");
    expect(within(word).getAllByText(/^(Dal|dall|Del)$/).map((one) => one.textContent)).toEqual([
      "Dal",
      "dall",
      "Del",
    ]);
    expect(within(text).queryByText(/پیشنهاد شده$/)).not.toBeInTheDocument();
  });

  it("shows the readings the word's own harakat rule out paler, and says why", async () => {
    const text = await openText();
    const word = within(text).getByRole("button", { name: /^دِل:/ });
    expect(word).toHaveAccessibleName("دِل: Del؛ اعراب متن با Dal، dall جور نیست");
    const pale = within(word)
      .getAllByText(/^(Dal|dall|Del)$/)
      .filter((one) => one.className.includes("ruledOut"))
      .map((one) => one.textContent);
    expect(pale).toEqual(["Dal", "dall"]);
    // The same spelling without signs keeps every reading alike.
    const plain = within(text).getAllByRole("button", { name: /^دلِ:/ })[0]!;
    expect(plain.querySelector("[class*=ruledOut]")).toBeNull();
    expect(within(text).getByText(/اعرابی\s+که در خود متن آمده با این خوانش جور نیست/)).toBeInTheDocument();

    await userEvent.click(word);
    const panel = within(text).getByRole("region", { name: "خوانش‌های دِل" });
    expect(within(panel).getAllByText("با اعراب متن جور نیست")).toHaveLength(2);
  });

  it("shows «؟» for a word the bank does not read, and never says it is not a word", async () => {
    const text = await openText();
    const word = within(text).getByRole("button", { name: /^رفتند:/ });
    expect(word).toHaveAttribute("data-state", "none");
    expect(within(word).getByText("؟")).toBeInTheDocument();
    await userEvent.click(word);
    const panel = within(text).getByRole("region", { name: "خوانش‌های رفتند" });
    expect(within(panel).getByText(/خوانشی ندارد/)).toBeInTheDocument();
    expect(panel.textContent).not.toMatch(/وجود ندارد|واژه نیست/);
    expect(within(panel).getByRole("link", { name: /جست‌وجوی این املا/ })).toHaveAttribute(
      "href",
      "/bank?q=%D8%B1%D9%81%D8%AA%D9%86%D8%AF",
    );
  });

  it("opens a word's panel with all readings, the count and the bank", async () => {
    const text = await openText();
    await userEvent.click(within(text).getAllByRole("button", { name: /^دلِ:/ })[0]!);
    const panel = within(text).getByRole("region", { name: "خوانش‌های دلِ" });
    expect(panel.textContent).toMatch(/۳ خوانش دارد/);
    expect(within(panel).getByText(/نمی‌گوییم کدام در این سطر درست است/)).toBeInTheDocument();
    // Del was marked before this visit, so only Dal and dall offer the mark.
    expect(await within(panel).findByText(/علامتِ «نادرست» خورده/)).toBeInTheDocument();
    expect(within(panel).getAllByRole("button", { name: "این خوانش نادرست است" })).toHaveLength(2);
    expect(panel.textContent).toMatch(/۱۴۸٬۶۹۷ بار در ۶۵٬۸۰۷ متن/);
    expect(within(panel).getByRole("link", { name: /این واژه در بانک واژه/ })).toHaveAttribute(
      "href",
      "/bank?q=%D8%AF%D9%84&exact=1",
    );
  });

  it("keeps a note as text, unnumbered and not split into words", async () => {
    const text = await openText();
    const note = within(text).getByText("یادداشت گردآورنده").closest("li")!;
    expect(within(note).queryAllByRole("button")).toHaveLength(0);
    expect(within(note).getByText("یادداشت سرچشمه")).toBeInTheDocument();
  });

  it("opens a citation at its line, with the word marked", async () => {
    const text = await openText("/texts?text=fixture%3Aa%3A1&unit=2&word=%D8%AF%D9%84");
    const unit = within(text).getByText(/شاهدمثالِ «دل» از همین سطر است/).closest("li")!;
    expect(unit).toHaveAttribute("id", "unit-2");
    expect(within(unit).getByRole("button", { name: /^دل:/ })).toHaveAttribute("data-sought", "true");
    expect(Element.prototype.scrollIntoView).toHaveBeenCalled();
  });

  it("marks a reading wrong only after asking, through the feedback store", async () => {
    const text = await openText();
    await userEvent.click(within(text).getAllByRole("button", { name: /^دلِ:/ })[0]!);
    const panel = within(text).getByRole("region", { name: "خوانش‌های دلِ" });
    const dall = within(panel).getByText("dall").closest("li")!;
    await userEvent.click(within(dall).getByRole("button", { name: "این خوانش نادرست است" }));
    expect(posted).toHaveLength(0);
    expect(within(dall).getByText(/دیگر نمی‌شود پاکش کرد/)).toBeInTheDocument();
    await userEvent.type(within(dall).getByRole("textbox"), "اینجا dil نیست");
    await userEvent.click(within(dall).getByRole("button", { name: "ثبت کن" }));
    expect(posted).toEqual([
      expect.objectContaining({
        category: "linguistic",
        target_type: "lexicon_entry",
        target_id: "دل:dall",
        verdict: "wrong",
        note: "اینجا dil نیست",
        corpus_version: "v17",
        context: expect.objectContaining({
          screen: "texts",
          spelling_fa: "دل",
          latin: "dall",
          written: "دلِ",
          document_id: "fixture:a:1",
          unit: 0,
        }),
      }),
    ]);
    expect(await within(dall).findByText(/علامتِ «نادرست» خورده/)).toBeInTheDocument();
  });

  it("finds texts by their heading and lists the marked readings for review", async () => {
    renderApp("/texts");
    const marks = await screen.findByRole("region", { name: "خوانش‌هایی که علامتِ «نادرست» خورده‌اند" });
    expect(within(marks).getByText("Dol")).toBeInTheDocument();
    expect(within(marks).getByText("در این بیت دل است")).toBeInTheDocument();
    expect(within(marks).getByRole("link", { name: /همان سطر/ })).toHaveAttribute(
      "href",
      "/texts?text=fixture%3Aa%3A1&unit=0&word=%D8%AF%D9%84",
    );

    await userEvent.type(screen.getByRole("combobox", { name: "متنی را باز کنید" }), "کتاب");
    await userEvent.click(screen.getByRole("button", { name: "باز کن" }));
    expect(
      await screen.findByRole("link", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" }),
    ).toBeInTheDocument();
  });

  it("shows one reading under each word, drawn by how sure the model is", async () => {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    const sure = within(text).getByRole("button", { name: /^دلِ: Del، مطمئن/ });
    expect(sure).toHaveAttribute("data-level", "sure");
    expect(within(sure).queryByText("Dal")).not.toBeInTheDocument();
    const unsure = within(text).getByRole("button", { name: /^رفتند: raftand، نامطمئن/ });
    expect(unsure).toHaveAttribute("data-level", "unsure");
    expect(within(text).getByText(/نامطمئن: کمتر از/)).toBeInTheDocument();
  });

  it("collects a typed reading as a proposal for karbon, and changes nothing", async () => {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    await userEvent.click(within(text).getByRole("button", { name: /^رفتند:/ }));
    const here = within(text).getByRole("region", { name: "خوانش در این سطر" });
    const send = within(here).getByRole("button", { name: /^ثبت/ });
    expect(send).toBeDisabled();
    await userEvent.type(within(here).getByRole("textbox"), "raftand");
    await userEvent.clear(within(here).getByRole("textbox"));
    await userEvent.type(within(here).getByRole("textbox"), "raftaand");
    await userEvent.click(send);
    expect(await within(here).findByText(/ثبت شد/)).toBeInTheDocument();
    expect(posted).toEqual([
      expect.objectContaining({
        target_type: "lexicon_entry",
        target_id: "رفتند:raftaand",
        verdict: "good",
        context: expect.objectContaining({
          kind: "reading_here",
          latin: "raftaand",
          in_bank: false,
          model_latin: "raftand",
          model_confidence: 0.4,
          written: "رفتند",
          before: "دل",
          after: null,
        }),
      }),
    ]);
  });

  it("lets a reader pick one of the offered readings instead", async () => {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    await userEvent.click(within(text).getByRole("button", { name: /^دلِ:/ }));
    const here = within(text).getByRole("region", { name: "خوانش در این سطر" });
    const dal = within(here).getByRole("radio", { name: /Dal/ });
    await userEvent.click(dal);
    expect(dal).toBeChecked();
    await userEvent.click(within(here).getByRole("button", { name: "ثبت «Dal»" }));
    await within(here).findByText(/ثبت شد/);
    expect(posted[0]).toEqual(
      expect.objectContaining({
        target_id: "دل:Dal",
        context: expect.objectContaining({ in_bank: true }),
      }),
    );
  });

  it("starts a fresh form for each word, so a pick never travels", async () => {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    await userEvent.click(within(text).getByRole("button", { name: /^دلِ:/ }));
    let here = within(text).getByRole("region", { name: "خوانش در این سطر" });
    await userEvent.click(within(here).getByRole("radio", { name: /Dal/ }));
    await userEvent.click(within(text).getByRole("button", { name: /^رفتند:/ }));
    here = within(text).getByRole("region", { name: "خوانش در این سطر" });
    expect(within(here).getByRole("button", { name: "ثبت" })).toBeDisabled();
    expect(posted).toEqual([]);
  });

  it("counts a variant as the bank's own reading", async () => {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    await userEvent.click(within(text).getByRole("button", { name: /^دلِ:/ }));
    const here = within(text).getByRole("region", { name: "خوانش در این سطر" });
    await userEvent.click(within(here).getByRole("radio", { name: /Dil/ }));
    await userEvent.click(within(here).getByRole("button", { name: "ثبت «Dil»" }));
    await within(here).findByText(/ثبت شد/);
    expect(posted[0]).toEqual(
      expect.objectContaining({ context: expect.objectContaining({ latin: "Dil", in_bank: true }) }),
    );
  });

  it("offers alternatives without an estimate where none was measured", async () => {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    await userEvent.click(within(text).getByRole("button", { name: /^رفتند:/ }));
    const here = within(text).getByRole("region", { name: "خوانش در این سطر" });
    const built = within(here).getByRole("radio", { name: "roftand" }).closest("label");
    expect(built).not.toHaveTextContent("٪");
    const measured = within(here).getByRole("radio", { name: /raftand/ }).closest("label");
    expect(measured).toHaveTextContent("٪");
  });

  it("lets a reader pick or type, never both, and says which will be saved", async () => {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    await userEvent.click(within(text).getByRole("button", { name: /^دلِ:/ }));
    const here = within(text).getByRole("region", { name: "خوانش در این سطر" });
    const dal = within(here).getByRole("radio", { name: /Dal/ });
    const field = within(here).getByRole("textbox");
    await userEvent.click(dal);
    expect(within(here).getByText(/ثبت می‌شود/)).toHaveTextContent(/Dal.*برگزیده/);
    // Typing clears the pick …
    await userEvent.type(field, "Dol");
    expect(dal).not.toBeChecked();
    const readings = within(here).getByRole("group", { name: "یکی را برگزینید:" });
    expect(within(readings).queryAllByRole("radio", { checked: true })).toHaveLength(0);
    expect(within(here).getByText(/ثبت می‌شود/)).toHaveTextContent(/Dol.*نوشتهٔ شما/);
    // … and picking clears what was typed.
    await userEvent.click(within(here).getByRole("radio", { name: /Del/ }));
    expect(field).toHaveValue("");
    expect(within(here).getByRole("button", { name: "ثبت «Del»" })).toBeEnabled();
    expect(posted).toEqual([]);
  });

  it("shows a saved reading under its word, with a check mark", async () => {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    await userEvent.click(within(text).getByRole("button", { name: /^دلِ:/ }));
    const here = within(text).getByRole("region", { name: "خوانش در این سطر" });
    await userEvent.click(within(here).getByRole("radio", { name: /Dal/ }));
    await userEvent.click(within(here).getByRole("button", { name: "ثبت «Dal»" }));
    expect(await within(here).findByText(/برنامه این خوانش را می‌شناسد/)).toBeInTheDocument();
    const word = within(text).getByRole("button", { name: "دلِ: Dal، ثبت‌شده" });
    expect(word).toHaveAttribute("data-level", "mine");
    expect(word).toHaveTextContent("✓");
    expect(posted[0]).toEqual(
      expect.objectContaining({
        context: expect.objectContaining({ unit: 0, line: 0, word: 0, before: null, after: "رفتند" }),
      }),
    );
  });

  it("shows readings saved before the visit under their words", async () => {
    const row: Marked = {
      ...MARKED,
      id: 20,
      target_id: "دل:Dal",
      latin: "Dal",
      written: "دلِ",
      unit: 0,
      line: 0,
      word: 0,
      in_bank: true,
    };
    // An older proposal names no place: found by spelling and neighbours.
    const older: Marked = {
      ...MARKED,
      id: 19,
      target_id: "رفتند:raftaand",
      spelling_fa: "رفتند",
      latin: "raftaand",
      written: "رفتند",
      unit: 0,
      before: "دل",
      after: null,
      in_bank: false,
    };
    saved = [row, older, { ...row, id: 18, latin: "Del" }];
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    // The newest wins.
    expect(await within(text).findByRole("button", { name: "دلِ: Dal، ثبت‌شده" })).toBeInTheDocument();
    expect(within(text).getByRole("button", { name: "رفتند: raftaand، ثبت‌شده" })).toBeInTheDocument();
    await userEvent.click(within(text).getByRole("button", { name: /^دلِ:/ }));
    const here = within(text).getByRole("region", { name: "خوانش در این سطر" });
    expect(within(here).getByText(/پیش‌تر برای این سطر .*ثبت شده است/)).toHaveTextContent("Dal");
  });

  it("learns a function word's own reading rather than sending it to karbon", async () => {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    await userEvent.click(within(text).getByRole("button", { name: /^و:/ }));
    const here = within(text).getByRole("region", { name: "خوانش در این سطر" });
    await userEvent.click(within(here).getByRole("radio", { name: /va/ }));
    expect(within(here).getByText(/ثبت می‌شود/)).toHaveTextContent(/می‌شناسد/);
    await userEvent.click(within(here).getByRole("button", { name: "ثبت «va»" }));
    await within(here).findByText(/ثبت شد/);
    expect(posted[0]).toEqual(
      expect.objectContaining({ context: expect.objectContaining({ latin: "va", in_bank: true }) }),
    );
  });

  it("moves the pick with the arrow keys, as radio buttons do", async () => {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    await userEvent.click(within(text).getByRole("button", { name: /^دلِ:/ }));
    const here = within(text).getByRole("region", { name: "خوانش در این سطر" });
    await userEvent.click(within(here).getByRole("radio", { name: /Del/ }));
    await userEvent.keyboard("{ArrowDown}");
    expect(within(here).getByRole("radio", { name: /Dal/ })).toBeChecked();
    expect(within(here).getByRole("button", { name: "ثبت «Dal»" })).toBeEnabled();
  });
});

describe("the short vowels on the reading screen", () => {
  it("marks a word the bank reads one way, and leaves a word of several readings plain", async () => {
    renderApp(`/texts?text=fixture%3Ac%3A1&unit=0&word=${encodeURIComponent("نثر")}`);
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    // The label, the keys and the sought word stay on the plain spelling.
    const one = within(text).getByRole("button", { name: /^نثر: nasr$/ });
    expect(one).toHaveTextContent("نَثر");
    expect(one).toHaveAttribute("data-sought", "true");
    const several = within(text).getByRole("button", { name: /^دل:/ });
    expect(several).toHaveAttribute("data-state", "several");
    expect(several).toHaveTextContent(/^دل/);
  });

  it("marks a word with the model's one reading", async () => {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    const word = within(text).getByRole("button", { name: /^دلِ: Del، مطمئن/ });
    expect(word).toHaveTextContent(/^دِلِ/);
    // No marks sent: as written.
    expect(within(text).getByRole("button", { name: /^رفتند:/ })).toHaveTextContent(/^رفتند/);
  });

  it("never shows the model's vowels under another reading picked here", async () => {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    await userEvent.click(within(text).getByRole("button", { name: /^دلِ:/ }));
    const here = within(text).getByRole("region", { name: "خوانش در این سطر" });
    await userEvent.click(within(here).getByRole("radio", { name: /Dal/ }));
    await userEvent.click(within(here).getByRole("button", { name: "ثبت «Dal»" }));
    const word = await within(text).findByRole("button", { name: "دلِ: Dal، ثبت‌شده" });
    expect(word).toHaveTextContent(/^دلِ/);
  });

  it("marks a reading saved before the visit with its own vowels", async () => {
    saved = [
      {
        ...MARKED,
        id: 20,
        target_id: "دل:Dal",
        latin: "Dal",
        written: "دلِ",
        written_marked: "دَلِ",
        unit: 0,
        line: 0,
        word: 0,
        in_bank: true,
      },
    ];
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    const word = await within(text).findByRole("button", { name: "دلِ: Dal، ثبت‌شده" });
    expect(word).toHaveTextContent(/^دَلِ/);
  });

  it("takes the vowels of the reading shown, and none it cannot know", () => {
    const auto = AUTO.units[0]!.lines[0]!.words![0]!.auto!;
    expect(markedFor(auto, undefined)).toBe("دِلِ");
    expect(markedFor(auto, { latin: "Del", inBank: true, id: 1 })).toBe("دِلِ");
    expect(markedFor(auto, { latin: "Dal", inBank: true, id: 1 })).toBeUndefined();
    expect(markedFor(auto, { latin: "Dal", inBank: true, id: 1, marked: "دَلِ" })).toBe("دَلِ");
  });

  it("shows the review list's words with their vowels, or as written", async () => {
    review = [
      { ...MARKED, written_marked: "دُلِ", spelling_fa_marked: "دُل" },
      {
        ...MARKED,
        id: 6,
        target_id: "ما:mo",
        spelling_fa: "ما",
        latin: "mo",
        written: null,
        note: null,
      },
    ];
    renderApp("/texts");
    const marks = await screen.findByRole("region", { name: "خوانش‌هایی که علامتِ «نادرست» خورده‌اند" });
    expect(within(marks).getByText("دُلِ")).toBeInTheDocument();
    expect(within(marks).getByText("ما")).toBeInTheDocument();
    // The way back to the line goes on the plain spelling.
    expect(within(marks).getAllByRole("link", { name: /همان سطر/ })[0]).toHaveAttribute(
      "href",
      "/texts?text=fixture%3Aa%3A1&unit=0&word=%D8%AF%D9%84",
    );
  });
});

describe("where a saved reading belongs", () => {
  const row: Marked = {
    ...MARKED,
    spelling_fa: "دل",
    latin: "Dal",
    written: "دلِ",
    unit: 0,
    line: 0,
    word: 1,
    before: "ما",
    after: "ما",
    in_bank: true,
  };
  const moved: Text = {
    ...AUTO,
    units: [
      {
        index: 0,
        number: 1,
        kind: "couplet",
        lines: [
          {
            position: "first",
            // A revision put another دلِ where the saved one stood.
            words: [
              { fa: "ما", s: "ما" },
              { fa: "دلِ", s: "دل" },
              { fa: "ما", s: "ما" },
              { fa: "دلِ", s: "دل" },
            ],
          },
        ],
      },
    ],
  };

  it("trusts the saved place only where the word there is the one saved", () => {
    expect([...placeSaved(moved, [row]).keys()]).toEqual(["0:0:1"]);
    const elsewhere = { ...row, before: "رفت" };
    expect([...placeSaved(moved, [elsewhere]).keys()]).toEqual([]);
    // Saved at 1 between ما and the line's end: that word is now at 3.
    const stale = { ...row, after: null };
    expect([...placeSaved(moved, [stale]).keys()]).toEqual(["0:0:3"]);
  });

  it("leaves an old save without a place unshown where its context repeats", () => {
    const twice: Text = {
      ...moved,
      units: [
        {
          index: 0,
          number: 1,
          kind: "couplet",
          lines: [
            { position: "first", words: [{ fa: "ما", s: "ما" }, { fa: "دلِ", s: "دل" }] },
            { position: "second", words: [{ fa: "ما", s: "ما" }, { fa: "دلِ", s: "دل" }] },
          ],
        },
      ],
    };
    const old = { ...row, line: null, word: null, after: null };
    expect(placeSaved(twice, [old]).size).toBe(0);
    expect([...placeSaved(twice, [{ ...old, line: 1, word: 1 }]).keys()]).toEqual(["0:1:1"]);
  });

  it("keeps the newest save at a place, however late an answer arrives", () => {
    const later = new Map([["0:0:0", { latin: "Dal", inBank: true, id: 9 }]]);
    const earlier = new Map([["0:0:0", { latin: "Del", inBank: true, id: 8 }]]);
    expect(newest(later, earlier).get("0:0:0")?.latin).toBe("Dal");
    expect(newest(earlier, later).get("0:0:0")?.latin).toBe("Dal");
  });
});

describe("deciding a reading once for every like place", () => {
  async function panelOf(word: RegExp) {
    renderApp("/texts?text=fixture%3Ab%3A1");
    const text = await screen.findByRole("region", { name: "نویسنده · کتاب · باب نخست · حکایت یکم" });
    await userEvent.click(within(text).getByRole("button", { name: word }));
    return within(text).getByRole("region", { name: "خوانش در این سطر" });
  }

  it("saves for this line only unless the reader says otherwise", async () => {
    const here = await panelOf(/^دلِ:/);
    const reach = within(here).getByRole("group", { name: "برای کجا؟" });
    expect(within(reach).getByRole("radio", { name: "فقط همین‌جا" })).toBeChecked();
    await userEvent.click(within(here).getByRole("radio", { name: /Dal/ }));
    await userEvent.click(within(here).getByRole("button", { name: "ثبت «Dal»" }));
    await within(here).findByText(/ثبت شد/);
    expect(posted[0]).toEqual(
      expect.objectContaining({ context: expect.objectContaining({ kind: "reading_here" }) }),
    );
  });

  it("says how many places each reach covers, from the measured list", async () => {
    const here = await panelOf(/^دلِ:/);
    const reach = within(here).getByRole("group", { name: "برای کجا؟" });
    // دلِ here stands before رفتند, at the start of its line.
    const before = await within(reach).findByRole("radio", { name: /هر جا پیش از «رفتند»/ });
    await waitFor(() => expect(before.closest("label")).toHaveTextContent("(۵۰ جا)"));
    expect(within(reach).queryByRole("radio", { name: /پس از/ })).not.toBeInTheDocument();
    const everywhere = within(reach).getByRole("radio", { name: /هر جا که «دل» آمده/ });
    expect(everywhere.closest("label")).toHaveTextContent("(۱٬۰۰۰ جا)");
  });

  it("sends a decision with its reach, and the summary says what it will do", async () => {
    const here = await panelOf(/^دلِ:/);
    await userEvent.click(within(here).getByRole("radio", { name: /Del/ }));
    await userEvent.click(within(here).getByRole("radio", { name: /هر جا پیش از «رفتند»/ }));
    expect(within(here).getByText(/ثبت می‌شود/)).toHaveTextContent(/هر جا پیش از «رفتند».*همهٔ این جاها/);
    await userEvent.click(
      within(here).getByRole("button", { name: "ثبت «Del» برای هر جا پیش از «رفتند»" }),
    );
    await within(here).findByText(/برای هر جا پیش از «رفتند» ثبت شد/);
    expect(posted[0]).toEqual(
      expect.objectContaining({
        verdict: "good",
        target_id: "دل:Del",
        context: expect.objectContaining({
          kind: "reading_decided",
          scope: "before_word",
          scope_word: "رفتند",
          latin: "Del",
          in_bank: true,
          withdrawn: false,
          document_id: "fixture:b:1",
          unit: 0,
          line: 0,
          word: 0,
        }),
      }),
    );
  });

  it("takes a new decision into the panel's list, replacing the one with its reach", async () => {
    // Saved before: an older store id than the one the save gets back (8).
    decided = [
      { id: 3, latin: "Dal", scope: "before_word", scope_word: "رفتند", in_bank: true, created_at: null },
    ];
    const here = await panelOf(/^دلِ:/);
    await within(here).findByText(/برای این املا پیش‌تر تصمیم گرفته شده است/);
    await userEvent.click(within(here).getByRole("radio", { name: /Del/ }));
    await userEvent.click(within(here).getByRole("radio", { name: /هر جا پیش از «رفتند»/ }));
    await userEvent.click(within(here).getByRole("button", { name: /^ثبت «Del»/ }));
    await within(here).findByText(/ثبت شد/);
    const inForce = within(here).getByText(/برای این املا پیش‌تر تصمیم گرفته شده است/).parentElement!;
    expect(inForce).toHaveTextContent(/هر جا پیش از «رفتند»: Del/);
    expect(inForce).not.toHaveTextContent(/: Dal/);
  });

  it("names a decision already in force in the panel", async () => {
    decided = [
      { id: 30, latin: "Del", scope: "everywhere", scope_word: null, in_bank: true, created_at: null },
    ];
    const here = await panelOf(/^دلِ:/);
    const note = await within(here).findByText(/برای این املا پیش‌تر تصمیم گرفته شده است/);
    expect(note.parentElement).toHaveTextContent(/همه‌جا: Del/);
  });

  it("lists the most frequent unsure spellings, with what a decision would reach", async () => {
    renderApp("/texts?view=unsure");
    const list = await screen.findByRole("region", { name: "پرتکرارترین واژه‌های نامطمئن" });
    expect(await within(list).findByText(/واژهٔ متن‌ها/)).toHaveTextContent(
      "در پیکرهٔ v22، از ۱۰٬۰۰۰ واژهٔ متن‌ها ۳٬۳۰۰ تا (۳۳٪) به شما سپرده می‌شود.",
    );
    const row = within(list).getByRole("button", { name: /دل/ });
    expect(row).toHaveTextContent("۶۰۰ جای نامطمئن از ۱٬۰۰۰");
    expect(row).toHaveTextContent("چند خوانش در بانک");
    await userEvent.click(row);
    const panel = within(list).getByRole("region", { name: "تصمیم دربارهٔ دل" });
    // The bank's readings first, then what the model offered.
    expect(
      within(within(panel).getByRole("group", { name: "این املا را چطور می‌خوانید؟" }))
        .getAllByRole("radio")
        .map((one) => (one as HTMLInputElement).value),
    ).toEqual(["Dal", "Del", "dall", "Dol"]);
    expect(within(panel).getByText(/در ۶۰٪ آن‌ها جور است/)).toHaveTextContent(/به‌جای «همه‌جا»/);
    expect(within(panel).getByRole("link", { name: "در متن ←" })).toHaveAttribute(
      "href",
      "/texts?text=fixture%3Aa%3A1&unit=0&word=%D8%AF%D9%84",
    );
  });

  it("marks the spelling in its example line, and cuts a long one around it", () => {
    renderWithRouter(<ExampleLine text="یک دلِ دو سه" at={1} spelling="دل" />);
    expect(screen.getByText("دلِ").tagName).toBe("MARK");
    const long = Array.from({ length: 40 }, (_, i) => (i === 30 ? "دل" : `w${i}`)).join(" ");
    renderWithRouter(<ExampleLine text={long} at={30} spelling="دل" />);
    const line = screen.getByText("دل").parentElement!;
    expect(line.textContent).toMatch(/^… w20 .* دل .* w39$/);
    // A place that does not find the spelling marks nothing …
    renderWithRouter(<ExampleLine text="یک دو" at={1} spelling="دل" />);
    expect(screen.getByText("یک دو").querySelector("mark")).toBeNull();
    // … nor a longer word that holds its letters; a token with a space of its
    // own moves the word one place on.
    renderWithRouter(<ExampleLine text="A B دلداده دلِ،" at={2} spelling="دل" />);
    expect(screen.getByText("دلِ،").tagName).toBe("MARK");
  });

  it("decides a spelling after one word from the list, and takes a decision back", async () => {
    decided = [
      { id: 31, latin: "Dal", scope: "everywhere", scope_word: null, in_bank: true, created_at: null },
    ];
    renderApp("/texts?view=unsure");
    const list = await screen.findByRole("region", { name: "پرتکرارترین واژه‌های نامطمئن" });
    await userEvent.click(await within(list).findByRole("button", { name: /دل/ }));
    const panel = within(list).getByRole("region", { name: "تصمیم دربارهٔ دل" });
    await userEvent.click(within(panel).getByRole("radio", { name: "Del" }));
    await userEvent.selectOptions(within(panel).getByRole("combobox", { name: /پس از: کدام واژه/ }), "ما");
    expect(within(panel).getByText(/ثبت می‌شود/)).toHaveTextContent(/هر جا پس از «ما» \(۱۲۰ جا\)/);
    await userEvent.click(within(panel).getByRole("button", { name: "ثبت «Del» برای هر جا پس از «ما»" }));
    await within(panel).findByText(/برای هر جا پس از «ما» ثبت شد/);
    expect(posted[0]).toEqual(
      expect.objectContaining({
        context: expect.objectContaining({
          kind: "reading_decided",
          scope: "after_word",
          scope_word: "ما",
          latin: "Del",
          in_bank: true,
        }),
      }),
    );
    // The decision in force before is still there, and can be taken back.
    const earlier = within(panel).getByText(/همه‌جا:/).closest("li")!;
    await userEvent.click(within(earlier).getByRole("button", { name: "پس گرفتن" }));
    await waitFor(() => expect(posted).toHaveLength(2));
    expect(posted[1]).toEqual(
      expect.objectContaining({
        verdict: "unsure",
        context: expect.objectContaining({ withdrawn: true, scope: "everywhere", replaces: 31 }),
      }),
    );
    await waitFor(() => expect(within(panel).queryByText(/همه‌جا: /)).not.toBeInTheDocument());
  });

  it("filters by the kind of decision, and says when the list is not built", async () => {
    renderApp("/texts?view=unsure");
    const list = await screen.findByRole("region", { name: "پرتکرارترین واژه‌های نامطمئن" });
    await within(list).findByRole("button", { name: /دل/ });
    await userEvent.click(within(list).getByRole("button", { name: "در بانک نیست" }));
    await waitFor(() =>
      expect(within(list).getByText(/املا، از آنکه/)).toHaveTextContent(/^۰ املا/),
    );
    expect(within(list).queryByRole("button", { name: /دل/ })).not.toBeInTheDocument();
  });

  it("says plainly when the list has not been measured", async () => {
    listGone = true;
    renderApp("/texts?view=unsure");
    expect(await screen.findByText("این فهرست هنوز برای این نسخهٔ برنامه ساخته نشده است.")).toBeInTheDocument();
  });

  it("says a decided reading is a person's, not the model's", async () => {
    const decidedText: Text = structuredClone(AUTO);
    const first = decidedText.units[0]!.lines[0]!.words![0]!;
    first.auto = {
      ...first.auto!,
      source: "decided",
      confidence: 0.95,
      candidates: [
        ["Del", 0.95],
        ["Dal", null],
      ],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => ({
        ok: true,
        status: 200,
        statusText: "",
        json: async () => (String(url).includes("fixture%3Ab%3A1") ? decidedText : answer(String(url))),
      })),
    );
    const here = await panelOf(/^دلِ:/);
    expect(within(here).getByText(/کسی برای همهٔ جاهای همانندِ این املا برگزیده است/)).toBeInTheDocument();
    expect(within(here).queryByText(/این خوانش را برنامه پیشنهاد می‌کند/)).not.toBeInTheDocument();
  });

  it("is reached from the reading screen's start", async () => {
    renderApp("/texts");
    expect(await screen.findByRole("link", { name: /پرتکرارترین واژه‌های نامطمئن/ })).toHaveAttribute(
      "href",
      "/texts?view=unsure",
    );
  });
});
