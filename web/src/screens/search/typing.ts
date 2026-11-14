/**
 * The term being typed at the end of a query, which is what the box suggests
 * for.
 *
 * A query is several terms — `*nā type:nam in:corpus` — and only the last one
 * is being typed, so only the last one is completed: a suggestion replaces it
 * and leaves everything before it as it was. Nothing is suggested after a
 * space (the term is finished) or inside an open quote, double or single (the
 * term is not over); the box asks only while the caret is at the end.
 */

import { writeValue } from "./syntax";

export interface Typing {
  /** Everything before the term, its last space included. */
  before: string;
  term: string;
}

/**
 * Whether a quote is still open at the end, read the way the parser's `shlex`
 * reads one: either quote opens a value, the other kind inside it is a plain
 * letter (`author:"O'Connor"` is closed), and a backslash inside double
 * quotes escapes the next letter, as `writeValue` writes them.
 */
function quoteOpen(query: string): boolean {
  let open: string | null = null;
  for (let at = 0; at < query.length; at += 1) {
    const letter = query[at];
    if (open === null) {
      if (letter === '"' || letter === "'") open = letter;
      else if (letter === "\\") at += 1;
    } else if (open === '"') {
      if (letter === "\\") at += 1;
      else if (letter === '"') open = null;
    } else if (letter === "'") {
      open = null;
    }
  }
  return open !== null;
}

export function typing(query: string): Typing | null {
  const match = /^([\s\S]*?)(\S+)$/.exec(query);
  if (!match || quoteOpen(query)) return null;
  return { before: match[1] ?? "", term: match[2] ?? "" };
}

/** The foldings the corpus counting makes (`corpus/wordtypes.normalise`). */
const FOLD: Record<string, string> = { ي: "ی", ك: "ک", ة: "ه", أ: "ا", إ: "ا", ؤ: "و" };

/**
 * A Persian spelling as the search index holds it. The bank keeps sixteen
 * spellings with an Arabic yeh (مسکينی); the index folded them when it was
 * built, and the search compares letters exactly, so the bank's own spelling
 * would find nothing there.
 */
export function asIndexed(spelling: string): string {
  return spelling
    .normalize("NFC")
    .replace(/[\u064B-\u0652\u0670\u0640]/g, "")
    .replace(/[يكةأإؤ]/g, (letter) => FOLD[letter] ?? letter);
}

/** What a term is: a word to complete, an author to complete, or neither. */
export type Wanted = { kind: "word"; text: string } | { kind: "author"; text: string } | null;

const AUTHOR = "author:";

export function wanted(term: string): Wanted {
  if (term.startsWith(AUTHOR)) {
    const text = term.slice(AUTHOR.length).replace(/^"/, "");
    return text ? { kind: "author", text } : null;
  }
  // A pattern, a field, a regular expression or a quote is not a word: the
  // bank has nothing to finish it with.
  if (/[*:/"'()]/.test(term) || term.startsWith("-")) return null;
  return { kind: "word", text: term };
}

/** The query with its last term replaced. */
export function complete(at: Typing, kind: "word" | "author", value: string): string {
  const written = writeValue(kind === "word" ? asIndexed(value) : value);
  return `${at.before}${kind === "author" ? `${AUTHOR}${written}` : written}`;
}
