/**
 * Contrast, computed from the tokens rather than eyeballed.
 *
 * WCAG 2.1 AA is promised in the funding application: **4.5:1** for body text,
 * **3:1** for large text and for the boundary of anything a reader has to see
 * to use — a button, an input, the filled part of a bar.
 *
 * It is checked here, on the palette, and not only in the browser. A page can
 * pass an automated audit simply by not happening to put a given pair of
 * colours together on the day it ran; the palette either has the ratio or it
 * does not, and a colour with no combination that passes is a fault whichever
 * component reaches for it next.
 *
 * The formula is the one WCAG defines, not an approximation.
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const TOKENS = readFileSync(join(process.cwd(), "src/styles/tokens.css"), "utf8");

function value(name: string): string {
  const found = new RegExp(`${name}:\\s*(#[0-9a-fA-F]{6})\\s*;`).exec(TOKENS);
  if (!found) throw new Error(`no colour for ${name}`);
  return found[1]!;
}

/** WCAG relative luminance. */
function luminance(hex: string): number {
  const parts = [1, 3, 5].map((at) => parseInt(hex.slice(at, at + 2), 16) / 255);
  const linear = parts.map((channel) =>
    channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4,
  );
  return 0.2126 * linear[0]! + 0.7152 * linear[1]! + 0.0722 * linear[2]!;
}

function ratio(one: string, other: string): number {
  const [light, dark] = [luminance(one), luminance(other)].sort((a, b) => b - a);
  return (light! + 0.05) / (dark! + 0.05);
}

/** Rounded down, so a pair that only just fails cannot round its way past. */
function measured(front: string, back: string): number {
  return Math.floor(ratio(value(front), value(back)) * 100) / 100;
}

const BODY = 4.5;
const LARGE = 3;

/**
 * Every ground the app actually paints text on.
 *
 * There are three, not two, and the third is why this list exists: the tinted
 * panel behind a finding is darker than the sunk grey, and a check against
 * white and grey alone passed while `--ink-faint` sat at 4.24:1 on it. The
 * page audit caught that; the palette check should have.
 */
const GROUNDS = ["--paper", "--paper-sunk", "--accent-wash"];

describe("text on the page", () => {
  it.each(
    ["--ink", "--ink-soft", "--ink-faint", "--accent", "--accent-strong"].flatMap(
      (front) => GROUNDS.map((back) => [front, back]),
    ),
  )("%s on %s reaches 4.5:1", (front, back) => {
    expect(measured(front!, back!)).toBeGreaterThanOrEqual(BODY);
  });

  it("keeps white legible on the accent, which is every primary button", () => {
    expect(measured("--paper", "--accent")).toBeGreaterThanOrEqual(BODY);
    expect(measured("--paper", "--accent-strong")).toBeGreaterThanOrEqual(BODY);
  });
});

describe("the evidence colours", () => {
  /**
   * These carry meaning — the corpus confirms this reading, the corpus has the
   * letters only, the corpus does not have it — so they are read as text and
   * held to the text ratio.
   */
  it.each(
    ["--evidence-reading", "--evidence-spelling"].flatMap((front) =>
      GROUNDS.map((back) => [front, back]),
    ),
  )("%s on %s reaches 4.5:1", (front, back) => {
    expect(measured(front!, back!)).toBeGreaterThanOrEqual(BODY);
  });

  it("never leaves colour as the only difference", () => {
    // WCAG 1.4.1. Each level is written out in Persian beside its colour —
    // `Evidence` renders the wording, not a coloured dot — so a reader who
    // cannot tell green from brown loses nothing.
    const evidence = readFileSync(
      join(process.cwd(), "src/screens/build/Evidence.tsx"),
      "utf8",
    );
    expect(evidence).toMatch(/wording|attestation\.\w+/);
  });
});

describe("things that are not text", () => {
  it.each(GROUNDS)("draws focus at 3:1 against %s", (ground) => {
    // 2.4.11: the focus indicator has to be visible against what is behind it.
    expect(measured("--focus", ground)).toBeGreaterThanOrEqual(LARGE);
  });

  it("draws a filled bar at 3:1 against its track", () => {
    // The coverage bars on the corpus screen: the filled part against the
    // unfilled part is the whole information in the graphic. 1.4.11.
    expect(measured("--accent", "--paper-sunk")).toBeGreaterThanOrEqual(LARGE);
  });

  it.each(GROUNDS)("draws a control's edge at 3:1 against %s", (ground) => {
    // An input's border is the only thing saying where to type. 1.4.11.
    // `--line` is 1.26:1 and stays that way, because it only ever separates —
    // a rule under a table head, which nothing depends on seeing.
    expect(measured("--line-strong", ground)).toBeGreaterThanOrEqual(LARGE);
  });

  it("puts the stronger line on every control, and only there", () => {
    const controls = [
      "screens/search/QueryBox.module.css",
      "screens/build/WordInput.module.css",
      "screens/explain/Explain.module.css",
      "screens/affixes/Affixes.module.css",
      "feedback/Feedback.module.css",
    ];
    for (const file of controls) {
      const css = readFileSync(join(process.cwd(), "src", file), "utf8");
      expect(css, file).toContain("var(--line-strong)");
    }
  });
});
