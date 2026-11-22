/**
 * Compounds on screen.
 *
 * The behaviour that matters is not that the words appear — it is that the
 * counts appear beside them, and that a row which may not be a compound says
 * so instead of being dropped. A list of forty attested compounds with no
 * mention of the four thousand it came from is a different claim entirely.
 */

import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Compounds, Pairing } from "../../api/compound";
import { renderApp } from "../../test/render";
import { LEXICON, notFound } from "../../text/lexicon";

function pairing(over: Partial<Pairing> = {}): Pairing {
  return {
    form_latin: "dalbar",
    form_fa: "دلبر",
    word_class: "karandekarbahr",
    rule_id: "V-078",
    label_fa: null,
    explanation_fa: "از نام و کنون‌کاربن ساخته می‌شود",
    front: { fa: "دل", latin: "dal", type: "nam" },
    behind: {
      fa: "بر",
      latin: "bar",
      type: "karbon_do",
      of: { fa: "بردن", latin: "bordan" },
    },
    role: "front",
    attestation: {
      level: "spelling",
      corpus_version: "v8",
      total_count: 4000,
      doc_count: 2920,
      author_count: 210,
      first_century: 11,
      last_century: 20,
      wording: "در پیکره آمده است",
    },
    is_attested: true,
    score: {
      build: 61,
      corpus: "letters",
      texts: 2920,
      confirmed: false,
      weakest_rule: { rule_id: "V-078", affix: "بر", types: 21688, attested: 6 },
      meaning_mark: null,
      unmeasured_step: false,
    },
    also_an_inflection: null,
    already_a_word: true,
    ...over,
  };
}

const ANSWER: Compounds = {
  word: "دل",
  partner: null,
  rule_pack_version: "0.1.0",
  lexicon_snapshot_id: "lexicon:abc",
  showing: "attested",
  readings: [
    {
      latin: "Dal",
      spelling_fa: "دل",
      lexicon_category: "اسم ذات",
      needs_review: false,
      built: 4652,
      attested: 220,
      unattested: 4432,
      partners_tried: 1741,
      skipped: { template: "a template joins one verb's two stems" },
      word_classes: ["nam"],
      slot_wants: ["barnam", "nam"],
      returned: 2,
      pairings: [
        pairing(),
        pairing({
          form_latin: "dalm",
          form_fa: "دلم",
          rule_id: "V-079",
          behind: {
            fa: "م",
            latin: "m",
            type: "karbon_do",
            of: { fa: "میدن", latin: "midan" },
          },
          already_a_word: true,
          also_an_inflection: {
            base: "دل",
            pattern: "noun:م",
            label_fa: "ضمیر پیوستهٔ اول مفرد",
            shared_with_rules: [],
            is_shared: false,
          },
        }),
      ],
    },
  ],
};

function answers(body: unknown, status = 200) {
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

describe("the same word built two ways", () => {
  /** دلبر from V-078 and دلبر from V-079: the screenshot the project lead sent. */
  const TWICE: Compounds = {
    ...ANSWER,
    readings: [
      {
        ...ANSWER.readings[0]!,
        returned: 2,
        pairings: [
          pairing({ rule_id: "V-078", word_class: "karandekarbahr" }),
          pairing({ rule_id: "V-079", word_class: "karidekarbahr" }),
        ],
      },
    ],
  };

  const CLASSES = [
    {
      name: "karandekarbahr",
      label_fa: "کارنده‌کاربهر",
      label_is_traditional: false,
      explanation_fa: "آنکه کار را می‌کند",
      traditional_fa: "اسم فاعل مرکب",
    },
    {
      name: "karidekarbahr",
      label_fa: "کاریده‌کاربهر",
      label_is_traditional: false,
      explanation_fa: "آنکه کار بر او رفته است",
      traditional_fa: "اسم مفعول مرکب",
    },
  ];

  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        const path = String(url).replace("/api", "").split("?")[0];
        const body = path === "/rules" ? { word_classes: CLASSES } : TWICE;
        return Promise.resolve({
          ok: true,
          status: 200,
          statusText: "",
          json: async () => body,
        } as Response);
      }),
    );
  });

  it("says what each row builds, so two identical-looking rows are not identical", async () => {
    // `compounding.py` keeps both on purpose — V-078 means the doer and V-079
    // the done-to — but the screen printed only the rule id, so the reader saw
    // دلبر twice with the same parts and the same evidence and no way to tell
    // why. The class is what differs and it was on the row all along.
    renderApp("/compound?word=%D8%AF%D9%84");
    expect(
      await screen.findByRole("button", { name: "کارنده‌کاربهر" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "کاریده‌کاربهر" })).toBeInTheDocument();
  });

  it("explains the class rather than only naming it", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    await userEvent.click(
      await screen.findByRole("button", { name: "کارنده‌کاربهر" }),
    );
    expect(screen.getByRole("tooltip")).toHaveTextContent("آنکه کار را می‌کند");
  });

  it("shows no class rather than a machine id when the API does not serve them", async () => {
    vi.stubGlobal("fetch", answers(TWICE));
    renderApp("/compound?word=%D8%AF%D9%84");
    expect(await screen.findAllByText("dalbar")).toHaveLength(2);
    // The rows' class cells stay empty; only the tabs fall back to the id,
    // as on the build screen.
    for (const row of screen.getAllByRole("listitem")) {
      expect(row.textContent).not.toMatch(/karandekarbahr/);
    }
  });
});

