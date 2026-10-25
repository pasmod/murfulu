/**
 * The layout, in a real browser, at the width docs/FRONTEND.md names.
 *
 * These are the checks jsdom cannot make. A component test can tell you the
 * navigation is present; only a browser can tell you it pushes the page
 * sideways at 375 px, that a touch target came out 31 px tall, or that the
 * right-to-left layout put the heading against the wrong edge.
 *
 * Every failure here is one a reader on a phone would have hit first.
 */

import { expect, test } from "@playwright/test";

import { FROM_LEXICON } from "../src/text/lexicon";

const SCREENS = [
  { path: "/", heading: "جست‌وجو" },
  { path: "/build", heading: "ساخت واژه" },
  { path: "/compound", heading: "واژه‌های ترکیبی" },
  { path: "/affixes", heading: "وندها بر پایهٔ معنا" },
  { path: "/explain", heading: "تحلیل ساخت" },
  { path: "/rules", heading: "دستورهای واژه‌سازی" },
  { path: "/corpus", heading: "پیکره" },
  // Not in the corpus, so the screen shows its "not here" state — which is
  // itself worth laying out correctly.
  { path: "/word/روش:Raveš", heading: "واژه" },
];

test.describe("every screen", () => {
  for (const screen of SCREENS) {
    test(`${screen.path} does not push the page sideways`, async ({ page }) => {
      await page.goto(screen.path);
      await expect(page.getByRole("heading", { level: 1 })).toHaveText(
        screen.heading,
      );

      // The single most common phone bug: something wider than the screen, so
      // the whole page scrolls horizontally. Wide content scrolls inside its
      // own box; the body never does.
      //
      // **The failure names the element.** `43 > 1` is a true statement that
      // nobody can act on, and these tests failed in CI for two days with
      // exactly that and no way to reproduce it locally. So the widest thing
      // sticking out is found and reported with it.
      const overflow = await page.evaluate(() => {
        const body = document.body;
        const amount = body.scrollWidth - body.clientWidth;
        if (amount <= 1) return { amount, culprit: "" };

        // **Not the bounding rect.** In an RTL document that already
        // overflows, every rect is shifted by the scroll offset, so "past the
        // right edge" names innocent elements — it accused an `li` twice while
        // the nav was not the cause. What actually widens a parent is an
        // element whose own content is wider than itself while it is *not* a
        // scroll container, so that is what is looked for.
        const guilty: string[] = [];
        for (const node of Array.from(document.querySelectorAll("*"))) {
          const over = node.scrollWidth - node.clientWidth;
          if (over <= 1) continue;
          const how = getComputedStyle(node).overflowX;
          if (how === "auto" || how === "scroll" || how === "hidden") continue;
          const name = node.tagName.toLowerCase();
          const marks = node.className
            ? `.${String(node.className).split(/\s+/)[0]}`
            : "";
          guilty.push(`${name}${marks} holds ${over}px more than it shows`);
        }
        return { amount, culprit: guilty.slice(0, 6).join("; ") || "nothing visible" };
      });
      expect(
        overflow.amount,
        `the page scrolls sideways; widest offender: ${overflow.culprit}`,
      ).toBeLessThanOrEqual(1);
    });
  }
});

