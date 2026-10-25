/**
 * What corpus is being served, and what one ingest measured about it.
 *
 * `report` is null on a machine that has never run an ingest. That is a
 * legitimate state, not an error, and it never shares a shape with a report
 * full of zeros.
 *
 * `describes_the_served_version` is false when the stored report describes a
 * different corpus version from the one the aliases point at. Every count in
 * this system is true for one version only, so the screen has to be able to
 * say which.
 */

import { get } from "./client";

/** One spelling the lexicon has no entry for. */
export interface Gap {
  spelling_fa: string;
  total_count: number;
  doc_count: number;
  author_count: number;
}

export interface CorpusReport {
  corpus_version: string;
  source_id: string;
  /** The source's Persian name. Absent on an older report. */
  source_name_fa?: string;
  /** English. What the ingest log and NOTICE carry, not what the reader sees. */
  licence: string;
  /**
   * The same statement in Persian, which is what the screen shows.
   *
   * Empty on a report written before 2026-08-17 and on a source that has not
   * written its Persian yet; the screen falls back to `licence`, because a
   * sentence about copyright in the wrong language beats no sentence at all.
   */
  licence_fa?: string;
  built_at: string;
  lexicon_snapshot_id: string;

  documents: number;
  /** Words of running text. */
  tokens: number;
  /** Distinct spellings. The corpus has no vowels, so not distinct words. */
  spellings: number;
  /** One per reading, so a spelling read two ways counts twice. */
  word_types: number;

  documents_without_author: number;
  documents_without_century: number;

  spellings_linked: number;
  spellings_unlinked: number;
  tokens_linked: number;
  ambiguous_spellings: number;

  type_share: number;
  token_share: number;

  poets_without_a_century: string[];
  centuries_without_a_poet: string[];
  biggest_gaps: Gap[];
}

export interface CorpusState {
  serving: Record<string, string | null>;
  built: Record<string, string[]>;
  report: CorpusReport | null;
  describes_the_served_version: boolean;
}

export function corpus(signal?: AbortSignal): Promise<CorpusState> {
  // The gaps are filled here rather than at every use. An API one version
  // behind the app must give a screen with less on it, never a screen that
  // fell over — which is what a missing `serving` did the first time, exactly
  // as it did on the build screen (PLAN 7.4).
  return get<Partial<CorpusState>>("/corpus", {}, signal).then((body) => ({
    serving: body.serving ?? {},
    built: body.built ?? {},
    report: body.report ?? null,
    describes_the_served_version: body.describes_the_served_version ?? false,
  }));
}
