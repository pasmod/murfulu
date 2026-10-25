/**
 * The build screen.
 *
 * What is checked is what the project keeps insisting on: forms are ranked by
 * evidence rather than by depth, every alternative derivation is kept, and the
 * four states of evidence never collapse into each other.
 */

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { BuiltForm, Generated } from "../../api/generate";
import { renderApp } from "../../test/render";
import {
  FROM_LEXICON,
  FUNCTION_WORD_SHORT,
  NEEDS_REVIEW,
  notFound,
} from "../../text/lexicon";

function step(
  ruleId: string,
  appliedTo: string,
  affix: string | null,
  tagsFa: string[] = [],
) {
  return {
    rule_id: ruleId,
    affix,
    applied_to: appliedTo,
    label_fa: "پسوند",
    explanation_fa: `دستور ${ruleId}`,
    tags_fa: tagsFa,
    stem_form: null,
    glide_id: null,
    glide_alternatives: [],
  };
}

function form(
  latin: string,
  fa: string,
  wordClass: string,
  attestation: BuiltForm["attestation"],
  paths = [[step("V-010", "raft", "-ār")]],
): BuiltForm {
  return {
    form_latin: latin,
    form_fa: fa,
    word_class: wordClass,
    depth: paths[0]!.length,
    semantic_tags: [],
    meaning_fa: null,
    attestation,
    paths,
  };
}

function attested(level: "reading" | "spelling" | "none", docs = 0) {
  return {
    level,
    corpus_version: "v1",
    total_count: docs * 2,
    doc_count: docs,
    author_count: docs,
    first_century: 11,
    last_century: 13,
    other_readings: level === "spelling" ? ["goftār"] : [],
    unlinked: false,
    wording: "",
  };
}

const BUILT: Generated = {
  word: "رفتن",
  depth: 2,
  rule_pack_version: "0.1.0",
  lexicon_snapshot_id: "lexicon:abc",
  corpus_version: "v1",
  readings: [
    {
      latin: "raftan",
      spelling_fa: "رفتن",
      lexicon_category: "مصدر",
      latin_variants: [],
      definition_fa: null,
      built_from: [{ latin: "raft", fa: "رفت", word_class: "karbon_yek" }],
      truncated: false,
      count: 3,
      forms: [
        form("Ravešnāk", "روشناک", "barnam", attested("none")),
        form("Raftār", "رفتار", "karnam", attested("reading", 400), [
          [step("V-010", "raft", "-ār")],
          [step("V-011", "raft", "-ār")],
        ]),
        form("Raveš", "روش", "karnam", attested("spelling", 12)),
      ],
    },
  ],
};

const CLASSES = {
  word_classes: [
    {
      name: "karnam",
      label_fa: "کارنام",
      label_is_traditional: false,
      coined_fa: "کارنام",
      traditional_fa: "اسم مصدر / اسم معنی",
      behnevis: "Kārnām",
      explanation_fa: "خودِ کار، که همچون نام آورده می‌شود.",
      term_confirmed: true,
      description_en: "",
    },
    {
      name: "barnam",
      label_fa: "برنام",
      label_is_traditional: false,
      coined_fa: "برنام",
      traditional_fa: "صفت",
      behnevis: "Barnām",
      explanation_fa: "واژه‌ای که چگونگیِ نام را می‌گوید.",
      term_confirmed: true,
      description_en: "",
    },
  ],
};

function answers(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: "",
    json: async () => body,
  } as Response;
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve(
        String(url).includes("/rules") ? answers(CLASSES) : answers(BUILT),
      ),
    ),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const ROUTE = "/build?word=%D8%B1%D9%81%D8%AA%D9%86&depth=2";


/**
 * Open a word class, so its rows are on the page.
 *
 * The classes are folded from 2026-08-18 and only **one is open at a time**
 * from later the same day — the words render below the grid, and two open
 * classes put the long scroll back. So a test that reads a row asks for the
 * class it lives in, the way a reader does. Without a name it opens the first,
 * which is where a single-class fixture puts everything.
 */
async function showForms(name?: RegExp) {
  const headings = await screen.findAllByRole("heading", { level: 3 });
  const wanted = name
    ? headings.find((one) => name.test(one.textContent ?? ""))
    : headings[0];
  await userEvent.click(within(wanted!).getByRole("button"));
}

