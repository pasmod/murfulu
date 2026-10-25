/**
 * The rules screen.
 *
 * Its reason for existing is the disagreement between what the source says
 * and what the corpus shows, so that is what most of these check — along with
 * the distinction the whole scoring argument rests on: a rule measured at
 * zero is not a rule nobody could measure.
 */

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { RulePack } from "../../api/rules";
import { renderApp } from "../../test/render";

function rule(id: string, extra: Record<string, unknown> = {}) {
  return {
    id,
    family: id[0]!,
    kind: "suffix",
    affix: "-ār",
    affix_fa: "ار",
    input_types: ["karbon_yek"],
    output_types: ["karnam"],
    semantic_tags: [],
    strength: null,
    examples: ["Goftār"],
    label_fa: null,
    explanation_fa: "کارنام ساخته می‌شود",
    active: true,
    needs_expert_check: false,
    productivity: null,
    semantic: null,
    ...extra,
  };
}

function measured(extra: Record<string, unknown> = {}) {
  return {
    rule_id: "V-010",
    authored_strength: null,
    types_built: 1442,
    types_attested: 1106,
    types_confirmed: 40,
    tokens: 900,
    hapaxes: 3,
    types_echoing_source: 0,
    echo_share: 0,
    potential_p: 0.003,
    potential_p_confirmed: null,
    realisation_rate: 0.767,
    measured: true,
    unmeasurable_reason: "",
    band: "high",
    disagrees_with_strength: false,
    expected_band: null,
    corpus_version: "v1",
    ...extra,
  };
}

const PACK: RulePack = {
  rule_pack_version: "0.1.0",
  count: 3,
  corpus_version: "v1",
  measured_rules: 195,
  semantic_rules: 57,
  rules: [
    rule("V-010", {
      strength: "typical",
      semantic: {
        bases: 402,
        typical_bases: [
          { latin: "goft", fa: "گفت", typicality: 0.89 },
          { latin: "raft", fa: "رفت", typicality: 0.87 },
        ],
      },
      productivity: measured({
        disagrees_with_strength: true,
        expected_band: "middle",
        authored_strength: "typical",
      }),
    }),
    rule("N-020", { productivity: measured({ rule_id: "N-020", realisation_rate: 0 }) }),
    rule("S-01", {
      family: "S",
      kind: "stem",
      affix: null,
      productivity: measured({
        rule_id: "S-01",
        measured: false,
        band: null,
        unmeasurable_reason: "a stem rule is a different operation",
      }),
    }),
    // A glide, in the shape the route serves it: no affix, no input class, no
    // tag, no productivity and no semantic centre — because it does not build
    // a word, it decides a letter where two vowels meet.
    {
      id: "G-03",
      family: "G",
      kind: "glide",
      left: "ā",
      right: "e",
      result: "āye",
      examples: ["Pā + e = Pāye"],
      explanation_fa: "هنگام برخورد ā و e واج‌میانجی می‌آید و āye ساخته می‌شود",
      active: true,
      retired_reason: "",
    },
  ],
};

/** Counts are a <Num> beside text, so a sentence is matched on its paragraph. */
function saying(pattern: RegExp) {
  return (_text: string, node: Element | null) => {
    if (!node) return false;
    const hasIt = pattern.test(node.textContent ?? "");
    const childHasIt = Array.from(node.children).some((child) =>
      pattern.test(child.textContent ?? ""),
    );
    return hasIt && !childHasIt;
  };
}

function answers(body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    statusText: "",
    json: async () => body,
  } as Response);
}

