/**
 * What a decision reaches, and how a newly known one joins those in force
 * (2026-11-21). Written for the test; no corpus text.
 */

import { describe, expect, it } from "vitest";

import type { Decision, UnsureSpelling } from "../../api/texts";
import { keyOf, reach, replacing, sameReach } from "./decide";

function decision(id: number, latin: string, scope: Decision["scope"], word: string | null = null): Decision {
  return { id, latin, scope, scope_word: word, in_bank: true, created_at: null };
}

describe("deciding once for every like place", () => {
  it("keys a spelling as the list does, without half-spaces", () => {
    expect(keyOf("می‌رود")).toBe("میرود");
    expect(sameReach(decision(1, "x", "after_word", "می‌رود"), "after_word", "میرود")).toBe(true);
    expect(sameReach(decision(1, "x", "after_word", "که"), "before_word", "که")).toBe(false);
  });

  it("lets the newer of two decisions for one reach stand, whichever comes back last", () => {
    const a = decision(5, "Del", "everywhere");
    const b = decision(6, "Dal", "everywhere");
    expect(replacing(replacing([], a), b)).toEqual([b]);
    expect(replacing(replacing([], b), a)).toEqual([b]);
    const other = decision(7, "Dol", "after_word", "که");
    expect(replacing([b], other)).toEqual([other, b]);
  });

  it("counts the places a reach covers from the measured list", () => {
    const listed = {
      places: 10,
      unsure: 7,
      before: [["که", 4, 3]],
      after: [["از", 2, 1]],
    } as unknown as UnsureSpelling;
    expect(reach(listed, "everywhere", null)).toEqual({ places: 10, unsure: 7 });
    expect(reach(listed, "after_word", "که")).toEqual({ places: 4, unsure: 3 });
    expect(reach(listed, "before_word", "از")).toEqual({ places: 2, unsure: 1 });
    expect(reach(listed, "before_word", "که")).toBeNull();
    expect(reach(null, "everywhere", null)).toBeNull();
  });
});
