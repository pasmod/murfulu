/**
 * The search language, in one place.
 *
 * Three things write queries — the examples the box suggests, the facet panel
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
    label: "با این تمام شود",
    write: (value) => `*${value}`,
    read: (term) =>
      term.startsWith("*") && !term.endsWith("*") ? term.slice(1) : null,
  },
  {
    key: "starts",
    label: "با این شروع شود",
    write: (value) => `${value}*`,
    read: (term) =>
      term.endsWith("*") && !term.startsWith("*") ? term.slice(0, -1) : null,
  },
  {
    key: "contains",
    label: "این را در خود داشته باشد",
    write: (value) => `*${value}*`,
    read: (term) =>
      term.startsWith("*") && term.endsWith("*") && term.length > 2
        ? term.slice(1, -1)
        : null,
  },
  {
    key: "exact",
    label: "درست همین واژه",
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
  /** An example value. */
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
    example: "مصدر",
    hint: `گونه‌ای که ${LEXICON} برای واژه نوشته است`,
  },
  {
    name: "in",
    title: "این واژه از کجاست",
    example: "corpus",
    hint: "در متن‌ها آمده، در واژه‌نامه هست، یا ساختهٔ دستور است",
  },
  { name: "stem1", title: "پیشین‌کاربن", example: "goft", hint: "بن گذشته" },
  { name: "stem2", title: "کنون‌کاربن", example: "gu", hint: "بن اکنون" },
  { name: "affix", title: "وند", example: "-eš", hint: "واژه‌هایی که این وند را دارند" },
  { name: "tag", title: "معنا", example: "ja", hint: "وندهایی که این معنا را می‌رسانند" },
  { name: "rule", title: "دستور", example: "V-010", hint: "ساخته‌شده با این دستور" },
  { name: "author", title: "نویسنده", example: "فردوسی", hint: "در متن‌های این نویسنده" },
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

/**
 * Every form the language takes, as the search box's suggestions. Each runs.
 *
 * Until 2026-11-20 these were a list behind an ⓘ beside the box. The project
 * lead asked for them to be what the box suggests instead: stepping into the
 * empty box shows them all, typing narrows them, and each says in a line of
 * Persian what it finds — so the list teaches what the search can do by
 * example, where the reader already is.
 *
 * Written out one by one rather than made from `FIELDS`, because a line that
 * says what *this* query finds is clearer than one that describes the field.
 * A test holds that every field has one.
 */
export const EXAMPLES: { query: string; hint: string }[] = [
  { query: "*eš", hint: "واژه‌هایی که با «ـِش» تمام می‌شوند" },
  { query: "bar*", hint: "واژه‌هایی که با «بر» شروع می‌شوند" },
  { query: "*raft*", hint: "واژه‌هایی که «رفت» را در خود دارند" },
  { query: "gereft", hint: "درست همین واژه: «گرفت»" },
  { query: "/g[ou]ft/", hint: "چند شکل با یک الگو: goft یا guft" },
  { query: "روش", hint: "با خط فارسی هم می‌شود جست‌وجو کرد" },
  { query: "type:karnam", hint: "همهٔ کارنام‌ها (اسم مصدر)" },
  { query: "category:مصدر", hint: `آنچه ${LEXICON} «مصدر» نامیده است` },
  { query: "in:corpus", hint: "واژه‌هایی که در متن‌ها آمده‌اند" },
  { query: "stem1:goft", hint: "واژه‌هایی که از پیشین‌کاربن «گفت» ساخته شده‌اند" },
  { query: "stem2:gu", hint: "واژه‌هایی که از کنون‌کاربن «گو» ساخته شده‌اند" },
  { query: "affix:-eš", hint: "واژه‌هایی که با وند «ـِش» ساخته شده‌اند" },
  { query: "tag:ja", hint: "واژه‌هایی که وندشان معنای «جا» دارد" },
  { query: "rule:V-010", hint: "واژه‌هایی که با دستور V-010 ساخته شده‌اند" },
  { query: "author:فردوسی", hint: "واژه‌هایی که در متن‌های فردوسی آمده‌اند" },
  { query: "source:ganjoor", hint: "واژه‌هایی که از گنجور آمده‌اند" },
  { query: "count:>10", hint: "بیش از ده بار در متن‌ها آمده" },
  { query: "count:1", hint: "تنها یک بار در متن‌ها آمده" },
  { query: "century:10-13", hint: "در متن‌های سدهٔ دهم تا سیزدهم آمده" },
  {
    query: "*nā type:nam in:corpus",
    hint: "چند خواسته با هم: نام‌هایی که با «ـنا» تمام می‌شوند و در متن‌ها آمده‌اند",
  },
];

/**
 * The examples that fit what is typed: all of them for an empty box, else
 * those whose query or line of Persian holds the text. Upper and lower case
 * are one, as they are nowhere else in a query, because a reader typing
 * «Type» means the field.
 */
export function examplesFor(text: string): { query: string; hint: string }[] {
  const wanted = text.trim().toLowerCase();
  if (!wanted) return EXAMPLES;
  return EXAMPLES.filter(
    (one) =>
      one.query.toLowerCase().includes(wanted) || one.hint.includes(text.trim()),
  );
}

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
