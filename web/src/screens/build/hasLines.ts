/**
 * Whether the corpus has lines to list for a word, and what that takes.
 *
 * In a file of its own because two places ask before anything is fetched: the
 * panel that lists the lines (`CorpusLines.tsx`) and the row that opens on
 * them (`Signals.tsx`).
 */

import type { BuiltForm } from "../../api/generate";

/**
 * What the lines are fetched by: a spelling and what the corpus counted for
 * it. A built word has both, and so has a compound (`api/compound.ts`), whose
 * row lists the same lines since 2026-11-22.
 */
export interface Counted {
  form_fa: string;
  attestation: Pick<
    NonNullable<BuiltForm["attestation"]>,
    "level" | "doc_count" | "corpus_version" | "function_word"
  > | null;
}

/**
 * **Nothing is listed where nothing is counted**: a word the corpus does not
 * have keeps its sentence, and the letters of a function word count that
 * word's uses, not this one's.
 */
export function hasLines(form: Counted): boolean {
  const found = form.attestation;
  return !!found && found.level !== "none" && !found.function_word;
}
