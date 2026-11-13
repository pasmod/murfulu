/**
 * The reading screen in a real browser, on the real corpus.
 *
 * What jsdom cannot see: that a couplet's halves stand side by side on a
 * desktop and one under the other on a phone, that a line of word blocks runs
 * right to left and wraps without pushing the page sideways, that every word
 * is a touch target, and that a word's panel fits the screen.
 *
 * It needs the API with corpus v17 or later (units). Without it, it skips —
 * and says so, which is the point of naming the reason.
 */

import { expect, test, type Page } from "@playwright/test";

const GHAZAL = "ganjoor:hafez:2132";
const PREFACE = "ganjoor:saadi:41293";

async function units(page: Page, id: string): Promise<boolean> {
  const answer = await page.request.get(`/api/texts/${encodeURIComponent(id)}?limit=5`);
  if (!answer.ok()) return false;
  const body = await answer.json();
  return body.units.some((unit: { kind: string }) => unit.kind !== "line");
}

async function sideways(page: Page): Promise<number> {
  return page.evaluate(() => document.body.scrollWidth - document.body.clientWidth);
}

test.describe("reading a text", () => {
  test("a ghazal: its halves side by side on a desktop, one under the other on a phone", async ({
    page,
  }) => {
    test.skip(!(await units(page, GHAZAL)), "no corpus with units (v17 or later) served");
    await page.goto(`/texts?text=${encodeURIComponent(GHAZAL)}`);
    const first = page.locator("#unit-0");
    await expect(first).toBeVisible();
    const [right, left] = await first.locator("[data-position]").all();
    const a = (await right!.boundingBox())!;
    const b = (await left!.boundingBox())!;
    const wide = (page.viewportSize()?.width ?? 0) >= 768;
    if (wide) {
      // Side by side, the first half on the right: the page is right to left.
      expect(Math.abs(a.y - b.y)).toBeLessThan(4);
      expect(a.x).toBeGreaterThan(b.x);
    } else {
      expect(b.y).toBeGreaterThan(a.y + a.height - 1);
    }
    expect(await sideways(page)).toBeLessThanOrEqual(1);
  });

  test("a page of prose flows as paragraphs and every word is a touch target", async ({
    page,
  }) => {
    test.skip(!(await units(page, PREFACE)), "no corpus with units (v17 or later) served");
    await page.goto(`/texts?text=${encodeURIComponent(PREFACE)}`);
    const paragraphs = page.locator('li[data-kind="prose"]');
    await expect(paragraphs.first()).toBeVisible();
    // The longest of the first paragraphs: the opening one can be a short
    // invocation, and what is checked is how a paragraph wraps.
    const sizes = await paragraphs.evaluateAll((all) =>
      all.slice(0, 5).map((one) => one.querySelectorAll("button").length),
    );
    const prose = paragraphs.nth(sizes.indexOf(Math.max(...sizes)));
    const words = prose.getByRole("button");
    const count = await words.count();
    expect(count).toBeGreaterThan(5);
    for (const index of [0, 1, count - 1]) {
      const box = (await words.nth(index).boundingBox())!;
      expect(box.height, "touch target").toBeGreaterThanOrEqual(44);
    }
    // Right to left: the first word stands to the right of the second on its row.
    const one = (await words.nth(0).boundingBox())!;
    const two = (await words.nth(1).boundingBox())!;
    if (Math.abs(one.y - two.y) < 4) expect(one.x).toBeGreaterThan(two.x);
    expect(await sideways(page)).toBeLessThanOrEqual(1);
  });

  test("a word's panel shows every reading and stays inside the screen", async ({ page }) => {
    test.skip(!(await units(page, GHAZAL)), "no corpus with units (v17 or later) served");
    await page.goto(`/texts?text=${encodeURIComponent(GHAZAL)}`);
    const several = page.locator('button[data-state="several"]').first();
    await several.click();
    const panel = page.getByRole("region", { name: /^خوانش‌های / });
    await expect(panel).toBeVisible();
    await expect(panel.getByText(/گفته نمی‌شود/)).toBeVisible();
    const wrong = panel.getByRole("button", { name: "این خوانش نادرست است" });
    expect(await wrong.count()).toBeGreaterThan(1);
    const box = (await panel.boundingBox())!;
    const view = page.viewportSize()!;
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(view.width + 1);
    expect(await sideways(page)).toBeLessThanOrEqual(1);
  });

  test("a citation on a word's page opens the text at its line", async ({ page }) => {
    test.skip(!(await units(page, GHAZAL)), "no corpus with units (v17 or later) served");
    const search = await page.request.get(`/api/search?q=${encodeURIComponent("دل")}&size=5`);
    const hits = (await search.json()).string_match_only as { id: string; spelling_fa: string }[];
    const id = hits.find((hit) => hit.spelling_fa === "دل")!.id;
    await page.goto(`/word/${encodeURIComponent(id)}`);
    await page.getByRole("link", { name: "در متن ←" }).first().click();
    await expect(page).toHaveURL(/\/texts\?text=.*&unit=\d+&word=/);
    await expect(page.getByText(/همان سطرِ شاهدمثالِ «دل»/)).toBeVisible();
    // The word itself is in view, not merely its unit: a paragraph of prose
    // can be taller than the window.
    await expect(page.locator("button[data-sought]").first()).toBeInViewport();
  });
});
