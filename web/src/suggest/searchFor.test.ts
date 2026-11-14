import { describe, expect, it } from "vitest";

import type { TextSuggestion } from "../api/suggest";
import { MOST, searchFor } from "./searchFor";

function text(parts: string[]): TextSuggestion {
  return { kind: "text", parts, query: parts.join(" "), texts: 1, document_id: "x:y:1" };
}

describe("the search a picked text stands for", () => {
  it("is its whole heading when that fits", () => {
    expect(searchFor(text(["سعدی", "گلستان", "دیباچه"]))).toBe("سعدی گلستان دیباچه");
  });

  it("leaves off whole parts, never half a word, when the heading is too long", () => {
    const title = "بخش ۷۶ - " + "در بیان آنکه پیغمبران ".repeat(10);
    expect(searchFor(text(["سلطان ولد", "ولدنامه", title]))).toBe("سلطان ولد ولدنامه");
  });

  it("cuts a part too long on its own at a word, and stays within the limit", () => {
    const long = "پیغمبران ".repeat(30).trim();
    const asked = searchFor(text([long]));
    expect(asked.length).toBeLessThanOrEqual(MOST);
    expect(asked.split(" ").every((word) => word === "پیغمبران")).toBe(true);
  });
});
