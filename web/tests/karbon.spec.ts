/**
 * Which readings are the bank's, and the list of those it lacks, in a real
 * browser (2026-11-22).
 *
 * What jsdom cannot see: that a star before a reading does not push a line
 * of word blocks sideways on a phone, and that the list for karbon — a row's
 * line, what the bank has, the linguist's button — stays inside a 375 px
 * screen with the button a touch target.
 *
 * It needs the API with the list for karbon, and a corpus with units for the
 * text. Without them it skips — and says so.
 */

import { expect, test, type Page } from "@playwright/test";

const GHAZAL = "ganjoor:hafez:2132";

async function sideways(page: Page): Promise<number> {
  return page.evaluate(() => document.body.scrollWidth - document.body.clientWidth);
}

test.describe("the readings the bank lacks", () => {
  test("a starred reading leaves its word a touch target and the page inside the screen", async ({
    page,
  }) => {
    const answer = await page.request.get(`/api/texts/${encodeURIComponent(GHAZAL)}?limit=5`);
    const body = answer.ok() ? await answer.json() : null;
    const told = body?.units?.some((unit: { lines?: { words?: { auto?: { bank?: string[] } }[] }[] }) =>
      unit.lines?.some((line) => line.words?.some((word) => word.auto?.bank !== undefined)),
    );
    test.skip(!told, "no API served that says which readings the bank holds");
    await page.goto(`/texts?text=${encodeURIComponent(GHAZAL)}`);
    const starred = page.locator('button[data-held="no"]');
    await expect(starred.first()).toBeVisible();
    await expect(starred.first()).toContainText("*");
    const box = (await starred.first().boundingBox())!;
    expect(box.height, "touch target").toBeGreaterThanOrEqual(44);
    // The legend says what the star means.
    await expect(page.getByText(/ستاره یعنی این خوانش در بانک واژه/)).toBeVisible();
    expect(await sideways(page)).toBeLessThanOrEqual(1);
  });

  test("the list for karbon stays inside the screen, its button a touch target", async ({
    page,
  }) => {
    const answer = await page.request.get("/api/texts/karbon?size=1");
    test.skip(!answer.ok(), "no API with the list for karbon served");
    await page.goto("/texts?view=karbon");
    const list = page.getByRole("region", { name: "خوانش‌هایی که کاربن ندارد" });
    await expect(list.getByText(/تای آن تأیید شده/)).toBeVisible();
    const button = list.getByRole("button", { name: /تأیید/ }).first();
    await expect(button).toBeVisible();
    const box = (await button.boundingBox())!;
    expect(box.height, "touch target").toBeGreaterThanOrEqual(44);
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual((page.viewportSize()?.width ?? 0) + 1);
    expect(await sideways(page)).toBeLessThanOrEqual(1);
  });
});
