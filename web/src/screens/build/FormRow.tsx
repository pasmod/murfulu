/**
 * One built word.
 *
 * The word, its level and one sentence of reason are always visible; what the
 * level rests on is behind «شواهد», and the derivation behind «راه ساخت».
 * docs/FRONTEND.md's rule: a translator wants the word, an expert wants the
 * machinery, and they get the same screen at different depths. The level is
 * the project lead's choice of 2026-11-13 (`Level.tsx`, `Signals.tsx`).
 *
 * **Where more than one chain produced the same form, all of them are shown**,
 * nested under it. Two derivations for one word is information — it often
 * means the word carries two senses — not noise to be deduplicated away.
 */

import { useState } from "react";

import type { BuiltForm, Step } from "../../api/generate";
import { Judge } from "../../feedback/Judge";
import { Latin } from "../../text/Latin";
import { Mixed } from "../../text/Mixed";
import { Num } from "../../text/Num";
import styles from "./FormRow.module.css";
import { LevelBadge, Reason } from "./Level";
import { Signals } from "./Signals";

/**
 * One route from the base to the word: its number, and its steps.
 *
 * **Numbered because four routes read as twelve rules otherwise.** وارفتنی is
 * built four ways of three steps each, and they used to sit in one grey box
 * separated by nothing but a gap — so what a reader saw was a list of twelve,
 * with «۴ راه» above it and no way to tell where one route ended. Asked what
 * it meant on 2026-08-18, the screen had no answer on it.
 */
function Chain({
  steps,
  index,
  of,
  result,
}: {
  steps: Step[];
  index: number;
  of: number;
  /** What the last step produces: the word itself. */
  result: string;
}) {
  /**
   * What each step *makes*, which the screen never showed.
   *
   * A step said `raft + vā-` and the next said `vāraft + -e`, and a reader had
   * to work out for themselves that the second base was the first step's
   * output. The chain was there and the arrow was missing. No new data is
   * needed: a step's result is the next step's base, and the last step's is
   * the word.
   */
  const producedBy = (at: number) => steps[at + 1]?.applied_to ?? result;

  return (
    <div className={styles.route}>
      {of > 1 ? (
        <p className={styles.routeTitle}>
          راه <Num value={index + 1} /> از <Num value={of} />
        </p>
      ) : null}
      <ol className={styles.chain}>
        {steps.map((step, at) => (
          <li key={`${step.rule_id}-${at}`} className={styles.step}>
            <span className={styles.ruleId}>
              <Latin>{step.rule_id}</Latin>
            </span>
            {/* The rule pack's sentence, with its Latin set apart: printed
                plain, the dash of "-ande" took the line's direction and the
                reader saw «ande-», a prefix (text/Mixed.tsx). */}
            <span className={styles.stepText}>
              <Mixed>{step.explanation_fa ?? step.label_fa ?? ""}</Mixed>
            </span>
            {/* What the rule *means*, where the pack gives it a tag. This is
                often the only thing telling one route from another: the four
                that build وارفتنی share their explanation word for word and
                differ only here — پس، دوباره، باز، آخشیج. */}
            {step.tags_fa?.length ? (
              <span className={styles.stepSense}>
                {step.tags_fa.join("، ")}
              </span>
            ) : null}
            <span className={styles.stepForms}>
              <Latin>{step.applied_to}</Latin>
              {step.affix ? (
                <>
                  {" + "}
                  <Latin affix>{step.affix}</Latin>
                </>
              ) : null}
              <span className={styles.becomes} aria-hidden="true">
                {" ← "}
              </span>
              <Latin className={styles.produced}>{producedBy(at)}</Latin>
            </span>
            {/* A stem written one way and behaving another — *row* becoming
             *rav* — is shown, so nothing changes silently. */}
            {step.stem_form ? (
              <span className={styles.aside}>
                <Latin>{step.stem_form}</Latin>
              </span>
            ) : null}
            {step.glide_id ? (
              <span className={styles.aside}>
                <Latin>{step.glide_id}</Latin>
              </span>
            ) : null}
          </li>
        ))}
      </ol>
    </div>
  );
}

export interface FormRowProps {
  form: BuiltForm;
  /** Which corpus version the evidence beside it came from. */
  corpusVersion?: string | null;
}

export function FormRow({ form, corpusVersion = null }: FormRowProps) {
  const [open, setOpen] = useState(false);
  const [showing, setShowing] = useState(false);

  return (
    <li className={styles.row}>
      <div className={styles.head}>
        <span className={styles.forms}>
          <span className={styles.fa}>{form.form_fa}</span>
          <Latin className={styles.latin}>{form.form_latin}</Latin>
        </span>
        <LevelBadge level={form.level} />
      </div>

      <Reason form={form} />

      {form.meaning_fa ? (
        <p className={styles.meaning}>{form.meaning_fa}</p>
      ) : null}

      <div className={styles.actions}>
        {/* What the level rests on: the three parts of the score, separate,
            one press away — never folded into the level and hidden. */}
        <button
          type="button"
          className={styles.toggle}
          aria-expanded={showing}
          onClick={() => setShowing((was) => !was)}
        >
          {showing ? "بستن شواهد" : "شواهد"}
        </button>

        <button
          type="button"
          className={styles.toggle}
          aria-expanded={open}
          onClick={() => setOpen((was) => !was)}
        >
          {open ? "بستن راه ساخت" : "راه ساخت"}
          {form.paths.length > 1 ? (
            <span className={styles.paths}>
              <Num value={form.paths.length} /> راه
            </span>
          ) : null}
        </button>

        {/* *Raftorow is not a word* is docs/REVIEW.md's own example, and it
            has to be sayable about the word rather than about the page. The
            whole record travels with it: the chain that built it, the
            evidence, and the corpus version that evidence is true for. */}
        <Judge
          subject={{
            target_type: "derivation",
            target_id: `${form.form_latin}:${form.word_class}`,
            label: form.form_fa,
            corpus_version: corpusVersion,
            context: {
              form_latin: form.form_latin,
              form_fa: form.form_fa,
              word_class: form.word_class,
              rule_chain: form.paths[0]?.map((step) => step.rule_id) ?? [],
              glide_rules:
                form.paths[0]?.flatMap((step) =>
                  step.glide_id ? [step.glide_id] : [],
                ) ?? [],
              meaning_fa: form.meaning_fa ?? null,
              attestation: form.attestation?.level ?? null,
              level: form.level?.level ?? null,
            },
          }}
        />
      </div>

      {showing ? <Signals form={form} corpusVersion={corpusVersion} /> : null}

      {open ? (
        <div className={styles.derivation}>
          {form.paths.map((steps, index) => (
            <Chain
              key={index}
              steps={steps}
              index={index}
              of={form.paths.length}
              result={form.form_latin}
            />
          ))}
        </div>
      ) : null}
    </li>
  );
}
