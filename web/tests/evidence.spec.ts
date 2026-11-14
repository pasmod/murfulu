/**
 * Every text of a spelling, open on a real word's page, in a real browser.
 *
 * The list is the longest thing the word page can show — a common word's
 * page of twenty texts holds hundreds of lines — so it is checked for what a
 * phone shows first: nothing pushing the page sideways, every control big
 * enough for a thumb, and a line's «در متن ←» landing on the line itself.
 * Against the live API; it skips where no corpus with units is served.
 */

import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

const WORD = "رفتند";

/** The id of the word's own record, or null where there is no corpus. */
async function served(page: Page): Promise<string | null> {
  const answer = await page.request.get(
    `/api/evidence?spelling=${encodeURIComponent(WORD)}&size=1&count_lines=0`,
  );
  if (!answer.ok()) return null;
  const body = await answer.json();
  if (!body.texts?.[0]?.lines?.[0] || body.texts[0].lines[0].unit === null) return null;
  const search = await page.request.get(`/api/search?q=${encodeURIComponent(WORD)}&size=5`);
  const found = await search.json();
  const hits = [...found.string_match_only, ...found.formed_with_affix] as {
    id: string;
    spelling_fa: string;
  }[];
  return hits.find((hit) => hit.spelling_fa === WORD)?.id ?? null;
}

test.describe("every text of a spelling", () => {
  test("opens below the citations and fits the screen", async ({ page }) => {
    const id = await served(page);
    test.skip(id === null, "no corpus with units (v17 or later) served");
    await page.goto(`/word/${encodeURIComponent(id!)}`);
    const block = page.getByRole("region", { name: "همهٔ شواهد" });
    await block.getByRole("button", { name: "نشان دادن همهٔ شواهد" }).click();
    await expect(page).toHaveURL(/[?&]all=1/);
    await expect(block.locator("ol > li").first()).toBeVisible();
    await expect(block.locator("mark").first()).toHaveText(WORD);

    expect(
      await page.evaluate(() => document.body.scrollWidth - document.body.clientWidth),
    ).toBeLessThanOrEqual(1);
    for (const control of await block.locator("button, select").all()) {
      const box = await control.boundingBox();
      expect(box!.height, await control.textContent()).toBeGreaterThanOrEqual(44);
    }

    const result = await new AxeBuilder({ page })
      .include("section[aria-labelledby=all-evidence]")
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(result.violations.map((one) => one.id)).toEqual([]);
  });

  test("a line opens the reading screen at its unit, the word marked", async ({ page }) => {
    const id = await served(page);
    test.skip(id === null, "no corpus with units (v17 or later) served");
    await page.goto(`/word/${encodeURIComponent(id!)}?all=1`);
    const list = page.locator("#all-evidence-list");
    await list.getByRole("link", { name: "در متن ←" }).first().click();
    await expect(page).toHaveURL(/\/texts\?text=.*&unit=\d+&word=/);
    await expect(page.getByText(new RegExp(`همان سطرِ شاهدمثالِ «${WORD}»`))).toBeVisible();
    await expect(page.locator("button[data-sought]").first()).toBeInViewport();
  });

  test("one author's texts are chosen from the list and kept in the address", async ({ page }) => {
    const id = await served(page);
    test.skip(id === null, "no corpus with units (v17 or later) served");
    await page.goto(`/word/${encodeURIComponent(id!)}?all=1`);
    const filter = page.getByRole("combobox", { name: "نویسنده" });
    const second = (await filter.locator("option").nth(1).getAttribute("value"))!;
    await filter.selectOption(second);
    await expect(page).toHaveURL(new RegExp(`author=${encodeURIComponent(second)}`));
    const sources = page.locator("#all-evidence-list ol > li > p").first();
    await expect(sources).toContainText(second);
  });
});

test.describe("the verses under a built word's figures", () => {
  test("open with the corpus field and lead to the line", async ({ page }) => {
    const answer = await page.request.get(`/api/generate?word=${encodeURIComponent("بس")}&depth=2`);
    test.skip(!answer.ok(), "no lexicon or corpus here");
    const lines = await page.request.get(
      `/api/evidence?spelling=${encodeURIComponent("بسمان")}&size=1&count_lines=0`,
    );
    test.skip(!lines.ok() || (await lines.json()).texts.length === 0, "no corpus with بسمان");

    await page.goto(`/build?word=${encodeURIComponent("بس")}&depth=2`);
    // The innermost item holding the word: a word class's item holds its rows.
    const row = page
      .getByRole("listitem")
      .filter({ has: page.getByText("Basmān", { exact: true }) })
      .last();
    // The row sits in one reading's folded word class; open them until it shows.
    const groups = page.getByRole("button", { name: /کارنام/ });
    await expect(groups.first()).toBeVisible();
    for (let at = 0; at < (await groups.count()); at += 1) {
      await groups.nth(at).click();
      if (await row.isVisible()) break;
    }
    await row.getByRole("button", { name: "شواهد" }).click();
    await row.getByRole("button", { name: /^پیکره/ }).click();
    await expect(row.locator("mark").first()).toHaveText("بسمان");
    expect(
      await page.evaluate(() => document.body.scrollWidth - document.body.clientWidth),
    ).toBeLessThanOrEqual(1);

    await row.getByRole("link", { name: "در متن ←" }).first().click();
    await expect(page).toHaveURL(/\/texts\?text=.*&unit=\d+&word=/);
    await expect(page.getByText(/همان سطرِ شاهدمثالِ «بسمان»/)).toBeVisible();
    await expect(page.locator("button[data-sought]").first()).toBeInViewport();
  });

  test("opens the whole list in the panel, thumb-sized and with no violations", async ({
    page,
  }) => {
    const answer = await page.request.get(
      `/api/generate?word=${encodeURIComponent("بستن")}&depth=1`,
    );
    test.skip(!answer.ok(), "no lexicon or corpus here");
    await page.goto(`/build?word=${encodeURIComponent("بستن")}&depth=1`);
    const row = page
      .getByRole("listitem")
      .filter({ has: page.getByText("Bande", { exact: true }) })
      .last();
    const groups = page.getByRole("button", { name: /کارنام/ });
    await expect(groups.first()).toBeVisible();
    for (let at = 0; at < (await groups.count()); at += 1) {
      await groups.nth(at).click();
      if (await row.isVisible()) break;
    }
    test.skip(!(await row.isVisible()), "no row بنده here");
    await row.getByRole("button", { name: "شواهد" }).click();
    await row.getByRole("button", { name: /^پیکره/ }).click();
    const more = row.getByRole("button", { name: /^همهٔ .* متن$/ });
    await more.click();
    // The same button, renamed: the reader's focus stays on it.
    await expect(row.getByRole("button", { name: "تنها چند متن نخست" })).toBeFocused();
    await expect(row.getByRole("combobox", { name: "نویسنده" })).toBeVisible();
    await expect(row.locator("ol > li").nth(9)).toBeVisible();

    expect(
      await page.evaluate(() => document.body.scrollWidth - document.body.clientWidth),
    ).toBeLessThanOrEqual(1);
    const panel = row
      .locator("[id]")
      .filter({ has: page.locator("ol") })
      .first();
    for (const control of await panel.locator("button, select").all()) {
      const box = await control.boundingBox();
      expect(box!.height, await control.textContent()).toBeGreaterThanOrEqual(44);
    }
    const result = await new AxeBuilder({ page })
      .include("main")
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(result.violations.map((one) => `${one.id}: ${one.nodes[0]?.target}`)).toEqual([]);
  });
});
