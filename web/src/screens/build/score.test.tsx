/**
 * The score on the build table, and the sorting and filtering it makes
 * possible — the project lead's choice of 2026-11-21 (DECISIONS), replacing
 * the three levels of 2026-11-13.
 */

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { BuiltForm, FormScore, Generated } from "../../api/generate";
import { renderApp } from "../../test/render";

const ROUTE = "/build?word=%D8%AF%D8%A7%D9%86%D8%B3%D8%AA%D9%86&depth=2";

function step(ruleId: string, appliedTo: string, affix: string | null) {
  return {
    rule_id: ruleId,
    affix,
    applied_to: appliedTo,
    label_fa: "پسوند",
    explanation_fa: `دستور ${ruleId}`,
    tags_fa: [],
    stem_form: null,
    glide_id: null,
    glide_alternatives: [],
  };
}

function scored(
  value: number | null,
  corpus: number | null,
  rule: number,
  weakest: FormScore["weakest_rule"] = null,
): FormScore {
  return {
    value,
    corpus,
    rule,
    confirmed: false,
    weakest_rule: weakest,
    meaning_mark: 2,
  };
}

function attested(level: "reading" | "spelling" | "none", docs = 0) {
  return {
    level,
    corpus_version: "v1",
    total_count: docs,
    doc_count: docs,
    author_count: Math.max(1, Math.floor(docs / 3)),
    first_century: 11,
    last_century: 13,
    other_readings: [],
    unlinked: false,
    wording: "",
  };
}

function form(
  latin: string,
  fa: string,
  wordClass: string,
  attestation: BuiltForm["attestation"],
  score: FormScore | undefined,
  affix = "-ā",
): BuiltForm {
  return {
    form_latin: latin,
    form_fa: fa,
    word_class: wordClass,
    depth: 1,
    semantic_tags: [],
    meaning_fa: null,
    attestation,
    score,
    paths: [[step("V-024", "dān", affix)]],
  };
}

const ZIR = { rule_id: "V-076", affix: "zir-", types: 7830, attested: 1 };
const VA = { rule_id: "V-070", affix: "vā-", types: 7835, attested: 38 };
const A = { rule_id: "V-024", affix: "-ā", types: 8337, attested: 748 };

/** Four words, given out of order, so the screen's own order shows. */
const FORMS = [
  form(
    "zirdānā",
    "زیردانا",
    "karandekarbahr",
    attested("none"),
    scored(1, 0, 1, ZIR),
    "zir-",
  ),
  form(
    "dānā",
    "دانا",
    "karandekarbahr",
    attested("reading", 2118),
    scored(100, 70, 30, A),
  ),
  form("vādān", "وادان", "nam", attested("none"), scored(17, 0, 17, VA), "vā-"),
  // In more texts than any other, as letters only: so sorting by texts and
  // sorting by score disagree about it.
  form("Row", "رو", "nam", attested("spelling", 5000), scored(45, 35, 10, VA)),
  form(
    "dānande",
    "داننده",
    "karandekarbahr",
    attested("reading", 306),
    scored(93, 63, 30, A),
    "-ande",
  ),
];

function built(forms: BuiltForm[]): Generated {
  return {
    word: "دانستن",
    depth: 2,
    rule_pack_version: "0.1.0",
    lexicon_snapshot_id: "lexicon:abc",
    corpus_version: "v1",
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
}

function answers(body: unknown) {
  return {
    ok: true,
    status: 200,
    statusText: "",
    json: async () => body,
  } as Response;
}

function serve(forms: BuiltForm[]) {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve(
        String(url).includes("/rules")
          ? answers({ word_classes: [] })
          : answers(built(forms)),
      ),
    ),
  );
}

beforeEach(() => serve(FORMS));
afterEach(() => vi.unstubAllGlobals());

/** The words in the order the table shows them. */
function order(): string[] {
  const list = screen.getByRole("tabpanel");
  return within(list)
    .getAllByRole("listitem")
    .map((row) => row.querySelector("span span")?.textContent ?? "");
}

describe("each word's score", () => {
  it("is a number from 0 to 100 on the row, said in full for a screen reader", async () => {
    renderApp(ROUTE);
    const row = (await screen.findByText("دانا")).closest("li")!;
    expect(within(row).getByLabelText("امتیاز ۱۰۰ از ۱۰۰")).toBeInTheDocument();
  });

  it("is a dash, never a zero, where nothing was measured", async () => {
    serve([form("dānā", "دانا", "nam", null, scored(null, null, 15))]);
    renderApp(ROUTE);
    const row = (await screen.findByText("دانا")).closest("li")!;
    expect(within(row).getByTitle("سنجیده نشده")).toHaveTextContent("—");
    expect(within(row).queryByText("۰")).toBeNull();
  });

  it("is explained once, under the table, as rough and about poetry", async () => {
    renderApp(ROUTE);
    await screen.findByText("دانا");
    expect(screen.getByText(/بیشترش شعر/)).toBeInTheDocument();
    expect(screen.getByText(/اندازه‌ای\s+تقریبی/)).toBeInTheDocument();
  });

  it("gives its two parts behind the evidence, out of 70 and 30", async () => {
    renderApp(ROUTE);
    const row = (await screen.findByText("داننده")).closest("li")!;
    await userEvent.click(within(row).getByRole("button", { name: "شواهد" }));
    expect(
      within(row).getByRole("button", { name: /پیکره: ۶۳ از ۷۰/ }),
    ).toBeInTheDocument();
    expect(
      within(row).getByRole("button", { name: /دستور: ۳۰ از ۳۰/ }),
    ).toBeInTheDocument();
  });

  it("says why a weak rule scores low, in the rule's own counts", async () => {
    renderApp(ROUTE);
    const row = (await screen.findByText("زیردانا")).closest("li")!;
    await userEvent.click(within(row).getByRole("button", { name: "شواهد" }));
    const reason = within(row).getByText(/در پیکره نیامده است/);
    expect(reason).toHaveTextContent(
      /۷٬?۸۳۰ واژه می‌سازد و تنها یکی از آن‌ها در پیکره آمده است/,
    );
  });

  it("says a middling rule's rate per thousand, never a percentage", async () => {
    renderApp(ROUTE);
    const row = (await screen.findByText("وادان")).closest("li")!;
    await userEvent.click(within(row).getByRole("button", { name: "شواهد" }));
    expect(within(row).getByText(/در پیکره نیامده است/)).toHaveTextContent(
      /از هر ۱٬?۰۰۰ واژه‌ای که می‌سازد، حدود ۵ تا/,
    );
  });

  it("keeps an affix's dash on the affix's side", async () => {
    renderApp(ROUTE);
    const row = (await screen.findByText("زیردانا")).closest("li")!;
    const chip = within(row).getByText("zir-");
    expect(chip).toHaveAttribute("dir", "ltr");
  });
});

