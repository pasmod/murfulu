/**
 * How much of the corpus the lexicon can read.
 *
 * **Two numbers, and reading one as the other is the mistake this component
 * exists to prevent.** Measured on Ganjoor against the 45,579-word lexicon:
 * 4.1% of the distinct spellings have a reading, but 45.7% of the running
 * text does. The first is how much of the vocabulary we can read; the second
 * is how much of the *text* we can read, and it is far higher because the
 * words we know are the words that occur.
 *
 * Anyone shown only the 4.1% would take it for a quality figure. It is not
 * one, so both are drawn, side by side, each with what it counts.
 */

import { Num } from "../../text/Num";
import styles from "./Coverage.module.css";

export interface Share {
  /** What this share is of, in Persian. */
  label: string;
  /** The sentence under the bar: what it counts, and what the rest is. */
  note: string;
  share: number;
  covered: number;
  total: number;
}

export interface CoverageProps {
  shares: Share[];
}

/** A percentage in Persian numerals, to one decimal place. */
const PERCENT = new Intl.NumberFormat("fa-IR", {
  style: "percent",
  maximumFractionDigits: 1,
});

export function Coverage({ shares }: CoverageProps) {
  return (
    <ul className={styles.shares}>
      {shares.map((one) => (
        <li key={one.label} className={styles.share}>
          <p className={styles.label}>{one.label}</p>
          <p className={styles.figure} data-value={String(one.share)}>
            {PERCENT.format(one.share)}
          </p>
          <div
            className={styles.track}
            role="img"
            aria-label={`${one.label}: ${PERCENT.format(one.share)}`}
          >
            <div
              className={styles.filled}
              style={{ inlineSize: `${Math.round(one.share * 100)}%` }}
            />
          </div>
          <p className={styles.counted}>
            <Num value={one.covered} /> از <Num value={one.total} />
          </p>
          <p className={styles.note}>{one.note}</p>
        </li>
      ))}
    </ul>
  );
}
