/**
 * One glide rule: what happens where two vowels meet.
 *
 * **Its own row, not an affix row with the fields left out.** A glide has no
 * affix, no input class, no semantic tag and nothing to measure — it decides
 * a letter at a join rather than building a word. Rendered through `RuleRow`
 * it would be blanks where the affix goes and *not yet measured* where a
 * measurement goes, and neither of those is true: there is nothing here to
 * measure, which is a different sentence from nobody having measured it.
 *
 * Seventeen of these sit in the pack and none of them was served anywhere,
 * so the rules screen's میانجی button emptied the list and a build result
 * naming `G-10` had nothing to link to.
 */

import type { Glide } from "../../api/rules";
import { Judge } from "../../feedback/Judge";
import { Latin } from "../../text/Latin";
import styles from "./RuleRow.module.css";

export function GlideRow({ glide }: { glide: Glide }) {
  return (
    <li className={styles.row}>
      <div className={styles.head}>
        <span className={styles.identity}>
          <Latin className={styles.id}>{glide.id}</Latin>
          {/* The rule itself, which is the whole of what a glide says. */}
          <span className={styles.meeting}>
            <Latin>{glide.left}</Latin>
            <span aria-hidden="true">+</span>
            <Latin>{glide.right}</Latin>
            <span aria-hidden="true">→</span>
            <Latin className={styles.result}>{glide.result}</Latin>
          </span>
        </span>
      </div>

      {glide.explanation_fa ? (
        <p className={styles.explanation}>{glide.explanation_fa}</p>
      ) : null}

      {glide.examples.length > 0 ? (
        <p className={styles.glideExamples}>
          {glide.examples.map((one) => (
            <Latin key={one}>{one}</Latin>
          ))}
        </p>
      ) : null}

      <div className={styles.marks}>
        {!glide.active ? <span className={styles.retired}>بازنشسته</span> : null}
      </div>

      {/* Why, in Persian. It used to be the badge and nothing more: every
          `retired_reason` is written in English for whoever reads the
          repository, and the interface may not invent Persian — so a reader
          was told *that* a rule no longer applies and never why. Authored in
          `rules/decisions.yaml` beside the ruling itself, and still absent for
          any retirement nobody has written up, which shows the badge alone
          rather than a guessed sentence. S14. */}
      {!glide.active && glide.retired_reason_fa ? (
        <p className={styles.retiredReason}>{glide.retired_reason_fa}</p>
      ) : null}

      <div className={styles.actions}>
        <Judge
          subject={{
            target_type: "rule",
            target_id: glide.id,
            label: `دستور ${glide.id}`,
            corpus_version: null,
            context: {
              rule_id: glide.id,
              left: glide.left,
              right: glide.right,
              result: glide.result,
            },
          }}
        />
      </div>
    </li>
  );
}
