/**
 * When a word was used, century by century.
 *
 * This is the chart docs/FRONTEND.md calls the thing that separates a real
 * word from one poet's rhyme. It is drawn as bars in plain SVG — no chart
 * library, because the data is one small object already on the record and a
 * library would be more code than the chart.
 *
 * **What is not dated is stated, not dropped.** Only 26% of this corpus can be
 * dated at all, and 27 entries of the century table match no poet in it, so
 * most occurrences of most words sit outside every bar. A chart that quietly
 * showed two occurrences out of twenty-two would be a lie about the evidence.
 * See OPEN_QUESTIONS N.
 */

import { Num } from "../../text/Num";
import { persianCentury } from "../../text/numbers";
import styles from "./Dispersion.module.css";

export interface DispersionProps {
  /** Century (as written by Elasticsearch, a string key) → occurrences. */
  counts: Record<string, number>;
  /** Every occurrence, dated or not. */
  total: number;
}

export function Dispersion({ counts, total }: DispersionProps) {
  const centuries = Object.entries(counts)
    .map(([century, count]) => ({ century: Number(century), count }))
    .sort((a, b) => a.century - b.century);

  const dated = centuries.reduce((sum, one) => sum + one.count, 0);
  const undated = Math.max(0, total - dated);

  if (centuries.length === 0) {
    return (
      <p className={styles.none}>
        هیچ‌یک از <Num value={total} /> کاربرد این واژه تاریخ‌دار نیست، پس
        نموداری نمی‌توان کشید.
      </p>
    );
  }

  const most = Math.max(...centuries.map((one) => one.count));
  const first = centuries[0]!.century;
  const last = centuries[centuries.length - 1]!.century;
  const span = Array.from({ length: last - first + 1 }, (_, step) => {
    const century = first + step;
    return { century, count: counts[String(century)] ?? 0 };
  });

  return (
    <figure className={styles.chart}>
      <figcaption className={styles.caption}>
        کاربرد در گذر سده‌ها
      </figcaption>

      <ul className={styles.bars}>
        {span.map((one) => (
          <li key={one.century} className={styles.column}>
            <span
              className={one.count > 0 ? styles.bar : styles.empty}
              style={{ blockSize: `${Math.round((one.count / most) * 100)}%` }}
              // The chart is a picture of a table; the table is the fact.
              aria-hidden="true"
            />
            <span className={styles.tick}>
              <Num value={one.century} />
            </span>
          </li>
        ))}
      </ul>

      <table className={styles.reading}>
        <caption className="visually-hidden">کاربرد در هر سده</caption>
        <tbody>
          {centuries.map((one) => (
            <tr key={one.century}>
              <th scope="row">{persianCentury(one.century)}</th>
              <td>
                <Num value={one.count} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {undated > 0 ? (
        <p className={styles.undated}>
          <Num value={undated} /> کاربرد دیگر تاریخ ندارد و در نمودار نیست.
        </p>
      ) : null}
    </figure>
  );
}
