/**
 * What the corpus says about a built word.
 *
 * Three answers and a fourth state, and the project's whole argument depends
 * on keeping them apart:
 *
 * - **not checked** — the corpus was never asked. Not the same as not found.
 * - **reading** — the corpus has the spelling and the dictionary reads it the
 *   way we built it. The strongest answer.
 * - **spelling** — the letters are there, under a different reading or under
 *   none. The word we built may still be new.
 * - **none** — *not found in corpus v1*. **Never "does not exist"**, and the
 *   version travels with the answer, because that is the only thing the
 *   sentence is true of.
 */

import type { Attestation } from "../../api/generate";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { FUNCTION_WORD_SHORT, LEXICON } from "../../text/lexicon";
import styles from "./Evidence.module.css";

export function Evidence({ attestation }: { attestation: Attestation | null }) {
  if (attestation === null) {
    return <span className={styles.unchecked}>سنجیده نشده</span>;
  }

  if (attestation.level === "none") {
    return (
      <span className={styles.none}>
        در پیکرهٔ <Latin>{attestation.corpus_version || "?"}</Latin> یافت نشد
      </span>
    );
  }

  // A function word's letters: the count is that word's, so none is shown.
  if (attestation.function_word) {
    return <span className={styles.spelling}>{FUNCTION_WORD_SHORT}</span>;
  }

  const confirmed = attestation.level === "reading";
  return (
    <span className={confirmed ? styles.reading : styles.spelling}>
      <Num value={attestation.total_count} /> بار، در{" "}
      <Num value={attestation.doc_count} /> سروده از{" "}
      <Num value={attestation.author_count} /> شاعر
      {confirmed ? null : (
        // A spelling-level hit counted the **letters**. بلندِ claimed 7,353
        // occurrences by 217 poets and every one of them is بلند. Naming the
        // other reading was not enough: the row has to say whose number this
        // is, or a borrowed count reads as a measured one.
        <span className={styles.caveat}>
          {attestation.unlinked
            ? ` — شمار برای این املاست؛ ${LEXICON} خوانشی برایش ندارد`
            : ` — شمار برای این املاست؛ به‌گونهٔ ${attestation.other_readings.join(" یا ")} خوانده می‌شود`}
        </span>
      )}
    </span>
  );
}
