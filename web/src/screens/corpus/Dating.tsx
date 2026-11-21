/**
 * The holes in the evidence, stated on the screen rather than in a document.
 *
 * The dispersion chart on the word screen — the thing that separates a real
 * word from one poet's rhyme — rests entirely on the poet→century table, and
 * that table covers 43 poets of the 237 in this corpus. Measured: **98,627 of
 * 133,148 poems carry no date at all.**
 *
 * And 27 of the table's entries name a poet slug this corpus does not use, so
 * they date nothing while looking exactly like entries that work. That is how
 * فردوسی — the largest poet in the corpus — came to be undated. See
 * OPEN_QUESTIONS N.
 *
 * A reader who does not know this would take an empty chart for an absent word.
 */

import type { CorpusReport } from "../../api/corpus";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import styles from "./Dating.module.css";

export interface DatingProps {
  report: CorpusReport;
}

const PERCENT = new Intl.NumberFormat("fa-IR", {
  style: "percent",
  maximumFractionDigits: 1,
});

/** How many slugs to name before the list turns into a count. */
const NAMED = 8;

export function Dating({ report }: DatingProps) {
  const undatedShare = report.documents
    ? report.documents_without_century / report.documents
    : 0;
  const stale = report.centuries_without_a_poet;
  // The slug is empty for a poem whose poet has no address of its own. It is
  // a real gap and stays in the count, but there is nothing to print.
  const missing = report.poets_without_a_century.filter(Boolean);

  return (
    <>
      <p className={styles.line}>
        <strong className={styles.figure}>
          {PERCENT.format(undatedShare)}
        </strong>{" "}
        از متن‌ها تاریخ ندارند: <Num value={report.documents_without_century} />{" "}
        از <Num value={report.documents} />. نمودار پراکندگی در صفحهٔ هر واژه فقط
        متن‌های تاریخ‌دار را می‌شمارد؛ پس اگر ستونی کوتاه است یا نیست، دلیل
        نمی‌شود که واژه در آن دوره به کار نمی‌رفته است.
      </p>

      {report.documents_without_author > 0 ? (
        <p className={styles.line}>
          <Num value={report.documents_without_author} /> متن نام نویسنده‌ای
          ندارد.
        </p>
      ) : null}

      {missing.length > 0 ? (
        <p className={styles.line}>
          سدهٔ <Num value={missing.length} /> نویسنده را در جدول نداریم، پس
          هیچ‌کدام از متن‌هایشان تاریخ ندارد.
        </p>
      ) : null}

      {stale.length > 0 ? (
        <div className={styles.fault}>
          <p className={styles.line}>
            <Num value={stale.length} /> سطر از جدول سده‌ها نویسنده‌ای را نام
            می‌برد که در این پیکره با این نام نیامده. چنین سطری به هیچ متنی تاریخ
            نمی‌دهد، ولی ظاهرش درست مثل سطرهای سالم است.
          </p>
          <ul className={styles.slugs}>
            {stale.slice(0, NAMED).map((slug) => (
              <li key={slug}>
                <Latin>{slug}</Latin>
              </li>
            ))}
          </ul>
          {stale.length > NAMED ? (
            <p className={styles.line}>
              و <Num value={stale.length - NAMED} /> سطر دیگر.
            </p>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
