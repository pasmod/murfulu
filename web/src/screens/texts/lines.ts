/**
 * A line of a text as one string (2026-11-22).
 *
 * Sent with a saved reading, so a reading the bank lacks reaches karbon with
 * the line it was read in: the line's words joined by spaces, as the screen
 * counts them, so the word's place in the line finds it again. A long
 * paragraph of prose is cut to the words around the word by whoever shows it.
 */

import type { TextWord } from "../../api/texts";

export function lineText(words: TextWord[]): string {
  return words.map((one) => one.fa + (one.after ?? "")).join(" ");
}
