/**
 * One hit.
 *
 * A table on a wide screen and a card on a phone — docs/FRONTEND.md is
 * explicit about that, and it is the same markup either way: a list whose
 * items become rows in a grid when there is room. Nothing is duplicated for
 * the two layouts, so they cannot drift apart.
 *
 * **Both scripts, always.** The project's whole argument is that the Latin
 * makes distinctions the Persian script hides, so showing one without the
 * other defeats it.
 *
 * The category shown is the **dictionary's own**, in its own Persian words.
 * The mapped word class is what the rules match on, and naming it here would
 * need a glossary nothing serves yet — see OPEN_QUESTIONS S3.
 */

import { Link } from "react-router-dom";

import type { WordType } from "../../api/search";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import {
  FUNCTION_WORD_LETTERS,
  FUNCTION_WORD_SHORT,
  NO_READING,
  POPULATION_LABEL,
} from "../../text/lexicon";
import { persianCenturyRange } from "../../text/numbers";
import styles from "./WordRow.module.css";

export interface WordRowProps {
  word: WordType;
}

export function WordRow({ word }: WordRowProps) {
  const centuries =
    word.first_century != null && word.last_century != null
      ? persianCenturyRange(word.first_century, word.last_century)
      : null;

  return (
    <li className={styles.row}>
      <Link className={styles.forms} to={`/word/${encodeURIComponent(word.id)}`}>
        <span className={styles.spelling}>{word.spelling_fa}</span>
        {word.latin ? (
          <>
            <Latin className={styles.latin}>{word.latin}</Latin>
            {/* The dictionary's own second spelling of the same reading —
                برنا is barnā and also bornā. Shown because a reader who hears
                the other one otherwise cannot tell whether we know it. */}
            {word.latin_variants?.length ? (
              <Latin className={styles.variants}>
                {word.latin_variants.join("، ")}
              </Latin>
            ) : null}
          </>
        ) : (
          // Not an error and not a blank: the corpus has the letters and the
          // dictionary has no entry, which is the coverage gap itself.
          <span className={styles.unread}>{NO_READING}</span>
        )}
      </Link>

      <span className={styles.category}>{word.lexicon_category ?? ""}</span>

      <span className={styles.populations}>
        {(word.population ?? []).map((where) => (
          <span key={where} className={styles.badge}>
            {POPULATION_LABEL[where] ?? where}
          </span>
        ))}
      </span>

      <span className={styles.counts}>
        {/* A function word's letters: a reading carries no count, and the
            spelling's own row says whose count it holds. */}
        {word.function_word ? (
          <span className={styles.faint}>
            {word.latin ? FUNCTION_WORD_SHORT : FUNCTION_WORD_LETTERS}
          </span>
        ) : null}
        {word.total_count != null ? (
          <span className={styles.count}>
            <Num value={word.total_count} /> بار
          </span>
        ) : null}
        {word.doc_count != null ? (
          <span className={styles.faint}>
            در <Num value={word.doc_count} /> سروده
          </span>
        ) : null}
        {word.author_count != null ? (
          <span className={styles.faint}>
            از <Num value={word.author_count} /> شاعر
          </span>
        ) : null}
        {centuries ? <span className={styles.faint}>{centuries}</span> : null}
      </span>
    </li>
  );
}
