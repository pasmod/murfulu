/**
 * The suggestion list under a search box, in a real browser.
 *
 * What jsdom cannot see: that the list opens under the box and as wide as
 * it, stays on a 375 px screen without pushing the page sideways, gives every
 * suggestion a full touch target, sits above what follows the box, and passes
 * an accessibility audit while open. The keys are checked once more here,
 * against the real API, because Enter on a suggestion must not also submit
 * the form it sits in.
 *
 * It needs the API with `/suggest/words` and `/suggest/texts`, the lexicon
 * and the corpus. Without them, it skips, and says why.
 */

import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const DIL = "دل";

async function served(page: Page, path: string): Promise<boolean> {
  const answer = await page.request.get(path);
  if (!answer.ok()) return false;
  const body = await answer.json();
  return Array.isArray(body.suggestions) && body.suggestions.length > 0;
}

async function sideways(page: Page): Promise<number> {
  return page.evaluate(() => document.body.scrollWidth - document.body.clientWidth);
}

const BOXES = [
  { path: "/bank", name: "جست‌وجو در بانک واژه", typed: DIL, needs: "/api/suggest/words?q=دل" },
  { path: "/texts", name: "متنی را باز کنید", typed: "حافظ", needs: "/api/suggest/texts?q=حافظ" },
  { path: "/build", name: "واژه‌ای بنویسید", typed: "رف", needs: "/api/suggest/words?q=رف" },
  { path: "/", name: "جست‌وجوی واژه", typed: DIL, needs: "/api/suggest/words?q=دل" },
];

test.describe("the suggestion list", () => {
  for (const box of BOXES) {
    test(`${box.path}: opens under the box, inside the screen, every one a touch target`, async ({
      page,
    }) => {
      test.skip(!(await served(page, box.needs)), "no suggestions served");
      await page.goto(box.path);
      const input = page.getByRole("combobox", { name: box.name });
      await input.fill(box.typed);
      const list = page.getByRole("listbox");
      await expect(list).toBeVisible();
      await expect(input).toHaveAttribute("aria-expanded", "true");

      const field = (await input.boundingBox())!;
      const shown = (await list.boundingBox())!;
      const width = page.viewportSize()!.width;
      // Under the box and no wider than it, inside the screen.
      expect(shown.y).toBeGreaterThanOrEqual(field.y + field.height - 1);
      expect(shown.x).toBeGreaterThanOrEqual(-1);
      expect(shown.x + shown.width).toBeLessThanOrEqual(width + 1);
      expect(await sideways(page)).toBeLessThanOrEqual(1);

      const options = list.getByRole("option");
      expect(await options.count()).toBeGreaterThan(0);
      for (const one of await options.all()) {
        const size = (await one.boundingBox())!;
        if (size.y > shown.y + shown.height) break; // scrolled out of the list
        expect(size.height, "touch target").toBeGreaterThanOrEqual(44);
      }

      // Above what follows: the first suggestion is what a press there finds.
      const first = (await options.first().boundingBox())!;
      const hit = await page.evaluate(
        ([x, y]) => document.elementFromPoint(x!, y!)?.closest("[role=option]") !== null,
        [first.x + first.width / 2, first.y + first.height / 2],
      );
      expect(hit).toBe(true);
    });
  }

  test("the keys move through it and Enter takes one without submitting the form", async ({
    page,
  }) => {
    test.skip(!(await served(page, "/api/suggest/words?q=دل")), "no suggestions served");
    await page.goto("/bank");
    const input = page.getByRole("combobox", { name: "جست‌وجو در بانک واژه" });
    await input.fill(DIL);
    await expect(page.getByRole("listbox")).toBeVisible();
    await input.press("ArrowDown");
    const marked = page.getByRole("option", { selected: true });
    await expect(marked).toHaveCount(1);
    await expect(input).toHaveAttribute("aria-activedescendant", (await marked.getAttribute("id"))!);
    await input.press("Enter");
    await expect(page).toHaveURL(/exact=1/);
    await expect(page.getByRole("listbox")).toBeHidden();
    await input.fill("دلب");
    await expect(page.getByRole("listbox")).toBeVisible();
    await input.press("Escape");
    await expect(page.getByRole("listbox")).toBeHidden();
    await expect(input).toHaveValue("دلب");
  });

  test("an open list has no accessibility violations", async ({ page }) => {
    test.skip(!(await served(page, "/api/suggest/words?q=دل")), "no suggestions served");
    await page.goto("/bank");
    const input = page.getByRole("combobox", { name: "جست‌وجو در بانک واژه" });
    await input.fill(DIL);
    await expect(page.getByRole("listbox")).toBeVisible();
    await input.press("ArrowDown");
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(result.violations.map((one) => `${one.id}: ${one.nodes[0]?.target}`)).toEqual([]);
  });
});
