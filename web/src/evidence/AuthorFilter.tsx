/**
 * One author's texts out of all of them: a choice among every author the list
 * holds, most texts first, each with how many are theirs.
 *
 * A select, not chips: a common word is in the texts of two hundred authors,
 * and a row of two hundred chips is not a filter anyone can use on a phone.
 */

import type { Evidence } from "../api/evidence";
import { persianNumber } from "../text/numbers";
import styles from "./Evidence.module.css";

/** The value for "every author", and for "the texts with no author". */
export const EVERY = "";
export const UNNAMED = "\u0000";

export function AuthorFilter({
  evidence,
  chosen,
  onChoose,
}: {
  evidence: Evidence;
  chosen: string;
  onChoose: (value: string) => void;
}) {
  return (
    <label className={styles.filter}>
      <span className={styles.filterLabel}>نویسنده</span>
      <select
        className={styles.select}
        value={chosen}
        onChange={(event) => onChoose(event.target.value)}
      >
        <option value={EVERY}>همهٔ نویسندگان ({persianNumber(evidence.total)} متن)</option>
        {evidence.authors.map((one) => (
          <option key={one.author ?? UNNAMED} value={one.author ?? UNNAMED}>
            {one.author ?? "بی‌نام"} ({persianNumber(one.texts)})
          </option>
        ))}
        {/* An author in the address the list does not have — an old link, a
            name typed by hand — is shown as chosen, with nothing, rather than
            the box claiming every author while the list shows none. */}
        {chosen !== EVERY && !evidence.authors.some((one) => (one.author ?? UNNAMED) === chosen) ? (
          <option value={chosen}>
            {chosen === UNNAMED ? "بی‌نام" : chosen} ({persianNumber(0)})
          </option>
        ) : null}
      </select>
    </label>
  );
}