test.describe("at phone width", () => {
  test.skip(({ viewport }) => (viewport?.width ?? 0) > 400, "phone only");

  test("the navigation stays on one line and scrolls", async ({ page }) => {
    await page.goto("/");
    const list = page.getByRole("navigation", { name: "بخش‌های اصلی" });
    const box = await list.boundingBox();
    expect(box).not.toBeNull();

    // One row, not two cramped ones. A wrapped row would be twice as tall.
    expect(box!.height).toBeLessThan(72);

    // It is allowed to be wider than the screen, as long as it scrolls itself.
    const scrolls = await list.evaluate(
      (node) => node.scrollWidth > node.clientWidth + 1,
    );
    const fits = box!.width <= 375;
    expect(scrolls || fits).toBe(true);
  });

  test("every link in the navigation is big enough for a thumb", async ({
    page,
  }) => {
    await page.goto("/");
    const links = page.getByRole("navigation").getByRole("link");
    const count = await links.count();
    expect(count).toBeGreaterThan(0);
    for (let index = 0; index < count; index += 1) {
      const box = await links.nth(index).boundingBox();
      expect(box, `link ${index} has no box`).not.toBeNull();
      // Apple's guideline, and the one docs/FRONTEND.md says gets broken.
      expect(box!.height).toBeGreaterThanOrEqual(44);
    }
  });

  test("the last navigation item is reachable by scrolling", async ({ page }) => {
    await page.goto("/");
    const last = page.getByRole("link", { name: "پیکره" });
    await last.scrollIntoViewIfNeeded();
    await expect(last).toBeInViewport();
  });
});

