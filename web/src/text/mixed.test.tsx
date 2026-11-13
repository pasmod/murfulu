/**
 * A Persian sentence with Latin inside it: each Latin run is set apart.
 *
 * Printed plain, «با پسوند -ande» showed the dash on the wrong side — the
 * reader saw «ande-», a prefix (measured in the browser on 2026-11-13). jsdom
 * cannot see where a dash lands, so what is checked is the cause: whether the
 * Latin sits in an island of its own direction.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Mixed } from "./Mixed";
import { splitLatin } from "./latinRuns";

describe("a rule's sentence", () => {
  it("sets a suffix apart, dash and all", () => {
    render(<Mixed>{"از کنون‌کاربن با پسوند -ande کارنده‌کاربهر ساخته می‌شود"}</Mixed>);
    expect(screen.getByText("-ande")).toHaveAttribute("dir", "ltr");
  });

  it("sets a prefix apart with its dash at the end", () => {
    render(<Mixed>{"از پیشین‌کاربن با پیشوند zir- نابسودکارواژه ساخته می‌شود"}</Mixed>);
    expect(screen.getByText("zir-")).toHaveAttribute("dir", "ltr");
  });

  it("keeps a Latin phrase in one island, so its words keep their order", () => {
    expect(splitLatin("پایه: Kārboné do است")).toEqual([
      { latin: false, text: "پایه: " },
      { latin: true, text: "Kārboné do" },
      { latin: false, text: " است" },
    ]);
  });

  it("keeps a rule id whole", () => {
    expect(splitLatin("دستور V-032 و N-098").filter((part) => part.latin)).toEqual([
      { latin: true, text: "V-032" },
      { latin: true, text: "N-098" },
    ]);
  });

  it("leaves a sentence with no Latin as it is", () => {
    expect(splitLatin("واژه‌ای که چگونگیِ نام را می‌گوید.")).toEqual([
      { latin: false, text: "واژه‌ای که چگونگیِ نام را می‌گوید." },
    ]);
  });

  it("changes no character of the sentence", () => {
    const said = "هنگام برخورد ā و e واج‌میانجی می‌آید و āye ساخته می‌شود";
    expect(splitLatin(said).map((part) => part.text).join("")).toBe(said);
  });
});
