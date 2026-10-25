import { defineConfig, devices } from "@playwright/test";

/**
 * The layout tests. Separate from the Vitest suite because they need a real
 * browser: jsdom has no layout engine, so it cannot tell you that a row
 * overflows a 375 px screen — and that is the exact failure
 * docs/FRONTEND.md asks to be checked for.
 *
 * The dev server is started by the test run, so `npm run test:layout` needs
 * nothing else running.
 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://localhost:4173",
    // Persian is the interface; a browser asking for English would load the
    // wrong locale defaults and hide bugs the real reader would see.
    locale: "fa-IR",
    // **Keep the evidence when something fails.** Five layout tests failed only
    // in CI and had done so, unnoticed, since before anyone looked: they passed
    // on a Mac with the API up and with it stopped, so the difference was the
    // CI browser itself and there was nothing to look at. The cause was found
    // by reasoning — a flex item that will not shrink below its own content —
    // and reasoning is what this replaces. A trace carries the DOM, the
    // stylesheets and the frame, so the next one is read rather than guessed at.
    // See OPEN_QUESTIONS S24.
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      // 375 px is the standard small case in docs/FRONTEND.md. Chromium with
      // touch and mobile emulation rather than the WebKit iPhone descriptor:
      // what is being checked is layout, and one engine is enough for that.
      // Adding WebKit later would catch rendering differences, not layout.
      name: "phone",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 375, height: 812 },
        isMobile: true,
        hasTouch: true,
        deviceScaleFactor: 3,
      },
    },
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 900 } },
    },
  ],
  webServer: {
    command: "npm run build && npm run preview -- --port 4173 --strictPort",
    url: "http://localhost:4173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