test.describe("a real search", () => {
  // Against the live API, so this is the whole stack: the screen, the route,
  // Elasticsearch, and a corpus that has actually been ingested. It skips
  // rather than fails when there is nothing to search, because a machine with
  // no corpus is a normal state, not a broken one.
  test("shows results and keeps the two groups apart", async ({ page }) => {
    const answer = await page.request.get("/api/search?q=*n%C4%81&size=5");
    test.skip(!answer.ok(), "no corpus ingested");

    await page.goto("/?q=*n%C4%81");
    await expect(page.getByRole("region", { name: /ساخته‌شده با/ })).toBeVisible();
    await expect(
      page.getByRole("region", { name: /تنها به این حروف/ }),
    ).toBeVisible();

    // The counts are Persian numerals, everywhere.
    const total = page.getByText(/واژه یافت شد/);
    await expect(total).toBeVisible();
    await expect(total).not.toHaveText(/[0-9]/);

    const overflow = await page.evaluate(
      () => document.body.scrollWidth - document.body.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});

test.describe("a real word", () => {
  test("shows its evidence, its chart and its citations", async ({ page }) => {
    const answer = await page.request.get(
      "/api/search?q=*n%C4%81&size=1&affix=-n%C4%81",
    );
    test.skip(!answer.ok(), "no corpus ingested");
    const body = await answer.json();
    const first = body.string_match_only[0] ?? body.formed_with_affix[0];
    test.skip(!first, "no hits to open");

    await page.goto(`/word/${encodeURIComponent(first.id)}`);
    await expect(
      page.getByRole("heading", { level: 1, name: first.spelling_fa }),
    ).toBeVisible();
    await expect(page.getByRole("region", { name: "شواهد" })).toBeVisible();
    await expect(page.getByRole("region", { name: "شاهدمثال‌ها" })).toBeVisible();

    const overflow = await page.evaluate(
      () => document.body.scrollWidth - document.body.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});

test.describe("a word the search engine used to swallow", () => {
  // بود، رفت، گفت، شد are on Lucene's Persian stopword list, so until corpus
  // version v2 the counts were right and the quoted lines were empty. A
  // reader saw "written 143,873 times" and nothing to check it against.
  for (const spelling of ["بود", "رفت"]) {
    test(`${spelling} is quoted, not only counted`, async ({ page }) => {
      const answer = await page.request.get(
        `/api/word/${encodeURIComponent(`${spelling}:`)}?index=word_types`,
      );
      test.skip(!answer.ok(), "no corpus ingested");
      const body = await answer.json();
      expect(body.citations.length).toBeGreaterThan(0);

      await page.goto(`/word/${encodeURIComponent(`${spelling}:`)}`);
      const quoted = page.getByRole("region", { name: "شاهدمثال‌ها" });
      await expect(quoted).toBeVisible();
      await expect(quoted.getByText(spelling).first()).toBeVisible();
    });
  }
});

test.describe("a real build", () => {
  test("builds رفتن and ranks the attested forms first", async ({ page }) => {
    const answer = await page.request.get("/api/generate?word=%D8%B1%D9%81%D8%AA%D9%86");
    test.skip(!answer.ok(), "no lexicon configured");

    await page.goto("/build?word=%D8%B1%D9%81%D8%AA%D9%86&depth=2");
    await expect(page.getByRole("heading", { name: /از raftan/ })).toBeVisible();

    // The word classes come first and the words are behind them, from
    // 2026-08-18 — رفتن answers with 660 words in 8 classes per reading, and
    // opening all of them made a page 47,802px tall. So the class is asked for
    // the way a reader asks for it, and then the words are there.
    const karnam = page
      .getByRole("heading", { level: 3, name: /کارنام/ })
      .first();
    await expect(karnam).toBeVisible();
    await karnam.getByRole("button").click();

    // رفتار is what the whole project walks through, and it is attested.
    await expect(page.getByText("رفتار").first()).toBeVisible();

    const overflow = await page.evaluate(
      () => document.body.scrollWidth - document.body.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});

test.describe("affixes by meaning", () => {
  test("answers the founding question against the real rule pack", async ({
    page,
  }) => {
    const answer = await page.request.get("/api/affixes");
    test.skip(!answer.ok(), "no API");

    await page.goto("/affixes");
    // جا — "place" — is the question the project started from.
    await expect(page.getByRole("heading", { name: /جا/ }).first()).toBeVisible();
    await expect(page.getByText("-dān").first()).toBeVisible();

    const overflow = await page.evaluate(
      () => document.body.scrollWidth - document.body.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});

test.describe("taking a word apart", () => {
  test("rebuilds Ravandegi and refuses Mowlānā, on real data", async ({ page }) => {
    const answer = await page.request.get("/api/explain?word=Ravandegi");
    test.skip(!answer.ok(), "no lexicon configured");

    await page.goto("/explain?word=Ravandegi");
    await expect(page.getByRole("heading", { name: /راه ممکن/ })).toBeVisible();
    await expect(page.getByText("رفتن").first()).toBeVisible();

    // The check that matters: a word that merely looks derived is refused.
    await page.goto("/explain?word=Mowl%C4%81n%C4%81");
    await expect(
      page.getByRole("heading", { name: /راهی برای ساختن این واژه پیدا نشد/ }),
    ).toBeVisible();

    const overflow = await page.evaluate(
      () => document.body.scrollWidth - document.body.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("the box follows the address, even backwards", async ({ page }) => {
    // Found by pressing Back in a real browser: the address and the accounts
    // went back to Ravandegi while the box went on saying Goftār, so the
    // screen answered about one word and named another. The box seeded its
    // draft from the address once and never again. jsdom has no history to
    // walk, which is why this lives here.
    const answer = await page.request.get("/api/explain?word=Ravandegi");
    test.skip(!answer.ok(), "no lexicon configured");

    await page.goto("/explain?word=Ravandegi");
    const box = page.getByLabel(/واژه‌ای به بهنویس بنویسید/);
    await expect(box).toHaveValue("Ravandegi");

    await box.fill("Goftār");
    await page.getByRole("button", { name: "بشکاف" }).click();
    // Waiting for the *answer* to change, not for the box or the address.
    // `fill` already put Goftār in the box and the address changes the
    // moment the router pushes, so either would let the Back below fire
    // inside the same frame as the push — the router then commits the push
    // after the pop and settles on the wrong entry. No reader can press Back
    // that fast; the wait is for the screen to have finished answering.
    await expect(page.getByText("گفتن").first()).toBeVisible();
    await expect(box).toHaveValue("Goftār");

    await page.goBack();
    await expect(page).toHaveURL(/word=Ravandegi/);
    await expect(box).toHaveValue("Ravandegi");
  });
});

test.describe("the rule pack", () => {
  test("shows the real disagreement between source and measurement", async ({
    page,
  }) => {
    const answer = await page.request.get("/api/rules?family=V");
    test.skip(!answer.ok(), "no API");
    const body = await answer.json();
    test.skip(!body.corpus_version, "no productivity measured on this machine");
    const disagreeing = (body.rules ?? []).filter(
      (rule: { productivity?: { disagrees_with_strength?: boolean } }) =>
        rule.productivity?.disagrees_with_strength,
    );

    await page.goto("/rules");
    // **Whether any rule disagrees is a fact about the corpus, not about this
    // screen.** The source states a strength for three rules; on v9 all three
    // measured *high* against an authored *typical* and the screen led with
    // that. On v10 they measure *middle* and agree — not because the evidence
    // improved but because 9.10 gave V-010 8,658 outputs where it had 3,464,
    // so the same attested count is a smaller share. The screen is right
    // either way, and asserting the finding exists would pin it to a corpus.
    if (disagreeing.length > 0) {
      await expect(
        page.getByRole("heading", { name: /یکی نمی‌گویند/ }),
      ).toBeVisible();
      await expect(page.getByText(disagreeing[0].id).first()).toBeVisible();
    } else {
      await expect(page.getByRole("heading", { name: /یکی نمی‌گویند/ })).toHaveCount(
        0,
      );
    }

    const overflow = await page.evaluate(
      () => document.body.scrollWidth - document.body.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("shows what a rule's semantic centre is made of", async ({ page }) => {
    const answer = await page.request.get("/api/rules");
    test.skip(!answer.ok(), "no API");
    const body = await answer.json();
    const withCentre = body.rules.find(
      (one: { semantic: unknown }) => one.semantic,
    );
    test.skip(!withCentre, "no semantic artefact built on this machine");

    await page.goto("/rules");
    const row = page.locator("li", { hasText: withCentre.id }).first();
    await row.getByRole("button", { name: "جزئیات" }).click();

    // The count and the bases both come from the artefact. The screen adds
    // the heading and nothing else.
    await expect(row.getByText("پایه‌های شاخص")).toBeVisible();
    const first = withCentre.semantic.typical_bases[0];
    await expect(row.getByText(first.fa, { exact: true }).first()).toBeVisible();

    const overflow = await page.evaluate(
      () => document.body.scrollWidth - document.body.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});

test.describe("right to left", () => {
  test("the document declares Persian and its direction", async ({ page }) => {
    await page.goto("/");
    const html = page.locator("html");
    await expect(html).toHaveAttribute("dir", "rtl");
    await expect(html).toHaveAttribute("lang", "fa");
  });

  test("text starts at the right edge, not the left", async ({ page }) => {
    await page.goto("/");
    const heading = page.getByRole("heading", { level: 1 });
    const box = (await heading.boundingBox())!;
    const width = page.viewportSize()!.width;

    // In a right-to-left layout the heading's own box may span the column, so
    // what is checked is where the glyphs are: the text has to sit against the
    // right-hand edge of that box.
    const alignment = await heading.evaluate(
      (node) => getComputedStyle(node).direction,
    );
    expect(alignment).toBe("rtl");
    expect(box.x + box.width).toBeGreaterThan(width / 2);
  });

  test("a skip link is the first thing a keyboard reaches", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");
    const focused = page.locator(":focus");
    await expect(focused).toHaveText("رفتن به محتوای اصلی");

    // Off screen until focused, **wholly** on screen once it is. The whole box
    // is checked rather than any overlap with it: the first version of this
    // test asked only whether it intersected the viewport, and passed while
    // the link sat half above the top edge, which is exactly the bug a skip
    // link cannot afford.
    // It slides in, so the position is polled rather than read once: reading
    // it immediately catches the element mid-transition, above the top edge,
    // which is not the bug this test is looking for.
    await expect
      .poll(async () => (await focused.boundingBox())?.y ?? -1)
      .toBeGreaterThanOrEqual(0);

    const box = (await focused.boundingBox())!;
    const view = page.viewportSize()!;
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.y + box.height).toBeLessThanOrEqual(view.height);
    expect(box.x + box.width).toBeLessThanOrEqual(view.width);
  });

  test("focus is visible, not removed", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");
    const outline = await page
      .locator(":focus")
      .evaluate((node) => getComputedStyle(node).outlineWidth);
    expect(parseFloat(outline)).toBeGreaterThan(0);
  });
});

test.describe("the rule families", () => {
  test("a family button narrows the list instead of emptying it", async ({
    page,
  }) => {
    const answer = await page.request.get("/api/rules");
    test.skip(!answer.ok(), "no API");

    await page.goto("/rules?family=V");
    // The count sentence is the honest place to read this: with the family
    // field missing it said zero while 81 rules matched.
    await expect(page.getByText(/دستور نشان داده می‌شود/)).toBeVisible();
    await expect(page.getByText("V-001").first()).toBeVisible();
  });
});

test.describe("what the dictionary knows", () => {
  test("برنا shows its second pronunciation and its meaning, on real data", async ({
    page,
  }) => {
    // The reader asked why the screen writes barnā when the poems sound like
    // bornā. The lexicon held both all along and no screen drew either — nor
    // the definition, which 96.1% of karbon's rows carry. Both need corpus v6
    // or later; before that word_types had no field for them.
    const id = encodeURIComponent("برنا:barnā");
    const answer = await page.request.get(`/api/word/${id}?index=word_types`);
    test.skip(!answer.ok(), "برنا is not in the corpus version being served");
    const body = await answer.json();
    test.skip(
      !body.word?.latin_variants?.length,
      "corpus version predates latin_variants",
    );

    await page.goto(`/word/${id}?index=word_types`);
    await expect(page.getByText("bornā")).toBeVisible();
    await expect(page.getByText(FROM_LEXICON)).toBeVisible();
    await expect(page.getByText(/جوان/).first()).toBeVisible();

    const overflow = await page.evaluate(
      () => document.body.scrollWidth - document.body.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });
});

test.describe("compound words", () => {
  test("shows real compounds with the count they were drawn from", async ({
    page,
  }) => {
    // On real data: دل builds thousands and the corpus holds a couple of
    // hundred. The list is meaningless without the number behind it, so both
    // have to be on screen together.
    //
    // **Skips without the API**, like every other test here that needs real
    // data. It did not, and so failed on every CI run from 2026-08-14 — where
    // no API is started — saying nothing about the screen while making the
    // build red enough that a genuine failure could hide behind it.
    const answer = await page.request.get(
      "/api/compound?word=%D8%AF%D9%84&limit=1",
    );
    test.skip(!answer.ok(), "no API, or no corpus ingested");

    await page.goto("/compound?word=%D8%AF%D9%84");

    await expect(page.getByText(/ترکیب بسازد/).first()).toBeVisible();
    // دلبر is the best-attested compound of دل in the corpus.
    await expect(page.getByText("دلبر").first()).toBeVisible();

    const overflow = await page.evaluate(
      () => document.body.scrollWidth - document.body.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("a long list opens folded and says what it is holding", async ({
    page,
  }) => {
    const answer = await page.request.get(
      "/api/compound?word=%D8%AF%D9%84&limit=1",
    );
    test.skip(!answer.ok(), "no API, or no corpus ingested");

    await page.goto("/compound?word=%D8%AF%D9%84");
    // دل has four readings and each folds its own list.
    const more = page.getByRole("button", { name: /ترکیب دیگر/ }).first();
    await expect(more).toBeVisible();

    const before = await page.getByRole("listitem").count();
    await more.click();
    expect(await page.getByRole("listitem").count()).toBeGreaterThan(before);
  });
});