describe("the build screen", () => {
  it("says when the dictionary itself doubts the reading", async () => {
    // بلند has two readings in the snapshot: Baland, filed as an اسم ذات and
    // flagged needs_review, and boland, filed as a صفت and clean. The screen
    // showed Baland first, built 2,612 words from it, and never mentioned the
    // flag — while the same snapshot spells سربلند sarboland. 31.5% of active
    // rows carry the flag.
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [{ ...BUILT.readings[0]!, needs_review: true }],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    expect(await screen.findByText(NEEDS_REVIEW)).toBeInTheDocument();
  });

  it("says nothing about review when the dictionary is content", async () => {
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("رفتار");
    expect(screen.queryByText(/بازبینی‌نشده/)).toBeNull();
  });

  it("names the rule the figure belongs to, and what it was measured against", async () => {
    // Measured on the chain's FIRST rule, and 94.1% of scored forms are two
    // steps deep — so "this rule" used to name a rule the row is not built by.
    // It now always names the rule and shows the bases the number was measured
    // against, because a percentage whose method a reader was never told
    // cannot be read at all. Project lead, 2026-08-18. See S15.
    const deep = {
      ...form("yānisār", "یانیسار", "karnam", attested("none"), [
        [step("N-098", "Yān", "-i"), step("N-055", "yāni", "-sār")],
      ]),
      semantic: {
        typicality: 0.8625,
        rule_id: "N-098",
        base: "Yān",
        bases_measured: 316,
        rule_says_fa: "از نام با پسوند -i نام ساخته می‌شود",
        typical: [
          { latin: "gol", fa: "گل", typicality: 0.91, of: [] },
          { latin: "row", fa: "رو", typicality: 0.89, of: ["رفتن"] },
        ],
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [{ ...BUILT.readings[0]!, count: 1, forms: [deep] }],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    await showForms();
    // Twice now: on the step that applied it, and under the semantic block,
    // which names the rule it belongs to instead of only its id.
    expect(await screen.findAllByText("N-098")).not.toHaveLength(0);
    // The sentence says the rule *built a word* from these stems and that word
    // was found — not that the stems were found. Those are different claims,
    // and the first shipped before being caught on 2026-08-18.
    expect(screen.getByText(/واژه‌ای ساخته که در پیکرهٔ/)).toBeInTheDocument();
    expect(screen.queryByText(/بن‌هایی که در پیکره یافته‌ایم/)).toBeNull();
    const said = screen.getByText(/مرکزِ معنایی/).parentElement!;
    expect(said.textContent).toContain("گل");
    expect(said.textContent).toContain("رو");
    expect(said.textContent).toContain("Yān");
    // **The infinitive in brackets where the stem has one.** رو is nothing a
    // reader can place; رو (رفتن) is. A base with no verb behind it — گل, a
    // noun — gets no brackets rather than an empty pair.
    expect(said.textContent).toContain("(رفتن)");
    expect(said.textContent).not.toContain("گل ()");
    // And the rule is written out here the way every step row writes it.
    expect(said.textContent).toContain("از نام با پسوند -i نام ساخته می‌شود");
    // The old bare-percentage sentence is gone.
    expect(screen.queryByText(/سنجیده بر گام نخست/)).toBeNull();
    expect(screen.queryByText(/در میان همهٔ واژه/)).toBeNull();
  });

  it("says nothing about meaning where there is nothing to check it against", async () => {
    // An absent artefact is legitimate. A figure with no bases beside it is
    // precisely the thing that could not be read, so it is not shown at all
    // rather than shown alone.
    const bare = {
      ...form("yāni", "یانی", "karnam", attested("none"), [
        [step("N-098", "Yān", "-i")],
      ]),
      semantic: {
        typicality: 0.828,
        rule_id: "N-098",
        base: "Yān",
        bases_measured: 316,
        typical: [],
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [{ ...BUILT.readings[0]!, count: 1, forms: [bare] }],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("یانی");
    expect(screen.queryByText(/مرکزِ معنایی/)).toBeNull();
  });

  it("shows the dictionary's own definition, marked as the dictionary's", async () => {
    // 96.1% of karbon's rows carry one and nothing of ours read it until the
    // columns were listed. Labelled «از واژه‌نامهٔ کاربن» because an
    // unattributed sentence here would read as something Murfulu worked out.
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [
                  { ...BUILT.readings[0]!, definition_fa: "دراز. مرتفع" },
                ],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    expect(await screen.findByText(/دراز. مرتفع/)).toBeInTheDocument();
    expect(screen.getByText(FROM_LEXICON)).toBeInTheDocument();
  });

  it("filters by stem, and the class counts follow", async () => {
    // A stem is where a word starts, so it is the other axis a reader wants
    // beside the class. Measured on گفتن: 16 words from گفت, 22 from گو, and
    // none reachable from both. Asked for by the project lead on 2026-08-18.
    const twoStems = {
      ...BUILT,
      readings: [
        {
          ...BUILT.readings[0]!,
          count: 3,
          built_from: [
            { latin: "raft", fa: "رفت", word_class: "karbon_yek" },
            { latin: "row", fa: "رو", word_class: "karbon_do" },
          ],
          forms: [
            form("Raftār", "رفتار", "karnam", attested("none"), [
              [step("V-010", "raft", "-ār")],
            ]),
            form("Ravande", "رونده", "karandekarbahr", attested("none"), [
              [step("V-020", "row", "-ande")],
            ]),
          ],
        },
      ],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules") ? answers(CLASSES) : answers(twoStems),
        ),
      ),
    );
    renderApp(ROUTE);

    // Both stems on, both classes offered.
    const stems = await screen.findAllByRole("button", { pressed: true });
    expect(stems).toHaveLength(2);
    expect(screen.getAllByRole("heading", { level: 3 })).toHaveLength(2);

    // Turn one off: the classes recount against what is left.
    await userEvent.click(stems[0]!);
    expect(stems[0]).toHaveAttribute("aria-pressed", "false");
    expect(screen.getAllByRole("heading", { level: 3 })).toHaveLength(1);

    // And back on.
    await userEvent.click(stems[0]!);
    expect(screen.getAllByRole("heading", { level: 3 })).toHaveLength(2);
  });

  it("never turns the last stem off, which would empty the screen", async () => {
    renderApp(ROUTE);
    const stems = await screen.findAllByRole("button", { pressed: true });
    for (const one of stems) await userEvent.click(one);
    // Whatever the reader pressed, something is still showing.
    expect(screen.getAllByRole("button", { pressed: true }).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getAllByRole("heading", { level: 3 }).length,
    ).toBeGreaterThan(0);
  });

  it("shows the classes first and the words only when one is asked for", async () => {
    // رفتن at depth 2 answers with 660 words in 8 classes, per reading. Every
    // group used to be open at twenty rows, so the screen handed back a scroll
    // of rows with the headings buried in it — the categories existed and were
    // useless. The project lead named it on 2026-08-18.
    renderApp(ROUTE);

    // The class is on screen, with its count and what it means.
    const heading = await screen.findByRole("heading", {
      level: 3,
      name: /کارنام/,
    });
    const toggle = within(heading).getByRole("button");
    expect(toggle).toHaveAttribute("aria-expanded", "false");

    // Its words are not.
    expect(screen.queryByText("رفتار")).toBeNull();

    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(await screen.findByText("رفتار")).toBeInTheDocument();
  });

  it("opens one class without opening the others", async () => {
    renderApp(ROUTE);
    const headings = await screen.findAllByRole("heading", { level: 3 });
    expect(headings.length).toBeGreaterThan(1);
    await userEvent.click(within(headings[0]!).getByRole("button"));
    expect(within(headings[0]!).getByRole("button")).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(within(headings[1]!).getByRole("button")).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("marks a definition karbon cut, and leaves a whole one alone", async () => {
    // The screens appended «…» to every definition on the strength of karbon
    // cutting at 200 characters. Only 53.5% of v11's 17,471 definitions are
    // anywhere near that; the other 8,118 end in a full stop and their own
    // citation, and فنا — 90 characters, complete — was shown as
    // «…(فهرست مخزن الادویه).» with an ellipsis after the stop.
    const whole = "دارویی است که آن را به فارسی روباه تربک خوانند. (مخزن)";
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [
                  { ...BUILT.readings[0]!, definition_fa: whole },
                ],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    const shown = await screen.findByText(whole, { exact: false });
    expect(shown.textContent).toContain(whole);
    expect(shown.textContent).not.toContain("…");
  });

  it("does mark one that karbon cut at its 200-character limit", async () => {
    const cut = "ا".repeat(200);
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [{ ...BUILT.readings[0]!, definition_fa: cut }],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    const shown = await screen.findByText(cut, { exact: false });
    expect(shown.textContent).toContain("…");
  });

  it("says nothing where the dictionary has no definition", async () => {
    // Every class is 100% covered except مصدر, which is 0 of 1,752 — and a
    // verb is what this screen mostly starts from.
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("رفتار");
    expect(screen.queryByText(FROM_LEXICON)).toBeNull();
  });

  it("shows a second pronunciation the dictionary lists", async () => {
    // برنا is barnā and the same lexicon row also says bornā. The screen
    // printed the first and never said the second existed, so a reader who
    // hears bornā had no way to tell whether we knew it. 7,181 of 44,788
    // readings — 16.0% — carry one. Shown, never chosen between.
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [
                  { ...BUILT.readings[0]!, latin_variants: ["bornā"] },
                ],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    expect(await screen.findByText("bornā")).toBeInTheDocument();
  });

  it("says nothing about a second pronunciation when there is none", async () => {
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("رفتار");
    expect(screen.queryByText(/چنین هم نوشته/)).toBeNull();
  });

  it("shows a group's first rows and offers the rest, saying how many", async () => {
    // Measured in a real browser at 375 px: بلند at depth 2 rendered 3,185
    // rows and 588,102 px of page — 724 phone screens — and رفتن 180,547 px.
    // Every form the engine made was in the DOM at once.
    //
    // Nothing is hidden: the count of what is folded away is on the button
    // that opens it, and one press shows the lot. What changes is that the
    // page starts at a length somebody can read.
    const many = Array.from({ length: 30 }, (_, index) =>
      form(`Raft${index}`, `رفت${index}`, "karnam", attested("none")),
    );
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [{ ...BUILT.readings[0]!, count: 30, forms: many }],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    await showForms();
    await screen.findByRole("heading", { name: /کارنام/ });
    // Counted rather than named: the last tie-break is alphabetical, so which
    // twenty come first is not the point — how many do. Counted by the
    // «راه ساخت» control, one per row; it used to be the copy button, which
    // the project lead removed on 2026-08-18.
    const rows = () =>
      screen.getAllByRole("button", { name: /راه ساخت/ }).length;
    expect(rows()).toBe(20);

    await userEvent.click(screen.getByRole("button", { name: /۱۰ واژهٔ دیگر/ }));
    expect(rows()).toBe(30);
    expect(screen.queryByRole("button", { name: /واژهٔ دیگر/ })).toBeNull();
  });

  it("does not offer to expand a group that is already whole", async () => {
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("رفتار");
    expect(screen.queryByRole("button", { name: /واژهٔ دیگر/ })).toBeNull();
  });

  it("groups results by what they are, named in Persian", async () => {
    renderApp(ROUTE);
    expect(
      await screen.findByRole("heading", { name: /کارنام/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /برنام/ })).toBeInTheDocument();
  });

  it("ranks by evidence, never by depth", async () => {
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("رفتار");
    // The open class's words render below the grid, not inside the tile, so
    // the panel is scoped by its own id rather than by the heading's parent.
    const group = document.querySelector('[id^="words-"]') as HTMLElement;
    const words = within(group)
      .getAllByText(/^(رفتار|روش)$/)
      .map((node) => node.textContent);
    // Confirmed reading first, bare spelling second.
    expect(words).toEqual(["رفتار", "روش"]);
  });

  it("does not put a rare word above a common one for being in the dictionary", async () => {
    // Found by building گفتن and reading the list. گویه, in 6 poems, sat
    // above گفت, in 19,839, because the sort put the attestation *level*
    // first — and the level says whether the lexicon holds a headword for
    // that spelling, which is a fact about the dictionary, not about the
    // word. The level still breaks ties; it no longer outranks the evidence.
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [
                  {
                    ...BUILT.readings[0]!,
                    count: 2,
                    forms: [
                      form("Guye", "گویه", "karnam", attested("reading", 6)),
                      // The lexicon reads گفت as `goft`, which is `Goft` in
                      // another class — one word, so the count is ours. The
                      // shared helper's stand-in reading would make it a
                      // different word, which is the case below rather than
                      // this one.
                      form("Goft", "گفت", "karnam", {
                        ...attested("spelling", 19839),
                        other_readings: ["goft"],
                      }),
                    ],
                  },
                ],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("گفت");
    // The open class's words render below the grid, not inside the tile, so
    // the panel is scoped by its own id rather than by the heading's parent.
    const group = document.querySelector('[id^="words-"]') as HTMLElement;
    const words = within(group)
      .getAllByText(/^(گفت|گویه)$/)
      .map((node) => node.textContent);
    expect(words).toEqual(["گفت", "گویه"]);
  });

  it("never ranks a form on a function word's count, and says so instead", async () => {
    // karbon 1.2.0 reads که as the adjective *keh*, and the noun *Keh* built
    // from it was credited with the conjunction's 609,699 occurrences — first
    // on the screen, and "ours" because the case-folded reading matched. The
    // API now marks the letters as a function word's and credits nothing.
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [
                  {
                    ...BUILT.readings[0]!,
                    count: 2,
                    forms: [
                      form("Keh", "که", "karnam", {
                        ...attested("spelling", 0),
                        other_readings: ["keh"],
                        function_word: "conjunction",
                      }),
                      form("Kehin", "کهین", "karnam", attested("reading", 5)),
                    ],
                  },
                ],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("کهین");
    const group = document.querySelector('[id^="words-"]') as HTMLElement;
    const words = within(group)
      .getAllByText(/^(که|کهین)$/)
      .map((node) => node.textContent);
    expect(words).toEqual(["کهین", "که"]);
    expect(within(group).getByText(FUNCTION_WORD_SHORT)).toBeInTheDocument();
  });

  it("does not rank a form on a count the dictionary says is another word", async () => {
    // Found by re-reading رفتن after the ranking was changed to sort on the
    // count: the screen opened on روی — `ravi`, 31,830 poems — which the
    // lexicon reads as *Rui*, "face". Behind it رو (*Ru*) and روا (*Revā*).
    // رفتار at 1,091 and روش at 912, the outputs the plan names, sat below
    // all three.
    //
    // The narrow rule: when the lexicon holds a reading for that spelling and
    // none of them is ours, the count is evidence about a different word.
    // Case is folded first — گفت is `Goft` to us and `goft` in the lexicon,
    // one word in two classes, and demoting it would undo the fix above.
    //
    // Measured on the real pack: 11 of رفتن's 500 forms, 9 of مهر's, 1 of
    // گفتن's. Narrow on purpose — where the lexicon knows no reading at all,
    // nothing here can tell رفتی from گفتار, and neither is touched.
    const elsewhere = attested("spelling", 31830);
    elsewhere.other_readings = ["Rui"];
    const ourWord = attested("spelling", 1091);
    ourWord.other_readings = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [
                  {
                    ...BUILT.readings[0]!,
                    count: 2,
                    forms: [
                      form("ravi", "روی", "karnam", elsewhere),
                      form("Raftār", "رفتار", "karnam", ourWord),
                    ],
                  },
                ],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("رفتار");
    // The open class's words render below the grid, not inside the tile, so
    // the panel is scoped by its own id rather than by the heading's parent.
    const group = document.querySelector('[id^="words-"]') as HTMLElement;
    const words = within(group)
      .getAllByText(/^(رفتار|روی)$/)
      .map((node) => node.textContent);
    expect(words).toEqual(["رفتار", "روی"]);
  });

  it("still ranks a form the corpus reads the way we built it", async () => {
    // گفت is `Goft` here and `goft` in the lexicon — one word in two classes,
    // not two words. Folding case is what keeps it at the top.
    const sameWord = attested("spelling", 19839);
    sameWord.other_readings = ["goft"];
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [
                  {
                    ...BUILT.readings[0]!,
                    count: 2,
                    forms: [
                      form("Guye", "گویه", "karnam", attested("reading", 6)),
                      form("Goft", "گفت", "karnam", sameWord),
                    ],
                  },
                ],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("گفت");
    // The open class's words render below the grid, not inside the tile, so
    // the panel is scoped by its own id rather than by the heading's parent.
    const group = document.querySelector('[id^="words-"]') as HTMLElement;
    const words = within(group)
      .getAllByText(/^(گفت|گویه)$/)
      .map((node) => node.textContent);
    expect(words).toEqual(["گفت", "گویه"]);
  });

  it("keeps every derivation of a form, because two is information", async () => {
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("رفتار");
    const toggles = screen.getAllByRole("button", { name: /راه ساخت/ });
    expect(toggles[0]).toHaveTextContent("۲ راه");
    await userEvent.click(toggles[0]!);
    expect(screen.getByText("دستور V-010")).toBeInTheDocument();
    expect(screen.getByText("دستور V-011")).toBeInTheDocument();
  });

  it("numbers each route and says what tells them apart", async () => {
    // وارفتنی is built four ways, and all four attach the same vā- to the same
    // stem: V-070..V-073 share their explanation word for word. What separates
    // them is the sense — پس، دوباره، باز، آخشیج — and the screen used to print
    // twelve steps in one box with «۴ راه» above them and nothing else.
    const four = ["پس", "دوباره", "باز", "آخشیج"].map((sense, at) => [
      step(`V-07${at}`, "raft", "vā-", [sense]),
      step("V-006", "vāraft", "-an"),
    ]);
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [
                  {
                    ...BUILT.readings[0]!,
                    forms: [
                      { ...BUILT.readings[0]!.forms[0]!, paths: four },
                    ],
                  },
                ],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    await showForms();
    await userEvent.click(
      screen.getAllByRole("button", { name: /راه ساخت/ })[0]!,
    );

    // Each route says which of the four it is. Matched on the paragraph's own
    // text, because the numerals are their own elements — `Num` writes Persian
    // digits — so the sentence is split across nodes.
    const titles = screen
      .getAllByText((_, node) => node?.tagName === "P")
      .map((node) => node.textContent?.replace(/\s+/g, " ").trim())
      .filter((text) => text?.startsWith("راه "));
    expect(titles).toEqual([
      "راه ۱ از ۴",
      "راه ۲ از ۴",
      "راه ۳ از ۴",
      "راه ۴ از ۴",
    ]);

    // And each carries the sense that is the whole of the difference.
    for (const sense of ["پس", "دوباره", "باز", "آخشیج"]) {
      expect(screen.getByText(sense)).toBeInTheDocument();
    }
  });

  it("does not number a route when it is the only one", async () => {
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("رفتار");
    const single = screen
      .getAllByRole("button", { name: /راه ساخت/ })
      .find((one) => !one.textContent?.includes("راه ۲"));
    await userEvent.click(single!);
    expect(screen.queryByText(/راه ۱ از ۱/)).toBeNull();
  });

  it("hides the derivation until it is asked for", async () => {
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("رفتار");
    expect(screen.queryByText("دستور V-010")).not.toBeInTheDocument();
  });
});

describe("the evidence", () => {
  it("never says a word does not exist, only that it was not found", async () => {
    renderApp(ROUTE);
    // Ravešnāk is the fixture's unattested word and it is a برنام, so the
    // class holding it is the one to open — one class is open at a time.
    await showForms(/برنام/);
    expect(await screen.findByText(/یافت نشد/)).toBeInTheDocument();
    expect(screen.queryByText(/وجود ندارد/)).not.toBeInTheDocument();
  });

  it("names the corpus version the counts belong to", async () => {
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("رفتار");
    expect(screen.getAllByText("v1").length).toBeGreaterThan(0);
  });

  it("says a spelling-level hit is read another way", async () => {
    renderApp(ROUTE);
    await showForms();
    expect(await screen.findByText(/goftār/)).toBeInTheDocument();
  });

  it("says whose count it is when only the letters matched", async () => {
    // Found by reading بلندِ, which claimed 7,353 occurrences by 217 poets.
    // Those are occurrences of بلند. A spelling-level hit counts the
    // spelling, and the row named the other reading without ever saying the
    // number might not be about this word.
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("روش");
    expect(screen.getByText(/شمار برای این املاست/)).toBeInTheDocument();
  });

  it("distinguishes not-checked from not-found", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                corpus_version: null,
                readings: [
                  {
                    ...BUILT.readings[0]!,
                    forms: [form("Raftār", "رفتار", "karnam", null)],
                    count: 1,
                  },
                ],
              }),
        ),
      ),
    );
    renderApp(ROUTE);
    await showForms();
    expect(await screen.findByText("سنجیده نشده")).toBeInTheDocument();
    expect(
      screen.getByText(/پیکره‌ای در دسترس نبود/),
    ).toBeInTheDocument();
  });
});

