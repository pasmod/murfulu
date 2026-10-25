/**
 * The narrowest phone we claim to support.
 *
 * **The layout suite runs at 375px and that was not narrow enough.** Four
 * screens pushed the page sideways from 2026-08-14 and passed here every time,
 * because the fault only shows where the default face renders a little wider
 * than it does on macOS — which is exactly what CI's Linux Chromium does. It
 * was green locally and 43px past the edge there, on every run, for two days.
 *
 * 320px is the iPhone SE and the floor of what a Persian interface has to hold.
 * Testing at it turns "wider fonts somewhere else" into a failure anybody can
 * reproduce, which is the only reason the cause was ever found.
 *
 * The cause both times was the same: a flex item will not shrink below its own
 * content unless it is told to. `overflow-x: auto` on the navigation never
 * scrolled, and `flex: 1` on a search box kept the input at its intrinsic
 * twenty characters. Both now set `min-width: 0`.
 */

import { expect, test } from "@playwright/test";

/**
 * The screens with a text input, which is where this went wrong — plus
 * `/corpus`, which carries the longest label in the interface. Naming karbon's
 * dictionary «واژه‌نامهٔ کاربن» rather than «فرهنگ» on 2026-08-16 tripled that
 * label's length, and it sits in a heading and in a two-column definition list.
 */
const NARROW = ["/", "/build", "/compound", "/explain", "/corpus"];

test.describe("at the narrowest phone", () => {
  test.skip(({ viewport }) => (viewport?.width ?? 0) > 400, "phone only");

  for (const path of NARROW) {
    test(`${path} does not scroll sideways at 320px`, async ({ page }) => {
      await page.setViewportSize({ width: 320, height: 700 });
      await page.goto(path);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

      const over = await page.evaluate(
        () => document.body.scrollWidth - document.body.clientWidth,
      );
      expect(over).toBeLessThanOrEqual(1);
    });
  }
});