describe("the order", () => {
  it("is by score, highest first", async () => {
    renderApp(ROUTE);
    await screen.findByText("دانا");
    expect(order()).toEqual(["دانا", "داننده", "رو", "وادان", "زیردانا"]);
  });

  it("can be by the texts a word is in, or by the alphabet", async () => {
    renderApp(ROUTE);
    await screen.findByText("دانا");
    const head = screen.getAllByRole("button", { name: /در پیکره/ })[0]!;
    await userEvent.click(head);
    expect(order().slice(0, 3)).toEqual(["رو", "دانا", "داننده"]);
    await userEvent.click(screen.getAllByRole("button", { name: /^واژه/ })[0]!);
    expect(order()).toEqual(["دانا", "داننده", "رو", "زیردانا", "وادان"]);
  });
});

describe("the keyboard", () => {
  it("moves between the class tabs with the arrows, one tab stop for the row", async () => {
    renderApp(ROUTE);
    await screen.findByText("دانا");
    const tabs = screen.getAllByRole("tab");
    expect(tabs.filter((one) => one.tabIndex === 0)).toHaveLength(1);
    tabs[0]!.focus();
    // Right to left: the left arrow is the next tab.
    await userEvent.keyboard("{ArrowLeft}");
    const now = screen.getAllByRole("tab");
    expect(now[1]).toHaveAttribute("aria-selected", "true");
    expect(now[1]).toHaveFocus();
    await userEvent.keyboard("{Home}");
    expect(screen.getAllByRole("tab")[0]).toHaveAttribute("aria-selected", "true");
  });

  it("chooses a filter with the arrows, as native radio buttons do", async () => {
    renderApp(ROUTE);
    await screen.findByText("دانا");
    const all = screen.getAllByRole("radio", { name: "همه" })[0]!;
    expect(all).toBeChecked();
    expect(all.tagName).toBe("INPUT");
  });
});

describe("the filters", () => {
  it("keep a score range, and say how many words are left", async () => {
    renderApp(ROUTE);
    await screen.findByText("دانا");
    await userEvent.click(screen.getByRole("radio", { name: "زیر ۴۰" }));
    expect(order()).toEqual(["وادان", "زیردانا"]);
    expect(screen.getByRole("status")).toHaveTextContent("۲ واژه");
  });

  it("keep only what the corpus has, or only what it does not", async () => {
    renderApp(ROUTE);
    await screen.findByText("دانا");
    await userEvent.click(screen.getByRole("radio", { name: "در پیکره آمده" }));
    expect(order()).toEqual(["دانا", "داننده", "رو"]);
    await userEvent.click(
      screen.getByRole("radio", { name: "در پیکره نیامده" }),
    );
    expect(order()).toEqual(["وادان", "زیردانا"]);
  });

  it("combine with the class tab", async () => {
    renderApp(ROUTE);
    await screen.findByText("دانا");
    await userEvent.click(
      screen.getByRole("radio", { name: "در پیکره نیامده" }),
    );
    await userEvent.click(screen.getByRole("tab", { name: /nam/ }));
    expect(order()).toEqual(["وادان"]);
  });

  it("say so when nothing is left, rather than showing an empty table", async () => {
    renderApp(ROUTE);
    await screen.findByText("دانا");
    await userEvent.click(screen.getByRole("radio", { name: "۷۰ و بیشتر" }));
    await userEvent.click(screen.getByRole("radio", { name: "در پیکره نیامده" }));
    expect(
      screen.getByText(/با این گزینه‌ها هیچ واژه‌ای نمی‌ماند/),
    ).toBeInTheDocument();
  });
});

describe("the short vowels", () => {
  it("are shown on the word, from the API, while the plain spelling stays the key", async () => {
    // DECISIONS 2026-11-21: marks made from the reading, for display only.
    serve([
      {
        ...form("dānande", "داننده", "karandekarbahr", attested("reading", 306), scored(89, 63, 26, A)),
        form_fa_marked: "دانَنده",
      },
    ]);
    renderApp(ROUTE);
    expect(await screen.findByText("دانَنده")).toBeInTheDocument();
    expect(screen.queryByText("داننده")).toBeNull();
  });

  it("fall back to the plain spelling when an older API sends none", async () => {
    renderApp(ROUTE);
    expect(await screen.findByText("داننده")).toBeInTheDocument();
  });
});