describe("a word the lexicon does not have", () => {
  it("says why rather than showing an empty list", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({ detail: "not in lexicon" }, 404),
        ),
      ),
    );
    renderApp(ROUTE);
    expect(
      await screen.findByText(notFound("نمی‌دانیم از چه ساخته شده است.")),
    ).toBeInTheDocument();
  });
});


describe("the ground under a chain", () => {
  // Measured on رفتن: 231 of 510 words are built on an intermediate nobody
  // ever wrote. Their place in the list is the one thing that changes;
  // nothing is hidden, because absence from a corpus of classical poetry is
  // not a verdict on a word.
  const airborne = {
    ...form("DošRaftbān", "دشرفتبان", "karnam", attested("none")),
    base_attested: false,
  };
  const groundedOne = {
    ...form("Raftegi", "رفتگی", "karnam", attested("none")),
    base_attested: true,
  };

  function serving(forms: BuiltForm[]) {
    const body: Generated = {
      ...BUILT,
      readings: [{ ...BUILT.readings[0]!, count: forms.length, forms }],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules") ? answers(CLASSES) : answers(body),
        ),
      ),
    );
  }

  it("sinks a form built on an unwritten base below its peers", async () => {
    serving([airborne, groundedOne]);
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("DošRaftbān");
    const names = screen
      .getAllByRole("listitem")
      .map((row) => row.textContent ?? "");
    const sunk = names.findIndex((text) => text.includes("DošRaftbān"));
    const held = names.findIndex((text) => text.includes("Raftegi"));
    expect(held).toBeGreaterThanOrEqual(0);
    expect(sunk).toBeGreaterThan(held);
  });

  it("says why, in the project's wording, never does-not-exist", async () => {
    serving([airborne]);
    renderApp(ROUTE);
    await showForms();
    // Names the middle word, says where it was looked for, says who made it —
    // and never that nobody wrote it. FRONTEND.md: never "does not exist".
    expect(await screen.findByText(/آن را ما ساخته‌ایم/)).toBeInTheDocument();
    expect(screen.queryByText(/وجود ندارد/)).toBeNull();
    expect(screen.queryByText(/هیچ‌کس ننوشته/)).toBeNull();
    expect(screen.queryByText(/ساختی روی ساخت/)).toBeNull();
  });

  it("does not sink a form the corpus was never asked about", async () => {
    serving([{ ...airborne, form_latin: "Navā", base_attested: null }]);
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("Navā");
    // An unchecked chain is not a broken one, and gets no warning sentence.
    expect(screen.queryByText(/پایهٔ میانی/)).toBeNull();
  });
});


