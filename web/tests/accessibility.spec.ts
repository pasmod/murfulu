/**
 * WCAG 2.1 AA, checked in a real browser on every screen.
 *
 * Two halves, and neither replaces the other.
 *
 * **axe** finds what a machine can find — a control with no name, a heading
 * that skips a level, a colour pair that fails on the page as rendered. It is
 * run against A, AA and the WCAG 2.1 additions, and against the panels and
 * expanders too, because most of this interface is behind a click.
 *
 * **The rest is written out below**, because axe cannot check it: that the
 * whole app is reachable with a keyboard, that focus is visible where it
 * lands, that the Persian screen-reader labels are actually Persian, and that
 * the document says which language and direction it is in. Those are the
 * failures a real reader hits first.
 *
 * The palette itself is checked separately in `src/styles/contrast.test.ts`:
 * a page can pass an audit by not happening to put two colours together.
 */

import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const SCREENS = [
  { path: "/", name: "search" },
  { path: "/build?word=%D8%B1%D9%81%D8%AA%D9%86", name: "build" },
  { path: "/affixes", name: "affixes" },
  { path: "/explain", name: "explain" },
  { path: "/rules", name: "rules" },
  { path: "/corpus", name: "corpus" },
  // Reached by clicking a result rather than from the menu, and the only
  // screen carrying a chart. Its "not in this corpus" state is a real state
  // and is laid out like any other.
  { path: "/word/%D8%B1%D9%88%D8%B4:Rave%C5%A1", name: "word" },
];

const STANDARD = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

async function audit(page: Page) {
  return new AxeBuilder({ page }).withTags(STANDARD).analyze();
}

/** What failed, named, so a failure says which rule and where. */
function readable(violations: Awaited<ReturnType<typeof audit>>["violations"]) {
  return violations.map(
    (one) => `${one.id} (${one.impact}): ${one.nodes[0]?.target.join(" ")}`,
  );
}

test.describe("every screen", () => {
  for (const screen of SCREENS) {
    test(`${screen.name} has no accessibility violations`, async ({ page }) => {
      await page.goto(screen.path);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      const result = await audit(page);
      expect(readable(result.violations)).toEqual([]);
    });
  }
});

test.describe("the parts behind a click", () => {
  test("the feedback panel", async ({ page }) => {
    await page.goto("/rules");
    await page.getByRole("button", { name: "بازخورد" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    expect(readable((await audit(page)).violations)).toEqual([]);
  });

  test("an expanded rule", async ({ page }) => {
    // **A family whose rows are affix rules**, because only those expand — a
    // glide row has nothing to open. This asked for `family=G` until
    // 2026-08-17 and passed by accident: the disagreement section above the
    // list rendered affix rules whatever family was chosen, and the click
    // landed on one of those. v10 resolved the last disagreement and the
    // button vanished, taking an accessibility check with it.
    const answer = await page.request.get("/api/rules?family=V");
    test.skip(!answer.ok(), "no API");
    await page.goto("/rules?family=V");
    await page.getByRole("button", { name: "جزئیات" }).first().click();
    expect(readable((await audit(page)).violations)).toEqual([]);
  });

  test("a built word with its derivation open", async ({ page }) => {
    const answer = await page.request.get("/api/generate?word=%D8%B1%D9%81%D8%AA%D9%86");
    test.skip(!answer.ok(), "no API");
    await page.goto("/build?word=%D8%B1%D9%81%D8%AA%D9%86");
    // A word class is opened first: the rows live inside one from 2026-08-18.
    const group = page.getByRole("heading", { level: 3 }).first();
    await group.waitFor();
    await group.getByRole("button").click();
    const path = page.getByRole("button", { name: /راه ساخت/ }).first();
    await path.waitFor();
    await path.click();
    expect(readable((await audit(page)).violations)).toEqual([]);
  });
});

test.describe("what axe cannot check", () => {
  test("every screen is reachable with a keyboard alone", async ({ page }) => {
    await page.goto("/");
    // Tab from the top and collect what the browser stops on. If a screen can
    // only be reached by clicking, it is not reachable at all for some readers.
    const reached: string[] = [];
    for (let step = 0; step < 20; step += 1) {
      await page.keyboard.press("Tab");
      const where = await page.evaluate(() => {
        const node = document.activeElement as HTMLElement | null;
        return node?.getAttribute("href") ?? null;
      });
      if (where) reached.push(where);
    }
    for (const path of ["/", "/build", "/affixes", "/explain", "/rules", "/corpus"]) {
      expect(reached, `${path} is not reachable by keyboard`).toContain(path);
    }
  });

  test("focus is visible wherever it lands, not only on the first stop", async ({
    page,
  }) => {
    await page.goto("/rules");
    for (let step = 0; step < 8; step += 1) {
      await page.keyboard.press("Tab");
      const shown = await page.evaluate(() => {
        const node = document.activeElement;
        if (!node || node === document.body) return true;
        const style = getComputedStyle(node);
        return (
          parseFloat(style.outlineWidth) > 0 ||
          style.boxShadow !== "none" ||
          style.outlineStyle !== "none"
        );
      });
      expect(shown, `stop ${step} has no visible focus`).toBe(true);
    }
  });

  test("the feedback panel can be opened and closed from the keyboard", async ({
    page,
  }) => {
    await page.goto("/rules");
    const button = page.getByRole("button", { name: "بازخورد" });
    await button.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.getByRole("button", { name: "بستن" }).focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("dialog")).toBeHidden();
  });

  test("the labels a screen reader announces are in Persian", async ({ page }) => {
    await page.goto("/corpus");
    // The interface is in Farsi (docs/FRONTEND.md) and an accessible name in
    // English would be the one place that stopped being true.
    const names = await page.evaluate(() =>
      Array.from(document.querySelectorAll("[aria-label]")).map((node) =>
        node.getAttribute("aria-label"),
      ),
    );
    expect(names.length).toBeGreaterThan(0);
    for (const name of names) {
      expect(name, `not Persian: ${name}`).toMatch(/[؀-ۿ]/);
    }
  });

  test("the document says what language it is and which way it runs", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("lang", "fa");
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  });

  test("the page has a title that says which screen it is", async ({ page }) => {
    // 2.4.2. A tab reading "murfulu" on all seven is no help to anyone.
    await page.goto("/rules");
    await expect(page).toHaveTitle(/دستورهای واژه‌سازی/);
    await page.goto("/corpus");
    await expect(page).toHaveTitle(/پیکره/);
  });
});
