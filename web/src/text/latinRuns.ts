/**
 * Where the Latin runs are in a Persian sentence — see {@link Mixed} in
 * `Mixed.tsx` for why they have to be set apart.
 */

const LETTER = "A-Za-z\\u00C0-\\u024F\\u1E00-\\u1EFF";
const WORD = `[-‒]?[${LETTER}][${LETTER}0-9'’]*(?:[-‒][${LETTER}0-9]+)*[-‒]?`;
const RUN = new RegExp(`${WORD}(?: +${WORD})*`, "g");

/** The sentence split into Persian text and Latin runs, in reading order. */
export function splitLatin(text: string): { latin: boolean; text: string }[] {
  const parts: { latin: boolean; text: string }[] = [];
  let at = 0;
  for (const found of text.matchAll(RUN)) {
    const start = found.index ?? 0;
    if (start > at) parts.push({ latin: false, text: text.slice(at, start) });
    parts.push({ latin: true, text: found[0] });
    at = start + found[0].length;
  }
  if (at < text.length) parts.push({ latin: false, text: text.slice(at) });
  return parts;
}
