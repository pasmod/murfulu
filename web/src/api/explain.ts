/**
 * Taking a word apart — the *sāzāyi* check.
 *
 * Every account the API returns was **rebuilt forward** and reproduced the
 * word exactly. Nothing here is a guess that survived on the strength of its
 * spelling: *Mowlānā* strips to a real dictionary word and is still refused,
 * because nothing can build it back.
 */

import { get } from "./client";

export interface AnalysisStep {
  rule_id: string;
  affix: string;
  affix_fa: string | null;
  label_fa: string | null;
  explanation_fa: string | null;
  applied_to: string;
  stem_form: string | null;
  glide_id: string | null;
}

/** What the corpus has for a form. Null means it was never asked. */
export interface BaseEvidence {
  level: "reading" | "spelling" | "none";
  corpus_version: string;
  total_count: number;
  doc_count: number;
  author_count: number;
  /** Set when the letters are a function word's: counts zero, meaning unknown. */
  function_word?: string | null;
  wording: string;
}

export interface Account {
  /** Which Behnevis reading this account takes apart. */
  form_latin: string;
  base: {
    latin: string;
    spelling_fa: string;
    lexicon_category: string | null;
    /**
     * How much of the corpus the **base itself** has.
     *
     * The one signal we already hold that separates a parse a reader would
     * accept from one that is merely arithmetic. It is evidence and never a
     * verdict — see `rebuilt`.
     */
    attestation: BaseEvidence | null;
  };
  depth: number;
  steps: AnalysisStep[];
}

export interface Explanation {
  word: string;
  /**
   * Which Behnevis forms were taken apart. The same as `word` unless the
   * reader typed Persian, in which case it is every reading the dictionary
   * records for that spelling — کنار is *Kanār* or *Kenār* and both are tried.
   */
  analysed_as: string[];
  depth: number;
  rule_pack_version: string;
  lexicon_snapshot_id: string;
  /**
   * A chain of real rules reproduces these letters from a dictionary entry.
   *
   * **It was called `explained` and that claimed more than it can.** The route
   * returned true for *Nāxodāgāhi* on ناخدا — a ship's captain — and for
   * *Hamzamāni* on a base of `Zam`. Both accounts are right about the letters
   * and useless about the word. Nothing here judges meaning; the screen says
   * what the flag is, and shows the base's own corpus evidence beside it.
   */
  rebuilt: boolean;
  /**
   * Whether an empty answer means *no* or *we did not finish looking*.
   *
   * The engine stops at 20,000 forms per base. Building forward from افکندن
   * reaches 20,050 at three steps, so درافکندگی — the word the coining
   * experiment called the engine's largest gap — came back as impossible when
   * every rule its chain needs exists and fires. The screen must not print
   * *this word cannot be built* when this is false.
   */
  settled: boolean;
  /** Which bases ran out of room, so the caveat names something. */
  searched_partially: string[];
  /** Every account that rebuilt the word. More than one is normal. */
  accounts: Account[];
  /** Affixes whose shape fits but whose remainder is in no dictionary. */
  affixes_tried_without_a_base: string[];
}

export function explain(
  word: string,
  signal?: AbortSignal,
): Promise<Explanation> {
  return get<Explanation>("/explain", { word }, signal).then((body) => {
    const accounts = body.accounts ?? [];
    return {
      ...body,
      analysed_as: body.analysed_as ?? [],
      // An API that does not serve this is one that never checked, so the
      // safe default is the old behaviour: treat the answer as settled.
      settled: body.settled ?? true,
      searched_partially: body.searched_partially ?? [],
      accounts,
      // Derived when the field is absent, which is what an API a version
      // behind this code serves — the field was renamed from `explained` on
      // 2026-08-17. Derived from the accounts rather than read from the old
      // name: the flag has always meant *at least one account rebuilt the
      // word*, so the data says it whether or not the field does. Without
      // this a stale container makes every word answer "no way to build this
      // was found", which is a wrong answer given confidently — the exact
      // failure the rename was meant to stop.
      rebuilt: body.rebuilt ?? accounts.length > 0,
      affixes_tried_without_a_base: body.affixes_tried_without_a_base ?? [],
    };
  });
}