describe("how often a chain's rules produce real words", () => {
  // The criterion that makes three steps usable. At three steps one verb
  // builds 17,717 words, fifty of which the corpus has — so the ordering of
  // the other 17,667 is the whole feature. Nothing above this can separate
  // them: they are the same depth, from the same verb, and none is written.
  //
  // The semantic score cannot do it either, and that is not a fault in it: a
  // base's vector is the average of corpus lines using the word, so a word
  // nobody wrote can never have one. 12,999 forms share 22 values between
  // them.
  function chained(
    latin: string,
    fa: string,
    median: number,
    base_attested = false,
  ) {
    return {
      ...form(latin, fa, "karnam", attested("none")),
      base_attested,
      realisation: { median, steps_measured: 3, steps: 3 },
    };
  }

  const good = chained("hamandišande", "هماندیشنده", 0.2184);
  const nonsense = chained("hamandišidbāngāne", "هماندیشیدبانگانه", 0.0012);

  function serving(forms: BuiltForm[], extra: Partial<Generated["readings"][0]> = {}) {
    const body: Generated = {
      ...BUILT,
      readings: [
        { ...BUILT.readings[0]!, count: forms.length, forms, ...extra },
      ],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules") ? answers(CLASSES) : answers(body),
        ),
      ),
    );
  }

  function order(): string[] {
    return screen
      .getAllByRole("listitem")
      .map((row) => row.textContent ?? "");
  }

  it("puts the word with the stronger rules first", async () => {
    serving([nonsense, good]);
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("hamandišande");
    const names = order();
    expect(names.findIndex((t) => t.includes("hamandišande"))).toBeLessThan(
      names.findIndex((t) => t.includes("hamandišidbāngāne")),
    );
  });

  it("never outranks what the corpus actually says", async () => {
    // A tie-breaker among the unwritten, not a rival to evidence.
    const written = {
      ...form("Raftār", "رفتار", "karnam", attested("reading", 400)),
      realisation: { median: 0.0001, steps_measured: 3, steps: 3 },
    };
    serving([good, written]);
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("Raftār");
    const names = order();
    expect(names.findIndex((t) => t.includes("Raftār"))).toBeLessThan(
      names.findIndex((t) => t.includes("hamandišande")),
    );
  });

  it("leaves the order alone where the figure is missing", async () => {
    // An older API sends none. Unmeasured must never sink a word.
    const { realisation: _a, ...noFigureA } = chained("Alef", "الف", 0.9);
    const { realisation: _b, ...noFigureB } = chained("Bee", "ب", 0.1);
    serving([noFigureB, noFigureA]);
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("Alef");
    const names = order();
    expect(names.findIndex((t) => t.includes("Alef"))).toBeLessThan(
      names.findIndex((t) => t.includes("Bee")),
    );
  });

  it("says how many of how many it is showing, when a page holds part", async () => {
    // A page must never look like the answer.
    serving([good, nonsense], { count: 17717, returned: 2, has_more: true });
    renderApp(ROUTE);
    const note = await screen.findByText(/نیرومندترین/);
    // Both numbers in one sentence: what came back, and what was built.
    expect(note.textContent).toMatch(/۲/);
    expect(note.textContent).toMatch(/۱۷٬۷۱۷/);
  });

  it("says nothing about paging when the whole answer came back", async () => {
    serving([good, nonsense], { count: 2, returned: 2, has_more: false });
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("hamandišande");
    expect(screen.queryByText(/نیرومندترین/)).toBeNull();
  });
});

