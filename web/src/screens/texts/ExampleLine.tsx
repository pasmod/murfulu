/**
 * One line where the model was unsure, the spelling marked in it, for the
 * list of unsure spellings. Split out of `Unsure.tsx` unchanged.
 */

import styles from "./Unsure.module.css";

/** Harakat and half-spaces, which the list's spelling does not carry. */
const MARKS = /[\u064B-\u065F\u0670\u200c]/g;

/** A token as the list keys it: no harakat, no half-space, no punctuation after it. */
function bare(token: string | undefined): string | undefined {
  return token?.replace(MARKS, "").replace(/[^\p{L}]+$/u, "");
}

/** How many words around the spelling a long line keeps. */
const AROUND = 10;

/**
 * One line where the model was unsure, the spelling marked in it. A long
 * paragraph of prose is cut to the words around it. The line is the words
 * as the screen counts them, joined by spaces, so the word's place finds it;
 * where it does not (a token with a space of its own), the line is shown
 * whole and unmarked rather than marking the wrong word.
 */
export function ExampleLine({ text, at: place, spelling }: { text: string; at: number; spelling: string }) {
  const pieces = text.split(" ");
  // The word itself, not a longer word holding its letters (دل in دلداده).
  // A token with spaces of its own (a Latin name) moves the words after it
  // on, so a few places further are tried; otherwise nothing is marked.
  const at = [0, 1, 2, 3].map((k) => place + k).find((i) => bare(pieces[i]) === spelling);
  const found = at === undefined ? undefined : pieces[at];
  if (at === undefined || found === undefined) {
    return <p className={styles.lineText}>{text}</p>;
  }
  const from = pieces.length > 2 * AROUND + 4 ? Math.max(0, at - AROUND) : 0;
  const to = pieces.length > 2 * AROUND + 4 ? Math.min(pieces.length, at + AROUND + 1) : pieces.length;
  return (
    <p className={styles.lineText}>
      {from > 0 ? "… " : null}
      {pieces.slice(from, at).join(" ")}
      {at > from ? " " : null}
      <mark className={styles.hit}>{found}</mark>
      {to > at + 1 ? " " : null}
      {pieces.slice(at + 1, to).join(" ")}
      {to < pieces.length ? " …" : null}
    </p>
  );
}
