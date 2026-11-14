/**
 * Asking `/evidence` for one list: its counts, and one page of it.
 *
 * Shared by the word page's «همهٔ شواهد» and the build screen's corpus panel,
 * which keep their choice in different places — the address, and the row's
 * own state — and ask the same two questions.
 *
 * **Two requests, each answered for what it asked.** The counts (with the
 * lines counted once, for a short list) change with the author; the page
 * with the page too. Each answer is kept with the request it answers, so a
 * late answer is never shown for another request, and each failure is its
 * own, so one never hides the other.
 */

import { useEffect, useState } from "react";

import { evidence as fetchEvidence, type Evidence } from "../api/evidence";
import { EVERY, UNNAMED } from "./AuthorFilter";

/** Which list is being paged, and where in it. */
export interface Choice {
  /** One author's texts; absent for every author's. */
  author?: string;
  /** Only the texts with no author. */
  unnamed: boolean;
  /** From 1. */
  page: number;
}

export interface Found {
  /** The whole list's figures: every author's total and the authors. */
  whole: Evidence | null;
  /** The figures of the list being paged, once they are its own. */
  current: Evidence | null;
  /** The page asked for, once it is the one asked for. */
  shown: Evidence | null;
  summaryFailed: boolean;
  pageFailed: boolean;
}

interface Answer {
  key: string;
  data: Evidence;
}

/** The value of the author select for a choice. */
export function chosenOf(choice: Choice): string {
  return choice.unnamed ? UNNAMED : (choice.author ?? EVERY);
}

export function useEvidence(
  spelling: string,
  choice: Choice,
  { open, size }: { open: boolean; size: number },
): Found {
  const { author, unnamed, page } = choice;
  const listKey = [spelling, chosenOf(choice)].join("\u0001");
  const pageKey = `${listKey}\u0001${page}\u0001${size}`;
  const [summary, setSummary] = useState<Answer | null>(null);
  const [found, setFound] = useState<Answer | null>(null);
  const [summaryFailed, setSummaryFailed] = useState(false);
  const [pageFailed, setPageFailed] = useState(false);

  useEffect(() => {
    const stop = new AbortController();
    setSummaryFailed(false);
    fetchEvidence({ spelling, author, unnamed, size: 0, countLines: true }, stop.signal)
      .then((data) => setSummary({ key: listKey, data }))
      .catch(() => {
        // An abandoned request — the reader moved on — is no failure, however
        // it ended: an abort can surface as an unreadable error body.
        if (!stop.signal.aborted) setSummaryFailed(true);
      });
    return () => stop.abort();
  }, [spelling, author, unnamed, listKey]);

  useEffect(() => {
    if (!open) return;
    const stop = new AbortController();
    setPageFailed(false);
    fetchEvidence({ spelling, author, unnamed, page: page - 1, size }, stop.signal)
      .then((data) => setFound({ key: pageKey, data }))
      .catch(() => {
        if (!stop.signal.aborted) setPageFailed(true);
      });
    return () => stop.abort();
  }, [open, spelling, author, unnamed, page, size, pageKey]);

  return {
    whole: summary?.data.spelling === spelling ? summary.data : null,
    current: summary?.key === listKey ? summary.data : null,
    shown: found?.key === pageKey ? found.data : null,
    summaryFailed,
    pageFailed,
  };
}
