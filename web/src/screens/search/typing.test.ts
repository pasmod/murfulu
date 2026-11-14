import { describe, expect, it } from "vitest";

import { complete, typing, wanted } from "./typing";

describe("the term being typed", () => {
  it("is the last one, with everything before it kept", () => {
    expect(typing("type:nam دل")).toEqual({ before: "type:nam ", term: "دل" });
    expect(typing("raf")).toEqual({ before: "", term: "raf" });
  });

  it("is nothing after a space or inside an open quote", () => {
    expect(typing("دل ")).toBeNull();
    expect(typing("")).toBeNull();
    expect(typing('category:"اسم ذا')).toBeNull();
    expect(typing("author:'سید دل")).toBeNull();
    // An apostrophe inside double quotes is a letter, as the parser reads it.
    expect(typing(`author:"O'Connor" دل`)).toEqual({ before: `author:"O'Connor" `, term: "دل" });
    expect(typing('category:"a \\" b" دل')?.term).toBe("دل");
  });

  it("is a word, an author, or something the bank cannot finish", () => {
    expect(wanted("دل")).toEqual({ kind: "word", text: "دل" });
    expect(wanted("author:فرد")).toEqual({ kind: "author", text: "فرد" });
    expect(wanted('author:"سید')).toEqual({ kind: "author", text: "سید" });
    expect(wanted("author:")).toBeNull();
    for (const term of ["*nā", "bar*", "type:nam", "/g[ou]ft/", "-eš"]) {
      expect(wanted(term)).toBeNull();
    }
  });

  it("is replaced whole, quoted when it holds a space", () => {
    const at = typing("in:corpus بااینه")!;
    expect(complete(at, "word", "با اینهمه")).toBe('in:corpus "با اینهمه"');
    expect(complete(typing("author:فرد")!, "author", "فردوسی")).toBe("author:فردوسی");
  });

  it("writes a Persian word as the index holds it", () => {
    expect(complete(typing("مسک")!, "word", "مسکينی")).toBe("مسکینی");
    expect(complete(typing("ك")!, "word", "كتاب")).toBe("کتاب");
  });
});
