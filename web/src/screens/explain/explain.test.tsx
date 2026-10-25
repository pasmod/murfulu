/**
 * The sāzāyi check, on screen.
 *
 * The behaviour that matters most is the refusal, and the wording around it:
 * *not explained* must never read as *not a word*.
 */

import { screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Explanation } from "../../api/explain";
import { renderApp } from "../../test/render";

function evidence(level: "reading" | "spelling" | "none", docs: number) {
  return {
    level,
    corpus_version: "v10",
    total_count: docs * 2,
    doc_count: docs,
    author_count: docs,
    wording: "",
  };
}

const EXPLAINED: Explanation = {
  word: "Ravandegi",
  analysed_as: ["Ravandegi"],
  settled: true,
  searched_partially: [],
  depth: 2,
  rule_pack_version: "0.1.0",
  lexicon_snapshot_id: "lexicon:abc",
  rebuilt: true,
  accounts: [
    {
      form_latin: "Ravandegi",
      base: {
        latin: "raftan",
        spelling_fa: "رفتن",
        lexicon_category: "مصدر",
        attestation: evidence("reading", 19839),
      },
      depth: 2,
      steps: [
        {
          rule_id: "V-022",
          affix: "-ande",
          affix_fa: "نده",
          label_fa: null,
          explanation_fa: "کارنده‌کاربهر ساخته می‌شود",
          applied_to: "rav",
          stem_form: "ow->av",
          glide_id: null,
        },
        {
          rule_id: "V-023",
          affix: "-gi",
          affix_fa: "گی",
          label_fa: null,
          explanation_fa: "کارنام ساخته می‌شود",
          applied_to: "ravande",
          stem_form: null,
          glide_id: null,
        },
      ],
    },
    {
      form_latin: "Ravandegi",
      base: {
        latin: "ravidan",
        spelling_fa: "رویدن",
        lexicon_category: "مصدر",
        attestation: evidence("none", 0),
      },
      depth: 2,
      steps: [
        {
          rule_id: "V-022",
          affix: "-ande",
          affix_fa: "نده",
          label_fa: null,
          explanation_fa: "کارنده‌کاربهر ساخته می‌شود",
          applied_to: "rav",
          stem_form: null,
          glide_id: null,
        },
        {
          rule_id: "V-023",
          affix: "-gi",
          affix_fa: "گی",
          label_fa: null,
          explanation_fa: "کارنام ساخته می‌شود",
          applied_to: "ravande",
          stem_form: null,
          glide_id: null,
        },
      ],
    },
  ],
  affixes_tried_without_a_base: [],
};

const REFUSED: Explanation = {
  ...EXPLAINED,
  word: "Mowlānā",
  analysed_as: ["Mowlānā"],
  rebuilt: false,
  accounts: [],
  affixes_tried_without_a_base: ["-nā", "-ā"],
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

describe("taking a word apart", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", answers(EXPLAINED));
  });

  it("shows every account, and chooses none of them", async () => {
    renderApp("/explain?word=Ravandegi");
    // The count is a <Num> beside text, so it is matched on the heading.
    expect(
      await screen.findByRole("heading", { name: /۲ راه ممکن/ }),
    ).toBeInTheDocument();
    expect(screen.getByText("رفتن")).toBeInTheDocument();
    expect(screen.getByText("رویدن")).toBeInTheDocument();
  });

  it("says the accounts were rebuilt, which is why they are here", async () => {
    renderApp("/explain?word=Ravandegi");
    expect(
      await screen.findByText(/یک املا می‌تواند از چند راه ساخته شده باشد/),
    ).toBeInTheDocument();
  });

  it("reads outwards from the dictionary entry, the way the word was made", async () => {
    renderApp("/explain?word=Ravandegi");
    const list = await screen.findByRole("list", { name: /۲ راه ممکن/ });
    const first = within(list).getAllByRole("listitem")[0]!;
    const steps = within(first).getAllByText(/^V-0\d\d$/);
    expect(steps.map((one) => one.textContent)).toEqual(["V-022", "V-023"]);
  });

  it("never hides a stem that is written one way and behaves another", async () => {
    renderApp("/explain?word=Ravandegi");
    expect(await screen.findByText("ow->av")).toBeInTheDocument();
  });

  it("never hides the y between two vowels either", async () => {
    // gu + -ande is guyande, and the y is in neither half. A reader who
    // cannot see which rule put it there cannot check the account.
    const account = EXPLAINED.accounts[0]!;
    vi.stubGlobal(
      "fetch",
      answers({
        ...EXPLAINED,
        accounts: [
          {
            ...account,
            depth: 1,
            steps: [
              {
                ...account.steps[0]!,
                applied_to: "gu",
                stem_form: null,
                glide_id: "G-06",
              },
            ],
          },
        ],
      }),
    );
    renderApp("/explain?word=Ravandegi");
    expect(await screen.findByText("G-06")).toBeInTheDocument();
  });

  it("shows the word from the address, not the one typed before it", async () => {
    // The box seeded its draft from the address once and never again, so any
    // route change that did not come from the box left the two disagreeing.
    // The Back button is where a reader meets it, and that case is in
    // web/tests/layout.spec.ts because jsdom has no history to go back in.
    renderApp("/explain?word=Ravandegi");
    await screen.findByRole("heading", { name: /راه ممکن/ });
    expect(screen.getByLabelText(/واژه‌ای به بهنویس بنویسید/)).toHaveValue(
      "Ravandegi",
    );
  });
});