describe("compound words", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", answers(ANSWER));
  });

  it("shows the compounds the corpus has", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    expect(await screen.findByText("دلبر")).toBeInTheDocument();
    expect(screen.getByText("دلم")).toBeInTheDocument();
  });

  /** Opens every row's «شواهد». */
  async function evidence() {
    for (const button of await screen.findAllByRole("button", { name: "شواهد" })) {
      await userEvent.click(button);
    }
  }

  it("says the count is the spelling's, because the corpus cannot hear a vowel", async () => {
    // دلبر is one row in the corpus whether it is read dalbar or dalber, so
    // both readings carry the same figure. Printed bare, one word's evidence
    // looked like two separate findings.
    renderApp("/compound?word=%D8%AF%D9%84");
    await evidence();
    // The numbers are their own elements, so the sentence is read off the
    // paragraph rather than matched as one text node.
    const said = await screen.findByText(/املای «دلبر» در/);
    expect(said.textContent).toMatch(/املای «دلبر» در ۲٬۹۲۰ متن از ۲۱۰ نویسنده/);
  });

  it("lists the lines the count was made from, under «شواهد»", async () => {
    // The sentence above is a claim, and until 2026-11-22 the page gave a
    // reader nothing to check it against; the build screen always had.
    const asked: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        const address = new URL(String(url), "http://localhost");
        const lines = address.pathname.endsWith("/evidence");
        if (lines) asked.push(address.searchParams.get("spelling") ?? "");
        const body = lines
          ? {
              spelling: address.searchParams.get("spelling"),
              corpus_version: "v8",
              total: 1,
              authors: [{ author: "حافظ", texts: 1 }],
              author: null,
              unnamed: false,
              matching: 1,
              lines: null,
              page: 0,
              size: 3,
              texts: [
                {
                  document_id: "fixture:1",
                  author: "حافظ",
                  title: "غزل",
                  century: 8,
                  work: "دیوان",
                  section: [],
                  lines: [{ unit: 4, kind: "couplet", parts: ["آن ", "دلبر", " که"] }],
                  held: "counted",
                },
              ],
            }
          : ANSWER;
        return Promise.resolve({
          ok: true,
          status: 200,
          statusText: "",
          json: async () => body,
        } as Response);
      }),
    );
    renderApp("/compound?word=%D8%AF%D9%84");
    const row = (await screen.findByText("دلبر")).closest("li")!;
    // The cell says what a spelling's count is worth, not «همین حروف».
    expect(within(row).getByText("شاید واژه‌ای دیگر با همین املا")).toBeInTheDocument();
    // Nothing is asked for while the row is closed.
    expect(asked).toHaveLength(0);
    await userEvent.click(within(row).getByRole("button", { name: "شواهد" }));
    expect(
      await within(row).findByText(/در این سطرها املای «دلبر» آمده است/),
    ).toBeInTheDocument();
    expect(within(row).getByRole("link", { name: "در متن ←" })).toHaveAttribute(
      "href",
      `/texts?text=fixture%3A1&unit=4&word=${encodeURIComponent("دلبر")}`,
    );
    expect(row.querySelector("mark")).toHaveTextContent("دلبر");
    expect(asked).toEqual(["دلبر"]);
  });

  it("says how many it built and how many were ever written", async () => {
    // ۴٬۶۵۲ built against ۲۲۰ attested. Without the first number the second
    // reads as the whole answer.
    renderApp("/compound?word=%D8%AF%D9%84");
    const counts = await screen.findByText(/ترکیب می‌سازند/);
    expect(counts.textContent).toMatch(/۴٬۶۵۲/);
    expect(counts.textContent).toMatch(/۲۲۰/);
    expect(counts.textContent).toMatch(/۱٬۷۴۱/);
  });

  it("says which verb the half the reader did not choose came from", async () => {
    // The row said `دل + بر` and stopped. بر is there as a کاربن دو and it is
    // the present stem of بردن — without that a reader cannot check the claim,
    // which is the whole reason they opened the row.
    renderApp("/compound?word=%D8%AF%D9%84");
    const [first] = await screen.findAllByRole("button", { name: "راه ساخت" });
    await userEvent.click(first!);
    expect(screen.getAllByText(/از کارواژهٔ بردن/)).not.toHaveLength(0);
  });

  it("names what was joined to what", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    expect(await screen.findByText(/دل \+ بر/)).toBeInTheDocument();
  });

  it("marks a row whose letters also read as an inflection", async () => {
    // دلم is دل plus a possessive. It is shown, ranked last by the API, and
    // told on rather than dropped.
    renderApp("/compound?word=%D8%AF%D9%84");
    await evidence();
    expect(
      await screen.findByText(/ضمیر پیوستهٔ اول مفرد/),
    ).toBeInTheDocument();
  });

  it("says when the dictionary already holds the compound", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    await evidence();
    expect((await screen.findAllByText(`در ${LEXICON} هست`)).length).toBe(2);
  });

  it("says which kind of compounding this word cannot reach", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    expect(await screen.findByText(/هر دو نیمهٔ واژه را از یک کارواژه می‌گیرند/)).toBeInTheDocument();
  });

  it("says why nothing was built, instead of counting to zero three times", async () => {
    // کار is a کارنام and every slot rule wants a نام, so it builds nothing —
    // and «۰ ترکیب … ۰ تای آن … ۱٬۷۴۱ واژهٔ دیگر آزموده شد» answered a question
    // nobody asked. Reported by the project lead on 2026-08-18.
    const NOTHING: Compounds = {
      ...ANSWER,
      readings: [
        {
          ...ANSWER.readings[0]!,
          built: 0,
          attested: 0,
          unattested: 0,
          returned: 0,
          pairings: [],
          word_classes: ["karnam"],
          slot_wants: ["barnam", "nam"],
          skipped: {
            slot: "the slot rules take barnam, nam in front; this reading is karnam",
            template: "a template joins one verb's two stems",
          },
        },
      ],
    };
    vi.stubGlobal("fetch", answers(NOTHING));
    renderApp("/compound?word=%D8%AF%D9%84");
    expect(await screen.findByText(/با این واژه هیچ ترکیبی ساخته نشد/)).toBeInTheDocument();
    expect(screen.getByText(/در نیمهٔ نخست/)).toBeInTheDocument();
    // The corpus sentence must not appear: nothing was built, so nothing could
    // have been looked for.
    expect(screen.queryByText(/هیچ‌یک از این ترکیب‌ها در پیکره نیامده/)).toBeNull();
  });

  it("asks for every word, best built first, not only the attested ones", async () => {
    // دل builds 4,652 and the corpus has 109. The other 4,543 are what the
    // project is for; the table's view switch and filter replace the two
    // buttons that used to choose between them (2026-11-21).
    const fetcher = answers(ANSWER);
    vi.stubGlobal("fetch", fetcher);
    renderApp("/compound?word=%D8%AF%D9%84");
    await screen.findByText("دلبر");
    const asked = fetcher.mock.calls.map((call) => String(call[0]));
    expect(asked.some((one) => one.includes("attested=false"))).toBe(true);
    expect(asked.some((one) => one.includes("limit=1000"))).toBe(true);
  });

  it("tells a reader the word is not in the dictionary rather than blaming the server", async () => {
    vi.stubGlobal("fetch", answers({ detail: "no entry" }, 404));
    renderApp("/compound?word=%D9%86%DB%8C%D8%B3%D8%AA");
    expect(
      await screen.findByText(
        notFound("نمی‌توانیم آن را با واژهٔ دیگری ترکیب کنیم."),
      ),
    ).toBeInTheDocument();
  });
});

