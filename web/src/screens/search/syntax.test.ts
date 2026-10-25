/**
 * The query-writing half of the search language.
 *
 * `tests/test_search_syntax_contract.py` checks that what this file writes can
 * be *read* by the parser. This checks that it writes what the reader asked
 * for: that setting a term twice replaces it rather than contradicting itself,
 * that a term nobody has a control for survives, and that a value with a space
 * in it comes back whole.
 */

import { describe, expect, it } from "vitest";

import {
  FIELDS,
  PATTERNS,
  REFERENCE,
  getPattern,
  getTerm,
  readTerms,
  readValue,
  setPattern,
  setTerm,
  term,
  writeValue,
} from "./syntax";

describe("writing a value", () => {
  it("leaves an ordinary one alone", () => {
    expect(writeValue("karnam")).toBe("karnam");
    expect(term("type", "karnam")).toBe("type:karnam");
  });

  it("quotes one with a space, because the parser splits on it", () => {
    // The category facet wrote `category:اسم ذات` and the parser read two
    // different things from it and reported neither. It did not fail, which is
    // why it outlived the bug beside it.
    expect(term("category", "اسم ذات")).toBe('category:"اسم ذات"');
  });

  it("reads back what it wrote", () => {
    expect(readValue(writeValue("اسم ذات"))).toBe("اسم ذات");
    expect(getTerm(term("category", "اسم ذات"), "category")).toBe("اسم ذات");
  });

  it("keeps a quoted value in one piece when the query is split", () => {
    const query = `*nā ${term("category", "اسم ذات")} in:corpus`;
    expect(readTerms(query).map((one) => one.name)).toEqual([
      null,
      "category",
      "in",
    ]);
    expect(getTerm(query, "in")).toBe("corpus");
  });
});

describe("setting a term", () => {
  it("adds one that is not there", () => {
    expect(setTerm("*nā", "type", "karnam")).toBe("*nā type:karnam");
  });

  it("replaces one that is, rather than asking twice", () => {
    expect(setTerm("*nā type:karnam", "type", "nam")).toBe("*nā type:nam");
  });

  it("removes it when the reader clears the control", () => {
    expect(setTerm("*nā type:karnam", "type", null)).toBe("*nā");
  });

  it("leaves terms it has no control for exactly where they were", () => {
    // A reader who typed `tag:ja` and then picks a century keeps the tag.
    const before = "*nā tag:ja author:فردوسی";
    expect(setTerm(before, "century", "10-13")).toBe(
      "*nā tag:ja author:فردوسی century:10-13",
    );
  });
});

describe("the pattern", () => {
  it("is written the way each shape asks for", () => {
    const write = (key: string, value: string) =>
      PATTERNS.find((one) => one.key === key)!.write(value);
    expect(write("ends", "nā")).toBe("*nā");
    expect(write("starts", "bar")).toBe("bar*");
    expect(write("contains", "raft")).toBe("*raft*");
    expect(write("exact", "gereft")).toBe("gereft");
  });

  it("is read back to the same shape it was written in", () => {
    for (const one of PATTERNS) {
      const written = one.write("raft");
      const matched = PATTERNS.filter((other) => other.read(written) !== null);
      expect(matched.map((other) => other.key)).toEqual([one.key]);
      expect(one.read(written)).toBe("raft");
    }
  });

  it("replaces the pattern and keeps the filters", () => {
    expect(setPattern("*nā type:karnam", "bar*")).toBe("bar* type:karnam");
    expect(getPattern("*nā type:karnam")).toBe("*nā");
  });

  it("removes the pattern without touching the filters", () => {
    expect(setPattern("*nā type:karnam", null)).toBe("type:karnam");
  });

  it("never leaves two patterns, which the parser refuses outright", () => {
    expect(setPattern("*nā", "bar*").split(/\s+/).filter(Boolean)).toHaveLength(
      1,
    );
  });
});

describe("what the interface offers", () => {
  it("names every field once", () => {
    const names = FIELDS.map((one) => one.name);
    expect(new Set(names).size).toBe(names.length);
  });

  it("gives every field a Persian title and a plain-language hint", () => {
    for (const one of FIELDS) {
      expect(one.title.trim()).not.toBe("");
      expect(one.hint.trim()).not.toBe("");
      // The interface is in Persian; a title left in English is the bug the
      // project lead raised on the corpus screen.
      expect(one.title).toMatch(/[؀-ۿ]/);
      expect(one.hint).toMatch(/[؀-ۿ]/);
    }
  });

  it("shows every field in the reference, so nothing is reachable only by reading the source", () => {
    for (const one of FIELDS) {
      expect(REFERENCE.some((row) => row.query.startsWith(`${one.name}:`))).toBe(
        true,
      );
    }
  });
});
