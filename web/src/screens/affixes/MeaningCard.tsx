/**
 * One meaning, and the affixes that carry it.
 *
 * The Persian gloss is the heading, because a reader arrives with a meaning.
 * The tag's own name is shown beside it in Latin — it is the identifier a
 * search uses (`tag:ja`), so showing it teaches the query language the same
 * way the search examples do.
 */

import { Link } from "react-router-dom";

import type { Meaning } from "../../api/affixes";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import styles from "./MeaningCard.module.css";

export function MeaningCard({ meaning }: { meaning: Meaning }) {
  return (
    <li className={styles.card}>
      <h2 className={styles.gloss}>
        {meaning.gloss_fa ?? <Latin>{meaning.tag}</Latin>}
        <Latin className={styles.tag}>{meaning.tag}</Latin>
        <span className={styles.count}>
          <Num value={meaning.affixes.length} /> وند
        </span>
      </h2>

      <ul className={styles.affixes}>
        {meaning.affixes.map((one) => (
          <li key={one.rule_id} className={styles.affix}>
            <span className={styles.forms}>
              <Latin affix className={styles.latin}>
                {one.affix}
              </Latin>
              {one.affix_fa ? <span className={styles.fa}>{one.affix_fa}</span> : null}
            </span>

            {one.examples.length > 0 ? (
              <span className={styles.examples}>
                {one.examples.slice(0, 3).map((example) => (
                  <Latin key={example}>{example}</Latin>
                ))}
              </span>
            ) : (
              <span className={styles.noExample}>نمونه‌ای ثبت نشده</span>
            )}

            <Link className={styles.rule} to={`/rules?rule=${one.rule_id}`}>
              <Latin>{one.rule_id}</Latin>
            </Link>
          </li>
        ))}
      </ul>
    </li>
  );
}
