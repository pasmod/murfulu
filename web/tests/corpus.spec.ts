/**
 * The corpus screen in a real browser, against whatever this machine ingested.
 *
 * It skips rather than fails when no ingest has been reported here: a machine
 * with no corpus is a normal state, not a broken one, and the screen's own
 * "nothing has been measured yet" path is checked in the component tests.
 *
 * A separate file from `layout.spec.ts` so neither grows past what anyone
 * wants to read — docs/ENGINEERING.md, no file over 400 lines.
 */

import { expect, test } from "@playwright/test";

interface Body {
  report: { spellings: number; type_share: number; token_share: number } | null;
}

async function report(page: import("@playwright/test").Page) {
  const answer = await page.request.get("/api/corpus");
  if (!answer.ok()) return null;
  return ((await answer.json()) as Body).report;
}

test.describe("the corpus screen", () => {
  test("shows the real coverage, both shares, without overflowing", async ({
    page,
  }) => {
    const measured = await report(page);
    test.skip(!measured, "no ingest reported on this machine");

    await page.goto("/corpus");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("پیکره");

    // Both shares, and they are different numbers: type coverage is how much
    // of the vocabulary we can read, token coverage how much of the text.
    const vocabulary = page.getByRole("img", { name: /از واژگان/ });
    const text = page.getByRole("img", { name: /از متن/ });
    await expect(vocabulary).toBeVisible();
    await expect(text).toBeVisible();
    expect(await vocabulary.getAttribute("aria-label")).not.toBe(
      await text.getAttribute("aria-label"),
    );

    const overflow = await page.evaluate(
      () => document.body.scrollWidth - document.body.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("the unmatched pile scrolls inside its own box", async ({ page }) => {
    const measured = await report(page);
    test.skip(!measured, "no ingest reported on this machine");

    await page.goto("/corpus");
    const gaps = page.getByRole("region", { name: "املاهای بی‌مدخل" });
    await expect(gaps).toBeVisible();

    // Four columns do not fit at 375 px. The table is allowed to be wider
    // than the screen as long as it takes its own scrollbar.
    const table = gaps.locator("table");
    await expect(table).toBeVisible();
    const page_overflow = await page.evaluate(
      () => document.body.scrollWidth - document.body.clientWidth,
    );
    expect(page_overflow).toBeLessThanOrEqual(1);
  });

  test("every figure on the screen is in Persian numerals", async ({ page }) => {
    const measured = await report(page);
    test.skip(!measured, "no ingest reported on this machine");

    await page.goto("/corpus");
    const sizes = page.getByRole("region", { name: "اندازه" });
    await expect(sizes).toBeVisible();
    await expect(sizes).not.toHaveText(/[0-9]/);
  });
});
