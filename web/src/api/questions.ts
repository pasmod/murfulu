/**
 * The questions waiting on the linguist, and settling one.
 *
 * There is no author field, as with feedback: the API decides the author. A
 * ruling attributed to the wrong person would be worse than none, because this
 * is the record the documents are generated from.
 *
 * **Nothing here needs a credential as of 2026-08-17.** Reading used to need a
 * token and ruling used to need the expert role; there is one account and no
 * roles now, and the site password in front of the whole app is the whole of
 * the authentication. `answering_as` still comes back, and is now always the
 * caller — the screen keeps saying who is about to sign a ruling rather than
 * leaving it to be assumed.
 */

import { get, post } from "./client";

/** What a question is waiting on. */
export type State = "open" | "blocked" | "answered" | "withdrawn";

export interface Ruling {
  /**
   * His words — or, when he chose an option and wrote nothing, that option's
   * Persian. Never empty.
   */
  ruling_fa: string;
  /** The option chosen, if any, and its Persian as it read when chosen. */
  choice_id?: string | null;
  choice_fa?: string | null;
  /** The same ruling in Behnevis, if he gave one. His, like the Persian. */
  ruling_latin: string | null;
  ruling_en: string | null;
  affects: unknown;
  supersedes_earlier: boolean;
  ruled_at: string | null;
}

/**
 * One answer a question offers. Added 2026-10-18, when the screen became a
 * multiple-choice form; a free-text box is always offered beside the options.
 */
export interface Choice {
  id: string;
  /** A full Persian sentence saying what would follow. */
  text_fa: string;
  /** Marked «پیشنهاد ما» — only where the documents state a proposed default. */
  suggested: boolean;
  /** False for «نمی‌دانم»: recorded, and the question keeps waiting. */
  settles: boolean;
}

/** One downloadable file belonging to a question. */
export interface Attachment {
  filename: string;
  /** What it is, in Persian — it is read beside a Persian question. */
  description_fa: string;
  byte_size: number;
  href: string;
}

export interface Question {
  /** The handle the documents and the git history use — L13, S11. */
  reference: string;
  /** What he reads. */
  question_fa: string;
  /** The same question in Behnevis — the form the project actually holds. */
  question_latin: string | null;
  /** The English statement, for the repository. A gloss, never the original. */
  question_en: string | null;
  /** The evidence: what was measured, the list, the examples. */
  context: Record<string, unknown> | null;
  /** The options, in order; empty or absent for a free-text question. */
  choices?: Choice[];
  /** Files attached to the question, so it can be answered without leaving it. */
  files: Attachment[];
  state: State;
  blocks_work: boolean;
  origin: "document" | "app";
  asked_at: string | null;
  /** The ruling that stands, or nothing. */
  ruling: Ruling | null;
  /** How many there have been. More than one means the answer changed. */
  rulings: number;
}

export interface QuestionDetail extends Question {
  /** Every ruling ever given, oldest first. */
  history: Ruling[];
}

export interface Questions {
  count: number;
  /** The caller's name when the caller may answer, otherwise nothing. */
  answering_as: string | null;
  questions: Question[];
}

export interface RulingIn {
  /** May be empty when an option is chosen; the API stores its Persian. */
  ruling_fa: string;
  choice_id?: string | null;
  ruling_latin?: string | null;
  ruling_en?: string | null;
  affects?: unknown;
  supersedes_earlier?: boolean;
}

/** Everything waiting, blocking questions first. */
export async function questions(options?: {
  state?: State;
  blocking?: boolean;
}): Promise<Questions> {
  return get<Questions>(
    "/questions",
    {
      state: options?.state,
      blocking: options?.blocking ? "true" : undefined,
    },
    undefined,
  );
}

/** One question, with every ruling ever given on it. */
export async function question(reference: string): Promise<QuestionDetail> {
  return get<QuestionDetail>(
    `/questions/${encodeURIComponent(reference)}`,
    {},
  );
}

/** Settle a question. Open to anyone behind the password wall. */
export async function rule(
  reference: string,
  given: RulingIn,
): Promise<{ reference: string; state: State; ruling: Ruling }> {
  return post(
    `/questions/${encodeURIComponent(reference)}/ruling`,
    given,
  );
}
