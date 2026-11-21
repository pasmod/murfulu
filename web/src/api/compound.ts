/**
 * Compounds: what the grammar can join to a word, and who wrote which.
 *
 * **The counts are the point, not decoration.** One noun makes thousands of
 * compounds and the corpus holds a fraction of a percent of them — دل builds
 * 4,652 and 220 were ever written — so a list of forty means nothing without
 * the number it was drawn from. Every reading carries all three.
 *
 * **And an attested compound is marked, never trusted.** دلم has 12,947
 * documents and is دل plus a possessive, not a compound: میدن's present stem
 * is the single letter م. The row is shown with the reason on it and ranked
 * below the real compounds, because dropping it would hide a word the reader
 * has every right to see.
 */

import { get } from "./client";
import type { FormScore } from "./generate";

/** Where a spelling also reads as an inflection of a word we already hold. */
export interface Inflection {
  base: string;
  pattern: string;
  label_fa: string;
  /** Rules in the pack whose affix is spelled the same way. */
  shared_with_rules: string[];
  is_shared: boolean;
}

export interface Evidence {
  level: "reading" | "spelling" | "none";
  corpus_version: string;
  total_count: number;
  doc_count: number;
  author_count: number;
  first_century: number | null;
  last_century: number | null;
  /** Set when the letters are a function word's: counts zero, meaning unknown. */
  function_word?: string | null;
  /**
   * The bank reads these letters only as other words: *dalbar* built on the
   * tree has دلبر's letters, and دلبر is *delbar*. Absent from an older API.
   */
  headword_homograph?: boolean;
  wording: string;
}

/**
 * A compound's two values, in the build screen's shape (`FormScore`).
 *
 * **«ساخت» is the compounds' own** (DECISIONS 2026-11-21, *a build value for
 * compounds*): what the second half has made after this rule's words — the
 * compounds the dictionary holds under that reading and the corpus has — on a
 * scale where the best half measured, «‑دار», is 100. Null where the half was
 * not measured (one letter, or a template rule), which is never a zero.
 * `weakest_rule.affix` is the half, `types` the words it was tried after,
 * `attested` the compounds it made.
 */
export type CompoundScore = Omit<FormScore, "build"> & { build: number | null };

export interface Pairing {
  form_latin: string;
  form_fa: string;
  /** With its short vowels, for display only (DECISIONS 2026-11-21). */
  form_fa_marked?: string;
  word_class: string;
  rule_id: string;
  label_fa: string | null;
  explanation_fa: string | null;
  /** The first half, and what the rule counted it as: `nam`, `karbon_do`… */
  front: { fa: string; latin: string; type: string | null };
  /**
   * The second half — the one the reader did not choose — with the verb it is
   * a stem of. **`of` is what makes the row checkable**: ور alone is a letter
   * pair, ور از وشتن is a claim a reader can agree or disagree with.
   */
  behind: {
    fa: string;
    latin: string;
    type: string | null;
    of: { fa: string; latin: string } | null;
  };
  role: string;
  attestation: Evidence | null;
  is_attested: boolean;
  /** Absent from an API older than 2026-11-21. */
  score?: CompoundScore;
  also_an_inflection: Inflection | null;
  /**
   * The dictionary already holds this exact spelling. **Confirmation, not
   * doubt**: دلبر is a headword and is also دل + بر, the same word by both
   * routes. What it tells a reader is that this one is taken.
   */
  already_a_word: boolean;
}

