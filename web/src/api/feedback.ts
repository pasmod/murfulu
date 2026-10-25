/**
 * Leaving feedback, and asking what this account may do.
 *
 * There is no author field, deliberately: the API decides the author and
 * refuses to read one from the body. A record naming the wrong author is worse
 * than no record, because this set is the evaluation set the scoring weights
 * will be fitted against.
 *
 * **And nothing here carries a credential.** It used to send a bearer token;
 * as of 2026-08-17 there is one account and no roles, and the site password in
 * front of the whole app is the whole of the authentication.
 */

import { get, post } from "./client";

/** What the form adapts to. Chosen before anything else is written. */
export type Category = "linguistic" | "data" | "bug";

/** What is being judged. The last three are karbon's data and the app. */
export type TargetType =
  | "derivation"
  | "rule"
  | "meaning"
  | "statistic"
  | "lexicon_entry"
  | "stem_derivation"
  | "app";

/** A graded judgement. Free text alone cannot be aggregated. */
export type Verdict = "good" | "possible" | "wrong" | "unsure";

export interface Account {
  username: string;
  /**
   * Whether this caller may grade a generated word.
   *
   * True for everyone since 2026-08-17 — there is one account and no roles,
   * and the site password is the whole of the authentication. It is still
   * asked rather than assumed: the sentence *who may grade a word* belongs in
   * one place, and this project has already reversed a decision about roles
   * once.
   */
  may_leave_a_verdict: boolean;
}

export interface FeedbackIn {
  category: Category;
  target_type: TargetType;
  target_id?: string | null;
  verdict?: Verdict | null;
  note?: string | null;
  context: Record<string, unknown>;
  corpus_version?: string | null;
}

export interface FeedbackOut extends FeedbackIn {
  id: number;
  author_id: number;
  owner: "murfulu" | "karbon";
  created_at: string | null;
}

export function me(signal?: AbortSignal): Promise<Account> {
  return get<Account>("/me", {}, signal);
}

export function leave(
  given: FeedbackIn,
  signal?: AbortSignal,
): Promise<FeedbackOut> {
  return post<FeedbackOut>("/feedback", given, undefined, signal);
}
