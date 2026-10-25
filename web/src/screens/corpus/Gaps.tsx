/**
 * The unmatched pile: corpus spellings the lexicon has no entry for.
 *
 * docs/FRONTEND.md calls this a deliverable in its own right — words in
 * classical Persian that the dictionary does not cover — so it is shown, not
 * summarised into a percentage.
 *
 * **It is not a list of rare words, and saying so is the point.** The biggest
 * entries are و (1.1 million occurrences), ز, بر, آن and او: grammar words and
 * inflected verb forms that a dictionary of headwords was never going to list.
 * A reader who took the 4.1% type coverage for a quality figure would be
 * corrected by two seconds of looking at this table.
 */

import { Num } from "../../text/Num";
import { LEXICON } from "../../text/lexicon";
import type { Gap } from "../../api/corpus";
import styles from "./Gaps.module.css";

export interface GapsProps {
  gaps: Gap[];
  /** How many there are in all. The table shows the head of the list. */
  total: number;
}

export function Gaps({ gaps, total }: GapsProps) {
  if (gaps.length === 0) {
    return null;
  }
  return (
    <>
      <p className={styles.note}>
        <Num value={total} /> املا در پیکره هست که در {LEXICON} نیامده است.
        پرکاربردترین‌هایشان واژه‌های دستوری‌اند — «و»، «ز»، «بر» — و{" "}
        {/* Not karbon's dictionary but any dictionary of headwords, so the
            ordinary word is the right one here. */}
        فرهنگی که بر پایهٔ سرواژه‌ها ساخته شده، هیچ‌گاه آنها را در خود ندارد. پس
        این فهرست، فهرست خطاها نیست؛ خودش یک دستاورد است.
      </p>
      {/* A box that scrolls has to be reachable by keyboard, or the rows past
          the fold exist for a mouse only. `group` plus a name so a screen
          reader announces what is being scrolled. WCAG 2.1.1, found by the
          audit. */}
      <div
        className={styles.scroller}
        tabIndex={0}
        role="group"
        aria-label="فهرست املاهای بی‌مدخل"
      >
        <table className={styles.table}>
          <caption className={styles.caption}>
            پرکاربردترین املاهای بی‌مدخل، از پربسامدترین
          </caption>
          <thead>
            <tr>
              <th scope="col">املا</th>
              <th scope="col">بسامد</th>
              <th scope="col">شمار سروده</th>
              <th scope="col">شمار سراینده</th>
            </tr>
          </thead>
          <tbody>
            {gaps.map((gap) => (
              <tr key={gap.spelling_fa}>
                <th scope="row" className={styles.spelling}>
                  {gap.spelling_fa}
                </th>
                <td>
                  <Num value={gap.total_count} />
                </td>
                <td>
                  <Num value={gap.doc_count} />
                </td>
                <td>
                  <Num value={gap.author_count} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
