/**
 * The hits, in the two groups that make a suffix search worth running.
 *
 * The first group is words a rule actually formed with the affix; the second
 * is words that merely end in those letters. `*nā` puts *Tonoknā* in the first
 * and *Fanā* — an Arabic loan — in the second, and the whole point of the
 * search is that they are not the same answer.
 *
 * **An empty first group is stated, not hidden.** Filling it needs the
 * derivation pass to have written back which rule formed which corpus word
 * (PLAN 6.4), and until that has been run for this corpus version the honest
 * answer is "we have not worked that out yet" — which is not the same as
 * "nothing was formed this way".
 */

import type { SearchResult } from "../../api/search";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import styles from "./Results.module.css";
import { WordRow } from "./WordRow";

export interface ResultsProps {
  result: SearchResult;
  /** The affix the query asked about, when it asked about one. */
  affix?: string;
}

export function Results({ result, affix }: ResultsProps) {
  const formed = result.formed_with_affix;
  const merely = result.string_match_only;

  if (result.total === 0) {
    return (
      <div className={styles.none} role="status">
        <p className={styles.noneTitle}>هیچ واژه‌ای با این الگو یافت نشد.</p>
        <p className={styles.noneAdvice}>
          الگوی دیگری بیازمایید، یا الگو را کوتاه‌تر کنید.
        </p>
      </div>
    );
  }

  return (
    <div className={styles.results}>
      {affix ? (
        <section aria-labelledby="formed">
          <h2 className={styles.groupTitle} id="formed">
            ساخته‌شده با <Latin affix>{affix}</Latin>
            <span className={styles.groupCount}>
              <Num value={formed.length} />
            </span>
          </h2>
          {formed.length > 0 ? (
            <ul className={styles.list}>
              {formed.map((word) => (
                <WordRow key={word.id} word={word} />
              ))}
            </ul>
          ) : (
            <p className={styles.unknown}>
              هنوز روشن نیست کدام‌یک از این واژه‌ها با این وند ساخته شده‌اند. این
              با «هیچ‌کدام» یکی نیست.
            </p>
          )}
        </section>
      ) : null}

      <section aria-labelledby="matched">
        <h2 className={styles.groupTitle} id="matched">
          {affix ? (
            <>
              تنها به این حروف ختم می‌شوند
              <span className={styles.groupCount}>
                <Num value={merely.length} />
              </span>
            </>
          ) : (
            <>
              نتیجه‌ها
              <span className={styles.groupCount}>
                <Num value={merely.length} />
              </span>
            </>
          )}
        </h2>
        <ul className={styles.list}>
          {merely.map((word) => (
            <WordRow key={word.id} word={word} />
          ))}
        </ul>
      </section>

      {result.returned < result.total ? (
        <p className={styles.more}>
          <Num value={result.returned} /> از <Num value={result.total} /> نشان
          داده شده است.
        </p>
      ) : null}
    </div>
  );
}
