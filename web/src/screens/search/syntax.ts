/**
 * The search language, in one place.
 *
 * Three things write queries — the examples under the box, the facet panel
 * beside the results, and the builder — and until 2026-08-17 each spelled the
 * syntax out for itself. They drifted: the facet panel wrote `category:…` for
 * a year and `src/murfulu/search/query.py` had no `category` field, so every
 * click on a category value turned a working search into *this query was not
 * read*. Nothing caught it, because the screen's tests mock the API and the
 * parser is in Python.
 *
 * So the names live here, `tests/test_search_syntax_contract.py` reads this
 * file and asserts the parser accepts every one of them, and a fourth thing
 * that writes a query has one place to get it right.
 *
 * **Nothing here invents Persian about the grammar.** The word classes are
 * labelled from `rules/word_classes.yaml` through the API, per FRONTEND.md;
 * what is written here is interface language — *frequency*, *where found* —
 * which is this file's to name.
 */

import { LEXICON } from "../../text/lexicon";

/** How a bare pattern is written. One per query; the parser refuses two. */
export interface Pattern {
  key: string;
  label: string;
  write: (value: string) => string;
  /** Reads a pattern term back, so the builder can show what is in the box. */
  read: (term: string) => string | null;
}

export const PATTERNS: Pattern[] = [
  {
    key: "ends",
    label: "پایان‌یافته به",
    write: (value) => `*${value}`,
    read: (term) =>
      term.startsWith("*") && !term.endsWith("*") ? term.slice(1) : null,
  },
  {
    key: "starts",
    label: "آغازشده با",
    write: (value) => `${value}*`,
    read: (term) =>
      term.endsWith("*") && !term.startsWith("*") ? term.slice(0, -1) : null,
  },
  {
    key: "contains",
    label: "دربردارندهٔ",
    write: (value) => `*${value}*`,
    read: (term) =>
      term.startsWith("*") && term.endsWith("*") && term.length > 2
        ? term.slice(1, -1)
        : null,
  },
  {
    key: "exact",
    label: "دقیقاً همین",
    write: (value) => value,
    read: (term) =>
      term.includes("*") || term.startsWith("/") ? null : term || null,
  },
];

/**
 * A `name:value` term. `name` is the parser's, and the contract test checks it.
 *
 * `values` is filled in only where the set is closed and the interface already
 * has the words for it. A word class is not here: its Persian comes from the
 * rule pack at runtime, never from this file.
 */
export interface Field {
  name: string;
  title: string;
  /** An example value, for the reference list. */
  example: string;
  hint: string;
}

export const FIELDS: Field[] = [
  {
    name: "type",
    title: "گونه",
    example: "karnam",
    hint: "گونه‌ای که ما به واژه داده‌ایم",
  },
  {
    name: "category",
    title: `گونه در ${LEXICON}`,
    example: "اسم ذات",
    hint: `گونه‌ای که ${LEXICON} برای واژه نوشته است`,
  },
  { name: "in", title: "کجا پیدا شده", example: "corpus", hint: "پیکره، واژه‌نامه یا ساخته‌شده" },
  { name: "stem1", title: "کاربن یک", example: "goft", hint: "بن گذشته" },
  { name: "stem2", title: "کاربن دو", example: "gu", hint: "بن اکنون" },
  { name: "affix", title: "وند", example: "-eš", hint: "واژه‌هایی که این وند را دارند" },
  { name: "tag", title: "معنا", example: "ja", hint: "وندهایی که این معنا را می‌رسانند" },
  { name: "rule", title: "دستور", example: "V-010", hint: "ساخته‌شده با این دستور" },
  { name: "author", title: "شاعر", example: "فردوسی", hint: "در سروده‌های این شاعر" },
  { name: "source", title: "سرچشمه", example: "ganjoor", hint: "از این سرچشمه" },
];

/** Where a word was found. The one closed set the interface already names. */
export const POPULATIONS = ["corpus", "lexicon", "generated"];

/** How a frequency band is written. `count:1` is exactly one — the hapax. */
export const COUNTS = [
  { key: "gt", label: "بیش از", write: (n: number) => `count:>${n}` },
  { key: "lt", label: "کمتر از", write: (n: number) => `count:<${n}` },
  { key: "eq", label: "دقیقاً", write: (n: number) => `count:${n}` },
];

