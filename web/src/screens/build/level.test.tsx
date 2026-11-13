/**
 * The level on each built word, and what is behind «شواهد».
 *
 * The project lead's choice of 2026-11-13: a reader who is not a linguist
 * sees one of three levels and one sentence of reason; the three parts of the
 * score are one press away, as dots that give their numbers on a press; and
 * the list is sorted by level first. The figures here are dānestan's, from
 * corpus v16.
 */

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { BuiltForm, FormLevel, Generated } from "../../api/generate";
import { renderApp } from "../../test/render";

function step(ruleId: string, appliedTo: string, affix: string, types = 8337, attested = 748) {
  return {
    rule_id: ruleId,
    affix,
    applied_to: appliedTo,
    label_fa: "پسوند",
    explanation_fa: `از کنون‌کاربن با پسوند ${affix} کارنده‌کاربهر ساخته می‌شود`,
    tags_fa: [],
    built: { types, attested, corpus_version: "v16", band: "high" as const },
    stem_form: null,
    glide_id: null,
    glide_alternatives: [],
  };
}

function found(level: "reading" | "spelling" | "none", poems = 0, poets = 0) {
  return {
    level,
    corpus_version: "v16",
    total_count: poems,
    doc_count: poems,
    author_count: poets,
    first_century: null,
    last_century: null,
    other_readings: [],
    unlinked: level === "spelling",
    wording: "",
  };
}

function levelOf(
  value: FormLevel["level"],
  marks: FormLevel["marks"],
  weakest: FormLevel["weakest_rule"] = null,
): FormLevel {
  return { level: value, confirmed: false, weakest_rule: weakest, marks };
}

function built(
  latin: string,
  fa: string,
  attestation: BuiltForm["attestation"],
  level: FormLevel | undefined,
  paths = [[step("V-024", "dān", "-ā")]],
): BuiltForm {
  return {
    form_latin: latin,
    form_fa: fa,
    word_class: "karandekarbahr",
    depth: paths[0]!.length,
    semantic_tags: [],
    meaning_fa: null,
    attestation,
    paths,
    ...(level ? { level } : {}),
  };
}

const DANA = built(
  "dānā",
  "دانا",
  found("reading", 2118, 160),
  levelOf(3, { corpus: 3, rule: 3, meaning: 3 }, null),
);
const DANGAR = built(
  "dāngar",
  "دانگر",
  found("none"),
  levelOf(
    2,
    { corpus: 0, rule: 3, meaning: null },
    { rule_id: "V-032", affix: "-gar", types: 8339, attested: 139, band: "high" },
  ),
  [[step("V-032", "dān", "-gar", 8339, 139)]],
);
const ZIRDANA = built(
  "zirdānā",
  "زیردانا",
  found("none"),
  levelOf(
    1,
    { corpus: 0, rule: 1, meaning: null },
    { rule_id: "V-076", affix: "zir-", types: 7830, attested: 1, band: "low" },
  ),
  [[step("V-076", "dānest", "zir-", 7830, 1), step("V-024", "zirdān", "-ā")]],
);
const DANAR = built(
  "dānār",
  "دانار",
  found("spelling", 2, 2),
  levelOf(
    2,
    { corpus: 1, rule: 3, meaning: 3 },
    { rule_id: "V-048", affix: "-ār", types: 8337, attested: 285, band: "high" },
  ),
  [[step("V-048", "dān", "-ār", 8337, 285)]],
);

const CLASSES = {
  word_classes: [
    {
      name: "karandekarbahr",
      label_fa: "کارنده‌کاربهر",
      label_is_traditional: false,
      coined_fa: "کارنده‌کاربهر",
      traditional_fa: "صفت فاعلی",
      behnevis: null,
      explanation_fa: "آن که کار را انجام می‌دهد.",
      term_confirmed: true,
      description_en: "",
    },
  ],
};

function serving(forms: BuiltForm[]) {
  const body: Generated = {
    word: "دانستن",
    depth: 2,
    rule_pack_version: "0.1.0",
    lexicon_snapshot_id: "lexicon:abc",
    corpus_version: "v16",
    readings: [
      {
        latin: "dānestan",
        spelling_fa: "دانستن",
        lexicon_category: "مصدر",
        latin_variants: [],
        definition_fa: null,
        built_from: [{ latin: "dān", fa: "دان", word_class: "karbon_do" }],
        truncated: false,
        count: forms.length,
        forms,
      },
    ],
  };
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve({
        ok: true,
        status: 200,
        statusText: "",
        json: async () => (String(url).includes("/rules") ? CLASSES : body),
      } as Response),
    ),
  );
}

