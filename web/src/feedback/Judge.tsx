/**
 * The per-element affordance: judge *this* word, *this* rule, *this* figure.
 *
 * docs/REVIEW.md asks for feedback on any element, not on the page it happens
 * to be on. Without this, every record would name the screen and a reader
 * afterwards would have to guess which of five hundred generated words was
 * meant.
 *
 * It looks quiet on purpose. The reader is here to read; the button earns its
 * 44 px and no more attention than that.
 */

import { useFeedback, type Subject } from "./subject";
import styles from "./Judge.module.css";

export interface JudgeProps {
  subject: Subject;
  /** What the button says. Defaults to the one-word form. */
  label?: string;
}

export function Judge({ subject, label = "داوری" }: JudgeProps) {
  const { raise } = useFeedback();
  return (
    <button
      type="button"
      className={styles.judge}
      aria-haspopup="dialog"
      aria-label={`${label} دربارهٔ ${subject.label}`}
      onClick={() => raise(subject)}
    >
      {label}
    </button>
  );
}