/** Every form the language takes, for the reference list. Each one runs. */
export const REFERENCE: { query: string; hint: string }[] = [
  { query: "*nā", hint: "واژه‌هایی که به nā ختم می‌شوند" },
  { query: "bar*", hint: "واژه‌هایی که با bar آغاز می‌شوند" },
  { query: "*raft*", hint: "واژه‌هایی که raft در آن‌هاست" },
  { query: "gereft", hint: "دقیقاً همین واژه" },
  { query: "/g[ou]ft/", hint: "الگوی باقاعده" },
  { query: "روش", hint: "نوشتار فارسی، که در املا جست‌وجو می‌شود" },
  ...FIELDS.map((one) => ({
    query: `${one.name}:${one.example}`,
    hint: one.hint,
  })),
  { query: "count:>10", hint: "بیش از ده بار نوشته شده" },
  { query: "count:1", hint: "تنها یک بار نوشته شده" },
  { query: "century:10-13", hint: "میان سدهٔ دهم و سیزدهم" },
  { query: "*nā type:nam in:corpus", hint: "همه با هم می‌آیند" },
];

/** One term of a query: a `name:value`, or the bare pattern. */
export interface Term {
  name: string | null;
  value: string;
  raw: string;
}

/**
 * Write a value so the parser reads it whole.
 *
 * `query.py` splits a query with `shlex`, so an unquoted space ends the term:
 * the facet panel wrote `category:اسم ذات` and the parser read *category is
 * اسم*, and separately *the word is ذات*. It did not fail — it answered a
 * question nobody asked, which is why it outlived the missing-field bug beside
 * it. Dehkhoda's categories are two words more often than one.
 */
export function writeValue(value: string): string {
  return /[\s"']/.test(value) ? `"${value.replace(/"/g, '\\"')}"` : value;
}

/** The other half: read back what `writeValue` wrote. */
export function readValue(value: string): string {
  return value.startsWith('"') && value.endsWith('"') && value.length > 1
    ? value.slice(1, -1).replace(/\\"/g, '"')
    : value;
}

/** A whole `name:value` term, quoted where it has to be. */
export function term(name: string, value: string | number): string {
  return `${name}:${writeValue(String(value))}`;
}

/**
 * Split a query into terms.
 *
 * Deliberately simpler than `query.py`: this reads a query back to show it in
 * the builder, and a term it cannot place is kept whole and put back
 * untouched. Quoting and regexes are the parser's business, not the builder's.
 */
export function readTerms(query: string): Term[] {
  // Quoted values hold spaces, so the split has to keep them together — the
  // same job `shlex` does on the other side.
  return (query.trim().match(/(?:[^\s"]+|"[^"]*")+/g) ?? []).map((raw) => {
    if (raw.startsWith("/") || !raw.includes(":")) {
      return { name: null, value: raw, raw };
    }
    const [name, ...rest] = raw.split(":");
    return { name: name ?? null, value: readValue(rest.join(":")), raw };
  });
}

/**
 * Set one `name:value` term, or remove it when `value` is null.
 *
 * **Everything else keeps its place.** A builder that rebuilt the query from
 * its own controls would silently drop the terms it has no control for — a
 * reader who typed `tag:ja` and then picked a century would lose the tag.
 */
export function setTerm(
  query: string,
  name: string,
  value: string | null,
): string {
  const kept = readTerms(query).filter((one) => one.name !== name);
  const raws = kept.map((one) => one.raw);
  if (value) raws.push(term(name, value));
  return raws.join(" ");
}

/** Read back the value of a `name:value` term, if the query has one. */
export function getTerm(query: string, name: string): string {
  return readTerms(query).find((one) => one.name === name)?.value ?? "";
}

/** Set the bare pattern, or remove it when null. The parser allows only one. */
export function setPattern(query: string, pattern: string | null): string {
  const kept = readTerms(query).filter((one) => one.name !== null);
  return [...(pattern ? [pattern] : []), ...kept.map((one) => one.raw)].join(" ");
}

/** The bare pattern in a query, if it has one. */
export function getPattern(query: string): string {
  return readTerms(query).find((one) => one.name === null)?.raw ?? "";
}