async function open() {
  renderApp("/build?word=%D8%AF%D8%A7%D9%86%D8%B3%D8%AA%D9%86&depth=2");
  const heading = await screen.findByRole("heading", { level: 3 });
  await userEvent.click(within(heading).getByRole("button"));
}

function rowOf(fa: string): HTMLElement {
  return screen.getByText(fa).closest("li")!;
}

function order(): string[] {
  return screen.getAllByRole("listitem").map((row) => row.textContent ?? "");
}

beforeEach(() => serving([ZIRDANA, DANGAR, DANA, DANAR]));
afterEach(() => vi.unstubAllGlobals());

describe("each word's level", () => {
  it("is named on the row, with its three bars", async () => {
    await open();
    expect(within(rowOf("دانا")).getByText("آشنا")).toBeInTheDocument();
    expect(within(rowOf("دانگر")).getByText("خوش‌ساخت")).toBeInTheDocument();
    expect(within(rowOf("زیردانا")).getByText("کم‌پشتوانه")).toBeInTheDocument();
    const bars = rowOf("دانگر").querySelectorAll('[data-level="2"] i');
    expect(bars).toHaveLength(3);
  });

  it("gives a familiar word's reason as its poems and poets", async () => {
    await open();
    const row = rowOf("دانا");
    expect(row.textContent).toContain("در ۲٬۱۱۸ سروده از ۱۶۰ شاعر آمده است.");
  });

  it("names the rule a coinage stands on, never that it does not exist", async () => {
    await open();
    const row = rowOf("دانگر");
    expect(row.textContent).toContain("در پیکره نیامده است؛");
    expect(row.textContent).toContain("پسوند -gar ۱۳۹ واژه ساخته که در پیکره آمده‌اند.");
    expect(within(row).getByText("-gar")).toHaveAttribute("dir", "ltr");
    expect(row.textContent).not.toMatch(/وجود ندارد|یافت نشد/);
  });

  it("says why a weakly backed word is weak, in the rule's own counts", async () => {
    await open();
    expect(rowOf("زیردانا").textContent).toContain(
      "پیشوند zir- از ۷٬۸۳۰ واژه‌ای که ساخته، تنها یکی را در پیکره دارد.",
    );
  });

  it("says the letters alone may be another word", async () => {
    await open();
    expect(rowOf("دانار").textContent).toContain(
      "این حرف‌ها در ۲ سروده آمده‌اند، ولی شاید به خوانشی دیگر؛",
    );
  });

  it("says not measured, never a level, where the corpus was not asked", async () => {
    serving([built("dānā", "دانا", null, levelOf(null, { corpus: null, rule: 3, meaning: 3 }))]);
    await open();
    expect(within(rowOf("دانا")).getByText("سنجیده نشده")).toBeInTheDocument();
    expect(within(rowOf("دانا")).queryByText("آشنا")).toBeNull();
  });

  it("explains the three names and the corpus once, above the list", async () => {
    await open();
    const intro = screen.getByText(/هر واژه یک درجه دارد/).closest("div")!;
    expect(intro.textContent).toContain("دست‌کم در ده سروده");
    expect(intro.textContent).toContain("پیکره شعر کهن فارسی است");
    expect(within(intro).getByText("v16")).toHaveAttribute("dir", "ltr");
    expect(intro.textContent).toContain("ممکن است امروز به کار برود");
  });
});

describe("the order", () => {
  it("is by level first, even where the old order said the opposite", async () => {
    // Each pair is one the ranking before 2026-11-13 put the other way round,
    // so this fails on the old comparator. The letters of a weak word in
    // 1,565 poems outranked a well-formed word nobody wrote; the letters of a
    // well-formed word in 4,000 poems outranked a familiar word in twelve.
    const weakButWritten = built(
      "zirdānān",
      "زیردانان",
      found("spelling", 1565, 90),
      ZIRDANA.level,
    );
    const familiarFew = built(
      "dānān",
      "دانان",
      found("reading", 12, 9),
      levelOf(3, { corpus: 2, rule: 3, meaning: 3 }),
    );
    const formedMany = built(
      "Dānest",
      "دانست",
      found("spelling", 4000, 150),
      DANAR.level,
    );
    serving([weakButWritten, formedMany, DANGAR, familiarFew]);
    await open();
    const at = (word: string) => order().findIndex((text) => text.includes(word));
    expect(at("دانان")).toBeLessThan(at("دانست"));
    expect(at("دانگر")).toBeLessThan(at("زیردانان"));
    expect(at("دانست")).toBeLessThan(at("زیردانان"));
  });

  it("puts a word with no level above a weak one and below a well-formed one", async () => {
    const unknown = built("dānestār", "دانستار", found("none"), undefined);
    serving([ZIRDANA, unknown, DANGAR]);
    await open();
    const at = (word: string) => order().findIndex((text) => text.includes(word));
    expect(at("دانگر")).toBeLessThan(at("دانستار"));
    expect(at("دانستار")).toBeLessThan(at("زیردانا"));
  });
});

