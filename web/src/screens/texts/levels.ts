/**
 * The automatic Behnevis's levels, as the reading screen names and shows them
 * (direction A, 2026-11-14). The edges between them come with the text from
 * the API (`behnevis.sure`, `behnevis.mid`), so they live in one place.
 */

import type { AutoReading, Level } from "../../api/texts";

/** What each level is called, for the label and the legend. */
export const LEVEL_FA: Record<Level, string> = {
  sure: "مطمئن",
  mid: "کمابیش مطمئن",
  unsure: "نامطمئن",
};

/** A share as Persian digits with «٪». */
export function percent(share: number): string {
  return `${Math.round(share * 100).toLocaleString("fa-IR")}٪`;
}

/** A reading saved for one word in one line, from this visit or before. */
export interface Saved {
  latin: string;
  /** Held by the bank or the function-word list: the model learns it. */
  inBank: boolean;
  /** The store's id for it: the larger, the newer. */
  id: number;
  /** The word as written with this reading's short vowels, when the API sent them. */
  marked?: string;
}

/**
 * The word with the short vowels of the one reading shown under it, or
 * nothing (2026-11-21): the saved reading's where one is saved, else the
 * model's. A reading saved in this visit has no marks from the API until the
 * text is read again; it is shown plain rather than with another reading's
 * vowels.
 */
export function markedFor(
  auto: AutoReading,
  mine: Saved | undefined,
): string | undefined {
  if (!mine) return auto.fa_marked;
  if (mine.marked) return mine.marked;
  return mine.latin === auto.latin ? auto.fa_marked : undefined;
}