describe("when nothing rebuilds the word", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", answers(REFUSED));
  });

  it("does not say the word is wrong", async () => {
    renderApp("/explain?word=Mowl%C4%81n%C4%81");
    expect(
      await screen.findByText(/راهی برای ساختن این واژه پیدا نشد/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/این به معنای نادرست بودن واژه نیست/),
    ).toBeInTheDocument();
  });

  it("names the affixes it tried", async () => {
    renderApp("/explain?word=Mowl%C4%81n%C4%81");
    expect(await screen.findByText("-nā")).toBeInTheDocument();
    expect(screen.getByText("-ā")).toBeInTheDocument();
  });
});

describe("when the word is written in Persian script", () => {
  it("takes it apart, once for every reading the dictionary records", async () => {
    // S11. The route read the Behnevis and nothing else, so گفتار — the rule
    // pack's own example — came back with no accounts at all, which is
    // indistinguishable from "this word cannot be built". It is now looked up,
    // never transliterated: guessing the Behnevis was measured at 5.8% right.
    vi.stubGlobal(
      "fetch",
      answers({
        ...EXPLAINED,
        word: "کنار",
        analysed_as: ["Kanār", "Kenār"],
      }),
    );
    renderApp("/explain?word=%DA%A9%D9%86%D8%A7%D8%B1");
    await screen.findByRole("heading", { name: /راه ممکن/ });
    expect(screen.getByText("Kanār")).toBeInTheDocument();
    // Both readings, because the dictionary commits to neither and answering
    // on one of them would be a choice nobody made.
    expect(screen.getByText("Kenār")).toBeInTheDocument();
  });

  it("asks for the Behnevis only when the dictionary does not know the spelling", async () => {
    // The one refusal left, and it says which. It used to be given for every
    // Persian word, including the ones the lexicon holds.
    vi.stubGlobal("fetch", answers({ detail: "not in the lexicon" }, 400));
    renderApp("/explain?word=%DA%AF%D9%81%D8%AA%D8%A7%D8%B1");
    expect(await screen.findByText(/به بهنویس بنویسید/)).toBeInTheDocument();
    expect(screen.queryByText(/این به معنای نادرست بودن واژه نیست/)).toBeNull();
  });
});

describe("what `rebuilt` does and does not claim", () => {
  it("shows the base's own corpus evidence beside every account", async () => {
    // S21. The flag was called `explained` and came back true for Nāxodāgāhi
    // on ناخدا, a ship's captain — right about the letters, useless about the
    // word. Nothing refuses those, because refusing would need a judgement
    // about meaning this project does not make in code. What is shown instead
    // is the one fact that separates them.
    vi.stubGlobal("fetch", answers(EXPLAINED));
    renderApp("/explain?word=Ravandegi");
    await screen.findByRole("heading", { name: /راه ممکن/ });
    expect(document.querySelector('[data-value="19839"]')).toBeInTheDocument();
    expect(
      screen.getByText(/این پایه در پیکره نوشته نشده است/),
    ).toBeInTheDocument();
  });

  it("says the rebuild is about the letters, not about the word", async () => {
    vi.stubGlobal("fetch", answers(EXPLAINED));
    renderApp("/explain?word=Ravandegi");
    expect(
      await screen.findByText(/از روی املا معلوم نمی‌شود/),
    ).toBeInTheDocument();
  });
});

describe("when the search does not finish", () => {
  it("says so, instead of saying the word cannot be built", async () => {
    // Found 2026-08-17 asking why درافکندگی does not rebuild — the case the
    // coining experiment called the engine's largest gap. It is not a missing
    // rule: building forward from افکندن reaches 20,050 forms at three steps
    // and the engine stops at 20,000, so the search never arrives. Every rule
    // the chain needs exists and fires.
    vi.stubGlobal(
      "fetch",
      answers({
        ...REFUSED,
        word: "Darafkandegi",
        analysed_as: ["Darafkandegi"],
        settled: false,
        searched_partially: ["afkandan"],
        affixes_tried_without_a_base: [],
      }),
    );
    renderApp("/explain?word=Darafkandegi");
    expect(await screen.findByText(/جست‌وجو ناتمام ماند/)).toBeInTheDocument();
    expect(screen.getByText("afkandan")).toBeInTheDocument();
    // The settled refusal's wording must not appear here: "most words are
    // simple" is not the reason, and giving a reason that is not the reason is
    // the same failure S11 fixed on the Persian-script branch.
    expect(screen.queryByText(/راهی برای ساختن این واژه پیدا نشد/)).toBeNull();
    expect(screen.queryByText(/بیشتر واژه‌ها ساخته نشده‌اند/)).toBeNull();
  });

  it("still calls a real refusal a refusal", async () => {
    // مولانا is the case the whole sāzāyi check exists for. It must not be
    // softened into "we did not finish looking".
    vi.stubGlobal("fetch", answers(REFUSED));
    renderApp("/explain?word=Mowl%C4%81n%C4%81");
    expect(
      await screen.findByText(/راهی برای ساختن این واژه پیدا نشد/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/جست‌وجو ناتمام ماند/)).toBeNull();
  });
});
