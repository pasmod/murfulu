/**
 * A grammar term with its explanation.
 *
 * Nobody arrives knowing what *kārnām* or *kārbon-e do* means, and
 * docs/FRONTEND.md is explicit that the interface has to explain itself
 * without a manual. So the project's term is shown, and the traditional term
 * most readers were taught sits in the tooltip beside a one-line explanation.
 *
 * **The text is passed in, never written here.** Every Persian string about
 * the grammar comes from the rule pack; a component that invented one would be
 * inventing linguistics.
 *
 * Accessibility: it is a button, so it is reachable by keyboard; the tooltip
 * appears on focus as well as hover, and Escape dismisses it — WCAG 1.4.13.
 */

import { useEffect, useId, useRef, useState } from "react";

import styles from "./Term.module.css";

export interface TermProps {
  /** The project's term, in Persian. From the data. */
  term: string;
  /** The one-line explanation, in Persian. From the data. */
  explanation: string;
  /** What traditional grammar calls it, when it has a name there. */
  traditional?: string;
}

export function Term({ term, explanation, traditional }: TermProps) {
  const [open, setOpen] = useState(false);
  const tooltipId = useId();
  const holder = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!open) return;
    const dismiss = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", dismiss);
    return () => document.removeEventListener("keydown", dismiss);
  }, [open]);

  return (
    <span
      className={styles.holder}
      ref={holder}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className={styles.term}
        aria-describedby={open ? tooltipId : undefined}
        aria-expanded={open}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        // **Opening, not toggling.** One press is three events — enter, focus,
        // click — and toggling on the last undid what the first two had just
        // done. On a phone, where there is no hover to fall back on, tapping a
        // term therefore explained nothing: the tooltip opened and shut inside
        // one tap. Found on 2026-08-17 while giving Info.tsx the same
        // behaviour, and this component has had it since it was written.
        // Leaving it: the reader moves away, moves focus, or presses Escape.
        onClick={() => setOpen(true)}
      >
        {term}
      </button>
      {open ? (
        <span role="tooltip" id={tooltipId} className={styles.tooltip}>
          <span className={styles.explanation}>{explanation}</span>
          {traditional ? (
            <span className={styles.traditional}>{traditional}</span>
          ) : null}
        </span>
      ) : null}
    </span>
  );
}
