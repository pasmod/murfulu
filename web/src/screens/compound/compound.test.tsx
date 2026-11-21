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
    // Counted on the Latin, which appears once per row — the Persian is
    // printed again in the row's own «راه ساخت», where it is the result.
    expect(await screen.findAllByText("dalbar")).toHaveLength(2);
    expect(screen.queryByText(/karandekarbahr/)).not.toBeInTheDocument();
  });
});

describe("compound words", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", answers(ANSWER));
  });

  it("shows the compounds the corpus has", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    // Twice each: the row's own word, and the last step of «راه ساخت», where
    // it is what the two halves make.
    expect(await screen.findAllByText("دلبر")).toHaveLength(2);
    expect(screen.getAllByText("دلم")).toHaveLength(2);
  });

  it("says the count is the spelling's, because the corpus cannot hear a vowel", async () => {
    // دلبر is one row in the corpus whether it is read dalbar or dalber, so
    // both readings carry the same figure. Printed bare, one word's evidence
    // looked like two separate findings.
    renderApp("/compound?word=%D8%AF%D9%84");
    // The numbers are their own elements, so the sentence is read off the
    // paragraph rather than matched as one text node.
    const said = await screen.findByText(/املای «دلبر» در/);
    expect(said.textContent).toMatch(/املای «دلبر» در ۲٬۹۲۰ متن از ۲۱۰ نویسنده/);
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
    expect(await screen.findAllByText(/از کارواژهٔ بردن/)).not.toHaveLength(0);
    expect(screen.getAllByText("راه ساخت").length).toBeGreaterThan(0);
  });

  it("names what was joined to what", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
    expect(await screen.findByText(/دل \+ بر/)).toBeInTheDocument();
  });

  it("marks a row whose letters also read as an inflection", async () => {
    // دلم is دل plus a possessive. It is shown, ranked last by the API, and
    // told on rather than dropped.
    renderApp("/compound?word=%D8%AF%D9%84");
    expect(
      await screen.findByText(/ضمیر پیوستهٔ اول مفرد/),
    ).toBeInTheDocument();
  });

  it("says when the dictionary already holds the compound", async () => {
    renderApp("/compound?word=%D8%AF%D9%84");
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

  it("offers the words nobody has written, not only the attested ones", async () => {
    // دل builds 4,652 and the corpus has 109. The other 4,543 are what the
    // project is for, and the screen could not ask for them at all.
    const fetcher = answers(ANSWER);
    vi.stubGlobal("fetch", fetcher);
    renderApp("/compound?word=%D8%AF%D9%84");
    await userEvent.click(
      await screen.findByRole("button", { name: /همه، با واژه‌های نو/ }),
    );
    const asked = fetcher.mock.calls.map((call) => String(call[0]));
    expect(asked.some((one) => one.includes("attested=false"))).toBe(true);
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
