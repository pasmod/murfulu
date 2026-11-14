/**
 * Suggestions while a reader types (`/suggest/words`, `/suggest/texts`).
 *
 * Asked for on every pause in typing, so each answer is small: eight at most,
 * the ones that start with the letters first.
 */

import { get } from "./client";

/** A word of the bank: one spelling with its readings, or one reading with its spellings. */
export interface WordSuggestion {
  /** What goes into the box: in the script the reader typed in. */
  value: string;
  spellings: string[];
  latin: string[];
}

export interface WordSuggestions {
  q: string;
  /** The script the letters were typed in, and so the script of `value`. */
  script: "fa" | "latin";
  suggestions: WordSuggestion[];
}

export function suggestWords(
  q: string,
  options: { builds?: boolean; primary?: boolean; limit?: number } = {},
  signal?: AbortSignal,
): Promise<WordSuggestions> {
  return get<WordSuggestions>(
    "/suggest/words",
    {
      q,
      builds: options.builds ? "true" : undefined,
      primary: options.primary ? "true" : undefined,
      limit: options.limit,
    },
    signal,
  );
}

/** A group of texts — an author, a work, a section — or one text. */
export interface TextSuggestion {
  kind: "author" | "work" | "section" | "text";
  /** Author, work, sections and title, outermost first, as far as it goes. */
  parts: string[];
  /** What goes into the box to list the group's texts. */
  query: string;
  /** How many texts the group holds; 1 for a text. */
  texts: number;
  /** Set on a text, which is opened rather than searched for. */
  document_id: string | null;
}

export interface TextSuggestions {
  q: string;
  suggestions: TextSuggestion[];
}

export function suggestTexts(q: string, signal?: AbortSignal): Promise<TextSuggestions> {
  return get<TextSuggestions>("/suggest/texts", { q }, signal);
}
