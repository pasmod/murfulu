/**
 * One reading's compounds, as rows.
 *
 * The list opens at twenty and says what it is holding, which is the same
 * shape the build screen uses and for the same reason: the page length must
 * be set by how many readings there are, not by how many words were joined.
 *
 * Two marks matter more than anything else on the row. **«هم‌چنین …»** says
 * the letters also read as an inflection — دلم is دل plus a possessive — and
 * that row is already ranked last. **«در واژه‌نامهٔ کاربن هست»** says the
 * dictionary holds the word too, which is confirmation rather than doubt and
 * does not sink anything.
 */

import { useState } from "react";

import type { Pairing } from "../../api/compound";
import type { WordClass } from "../../api/generate";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { Term } from "../../text/Term";
import { FUNCTION_WORD_SHORT, LEXICON } from "../../text/lexicon";
import styles from "./Pairings.module.css";

/** How many rows a list opens with. The rest are one press away. */
const OPENS_AT = 20;

export function Pairings({
  rows,
  classes = [],
}: {
  rows: Pairing[];
  classes?: WordClass[];
}) {
  const [all, setAll] = useState(false);

  /**
   * What the row builds, in Persian, from the rule pack.
   *
   * Without it دلبر appears twice — once from V-078 and once from V-079 — with
   * the same parts, the same evidence and two rule ids that mean nothing to a
   * reader. The rules differ in exactly one thing and it is this: one makes
   * the *doer*, the other the *done-to*. An API that does not serve the labels
   * yet shows nothing here rather than the machine id.
   */
  const nameOf = (wordClass: string) => {
    const found = classes.find((one) => one.name === wordClass);
    if (!found?.label_fa) return null;
    return (
      <Term
        term={found.label_fa}
        explanation={found.explanation_fa}
        traditional={
          found.label_is_traditional ? undefined : (found.traditional_fa ?? undefined)
        }
      />
    );
  };
  /** The class in Persian, as plain text — for the steps, where a button
      inside a button is not allowed and the word is a label, not a control. */
  const wordFor = (wordClass: string | null) => {
    if (!wordClass) return null;
    const found = classes.find((one) => one.name === wordClass);
    return found?.label_fa ?? null;
  };

  const shown = all ? rows : rows.slice(0, OPENS_AT);
  const folded = rows.length - shown.length;

  return (
    <>
      <ol className={styles.list}>
        {shown.map((row, index) => (
          <li key={`${row.form_fa}-${row.rule_id}-${index}`} className={styles.row}>
            <div className={styles.word}>
              <span className={styles.fa}>{row.form_fa}</span>
              <Latin>{row.form_latin}</Latin>
            </div>

            <p className={styles.parts}>
              {row.front.fa} + {row.behind.fa}
              {nameOf(row.word_class) ? (
                <span className={styles.builds}>← {nameOf(row.word_class)}</span>
              ) : null}
              <span className={styles.rule}>{row.rule_id}</span>
            </p>

            {/* **How it was built, step by step.**
                The row said `دست + ور ← کارنده‌کاربهر V-078` and stopped
                there, which names the parts and hides the rule. A reader
                asked on 2026-08-18 where دستور came from and could not tell
                from the screen: not that ور is there as a کاربن دو, not which
                verb it is the stem of, not what the rule requires. All three
                are in the pack and in the API; this prints them in the order
                the engine applied them. Folded, because twenty rows of four
                lines is a scroll — and open on demand, because checking one
                claim is exactly what the reader is here for. */}
            <details className={styles.how}>
              <summary className={styles.howSummary}>راه ساخت</summary>
              <ol className={styles.steps}>
                <li className={styles.step}>
                  <span className={styles.stepWord}>{row.front.fa}</span>
                  {wordFor(row.front.type) ? (
                    <span className={styles.stepIs}>{wordFor(row.front.type)}</span>
                  ) : null}
                  <span className={styles.stepSays}>
                    {row.role === "front" ? "واژهٔ شما" : "نیمهٔ نخست"}
                  </span>
                </li>
                <li className={styles.step}>
                  <span className={styles.stepWord}>{row.behind.fa}</span>
                  {wordFor(row.behind.type) ? (
                    <span className={styles.stepIs}>{wordFor(row.behind.type)}</span>
                  ) : null}
                  {row.behind.of ? (
                    <span className={styles.stepSays}>
                      از کارواژهٔ {row.behind.of.fa}
                    </span>
                  ) : null}
                </li>
                <li className={styles.step}>
                  <span className={styles.stepWord}>{row.form_fa}</span>
                  {wordFor(row.word_class) ? (
                    <span className={styles.stepIs}>{wordFor(row.word_class)}</span>
                  ) : null}
                  <span className={styles.stepSays}>
                    این دو، بی‌آنکه چیزی میانشان بیاید
                  </span>
                </li>
              </ol>
              {/* The rule's own sentence, from the pack. It is the ruling the
                  three steps above are an instance of. */}
              {row.explanation_fa ? (
                <p className={styles.howRule}>
                  <Latin>{row.rule_id}</Latin>
                  {": "}
                  {row.explanation_fa}
                </p>
              ) : null}
            </details>

            {row.attestation?.function_word ? (
              <p className={styles.evidence}>{FUNCTION_WORD_SHORT}</p>
            ) : row.attestation ? (
              // **The count belongs to the spelling, not to this reading.**
              // The corpus has no vowels, so دلبر is one row in it whether it
              // is read dalbar or dalber — and both readings therefore print
              // the same figure. Saying so is the project's rule about a
              // qualified count; printing it bare made one word's evidence
              // look like two findings.
              <p className={styles.evidence}>
                املای «{row.form_fa}» در <Num value={row.attestation.doc_count} />{" "}
                سروده از <Num value={row.attestation.author_count} /> سراینده آمده
                است
              </p>
            ) : null}

            {row.also_an_inflection ? (
              <p className={styles.warning}>
                هم‌چنین خوانده می‌شود: {row.also_an_inflection.base} +{" "}
                {row.also_an_inflection.label_fa} — پس این شمار شاید از آنِ این
                ترکیب نباشد.
              </p>
            ) : null}

            {row.already_a_word ? (
              <p className={styles.known}>در {LEXICON} هست</p>
            ) : null}
          </li>
        ))}
      </ol>

      {folded > 0 ? (
        <button
          type="button"
          className={styles.more}
          onClick={() => setAll(true)}
        >
          <Num value={folded} /> ترکیب دیگر
        </button>
      ) : null}
    </>
  );
}
