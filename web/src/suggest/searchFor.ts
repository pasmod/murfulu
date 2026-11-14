/**
 * What the reading screen searches for when a text is picked from its
 * suggestions: the text's heading, as long as a search may be.
 */

import type { TextSuggestion } from "../api/suggest";

/** The most a search may say: the box's and the API's limit. */
export const MOST = 120;

/**
 * The search a suggestion stands for. A text's heading can be longer than a
 * search may be — a section title of the Valadnameh is ninety words — and
 * then the text is found through the group it is in: its last parts are left
 * off, a whole part at a time, and if the rest is still too long, a whole
 * word at a time. Never half a word: a search needs every word whole, and a
 * cut one would leave out the very text that was picked.
 */
export function searchFor(found: TextSuggestion): string {
  for (let keep = found.parts.length; keep > 0; keep -= 1) {
    const asked = found.parts.slice(0, keep).join(" ");
    if (asked.length <= MOST) return asked;
  }
  const words = (found.parts[0] ?? "").split(/\s+/);
  let asked = "";
  for (const word of words) {
    const longer = asked ? `${asked} ${word}` : word;
    if (longer.length > MOST) break;
    asked = longer;
  }
  return asked;
}
