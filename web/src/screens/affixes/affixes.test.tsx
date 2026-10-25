/**
 * Affixes by meaning.
 *
 * The founding question — *which affix means "place"?* — has to be answerable
 * in one look, and the half of the inventory the source says nothing about
 * must not be hidden or misrepresented.
 */

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Affixes } from "../../api/affixes";
import { renderApp } from "../../test/render";

const DATA: Affixes = {
  rule_pack_version: "0.1.0",
  count: 2,
  meanings: [
    {
      tag: "Jā",
      gloss_fa: "جا",
      gloss_en: "place",
      affixes: [
        {
          affix: "-dān",
          affix_fa: "دان",
          rule_id: "N-048",
          kind: "suffix",
          output_types: ["nam"],
          examples: ["Namakdān"],
        },
        {
          affix: "-estān",
          affix_fa: "ستان",
          rule_id: "N-051",
          kind: "suffix",
          output_types: ["nam"],
          examples: [],
        },
      ],
    },
    {
      tag: "Nesbat",
      gloss_fa: "نسبت",
      gloss_en: "relation",
      affixes: [
        {
          affix: "-i",
          affix_fa: "ی",
          rule_id: "N-001",
          kind: "suffix",
          output_types: ["barnam"],
          examples: ["Irāni"],
        },
      ],
    },
  ],
  without_a_meaning: [
    {
      affix: "-vār",
      affix_fa: "وار",
      rule_id: "N-090",
      kind: "suffix",
      output_types: ["barnam"],
      examples: [],
    },
    // Three rules that build no word with an affix, in the three shapes the
    // pack has them: a compounding template, a slot, and a zero-derivation.
    // The source writes a dash for the affix of the first and third, which is
    // exactly what the screen used to render.
    {
      affix: "‒",
      affix_fa: "",
      rule_id: "V-018",
      kind: "template",
      output_types: ["karnam"],
      examples: ["Goftogu"],
    },
    {
      affix: "Nām-",
      affix_fa: "",
      rule_id: "V-078",
      kind: "slot",
      output_types: ["karandekarbahr"],
      examples: ["soxanguy"],
    },
    {
      affix: "‒",
      affix_fa: "",
      rule_id: "V-020",
      kind: "none",
      output_types: ["karnam"],
      examples: ["Sāxt"],
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

beforeEach(() => {
  vi.stubGlobal("fetch", answers(DATA));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("the founding question", () => {
  it("answers 'which affix means place' in one look", async () => {
    renderApp("/affixes");
    const place = await screen.findByRole("heading", { name: /جا/ });
    const card = place.parentElement!;
    expect(within(card).getByText("-dān")).toBeInTheDocument();
    expect(within(card).getByText("-estān")).toBeInTheDocument();
  });

  it("leads with the meaning, not the affix", async () => {
    renderApp("/affixes");
    const headings = await screen.findAllByRole("heading", { level: 2 });
    // The Persian gloss is the heading; the affixes sit under it.
    expect(headings[0]).toHaveTextContent("جا");
  });

  it("shows both scripts for every affix", async () => {
    renderApp("/affixes");
    expect(await screen.findByText("-dān")).toHaveAttribute("dir", "ltr");
    expect(screen.getByText("دان")).toBeInTheDocument();
  });

  it("names the tag, which is what a search would use", async () => {
    renderApp("/affixes");
    expect(await screen.findByText("Jā")).toBeInTheDocument();
  });
});

describe("filtering", () => {
  it("narrows by the Persian meaning", async () => {
    renderApp("/affixes");
    await screen.findByRole("heading", { name: /جا/ });
    await userEvent.type(screen.getByRole("combobox"), "نسبت");
    expect(screen.queryByRole("heading", { name: /^جا/ })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /نسبت/ })).toBeInTheDocument();
  });

  it("narrows by the affix itself", async () => {
    renderApp("/affixes");
    await screen.findByRole("heading", { name: /جا/ });
    await userEvent.type(screen.getByRole("combobox"), "-dān");
    expect(screen.getByRole("heading", { name: /جا/ })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /نسبت/ })).not.toBeInTheDocument();
  });
});

describe("what the source does not say", () => {
  it("shows the untagged affixes apart, and says they are not meaningless", async () => {
    renderApp("/affixes");
    const silent = await screen.findByRole("region", {
      name: /سرچشمه معنایی برایشان ننوشته/,
    });
    expect(within(silent).getByText("-vār")).toBeInTheDocument();
    expect(within(silent).getByText(/بی‌معنا بودن آنها نیست/)).toBeInTheDocument();
  });

  it("says when an affix has no example recorded", async () => {
    renderApp("/affixes");
    expect(await screen.findByText("نمونه‌ای ثبت نشده")).toBeInTheDocument();
  });
});

describe("the rules that build no word with an affix", () => {
  /**
   * Found by looking at the screen: nineteen of the eighty-one entries in the
   * untagged list are not affixation at all — ten compounding templates, six
   * slots, three zero-derivations — and twelve of them rendered as a bare
   * `‒`, twelve identical blank chips in a row on a screen called *affixes*.
   *
   * They are not dropped. Where a template joins two words with nothing
   * between them, *nothing* is the answer, and hiding the row would leave a
   * reader believing the inventory is only affixes. They are shown as what
   * they are, with the example — which is the only readable thing about a
   * rule whose affix is a dash.
   */
  it("keeps them out of the list of affixes", async () => {
    renderApp("/affixes");
    const silent = await screen.findByRole("region", {
      name: /سرچشمه معنایی برایشان ننوشته/,
    });
    expect(within(silent).getByText("-vār")).toBeInTheDocument();
    expect(within(silent).queryByText("‒")).toBeNull();
    expect(within(silent).queryByText("Nām-")).toBeNull();
  });

  it("shows them under their own heading instead", async () => {
    renderApp("/affixes");
    const joined = await screen.findByRole("region", { name: /وندی ندارند/ });
    expect(within(joined).getByText("V-018")).toBeInTheDocument();
    expect(within(joined).getByText("V-078")).toBeInTheDocument();
    expect(within(joined).getByText("V-020")).toBeInTheDocument();
  });

  it("shows the example, because the affix column has nothing to say", async () => {
    renderApp("/affixes");
    const joined = await screen.findByRole("region", { name: /وندی ندارند/ });
    expect(within(joined).getByText("Goftogu")).toBeInTheDocument();
    expect(within(joined).getByText("soxanguy")).toBeInTheDocument();
    expect(within(joined).getByText("Sāxt")).toBeInTheDocument();
  });

  it("counts the two groups apart, so neither number is inflated", async () => {
    renderApp("/affixes");
    const silent = await screen.findByRole("region", {
      name: /سرچشمه معنایی برایشان ننوشته/,
    });
    const joined = screen.getByRole("region", { name: /وندی ندارند/ });
    // The fixture has four untagged entries: one affix and three that are not.
    // Counting all four as affixes is what the screen used to do.
    expect(silent.textContent).toContain("۱ وند.");
    expect(joined.textContent).toContain("۳ دستور.");
  });
});
