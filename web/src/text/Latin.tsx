/**
 * A Latin form inside Persian text.
 *
 * This is the component the whole interface leans on. Persian runs
 * right-to-left, a Behnevis form runs left-to-right, and the two sit in the
 * same sentence and the same table cell. Without an explicit direction *and*
 * bidi isolation, the brackets, hyphens and digits around a Latin form jump to
 * the wrong side — the most common way a Persian interface breaks.
 *
 * Two guarantees it makes:
 *
 * - **Never lowercased.** Capitalisation carries grammar in Behnevis:
 *   *Porsidan* the noun and *porsidan* the verb differ by nothing else.
 * - **Isolated, not merely directed.** `dir` alone still lets neighbouring
 *   punctuation reorder; `unicode-bidi: isolate` is what stops it.
 */

import styles from "./Latin.module.css";

export interface LatinProps {
  children: string;
  /** An affix is written with its dash — *-ār*, *nā-* — and reads as one unit. */
  affix?: boolean;
  className?: string;
}

export function Latin({ children, affix = false, className }: LatinProps) {
  const classes = [styles.latin, affix ? styles.affix : "", className ?? ""]
    .filter(Boolean)
    .join(" ");
  return (
    <span dir="ltr" lang="fa-Latn" className={classes} data-latin="">
      {children}
    </span>
  );
}
