/**
 * The word bank: the whole lexicon, by the linguist's groups (`/bank`).
 *
 * Read straight from the lexicon snapshot by the API, so it needs no corpus
 * build. The groups are karbon's `bank_group` keys, shown under his names.
 */

import { get } from "./client";

/** One of the linguist's twelve groups. */
export interface BankGroup {
  key: string;
  label_fa: string;
  /** How many words (readings) the group holds — what its list shows. */
  words: number;
  /** The rules' word classes the group feeds. Empty: it feeds no rule. */
  word_classes: string[];
  /** False only for وام‌واژه: out of word formation, still in the bank. */
  in_word_formation: boolean;
}

export interface BankGroups {
  lexicon_snapshot_id: string;
  /** False on a snapshot from before the word bank (karbon < 1.3.0). */
  has_bank: boolean;
  /** How many readings the bank lists in all. */
  total: number;
  /** The stems' names in the bank: پیشین‌کاربن and کنون‌کاربن. */
  stem_labels: { past: string; present: string };
  groups: BankGroup[];
}

/** One word of the bank, one reading of one spelling. */
export interface BankWord {
  spelling_fa: string;
  latin: string;
  latin_variants: string[];
  groups: { key: string; label_fa: string }[];
  lexicon_category: string | null;
  in_word_formation: boolean;
  needs_review: boolean;
  definition_fa: string | null;
  /** True when karbon cut the definition at 200 characters. */
  definition_truncated: boolean | null;
  past_stem_fa: string | null;
  past_stem_latin: string | null;
  present_stem_fa: string | null;
  present_stem_latin: string | null;
  /** How many dictionary entries this one reading collects. */
  sense_count: number;
}

export interface BankPage {
  lexicon_snapshot_id: string;
  group: string | null;
  q: string | null;
  /** True when only the word itself was asked for, not words holding it. */
  exact?: boolean;
  total: number;
  offset: number;
  limit: number;
  words: BankWord[];
}

export function bankGroups(signal?: AbortSignal): Promise<BankGroups> {
  return get<BankGroups>("/bank/groups", {}, signal);
}

export function bankPage(
  options: {
    group?: string;
    q?: string;
    exact?: boolean;
    offset?: number;
    limit?: number;
  },
  signal?: AbortSignal,
): Promise<BankPage> {
  return get<BankPage>(
    "/bank",
    {
      group: options.group,
      q: options.q,
      exact: options.exact ? "true" : undefined,
      offset: options.offset,
      limit: options.limit,
    },
    signal,
  );
}
