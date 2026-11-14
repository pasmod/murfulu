/**
 * The automatic Behnevis's levels, as the reading screen names and shows them
 * (direction A, 2026-11-14). The edges between them come with the text from
 * the API (`behnevis.sure`, `behnevis.mid`), so they live in one place.
 */

import type { Level } from "../../api/texts";

/** What each level is called, for the label and the legend. */
export const LEVEL_FA: Record<Level, string> = {
  sure: "مطمئن",
  mid: "کمابیش",
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
}
