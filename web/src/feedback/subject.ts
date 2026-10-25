/**
 * What is being judged, and how a screen says so.
 *
 * docs/FRONTEND.md is explicit that feedback is a UI-wide affordance and not
 * a screen: it has to be present on every view from the start, because
 * retrofitting it means touching every component. So the frame carries the
 * button and screens only declare *what is on screen*.
 *
 * Two ways to declare it:
 *
 * - `useSubject(...)` — the screen names its own subject, so the button in the
 *   corner is never about nothing.
 * - `raise(...)` — any element hands over its own, so a single generated word
 *   can be judged rather than the page it sits on.
 *
 * **The structured context is the reusable half of a record** (docs/REVIEW.md).
 * The route and the query are added by `whereWeAre` rather than by each
 * caller, because a screen that forgot them would leave a record nobody can
 * place afterwards.
 *
 * Separate from `context.tsx` so the provider is the only thing that file
 * exports — a module mixing a component with its hooks breaks fast refresh.
 */

import { createContext, useCallback, useContext, useEffect } from "react";

import type { TargetType } from "../api/feedback";

/** One thing that can be commented on. */
export interface Subject {
  target_type: TargetType;
  /** The word, rule or figure. Null only for the app itself. */
  target_id?: string | null;
  /** What the panel calls it, in Persian. */
  label: string;
  /** What was on screen, as data. Merged with the route and the query. */
  context?: Record<string, unknown>;
  /** Which corpus version the figures beside it came from. */
  corpus_version?: string | null;
}

/** The subject when a screen declares nothing. */
export const APP: Subject = { target_type: "app", label: "خودِ برنامه" };

export interface Handle {
  /** The subject the panel is open on, or null when it is closed. */
  open: Subject | null;
  /** Open the panel on one subject, or on whatever the screen declared. */
  raise: (subject?: Subject) => void;
  close: () => void;
  /** What the current screen says it is showing. */
  screen: Subject;
  /** Used by `useSubject`; not called from a component directly. */
  declare: (subject: Subject | null) => void;
}

export const FeedbackContext = createContext<Handle | null>(null);

export function useFeedback(): Handle {
  const found = useContext(FeedbackContext);
  if (!found) {
    throw new Error("useFeedback outside FeedbackProvider");
  }
  return found;
}

/**
 * Declare what this screen is showing.
 *
 * The subject is compared by its content rather than by identity, so a screen
 * may build it inline without re-declaring it on every render.
 */
export function useSubject(subject: Subject | null): void {
  const { declare } = useFeedback();
  const frozen = JSON.stringify(subject);
  const settle = useCallback(declare, [declare]);
  useEffect(() => {
    settle(frozen ? (JSON.parse(frozen) as Subject) : null);
  }, [frozen, settle]);
}

/** The route and the query, added to every record whatever raised it. */
export function whereWeAre(location: {
  pathname: string;
  search: string;
}): Record<string, unknown> {
  const query = new URLSearchParams(location.search);
  return {
    screen: location.pathname,
    query: query.get("q") ?? query.get("word") ?? null,
  };
}