export interface CompoundReading {
  latin: string;
  spelling_fa: string;
  /** With its short vowels, for display only (DECISIONS 2026-11-21). */
  spelling_fa_marked?: string;
  lexicon_category: string | null;
  /** The linguist's word-bank groups, by his names. Empty before karbon 1.3. */
  bank_groups?: string[];
  needs_review: boolean;
  /**
   * Which dictionary entry this is (karbon's first row id). The Latin cannot
   * name one: *Allākolang* is both الاکلنگ and الا کلنگ. Null for a word added
   * by an override, which has no row.
   */
  entry?: number | null;
  /** The dictionary's own words for this entry: what tells دل the heart from دل the tree. */
  definition_fa?: string | null;
  /**
   * How many words built on this reading the dictionary holds under exactly
   * this reading **and** the corpus has. The API puts the reading with the
   * most first: دل's *Del* has 24, its *Dal* and *Dol* none. Null when the
   * corpus did not answer, which is not a zero; absent from an API older than
   * 2026-11-21.
   */
  confirmed?: number | null;
  /** Everything the rules can join to this word. */
  built: number;
  /** How many of them the corpus has. */
  attested: number;
  unattested: number;
  /** How many partner words were offered to the rules. */
  partners_tried: number;
  /** The whole list's length, before the page was cut. */
  count?: number;
  /** Kinds of compounding this reading cannot reach, and why. */
  skipped: Record<string, string>;
  /** What this reading counts as in the grammar: `nam`, `karnam`… */
  word_classes: string[];
  /** What the slot rules want in the front position. */
  slot_wants: string[];
  returned: number;
  pairings: Pairing[];
}

export interface Compounds {
  word: string;
  partner: string | null;
  rule_pack_version: string;
  lexicon_snapshot_id: string;
  showing: string;
  /** The entries written this way, the best-evidenced first. */
  readings: CompoundReading[];
}

/** How many rows of a reading the page asks for: the best, as ranked by the API. */
export const BEST = 1000;

/**
 * @param attested `true` — the default the route has always had — returns only
 * the compounds the corpus holds. **`false` is where the new words are**: دل
 * builds 4,652 and 109 were ever written, and until 2026-08-18 the screen
 * could not ask for the other 4,543 at all. Coining is what this project is
 * for, so the list a coiner needs must be reachable.
 */
export function compound(
  word: string,
  attested = true,
  signal?: AbortSignal,
): Promise<Compounds> {
  return get<Compounds>(
    "/compound",
    // **The best thousand**, as the build screen asks: the API ranks by how
    // well built first (2026-11-21), so a thousand of دل's 4,685 hold every
    // measured word and every attested one.
    attested ? { word } : { word, attested: "false", limit: String(BEST) },
    signal,
  ).then((body) => ({
    ...body,
    readings: body.readings ?? [],
  }));
}

/** One row, across the two answers: the same join, by the same rule, of the same half. */
function rowKey(row: Pairing): string {
  return `${row.form_fa}|${row.form_latin}|${row.rule_id}|${row.behind.latin}`;
}

/**
 * The best thousand of every entry, **and every row the corpus has**.
 *
 * Asked as two answers because a cut at a thousand, best built first, can
 * drop attested words: چادر builds 1,419 rows with a value above zero, and
 * its attested چادرکشان, at zero, fell outside them — reachable before, when
 * the screen asked for the attested list, and not after (the review of
 * 2026-11-21). The attested rows beyond the thousand are added after it, in
 * the API's order; each list is the API's own, so nothing is reordered here.
 */
export async function everyCompound(
  word: string,
  signal?: AbortSignal,
): Promise<Compounds> {
  const [best, attested] = await Promise.all([
    compound(word, false, signal),
    get<Compounds>("/compound", { word, limit: "0" }, signal).then((body) => ({
      ...body,
      readings: body.readings ?? [],
    })),
  ]);
  const entryOf = (reading: CompoundReading) =>
    `${reading.entry ?? ""}|${reading.spelling_fa}|${reading.latin}`;
  const held = new Map(attested.readings.map((one) => [entryOf(one), one]));
  return {
    ...best,
    readings: best.readings.map((reading) => {
      const also = held.get(entryOf(reading));
      if (!also) return reading;
      const shown = new Set(reading.pairings.map(rowKey));
      const missing = also.pairings.filter((row) => !shown.has(rowKey(row)));
      return missing.length
        ? { ...reading, pairings: [...reading.pairings, ...missing] }
        : reading;
    }),
  };
}
