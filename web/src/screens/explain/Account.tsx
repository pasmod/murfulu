/**
 * One account of how a word could have been built.
 *
 * Read from the dictionary entry outwards, which is the order the word was
 * made in — not the order it was taken apart in. A reader following the
 * derivation should see it built, the same way the build screen shows it.
 */

import type { Account as Analysis } from "../../api/explain";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { FUNCTION_WORD_SHORT } from "../../text/lexicon";
import styles from "./Account.module.css";

export function Account({ account, form }: { account: Analysis; form: string }) {
  const evidence = account.base.attestation;
  return (
    <li className={styles.account}>
      <p className={styles.base}>
        از <span className={styles.baseFa}>{account.base.spelling_fa}</span>
        <Latin className={styles.baseLatin}>{account.base.latin}</Latin>
        {account.base.lexicon_category ? (
          <span className={styles.category}>{account.base.lexicon_category}</span>
        ) : null}
      </p>

      {/*
        How much of the corpus the base itself has.

        An account can be right about every letter and still rest on a base
        nobody would have meant: Nāxodāgāhi rebuilds from ناخدا, a ship's
        captain, and Hamzamāni from a base of `Zam`. Nothing here refuses those
        — that would need a judgement about meaning this project does not make
        in code — so the reader is given the one fact that separates them and
        left to judge. Absent when the corpus was never asked, which is not the
        same as a base the corpus does not have.
      */}
      {evidence ? (
        <p className={styles.evidence}>
          {evidence.level === "none" ? (
            <>این پایه در پیکره نوشته نشده است.</>
          ) : evidence.function_word ? (
            <>این پایه: {FUNCTION_WORD_SHORT}.</>
          ) : (
            <>
              این پایه در <Num value={evidence.doc_count} /> سند آمده است
              {evidence.level === "spelling" ? " — شمار برای این املاست" : null}.
            </>
          )}
        </p>
      ) : null}

      <ol className={styles.steps}>
        {account.steps.map((step, index) => (
          <li key={`${step.rule_id}-${index}`} className={styles.step}>
            <span className={styles.sum}>
              <Latin>{step.applied_to}</Latin>
              {step.affix ? (
                <>
                  {" + "}
                  <Latin affix>{step.affix}</Latin>
                </>
              ) : null}
            </span>
            <span className={styles.rule}>
              <Latin>{step.rule_id}</Latin>
            </span>
            <span className={styles.explanation}>
              {step.explanation_fa ?? step.label_fa ?? ""}
            </span>
            {/* A stem written one way and behaving another is never silent. */}
            {step.stem_form ? (
              <span className={styles.aside}>
                <Latin>{step.stem_form}</Latin>
              </span>
            ) : null}
            {/* Nor is the y between two vowels: gu + -ande is guyande, and a
             reader who cannot see where the letter came from cannot check
             the account. */}
            {step.glide_id ? (
              <span className={styles.aside}>
                <Latin>{step.glide_id}</Latin>
              </span>
            ) : null}
          </li>
        ))}
      </ol>

      <p className={styles.result}>
        <Latin className={styles.form}>{form}</Latin>
      </p>
    </li>
  );
}