beforeEach(() => {
  vi.stubGlobal("fetch", answers(PACK));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("the finding", () => {
  it("puts the disagreements first, because that is what this screen is for", async () => {
    renderApp("/rules");
    const finding = await screen.findByRole("region", { name: /یکی نمی‌گویند/ });
    expect(within(finding).getByText("V-010")).toBeInTheDocument();
  });

  it("calls a disagreement a finding, not an error", async () => {
    renderApp("/rules");
    expect(await screen.findByText(/این یافته است، نه خطا/)).toBeInTheDocument();
  });

  it("shows what the source said and what was measured, side by side", async () => {
    renderApp("/rules");
    const finding = await screen.findByRole("region", { name: /یکی نمی‌گویند/ });
    expect(within(finding).getByText(/سرچشمه: بیشتر/)).toBeInTheDocument();
    expect(within(finding).getByText(/سنجش: بالا/)).toBeInTheDocument();
  });
});

describe("measured and unmeasurable", () => {
  it("does not show a rule nobody could measure as measured at zero", async () => {
    renderApp("/rules?family=S");
    expect(await screen.findByText("سنجیده نشد")).toBeInTheDocument();
  });

  it("gives the reason a rule could not be measured", async () => {
    renderApp("/rules?family=S");
    // The disagreement section is never filtered away, so the S rule is the
    // last row rather than the first.
    const toggles = await screen.findAllByRole("button", { name: "جزئیات" });
    await userEvent.click(toggles[toggles.length - 1]!);
    expect(
      screen.getByText("a stem rule is a different operation"),
    ).toBeInTheDocument();
  });

  it("says which corpus version the numbers belong to", async () => {
    renderApp("/rules");
    expect(await screen.findByText(/سنجیده بر پیکرهٔ/)).toBeInTheDocument();
  });

  it("says plainly when nothing has been measured at all", async () => {
    vi.stubGlobal(
      "fetch",
      answers({ ...PACK, corpus_version: null, measured_rules: 0 }),
    );
    renderApp("/rules");
    expect(
      await screen.findByText(/هنوز هیچ سنجشی بر پیکره انجام نشده است/),
    ).toBeInTheDocument();
  });
});

describe("numerals", () => {
  it("writes even the percentages in Persian digits", async () => {
    // A rule id is an address, not a number, and stays Latin — so the check
    // is on the rate itself. 0.767 written the Persian way.
    renderApp("/rules");
    const rate = new Intl.NumberFormat("fa-IR", {
      style: "percent",
      maximumFractionDigits: 1,
    }).format(0.767);
    expect((await screen.findAllByText(rate))[0]).toBeInTheDocument();
    expect(rate).not.toMatch(/[0-9]/);
  });
});

describe("the length of the list", () => {
  /**
   * Measured in a real browser at 375 px: the whole pack renders 42,840 px of
   * page — 52 phone screens — because all 212 rules are in the DOM at once.
   * The build screen had the same shape and the same answer: open at a
   * readable length, say how many are folded, and open the lot on one press.
   */
  function many(count: number) {
    return {
      ...PACK,
      count,
      rules: Array.from({ length: count }, (_, index) =>
        rule(`V-${String(index + 1).padStart(3, "0")}`),
      ),
    };
  }

  /** The rules list itself. The navigation is a list too, and is not this. */
  const listed = () =>
    within(screen.getByText("V-001").closest("ul")!).getAllByRole("listitem")
      .length;

  it("opens at a readable length and says how many are folded", async () => {
    vi.stubGlobal("fetch", answers(many(60)));
    renderApp("/rules");
    await screen.findByText(saying(/۶۰ دستور نشان داده می‌شود/));
    expect(listed()).toBe(20);

    await userEvent.click(screen.getByRole("button", { name: /۴۰ دستور دیگر/ }));
    expect(listed()).toBe(60);
    expect(screen.queryByRole("button", { name: /دستور دیگر/ })).toBeNull();
  });

  it("offers nothing to open when the list already fits", async () => {
    renderApp("/rules");
    await screen.findByText(saying(/۴ دستور نشان داده می‌شود/));
    expect(screen.queryByRole("button", { name: /دستور دیگر/ })).toBeNull();
  });

  it("folds again when the reader narrows to another family", async () => {
    // Otherwise opening the whole pack and then pressing a family button
    // leaves the next list open too, and the page is long again for a reason
    // the reader did not choose.
    vi.stubGlobal("fetch", answers(many(60)));
    renderApp("/rules");
    await screen.findByText(saying(/۶۰ دستور نشان داده می‌شود/));
    await userEvent.click(screen.getByRole("button", { name: /۴۰ دستور دیگر/ }));
    expect(listed()).toBe(60);

    await userEvent.click(screen.getByRole("button", { name: "کارواژه" }));
    expect(listed()).toBe(20);
  });
});

describe("narrowing", () => {
  it("filters by family", async () => {
    renderApp("/rules");
    await screen.findByText(saying(/۴ دستور نشان داده می‌شود/));
    await userEvent.click(screen.getByRole("button", { name: "نام" }));
    expect(
      await screen.findByText(saying(/۱ دستور نشان داده می‌شود/)),
    ).toBeInTheDocument();
  });

  it("the میانجی button finds the glide rules instead of emptying the list", async () => {
    // Found by pressing it: 17 glide rules sit in the pack, /rules served
    // none of them, and this was the one family with a button and no
    // members — while build results name G-10 and G-11 with nowhere to look
    // them up.
    renderApp("/rules");
    await screen.findByText(saying(/۴ دستور نشان داده می‌شود/));
    await userEvent.click(screen.getByRole("button", { name: "میانجی" }));
    expect(
      await screen.findByText(saying(/۱ دستور نشان داده می‌شود/)),
    ).toBeInTheDocument();
    expect(screen.getByText("G-03")).toBeInTheDocument();
  });
});

describe("a glide rule", () => {
  it("is shown as a meeting of two vowels, not as an affix", async () => {
    // Rendered through the affix row it would be blanks where the affix, the
    // input class and the measurement go — the same mistake the affixes
    // screen made with its twelve empty chips.
    renderApp("/rules");
    const row = (await screen.findByText("G-03")).closest("li")!;
    expect(within(row).getByText("ā")).toBeInTheDocument();
    expect(within(row).getByText("āye")).toBeInTheDocument();
    expect(within(row).getByText(/واج‌میانجی/)).toBeInTheDocument();
    expect(within(row).getByText("Pā + e = Pāye")).toBeInTheDocument();
  });

  it("never puts the English retirement reason on a Persian screen", async () => {
    // Every retired_reason is written in English, for whoever reads the
    // repository. The interface is Persian, so the English one is never shown
    // — what is shown is the Persian authored beside the ruling. S14.
    renderApp("/rules");
    const row = (await screen.findByText("G-03")).closest("li")!;
    expect(within(row).queryByText(/Duplicate of/)).toBeNull();
  });

  it("does not claim a measurement it cannot have", async () => {
    // A glide builds no word, so "not yet measured" would be as wrong as a
    // zero: there is nothing here to measure.
    renderApp("/rules");
    const row = (await screen.findByText("G-03")).closest("li")!;
    // The three things the affix row prints about a measurement. The glide's
    // own Persian explanation ends in «ساخته می‌شود», so the count label is
    // matched as the whole of its element rather than as a substring.
    expect(within(row).queryByText(/^سنجش:/)).toBeNull();
    expect(within(row).queryByText("هنوز سنجشی انجام نشده")).toBeNull();
    expect(within(row).queryByText(/نوشته‌شده/)).toBeNull();
  });
});

describe("the semantic centre of a rule", () => {
  it("says how many written bases the centre was measured from", async () => {
    renderApp("/rules");
    const toggles = await screen.findAllByRole("button", { name: "جزئیات" });
    for (const toggle of toggles) await userEvent.click(toggle);
    // ۴۰۲ in Persian numerals — every count on every screen is.
    expect(screen.getAllByText(/۴۰۲/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("گفت").length).toBeGreaterThan(0);
  });

  it("a rule with no centre says so rather than showing nothing", async () => {
    vi.stubGlobal(
      "fetch",
      answers({
        ...PACK,
        semantic_rules: 0,
        rules: PACK.rules.map((one) => ({ ...one, semantic: null })),
      }),
    );
    renderApp("/rules");
    const toggles = await screen.findAllByRole("button", { name: "جزئیات" });
    await userEvent.click(toggles[0]!);
    expect(
      screen.getAllByText("برای این دستور سنجش معنایی در دست نیست").length,
    ).toBeGreaterThan(0);
  });
});

describe("why a rule was retired", () => {
  // S14. The screen showed a **بازنشسته** badge and stopped there, because
  // every `retired_reason` is written in English for whoever reads the
  // repository and the interface may not invent Persian. So a reader was told
  // *that* a rule no longer applies and never why — which for N-090, the ezāfe
  // filed as word formation, is the whole of the interesting part.
  const RETIRED = {
    ...PACK,
    count: 2,
    rules: [
      rule("N-090", {
        active: false,
        retired_reason: "Not word formation: this is the ezāfe.",
        retired_reason_fa: "واژه‌سازی نیست: این کسرهٔ اضافه است.",
      }),
      rule("N-091", {
        active: false,
        retired_reason: "Retired for a reason nobody has written up.",
        retired_reason_fa: "",
      }),
    ],
  };

  it("says why, in Persian", async () => {
    vi.stubGlobal("fetch", answers(RETIRED));
    renderApp("/rules");
    const row = (await screen.findByText("N-090")).closest("li")!;
    expect(within(row).getByText("بازنشسته")).toBeInTheDocument();
    expect(
      within(row).getByText("واژه‌سازی نیست: این کسرهٔ اضافه است."),
    ).toBeInTheDocument();
    // The English record is never put on a Persian screen.
    expect(within(row).queryByText(/Not word formation/)).toBeNull();
  });

  it("shows the badge alone where nobody has written the Persian", async () => {
    // An unwritten reason must not become a guessed one. The badge is honest
    // on its own; a sentence the interface made up would not be.
    vi.stubGlobal("fetch", answers(RETIRED));
    renderApp("/rules");
    const row = (await screen.findByText("N-091")).closest("li")!;
    expect(within(row).getByText("بازنشسته")).toBeInTheDocument();
    expect(within(row).queryByText(/Retired for a reason/)).toBeNull();
  });
});
