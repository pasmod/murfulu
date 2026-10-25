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
  level: string;
  corpus_version: string;
  total_count: number;
  doc_count: number;
  author_count: number;
  first_century: number | null;
  last_century: number | null;
  /** Set when the letters are a function word's: counts zero, meaning unknown. */
  function_word?: string | null;
  wording: string;
}

export interface Pairing {
  form_latin: string;
  form_fa: string;
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
  lexicon_category: string | null;
  needs_review: boolean;
  /** Everything the rules can join to this word. */
  built: number;
  /** How many of them the corpus has. */
  attested: number;
  unattested: number;
  /** How many partner words were offered to the rules. */
  partners_tried: number;
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
  readings: CompoundReading[];
}

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
    attested ? { word } : { word, attested: "false", limit: "500" },
    signal,
  ).then((body) => ({
    ...body,
    readings: body.readings ?? [],
  }));
}
