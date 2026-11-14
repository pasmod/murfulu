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

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Marked, Text, TextFound } from "../../api/texts";
import { renderApp } from "../../test/render";
import { newest, placeSaved } from "./Reader";

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

function answer(url: string): unknown {
  if (url.includes("/texts/marked") && url.includes("kind=proposed")) {
    return { total: saved.length, offset: 0, returned: saved.length, marked: saved };
  }
  if (url.includes("/texts/marked") && url.includes("spelling=")) {
    return { total: 1, offset: 0, returned: 1, marked: [EARLIER] };
  }
  if (url.includes("/texts/marked")) return { total: 1, offset: 0, returned: 1, marked: [MARKED] };
  if (url.includes("fixture%3Ab%3A1") || url.includes("fixture:b:1")) return AUTO;
  if (url.includes("/texts/")) return TEXT;
  return FOUND;
}

beforeEach(() => {
  posted = [];
  saved = [];
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
    expect(word).toHaveAccessibleName("دِل: Del؛ اعراب متن با Dal، dall نمی‌خواند");
    const pale = within(word)
      .getAllByText(/^(Dal|dall|Del)$/)
      .filter((one) => one.className.includes("ruledOut"))
      .map((one) => one.textContent);
    expect(pale).toEqual(["Dal", "dall"]);
    // The same spelling without signs keeps every reading alike.
    const plain = within(text).getAllByRole("button", { name: /^دلِ:/ })[0]!;
    expect(plain.querySelector("[class*=ruledOut]")).toBeNull();
    expect(within(text).getByText(/اعرابِ\s+خودِ متن با این خوانش نمی‌خواند/)).toBeInTheDocument();

    await userEvent.click(word);
    const panel = within(text).getByRole("region", { name: "خوانش‌های دِل" });
    expect(within(panel).getAllByText("اعرابِ متن با آن نمی‌خواند")).toHaveLength(2);
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
    expect(panel.textContent).toMatch(/به ۳ گونه می‌خواند/);
    expect(within(panel).getByText(/گفته نمی‌شود/)).toBeInTheDocument();
    // Del was marked before this visit, so only Dal and dall offer the mark.
    expect(await within(panel).findByText(/نادرست دانسته شده است/)).toBeInTheDocument();
    expect(within(panel).getAllByRole("button", { name: "این خوانش نادرست است" })).toHaveLength(2);
    expect(panel.textContent).toMatch(/۱۴۸٬۶۹۷ بار، در ۶۵٬۸۰۷ متن/);
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
    const unit = within(text).getByText(/همان سطرِ شاهدمثالِ «دل»/).closest("li")!;
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
    expect(within(dall).getByText(/پاک نمی‌شود/)).toBeInTheDocument();
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
    expect(await within(dall).findByText(/نادرست دانسته شده است/)).toBeInTheDocument();
  });

  it("finds texts by their heading and lists the marked readings for review", async () => {
    renderApp("/texts");
    const marks = await screen.findByRole("region", { name: "خوانش‌هایی که نادرست دانسته شده‌اند" });
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
    expect(within(here).queryAllByRole("radio", { checked: true })).toHaveLength(0);
    expect(within(here).getByText(/ثبت می‌شود/)).toHaveTextContent(/Dol.*نوشته‌شده/);
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
    expect(within(here).getByText(/پیش‌تر برای این سطر ثبت شده/)).toHaveTextContent("Dal");
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
