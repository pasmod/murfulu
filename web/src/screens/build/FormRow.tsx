/**
 * One built word.
 *
 * The word and what it means are always visible; the derivation is behind an
 * expander. docs/FRONTEND.md's rule: a translator wants the word, an expert
 * wants the machinery, and they get the same screen at different depths.
 *
 * **Where more than one chain produced the same form, all of them are shown**,
 * nested under it. Two derivations for one word is information — it often
 * means the word carries two senses — not noise to be deduplicated away.
 */

import { useState } from "react";

import type { BuiltForm, Step } from "../../api/generate";
import { Judge } from "../../feedback/Judge";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { persianPercent } from "../../text/numbers";
import { Evidence } from "./Evidence";
import styles from "./FormRow.module.css";

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
            <span className={styles.stepText}>
              {step.explanation_fa ?? step.label_fa ?? ""}
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

  /** The word the first step makes, which is the second step's base. */
  const middle = form.paths[0]?.[1]?.applied_to ?? null;

  /**
   * Each rule of the route this row shows, with its own record.
   *
   * The first route, not a merge of all of them: where routes differ they
   * differ in their first rule, and every route is listed in full under
   * «راه ساخت». A rule the run never measured is left out rather than shown
   * as a zero.
   */
  const counted = (form.paths[0] ?? [])
    .map((step) => ({ rule_id: step.rule_id, ...(step.built ?? {}) }))
    .filter(
      (one): one is {
        rule_id: string;
        types: number;
        attested: number;
        corpus_version: string;
      } => typeof one.types === "number" && typeof one.attested === "number",
    );

  return (
    <li className={styles.row}>
      <div className={styles.head}>
        <span className={styles.forms}>
          <span className={styles.fa}>{form.form_fa}</span>
          <Latin className={styles.latin}>{form.form_latin}</Latin>
        </span>
        <Evidence attestation={form.attestation} />
      </div>

      {form.meaning_fa ? (
        <p className={styles.meaning}>{form.meaning_fa}</p>
      ) : null}

      {/* Built on an intermediate form the corpus does not have. Said in the
          project's wording — never "does not exist" — and shown rather than
          hidden: it is the reason the row sits where it sits. */}
      {/* One part of the score, shown as its own sentence — never folded
          into a single number (docs/FRONTEND.md). Absent when unmeasured. */}
      {/* **Part four: what the base means, against what the rule takes.**
          This was a bare «۸۵٪», and the project lead's objection on
          2026-08-18 was the right one: a reader cannot know what a number
          means without knowing how it was measured. So the figure is shown
          against the bases it was measured against — and it then says the
          true thing it used to hide, that raft is further out than every one
          of them where the old sentence called it «زیاد». */}
      {form.semantic?.typical?.length ? (
        <div className={styles.semantic}>
          <p className={styles.semanticSays}>
            {/* **Not «بن‌هایی که در پیکره یافته‌ایم».** That said the *stems*
                were found in the corpus. What was found is a **word this rule
                built from them** — the artefact counts *attested pairs*, and a
                stem enters the count only when the rule's output on it was
                written. The two are different claims and the first one shipped
                on 2026-08-18 before being caught. */}
            دستور <Latin>{form.semantic.rule_id}</Latin> از{" "}
            <Num value={form.semantic.bases_measured} /> بن واژه‌ای ساخته که در
            پیکرهٔ <Latin>{corpusVersion ?? "?"}</Latin> پیدا شده است.
            نزدیک‌ترین‌های آن بن‌ها به مرکزِ معنایی این دستور:
          </p>
          {/* **The infinitive in brackets, where the base has one.** The list
              read «رو ۹۰٪ · آور ۹۰٪ · هز ۹۰٪ · واز ۹۰٪ · چا ۹۰٪», and a
              reader who cannot place هز cannot judge whether the centre is
              where we say it is. The project lead asked for the مصدر on
              2026-08-18. Nothing is invented: the verbs come from the same
              snapshot the stems do, and a nominal rule's bases show none. */}
          <p className={styles.semanticList}>
            {form.semantic.typical.slice(0, 5).map((one, at) => (
              <span key={one.latin}>
                {at > 0 ? " · " : ""}
                {one.fa}
                {one.of?.length ? (
                  <span className={styles.semanticOf}> ({one.of.join("، ")})</span>
                ) : null}{" "}
                {persianPercent(one.typicality)}
              </span>
            ))}
            {" — و "}
            <Latin>{form.semantic.base}</Latin>{" "}
            {persianPercent(form.semantic.typicality)}
          </p>

          {/* **The rule, written the way every step writes it.** The block
              named «دستور V-034» and left the reader to remember what that
              was; the step rows above have carried the sentence all along.
              Asked for on 2026-08-18: *write the rule here in the same way*. */}
          {form.semantic.rule_says_fa ? (
            <p className={styles.semanticRule}>
              <Latin>{form.semantic.rule_id}</Latin>
              <span className={styles.semanticRuleSays}>
                {form.semantic.rule_says_fa}
              </span>
            </p>
          ) : null}
        </div>
      ) : null}

      {/* **Part two: the middle step.** This said «ساختی روی ساخت», a metaphor
          that assumes the point it is making. It now names the intermediate
          word, says where it was looked for, and says who made it. It does
          **not** say nobody wrote it: FRONTEND.md forbids *does not exist*,
          and the corpus is classical poetry — a word absent from it may be
          ordinary prose. Corrected on 2026-08-18 after a draft of this
          sentence claimed exactly that. */}
      {form.base_attested === false ? (
        <p className={styles.ungrounded}>
          {middle ? (
            <>
              <Latin>{form.form_latin}</Latin> از <Latin>{middle}</Latin> ساخته
              شده است، و <Latin>{middle}</Latin> در پیکرهٔ{" "}
              <Latin>{corpusVersion ?? "?"}</Latin> پیدا نشد — آن را ما
              ساخته‌ایم. پس این واژه دو گام از متنی که خوانده‌ایم دور است.
            </>
          ) : (
            <>
              پایهٔ میانی این واژه در پیکرهٔ{" "}
              <Latin>{corpusVersion ?? "?"}</Latin> پیدا نشد — آن را ما
              ساخته‌ایم.
            </>
          )}
        </p>
      ) : null}

      {/* **Part three: the rules, with their own counts.**
          The form-level `realisation` is a *median* over the chain and is
          true of no rule in it — وارفته's steps realise 0.67% and 9.18%, and
          their median 4.9% describes neither. Asked on 2026-08-18 what «۱۰۰
          واژه» referred to, the answer was that there is no hundred: the
          denominators are 5,196 and 6,926. So each rule states what it built
          and what was found, and the screen computes nothing. */}
      {counted.length ? (
        <div className={styles.record}>
          <p className={styles.recordSays}>این واژه با این دستورها ساخته شده:</p>
          <ul className={styles.recordList}>
            {counted.map((one) => (
              <li key={one.rule_id}>
                <Latin>{one.rule_id}</Latin> — <Num value={one.types!} /> واژه
                ساخته، <Num value={one.attested!} /> تای آن‌ها در پیکرهٔ{" "}
                <Latin>{one.corpus_version}</Latin> پیدا شد.
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {/*
        The letters also read as an inflection of a word the dictionary holds.

        This is why the row sits where it sits, so it is said rather than left
        to be guessed at from an unexplained position — رفتی has 1,565 poems
        behind it and sits below رفتار, which has 1,091. Without the sentence
        that looks like a bug.

        **The second sentence is the honest half.** 95.6% of these are spelled
        by a derivational rule too, so the letters cannot settle which reading
        is meant, and the screen must not imply they can. The word is ranked
        down and never removed; which reading is right is the linguist's.
      */}
      {form.inflection ? (
        <p className={styles.inflection}>
          این املا خوانشِ دیگری هم دارد: {form.inflection.label_fa} از{" "}
          <span dir="rtl">{form.inflection.base}</span>.{" "}
          {form.inflection.shared_with.length > 0 ? (
            <>
              همین حرف‌ها را دستورِ واژه‌سازی هم می‌نویسد (
              {form.inflection.shared_with.map((id, index) => (
                <span key={id}>
                  {index > 0 ? "، " : ""}
                  <Latin>{id}</Latin>
                </span>
              ))}
              )، پس از روی املا نمی‌توان گفت کدام است.
            </>
          ) : (
            "هیچ دستورِ واژه‌سازی این حرف‌ها را نمی‌نویسد."
          )}
        </p>
      ) : null}

      <div className={styles.actions}>
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
            },
          }}
        />
      </div>

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
