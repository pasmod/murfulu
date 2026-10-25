/**
 * Everything the search language can do, on the screen that uses it.
 *
 * The four examples under the box are the syntax rather than a description of
 * it, and that is the right teaching device — but four of fourteen leaves ten
 * things a reader can only find by reading `docs/SEARCH.md`, which is not
 * shipped and is in English. This is the other ten, said in Persian, and every
 * row is a query that runs when it is clicked.
 *
 * A table rather than prose: a reader looking for *how do I ask for a century*
 * is scanning, not reading.
 */

import { REFERENCE } from "./syntax";
import styles from "./Reference.module.css";

export interface ReferenceProps {
  onPick: (query: string) => void;
}

/**
 * **Opened from an ⓘ, not from a grey bar.**
 *
 * It used to be a full-width `details` whose summary read «راهنمای نحو», and
 * it looked like an action the reader was being offered. The project lead:
 * *the information should not be a button — it should be an ⓘ you can click.*
 * So the mark lives beside the field's label and this is only the panel; the
 * box owns whether it is open.
 */
export function Reference({ onPick }: ReferenceProps) {
  return (
    <div className={styles.reference}>
      <p className={styles.about}>
        هر سطر یک جست‌وجوی درست است. روی آن بزنید تا اجرا شود. چند تا را
        می‌توانید کنار هم بگذارید؛ با فاصله از هم جدا می‌شوند.
      </p>

      <ul className={styles.rows}>
        {REFERENCE.map((one) => (
          <li key={one.query}>
            <button
              type="button"
              className={styles.row}
              onClick={() => onPick(one.query)}
            >
              {/* Syntax is shown as it must be typed: left to right, isolated.
                  See the same note in QueryBox. */}
              <span className={styles.query} dir="ltr">
                {one.query}
              </span>
              <span className={styles.hint}>{one.hint}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
