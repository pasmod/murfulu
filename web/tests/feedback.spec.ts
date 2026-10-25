/**
 * The feedback affordance in a real browser.
 *
 * docs/FRONTEND.md names the feedback button as one of the two things that
 * usually gets the 44 px touch target wrong, and the panel is fixed to the
 * corner of a 375 px screen — neither of which jsdom can tell you anything
 * about.
 */

import { expect, test } from "@playwright/test";

const SCREENS = ["/", "/build", "/affixes", "/explain", "/rules", "/corpus"];

test.describe("the feedback button", () => {
  test("is on every screen and is big enough for a thumb", async ({ page }) => {
    for (const route of SCREENS) {
      await page.goto(route);
      const button = page.getByRole("button", { name: "بازخورد" });
      await expect(button).toBeVisible();
      const box = (await button.boundingBox())!;
      expect(box.height, `${route}: touch target`).toBeGreaterThanOrEqual(44);
    }
  });

  test("opens a panel that stays inside the screen", async ({ page }) => {
    await page.goto("/rules");
    await page.getByRole("button", { name: "بازخورد" }).click();

    const panel = page.getByRole("dialog");
    await expect(panel).toBeVisible();

    const box = (await panel.boundingBox())!;
    const view = page.viewportSize()!;
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(view.width + 1);

    // The panel is not modal — a reader has to see the word while writing
    // about it — so the page behind it must still not scroll sideways.
    const overflow = await page.evaluate(
      () => document.body.scrollWidth - document.body.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  // This test used to assert the opposite — that the panel asks for an API key
  // before it shows anything — and it went on passing in nobody's eye-line
  // after the key was removed on 2026-08-17, because the layout suite is not
  // run as often as the unit one. What is worth checking in a browser is the
  // decision itself: a reader who can see the button can already use it.
  test("opens straight into the form, because there is nothing left to ask for", async ({
    page,
  }) => {
    const answer = await page.request.get("/api/me");
    test.skip(!answer.ok(), "no API");

    await page.goto("/rules");
    await page.getByRole("button", { name: "بازخورد" }).click();

    const panel = page.getByRole("dialog");
    await expect(
      panel.getByRole("group", { name: "دربارهٔ چه می‌گویید؟" }),
    ).toBeVisible();

    // Nothing to type a credential into, under any of the words this app has
    // used for one.
    await expect(
      panel.getByRole("textbox", { name: /کلید|رمز|توکن/ }),
    ).toHaveCount(0);
  });

  test("a rule can be judged on its own row", async ({ page }) => {
    const answer = await page.request.get("/api/rules?family=G");
    test.skip(!answer.ok(), "no API");

    await page.goto("/rules?family=G");
    const judge = page.getByRole("button", { name: /داوری دربارهٔ دستور/ }).first();
    await judge.scrollIntoViewIfNeeded();
    await expect(judge).toBeVisible();

    // The record has to name the rule that was clicked, not the page listing
    // 195 of them — so the panel is checked against that button's own rule.
    const named = (await judge.getAttribute("aria-label"))!.replace("داوری ", "");
    await judge.click();
    await expect(page.getByRole("dialog")).toHaveAttribute(
      "aria-label",
      `بازخورد ${named}`,
    );
  });
});
