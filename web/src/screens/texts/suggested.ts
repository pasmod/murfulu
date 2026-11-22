/**
 * The automatic suggestion beside a listed unsure spelling (2026-11-22): how
 * it is matched to the readings a panel offers, and how a person takes it up.
 *
 * A suggestion is only shown. Taking it up fills the panel's own controls —
 * it picks the offered reading that is the suggestion, or puts the reading
 * in the field where a person types one — and the person still chooses how
 * far it reaches and saves it. Nothing is decided by it.
 */

import type { Suggestion } from "../../api/texts";

/**
 * A reading as a suggestion is compared, as the API compares it
 * (`murfulu.behnevis.suggest.folded`): no ezafe, case or accents, letters
 * only, and no mark for ع, which never tells two readings of one spelling
 * apart.
 */
export function folded(reading: string): string {
  return (
    reading
      .trim()
      .normalize("NFC")
      .toLowerCase()
      .replaceAll("é", "e")
      .replaceAll("í", "i")
      // The ezafe after case and accents are folded: *Del-E*, *del-é* are *del*.
      .replace(/-(?:y?e)$/u, "")
      .replace(/[^\p{L}]/gu, "")
      .replaceAll("ˈ", "")
  );
}

/** The offered readings that are the suggestion, in their order. */
export function suggestedAmong(suggestion: Suggestion, offered: readonly string[]): string[] {
  const mine = folded(suggestion.latin);
  return [...new Set(offered)].filter(
    (one) => suggestion.matches.includes(one) || (mine !== "" && folded(one) === mine),
  );
}

/** How a person takes the suggestion up in a panel: which reading, picked or typed. */
export interface Use {
  latin: string;
  how: "pick" | "type";
}

/**
 * Pick the one offered reading that is the suggestion; where none is
 * offered, type it — as the bank writes it, if the bank holds it (*Bud* for
 * *bud*, so the model learns it), else as suggested. Where several are (*Xod*,
 * *xod*: the suggestion writes no capitals), nothing: the person picks.
 */
export function takeUpOf(suggestion: Suggestion, offered: readonly string[]): Use | null {
  const among = suggestedAmong(suggestion, offered);
  if (among.length === 1) return { latin: among[0]!, how: "pick" };
  if (among.length > 1) return null;
  if (suggestion.matches.length === 1) return { latin: suggestion.matches[0]!, how: "type" };
  if (suggestion.matches.length > 1) return null;
  return { latin: suggestion.latin, how: "type" };
}

/** «۸۸» of a hundred, for «از هر ۱۰۰ پیشنهاد … ۸۸ تا درست بود». */
export function outOf100(share: number): number {
  return Math.round(share * 100);
}

/** The word and its two neighbours as read, from «x [word] y»; null if it does not say. */
export function contextOf(
  context: string | null,
): { before: string; word: string; after: string } | null {
  if (typeof context !== "string") return null;
  const found = context.match(/^(.*?)\[(.+?)\](.*)$/u);
  if (!found) return null;
  return { before: found[1]!.trim(), word: found[2]!.trim(), after: found[3]!.trim() };
}

/** Whether a place is the line the suggestion was read in. */
export function readHere(
  suggestion: Suggestion,
  place: { document_id?: string | null; unit?: number | null; line?: number | null; word?: number | null },
): boolean {
  const at = suggestion.place;
  return (
    at !== null &&
    at.document_id === place.document_id &&
    at.unit === place.unit &&
    at.line === place.line &&
    at.word === place.word
  );
}
