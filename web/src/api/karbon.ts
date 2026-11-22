/**
 * The readings the bank lacks, gathered for karbon, and the linguist's word
 * on each (the project lead, 2026-11-22).
 *
 * A reading readers typed or decided that neither the bank nor the
 * function-word list holds, and the function-word list's own readings the
 * bank lacks, are listed by `GET /texts/karbon`: one row per spelling and
 * reading, with where it was proposed. The linguist confirms a row through
 * the feedback store, like every judgement of karbon's data — append-only,
 * and taken back by one more record. Only confirmed readings are written
 * into karbon's issue (`tools/export_reading_proposals.py --confirmed`).
 *
 * The app has one account, so a confirmation is a statement, not an
 * identity: whoever presses the button says the linguist confirmed.
 */

import { get } from "./client";
import { leave, type FeedbackOut } from "./feedback";
import type { Scope, UnsurePlace } from "./texts";

/** The bank lacks the spelling altogether, or only this reading of it. */
export type GapKind = "missing" | "reading";

/** Every reading, those not confirmed yet, or those confirmed. */
export type KarbonState = "all" | "open" | "confirmed";

/** Where a reading was proposed: a word in a line of a text. */
export interface KarbonPlace {
  document_id: string;
  unit: number | null;
  line: number | null;
  /** The word's place in the line, as the reading screen counts it. */
  word: number | null;
  heading: string | null;
  written: string | null;
  before: string | null;
  after: string | null;
  /** The line's own words, where the save carried them (since 2026-11-22). */
  text: string | null;
}

export interface KarbonRow {
  /** The spelling as the model keys it. */
  spelling: string;
  /** As the screen that proposed it wrote it. */
  spelling_fa: string;
  /** With this reading's short vowels, for display only. */
  spelling_fa_marked?: string | null;
  latin: string;
  kind: GapKind;
  /** What the bank holds for the spelling; empty when it holds none. */
  bank: string[];
  /** A reader's proposal, or the function-word list's own reading. */
  origin: "reader" | "function";
  /** How many saves proposed it. */
  times: number;
  /** What the model had read where it was first proposed. */
  model: string | null;
  /** The decisions in force for it: everywhere, or after or before one word. */
  decided: { scope: Scope; word: string | null }[];
  places: KarbonPlace[];
  /** Lines from the measured list, where the row has none of its own. */
  examples: UnsurePlace[];
  /** The linguist's confirmation in force, if any. */
  confirmed: { id: number; created_at: string | null } | null;
}

export interface KarbonPage {
  /** Every row, whatever the filter. */
  total: number;
  confirmed: number;
  missing: number;
  state: KarbonState;
  /** The rows the filter keeps. */
  matching: number;
  offset: number;
  size: number;
  rows: KarbonRow[];
}

/** One page of the readings the bank lacks, the most proposed first. */
export function forKarbon(
  options: { state?: KarbonState; offset?: number; size?: number } = {},
  signal?: AbortSignal,
): Promise<KarbonPage> {
  return get<KarbonPage>(
    "/texts/karbon",
    { state: options.state, offset: options.offset, size: options.size },
    signal,
  );
}

/** Record that the linguist confirmed a reading for karbon. Append-only. */
export function confirmReading(row: KarbonRow): Promise<FeedbackOut> {
  return leave({
    category: "linguistic",
    target_type: "lexicon_entry",
    target_id: `${row.spelling_fa}:${row.latin}`,
    verdict: "good",
    note: null,
    context: {
      screen: "texts",
      kind: "reading_confirmed",
      spelling_fa: row.spelling_fa,
      latin: row.latin,
      withdrawn: false,
      // What the row said when it was confirmed.
      gap: row.kind,
      bank: row.bank,
      origin: row.origin,
      times: row.times,
    },
  });
}

/** Take a confirmation back: the reading waits again. Append-only too. */
export function withdrawConfirmation(row: KarbonRow, id: number): Promise<FeedbackOut> {
  return leave({
    category: "linguistic",
    target_type: "lexicon_entry",
    target_id: `${row.spelling_fa}:${row.latin}`,
    verdict: "unsure",
    note: null,
    context: {
      screen: "texts",
      kind: "reading_confirmed",
      spelling_fa: row.spelling_fa,
      latin: row.latin,
      withdrawn: true,
      replaces: id,
    },
  });
}
