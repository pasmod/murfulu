/**
 * The design system, checked as a system.
 *
 * A stylesheet that names a token nobody defined does not fail — the browser
 * quietly drops the declaration and the element renders wrong. So the check has
 * to be here.
 */

import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const SOURCE = join(process.cwd(), "src");

function stylesheets(directory: string): string[] {
  const found: string[] = [];
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      found.push(...stylesheets(path));
    } else if (entry.name.endsWith(".css")) {
      found.push(path);
    }
  }
  return found;
}

const FILES = stylesheets(SOURCE);
const TOKENS = readFileSync(join(SOURCE, "styles/tokens.css"), "utf8");

const DEFINED = new Set(
  [...TOKENS.matchAll(/^\s*(--[a-z0-9-]+):/gm)].map((match) => match[1]),
);

describe("the tokens", () => {
  it("are all defined before they are used", () => {
    const missing: string[] = [];
    for (const file of FILES) {
      const css = readFileSync(file, "utf8");
      for (const use of css.matchAll(/var\((--[a-z0-9-]+)/g)) {
        if (!DEFINED.has(use[1])) {
          missing.push(`${file}: ${use[1]}`);
        }
      }
    }
    expect(missing).toEqual([]);
  });

  it("cover colour, space and type", () => {
    for (const token of [
      "--accent",
      "--ink",
      "--paper",
      "--line",
      "--space-4",
      "--text-base",
      "--font-fa",
      "--font-latin",
      "--touch-target",
    ]) {
      expect(DEFINED).toContain(token);
    }
  });

  it("keep the evidence colours apart, because each states a different fact", () => {
    for (const token of [
      "--evidence-reading",
      "--evidence-spelling",
      "--evidence-none",
    ]) {
      expect(DEFINED).toContain(token);
    }
  });

  it("give focus a colour of its own, not the accent", () => {
    const focus = /--focus:\s*([^;]+);/.exec(TOKENS)?.[1]?.trim();
    const accent = /--accent:\s*([^;]+);/.exec(TOKENS)?.[1]?.trim();
    expect(focus).toBeTruthy();
    expect(focus).not.toBe(accent);
  });
});

describe("the stylesheets", () => {
  it("hard-code no colours outside the token file", () => {
    const offenders: string[] = [];
    for (const file of FILES) {
      if (file.endsWith("tokens.css")) continue;
      const css = readFileSync(file, "utf8");
      for (const colour of css.matchAll(/#[0-9a-fA-F]{3,8}\b|\brgb\(/g)) {
        offenders.push(`${file}: ${colour[0]}`);
      }
    }
    expect(offenders).toEqual([]);
  });

  it("size the touch targets at 44 px, which is the guideline", () => {
    expect(TOKENS).toMatch(/--touch-target:\s*44px/);
    const shell = readFileSync(join(SOURCE, "shell/Shell.module.css"), "utf8");
    expect(shell).toContain("min-height: var(--touch-target)");
  });

  it("lay out with logical properties, so the RTL layout is not a mirror hack", () => {
    const offenders: string[] = [];
    for (const file of FILES) {
      const css = readFileSync(file, "utf8");
      // `left`/`right` in a right-to-left interface is nearly always a bug:
      // the layout has to follow the writing direction, not the screen.
      for (const side of css.matchAll(/^\s*(margin|padding|border)-(left|right)/gm)) {
        offenders.push(`${file}: ${side[0].trim()}`);
      }
    }
    expect(offenders).toEqual([]);
  });

  it("never fold Latin to lower case, because capitals carry grammar", () => {
    const latin = readFileSync(join(SOURCE, "text/Latin.module.css"), "utf8");
    expect(latin).toContain("text-transform: none");
    expect(latin).toContain("unicode-bidi: isolate");
  });
});