describe("the evidence behind the button", () => {
  async function evidenceOf(fa: string) {
    await open();
    const row = rowOf(fa);
    await userEvent.click(within(row).getByRole("button", { name: "شواهد" }));
    return row;
  }

  it("is closed until it is asked for", async () => {
    await open();
    expect(within(rowOf("دانگر")).queryByRole("button", { name: /^پیکره/ })).toBeNull();
  });

  it("shows three fields as dots, without numbers", async () => {
    const row = await evidenceOf("دانا");
    for (const name of [/^پیکره: ۳ از ۳/, /^دستور: ۳ از ۳/, /^معنا: ۳ از ۳/]) {
      expect(within(row).getByRole("button", { name })).toBeInTheDocument();
    }
    expect(row.querySelectorAll("button i")).toHaveLength(9);
    expect(row.textContent).not.toContain("۸٬۳۳۷");
  });

  it("says nothing was found, or nothing measured, in words rather than empty dots", async () => {
    const row = await evidenceOf("دانگر");
    expect(within(row).getByRole("button", { name: /^پیکره: نیامده/ })).toBeInTheDocument();
    expect(within(row).getByRole("button", { name: /^معنا: سنجیده نشده/ })).toBeInTheDocument();
  });

  it("says nothing it does not know when an older API sends no level", async () => {
    // Not «سنجیده نشده»: the figures may be behind the press all the same.
    serving([built("dānā", "دانا", found("reading", 2118, 160), undefined)]);
    const row = await evidenceOf("دانا");
    expect(within(row).getByRole("button", { name: "پیکره" })).toBeInTheDocument();
    expect(within(row).queryByText("سنجیده نشده")).toBeNull();
    await userEvent.click(within(row).getByRole("button", { name: "پیکره" }));
    expect(row.textContent).toContain("۲٬۱۱۸ سروده");
  });

  it("draws the letters only as a ring, not a dot", async () => {
    const row = await evidenceOf("دانار");
    const corpus = within(row).getByRole("button", { name: /^پیکره/ });
    expect(corpus.querySelectorAll("i[class*='ring']")).toHaveLength(1);
  });

  it("gives each field's numbers on a press, with the corpus version", async () => {
    const row = await evidenceOf("دانگر");
    const rule = within(row).getByRole("button", { name: /^دستور/ });
    await userEvent.click(rule);
    expect(rule).toHaveAttribute("aria-expanded", "true");
    expect(row.textContent).toContain("V-032 — ۸٬۳۳۹ واژه ساخته، ۱۳۹ تای آن‌ها در پیکرهٔ v16 پیدا شد.");

    await userEvent.click(within(row).getByRole("button", { name: /^پیکره/ }));
    expect(rule).toHaveAttribute("aria-expanded", "false");
    expect(row.textContent).toContain("در پیکرهٔ v16 نیامده است");
  });

  it("names the ground under a chain behind the rule's field", async () => {
    serving([{ ...ZIRDANA, base_attested: false }]);
    const row = await evidenceOf("زیردانا");
    await userEvent.click(within(row).getByRole("button", { name: /^دستور/ }));
    expect(row.textContent).toContain("zirdān در پیکرهٔ v16 نیامده است");
  });
});

describe("a rule's own sentence", () => {
  it("keeps the affix's dash on the affix's side", async () => {
    // The rule pack writes «با پسوند -ande». Printed plain inside Persian, the
    // dash took the line's direction and the reader saw «ande-», a prefix.
    // Measured in the browser on 2026-11-13. The Latin is an island now.
    serving([
      built("dānande", "داننده", found("reading", 306, 61), undefined, [
        [step("V-022", "dān", "-ande", 8308, 350)],
      ]),
    ]);
    await open();
    const row = rowOf("داننده");
    await userEvent.click(within(row).getByRole("button", { name: /راه ساخت/ }));
    const said = within(row).getByText(/کارنده‌کاربهر ساخته می‌شود/);
    expect(within(said).getByText("-ande")).toHaveAttribute("dir", "ltr");
  });
});