describe("a spelling that is several entries", () => {
  /** دل as the dictionary has it: the heart, a tree, an ailment. */
  const HEART = {
    ...ANSWER.readings[0]!,
    latin: "Del",
    entry: 11456,
    definition_fa: "قلب و فؤاد. (آنندراج). قلب که جسمی است گوشتی",
    confirmed: 24,
    pairings: [pairing({ form_latin: "delbar", front: { fa: "دل", latin: "Del", type: "nam" } })],
  };
  const TREE = {
    ...ANSWER.readings[0]!,
    latin: "Dal",
    entry: 11452,
    definition_fa: "در همدان اِشَنَک را گویند، که نوعی صنوبر است",
    confirmed: 0,
  };
  const AILMENT = {
    ...ANSWER.readings[0]!,
    latin: "Dol",
    entry: 11455,
    definition_fa: "(از برهان) گرهی چند که در امعاء و شکم از قبض",
    confirmed: 0,
  };
  const SEVERAL: Compounds = { ...ANSWER, readings: [HEART, TREE, AILMENT] };

  /** The paragraph above the buttons, read whole: its numbers are their own elements. */
  async function saying() {
    return (await screen.findByText(/مدخل جدا دارد|مدخل\s*پیدا شد/)).textContent ?? "";
  }

  it("opens on the first entry the API sends and shows only that one", async () => {
    // دل stacked all four entries, the tree first, so a reader met «دل Dal»
    // and the heart's words three cards down. Reported on 2026-11-21.
    vi.stubGlobal("fetch", answers(SEVERAL));
    renderApp("/compound?word=%D8%AF%D9%84");
    expect(await screen.findByRole("heading", { level: 2 })).toHaveTextContent("Del");
    expect(screen.getAllByRole("heading", { level: 2 })).toHaveLength(1);
    expect(screen.getByText(/قلب که جسمی است گوشتی/)).toBeInTheDocument();
    expect(screen.getByText("delbar")).toBeInTheDocument();
  });

  it("offers the other entries, each with the few words that tell it apart", async () => {
    vi.stubGlobal("fetch", answers(SEVERAL));
    renderApp("/compound?word=%D8%AF%D9%84");
    const entries = await screen.findByRole("group", { name: "مدخل‌های «دل»" });
    const buttons = within(entries).getAllByRole("button");
    // The ailment's definition opens with its source in brackets, which says
    // nothing about the word and is skipped.
    expect(buttons.map((one) => one.textContent)).toEqual([
      "Delقلب و فؤاد",
      "Dalدر همدان اِشَنَک را…",
      "Dolگرهی چند که در…",
    ]);
    expect(buttons[0]).toHaveAttribute("aria-pressed", "true");

    await userEvent.click(buttons[1]!);
    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent("Dal");
    expect(screen.getByText(/نوعی صنوبر است/)).toBeInTheDocument();
    expect(within(entries).getAllByRole("button")[1]).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("tells apart two entries that share their Latin", async () => {
    // Asked by *Allākolang*, the lexicon returns الاکلنگ (a seesaw) and الا
    // کلنگ (beetles). Chosen by the Latin, the second could never be opened.
    const SEESAW = { ...TREE, latin: "Allākolang", spelling_fa: "الاکلنگ", entry: 1 };
    const BEETLES = {
      ...TREE,
      latin: "Allākolang",
      spelling_fa: "الا کلنگ",
      entry: 2,
      definition_fa: "سوسک‌هایی که تاول آورند",
    };
    vi.stubGlobal("fetch", answers({ ...SEVERAL, readings: [SEESAW, BEETLES] }));
    renderApp("/compound?word=All%C4%81kolang");
    const entries = await screen.findByRole("group", { name: "مدخل‌های «Allākolang»" });
    // Two spellings, one entry each: the sentence counts what the search
    // matched, not entries of one spelling, and each button names its spelling.
    expect(await saying()).toMatch(/برای «Allākolang» در واژه‌نامهٔ کاربن ۲ مدخل پیدا شد/);
    expect(within(entries).getAllByRole("button")[1]).toHaveTextContent("الا کلنگ");
    await userEvent.click(within(entries).getAllByRole("button")[1]!);
    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent("الا کلنگ");
    expect(within(entries).getAllByRole("button")[1]).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("says why the first entry is first, with the number", async () => {
    vi.stubGlobal("fetch", answers(SEVERAL));
    renderApp("/compound?word=%D8%AF%D9%84");
    const said = await saying();
    expect(said).toMatch(/۳ مدخل جدا دارد/);
    expect(said).toMatch(
      /اول آن یکی آمده که ۲۴ واژهٔ ساخته از آن هم در همین واژه‌نامه هست و هم در پیکره/,
    );
  });

  it("says where the evidence ties at the top, without calling the whole order the dictionary's", async () => {
    // شیر's lion and milk build the same Latin, so their counts are equal —
    // and both still stand above an entry with none.
    vi.stubGlobal(
      "fetch",
      answers({
        ...SEVERAL,
        readings: [{ ...HEART, confirmed: 20 }, { ...TREE, confirmed: 20 }, AILMENT],
      }),
    );
    renderApp("/compound?word=%D8%AF%D9%84");
    const said = await saying();
    expect(said).toMatch(/از هر کدام ۲۰ واژهٔ ساخته/);
    expect(said).toMatch(/میان آن‌ها پیکره داوری نمی‌کند/);
    expect(said).not.toMatch(/ترتیب واژه‌نامه/);
  });

  it("says the order is the dictionary's when no entry has any evidence", async () => {
    vi.stubGlobal(
      "fetch",
      answers({ ...SEVERAL, readings: [{ ...HEART, confirmed: 0 }, TREE] }),
    );
    renderApp("/compound?word=%D8%AF%D9%84");
    expect(await saying()).toMatch(/ترتیبشان همان ترتیب واژه‌نامه است/);
  });

  it("says nothing about evidence the corpus did not give", async () => {
    // A corpus that did not answer is not a corpus that found nothing.
    vi.stubGlobal(
      "fetch",
      answers({ ...SEVERAL, readings: [{ ...HEART, confirmed: null }, TREE] }),
    );
    renderApp("/compound?word=%D8%AF%D9%84");
    const said = await saying();
    expect(said).not.toMatch(/اول آن|داوری|ترتیب واژه‌نامه/);
  });

  it("opens the entry the address names, so one can be linked to", async () => {
    vi.stubGlobal("fetch", answers(SEVERAL));
    renderApp("/compound?word=%D8%AF%D9%84&entry=11455");
    expect(await screen.findByRole("heading", { level: 2 })).toHaveTextContent("Dol");
  });

  it("opens the first entry when the address names none of them", async () => {
    vi.stubGlobal("fetch", answers(SEVERAL));
    renderApp("/compound?word=%D8%AF%D9%84&entry=999");
    expect(await screen.findByRole("heading", { level: 2 })).toHaveTextContent("Del");
  });

  it("forgets the chosen entry when another word is asked for", async () => {
    const fetcher = answers(SEVERAL);
    vi.stubGlobal("fetch", fetcher);
    renderApp("/compound?word=%D8%AF%D9%84&entry=11455");
    await screen.findByRole("heading", { level: 2 });
    const box = screen.getByLabelText("واژه‌ای بنویسید");
    await userEvent.clear(box);
    await userEvent.type(box, "سر{Enter}");
    const asked = fetcher.mock.calls.map((call) => String(call[0]));
    expect(asked.some((one) => one.includes(encodeURIComponent("سر")))).toBe(true);
    // The stub answers every word with the same three entries, so a choice
    // that survived would still show the ailment; a fresh word opens on the first.
    await waitFor(() =>
      expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent("Del"),
    );
  });

  it("shows no switch for a spelling that is one entry", async () => {
    vi.stubGlobal("fetch", answers(ANSWER));
    renderApp("/compound?word=%D8%AF%D9%84");
    await screen.findByRole("heading", { level: 2 });
    expect(screen.queryByRole("group", { name: /مدخل‌های/ })).toBeNull();
  });
});

describe("the compound table", () => {
  /** دل as the API ranks it: best built first. */
  const RANKED: Compounds = {
    ...ANSWER,
    readings: [
      {
        ...ANSWER.readings[0]!,
        latin: "Del",
        count: 4685,
        returned: 3,
        pairings: [
          pairing({
            form_fa: "دلدار",
            form_latin: "deldār",
            behind: { fa: "دار", latin: "dār", type: "karbon_do", of: { fa: "داشتن", latin: "dāštan" } },
            score: {
              build: 100,
              corpus: "reading",
              texts: 1724,
              confirmed: false,
              weakest_rule: { rule_id: "V-078", affix: "دار", types: 21688, attested: 73 },
              meaning_mark: null,
              unmeasured_step: false,
            },
            attestation: { ...pairing().attestation!, level: "reading", doc_count: 1724 },
          }),
          pairing({
            form_fa: "دلدان",
            form_latin: "deldān",
            is_attested: false,
            already_a_word: false,
            behind: { fa: "دان", latin: "dān", type: "karbon_do", of: { fa: "دانستن", latin: "dānestan" } },
            score: {
              build: 84,
              corpus: "none",
              texts: 0,
              confirmed: false,
              weakest_rule: { rule_id: "V-078", affix: "دان", types: 21688, attested: 36 },
              meaning_mark: null,
              unmeasured_step: false,
            },
            attestation: { ...pairing().attestation!, level: "none", doc_count: 0 },
          }),
          pairing({
            form_fa: "دلم",
            form_latin: "delm",
            behind: { fa: "م", latin: "m", type: "karbon_do", of: { fa: "میدن", latin: "midan" } },
            score: {
              build: null,
              corpus: "other",
              texts: 12947,
              confirmed: false,
              weakest_rule: null,
              meaning_mark: null,
              unmeasured_step: true,
            },
          }),
        ],
      },
    ],
  };

  beforeEach(() => {
    vi.stubGlobal("fetch", answers(RANKED));
  });

  it("shows how well built each compound is, with a dash where it was not measured", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    expect(await screen.findByLabelText("ساخت ۱۰۰ از ۱۰۰")).toBeInTheDocument();
    expect(screen.getByLabelText("ساخت ۸۴ از ۱۰۰")).toBeInTheDocument();
    // دلم's half is one letter: no value, never a zero.
    expect(screen.getByTitle("سنجیده نشده")).toHaveTextContent("—");
  });

  it("says behind «شواهد» what the value comes from", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    const [first] = await screen.findAllByRole("button", { name: "شواهد" });
    await userEvent.click(first!);
    const said = screen.getByText(/پس از/).textContent ?? "";
    expect(said).toMatch(/«‑دار»/);
    expect(said).toMatch(/۲۱٬۶۸۸ واژه/);
    expect(said).toMatch(/۷۳ ترکیب ساخته/);
  });

  it("says when the value was not measured, and why it may not be", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    const buttons = await screen.findAllByRole("button", { name: "شواهد" });
    await userEvent.click(buttons[2]!);
    expect(screen.getByText(/ساختِ این ترکیب سنجیده نشده است/)).toBeInTheDocument();
  });

  it("keeps only the words the corpus lacks in «واژه‌های تازه»", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    await screen.findByText("دلدار");
    await userEvent.click(screen.getByLabelText("واژه‌های تازه"));
    expect(screen.getByText("دلدان")).toBeInTheDocument();
    expect(screen.queryByText("دلدار")).toBeNull();
    expect(screen.queryByText("دلم")).toBeNull();
  });

  it("filters on the build value as the build screen does", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    await screen.findByText("دلدار");
    await userEvent.click(screen.getByLabelText("۷۰ و بیشتر"));
    expect(screen.getByText("دلدار")).toBeInTheDocument();
    expect(screen.getByText("دلدان")).toBeInTheDocument();
    // A row with no value is kept only by «همه».
    expect(screen.queryByText("دلم")).toBeNull();
    await userEvent.click(screen.getByLabelText("۴۰ تا ۶۹"));
    expect(screen.queryByText("دلدار")).toBeNull();
    expect(screen.queryByText("دلدان")).toBeNull();
  });

  it("sorts by texts from the head row", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    await screen.findByText("دلدار");
    const [byTexts] = screen.getAllByRole("button", { name: /در پیکره/ });
    await userEvent.click(byTexts!);
    const words = within(screen.getByRole("tabpanel"))
      .getAllByRole("listitem")
      .map((row) => row.querySelector("span span")?.textContent);
    // The build screen's texts order: دلم's 2,920, دلدار's 1,724, then the
    // new word with none.
    expect(words).toEqual(["دلم", "دلدار", "دلدان"]);
  });

  it("says it shows the best of a longer list, and every attested one", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    const said = await screen.findByText(/تا را نشان می‌دهیم/);
    expect(said.textContent).toMatch(/از ۴٬۶۸۵ ترکیب، ۳ تا را نشان می‌دهیم/);
    expect(said.textContent).toMatch(/همهٔ آن‌هایی که در پیکره آمده‌اند/);
  });

  it("says a word the corpus lacks is not in it, not that it is in no texts", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    const buttons = await screen.findAllByRole("button", { name: "شواهد" });
    await userEvent.click(buttons[1]!);
    expect(screen.getByText("«دلدان» در پیکره نیامده است")).toBeInTheDocument();
    expect(screen.queryByText(/املای «دلدان»/)).toBeNull();
  });

  it("returns to the best-built order for «واژه‌های تازه»", async () => {
    // Its line promises the best built first; an alphabetical order chosen
    // before must not carry over (the review of 2026-11-21).
    renderApp("/compound?word=%D8%AF%D9%84");
    await screen.findByText("دلدار");
    // The head row's «واژه» sorts by the alphabet (the phone's «الفبا» is the
    // same sort, shown only on a phone).
    await userEvent.click(screen.getByRole("button", { name: "واژه" }));
    expect(screen.getByRole("button", { name: "واژه" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await userEvent.click(screen.getByLabelText("واژه‌های تازه"));
    expect(screen.getByRole("button", { name: "واژه" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("names the class on the row, which tells the doer from the done-to on a phone", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        const path = String(url).replace("/api", "").split("?")[0];
        const body =
          path === "/rules"
            ? {
                word_classes: [
                  { name: "karandekarbahr", label_fa: "کارنده‌کاربهر", label_is_traditional: false },
                ],
              }
            : RANKED;
        return Promise.resolve({
          ok: true,
          status: 200,
          statusText: "",
          json: async () => body,
        } as Response);
      }),
    );
    renderApp("/compound?word=%D8%AF%D9%84");
    await screen.findByText("دلدار");
    const rows = within(screen.getByRole("tabpanel")).getAllByRole("listitem");
    expect(rows[0]!.textContent).toMatch(/کارنده‌کاربهر/);
  });
});

describe("the attested rows beyond the best thousand", () => {
  it("are added after it, so every word the corpus has stays reachable", async () => {
    // چادر builds 1,419 rows with a value above zero, and its attested
    // چادرکشان, at zero, fell outside the thousand (the review of 2026-11-21).
    const best = pairing({ form_fa: "دلدار", form_latin: "deldār" });
    const beyond = pairing({ form_fa: "دلکشان", form_latin: "delkešān" });
    const reading = { ...ANSWER.readings[0]!, entry: 11456, latin: "Del" };
    const fetcher = vi.fn().mockImplementation((url: string) => {
      const asked = String(url);
      const body = asked.includes("/rules")
        ? { word_classes: [] }
        : asked.includes("attested=false")
          ? { ...ANSWER, readings: [{ ...reading, pairings: [best] }] }
          : { ...ANSWER, readings: [{ ...reading, pairings: [best, beyond] }] };
      return Promise.resolve({
        ok: true,
        status: 200,
        statusText: "",
        json: async () => body,
      } as Response);
    });
    vi.stubGlobal("fetch", fetcher);
    renderApp("/compound?word=%D8%AF%D9%84");

    expect(await screen.findByText("دلکشان")).toBeInTheDocument();
    // Once each: the row both answers hold is not doubled.
    expect(screen.getAllByText("دلدار")).toHaveLength(1);
    const asked = fetcher.mock.calls.map((call) => String(call[0]));
    expect(asked.some((one) => one.includes("limit=0"))).toBe(true);
  });
});
