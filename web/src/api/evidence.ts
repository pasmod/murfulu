/**
 * Every text a spelling is written in, a page at a time.
 *
 * The word page's six citations are one line per author. This is the rest of
 * the evidence: every text, each with every line that holds the spelling.
 * Field names mirror `/evidence` exactly.
 */

import { get } from "./client";

/** One line holding the word. */
export interface EvidenceLine {
  /** The unit's place in its text, so the reading screen opens at it. */
  unit: number | null;
  kind: "couplet" | "half" | "prose" | null;
  /**
   * The line split around the word: text, word, text, word, …, text. The odd
   * places are the word as written, harakat and all.
   */
  parts: string[];
  /**
   * The spelling the marked word was counted under, where it is not the one
   * asked for — امد in a line found for آمد. Absent otherwise.
   */
  word?: string;
}

/** One text holding the word, and every line in it that does. */
export interface EvidenceText {
  document_id: string;
  author: string | null;
  title: string | null;
  century: number | null;
  work: string | null;
  section: string[];
  lines: EvidenceLine[];
  /**
   * How the text holds the word: as counted; only in a near spelling the
   * search index folds together with it (امد for آمد); or in no line the
   * counting would credit, so with no lines at all.
   */
  held: "counted" | "near" | "none";
}

/** One author, and how many of the list's texts are theirs. Null: no author. */
export interface EvidenceAuthor {
  author: string | null;
  texts: number;
}

export interface Evidence {
  spelling: string;
  corpus_version: string | null;
  /** Texts in the whole list, every author. */
  total: number;
  /** Every author, most texts first. */
  authors: EvidenceAuthor[];
  author: string | null;
  unnamed: boolean;
  /** Texts in the list being paged: one author's, when one is chosen. */
  matching: number;
  /** Lines in the list being paged; null when it was not counted. */
  lines: number | null;
  page: number;
  size: number;
  texts: EvidenceText[];
}

export interface EvidenceRequest {
  spelling: string;
  /** One author's texts. */
  author?: string;
  /** Only the texts with no author. */
  unnamed?: boolean;
  /** From 0. */
  page?: number;
  /** Texts per page; 0 for the counts alone. */
  size?: number;
  /** Count the lines of the whole list. Costly for a long one, so asked once. */
  countLines?: boolean;
  /**
   * A preview, not a page: one text from each of the first `size` authors,
   * one voice each as the six citations are.
   */
  voices?: boolean;
}

/** Texts per page. */
export const EVIDENCE_PAGE = 20;

export function evidence(request: EvidenceRequest, signal?: AbortSignal): Promise<Evidence> {
  return get<Evidence>(
    "/evidence",
    {
      spelling: request.spelling,
      author: request.author,
      unnamed: request.unnamed ? 1 : undefined,
      page: request.page,
      size: request.size ?? EVIDENCE_PAGE,
      count_lines: request.countLines ? 1 : 0,
      voices: request.voices ? 1 : undefined,
    },
    signal,
  );
}