describe("a form that also reads as an inflection", () => {
  // S8's second half. Where the lexicon knows no reading for a spelling,
  // nothing in the attestation record separates رفتی — "you went" — from
  // گفتار, which is exactly the word this project makes. Both are unlinked, so
  // رفتن's screen opened on the inflections: seven of the top twenty.
  const rafti = {
    ...form("rafti", "رفتی", "karnam", attested("spelling", 1565)),
    inflection: {
      base: "رفت",
      pattern: "verb:bare:past_stem:ی",
      label_fa: "دوم‌شخص مفرد گذشته",
      shared_with: ["N-095"],
    },
  };
  const raftar = form("Raftār", "رفتار", "karnam", attested("spelling", 1091));

  function showing(forms: BuiltForm[]) {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          String(url).includes("/rules")
            ? answers(CLASSES)
            : answers({
                ...BUILT,
                readings: [
                  { ...BUILT.readings[0]!, count: forms.length, forms },
                ],
              }),
        ),
      ),
    );
  }

  it("ranks below a form that reads as nothing but itself", async () => {
    // رفتی has 1,565 poems behind it and رفتار has 1,091, so the count alone
    // puts the inflection first. It is the count that may not be the word's.
    showing([rafti, raftar]);
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("رفتار");
    const shown = screen.getAllByRole("listitem").map((one) => one.textContent);
    const at = (word: string) => shown.findIndex((text) => text?.includes(word));
    expect(at("رفتار")).toBeLessThan(at("رفتی"));
  });

  it("says why it sank, and that the letters cannot settle it", async () => {
    // Without the sentence, a row with the bigger number sitting lower looks
    // like a bug. And 95.6% of these are spelled by a derivational rule too,
    // so the screen must not imply the letters decide.
    showing([rafti, raftar]);
    renderApp(ROUTE);
    await showForms();
    expect(
      await screen.findByText(/خوانشِ دیگری هم دارد/),
    ).toBeInTheDocument();
    expect(screen.getByText(/نمی‌توان گفت کدام است/)).toBeInTheDocument();
    expect(screen.getByText("N-095")).toBeInTheDocument();
  });

  it("never hides it — the count stays on screen", async () => {
    // The standing rule: an absent or doubtful word is ranked down, never
    // dropped. A word the corpus wrote is evidence whatever it is evidence of.
    showing([rafti, raftar]);
    renderApp(ROUTE);
    await showForms();
    await screen.findByText("رفتار");
    expect(screen.getByText("رفتی")).toBeInTheDocument();
    expect(document.querySelector('[data-value="1565"]')).toBeInTheDocument();
  });
});
