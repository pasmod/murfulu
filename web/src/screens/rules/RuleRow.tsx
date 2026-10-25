/**
 * One rule, with what the source says and what the corpus says.
 *
 * **Where the two disagree, that is shown as a finding rather than an error.**
 * The source states a strength for three of 195 rules and all three land in a
 * different band when measured. docs/FRONTEND.md is explicit that this is
 * information, and it is one of the few places the project can show its own
 * method working.
 *
 * A rule with no measurement and a rule measured at zero are drawn
 * differently. "Never fired in this run, because it is a stem rule" and
 * "built 1,433 words and nobody ever wrote one of them" are not the same
 * sentence.
 */

import { useState } from "react";

import type { Rule } from "../../api/rules";
import { Judge } from "../../feedback/Judge";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import styles from "./RuleRow.module.css";

const BAND_LABEL: Record<string, string> = {
  high: "بالا",
  middle: "میانه",
  low: "پایین",
};

const STRENGTH_LABEL: Record<string, string> = {
  obligatory: "همیشگی",
  typical: "بیشتر",
  occasional: "گاهی",
};

/** A share, in Persian numerals. Persian digits throughout, without exception. */
const PERCENT = new Intl.NumberFormat("fa-IR", {
  style: "percent",
  maximumFractionDigits: 1,
});

function rate(value: number | null): string {
  return value === null ? "—" : PERCENT.format(value);
}

export function RuleRow({ rule }: { rule: Rule }) {
  const [open, setOpen] = useState(false);
  const measured = rule.productivity;

  return (
    <li className={styles.row}>
      <div className={styles.head}>
        <span className={styles.identity}>
          <Latin className={styles.id}>{rule.id}</Latin>
          {rule.affix ? (
            <>
              <Latin affix className={styles.affix}>
                {rule.affix}
              </Latin>
              {rule.affix_fa ? (
                <span className={styles.affixFa}>{rule.affix_fa}</span>
              ) : null}
            </>
          ) : (
            <span className={styles.kind}>{rule.kind}</span>
          )}
        </span>

        <span className={styles.numbers}>
          {measured?.measured ? (
            <>
              <span className={styles.built}>
                <Num value={measured.types_built} /> ساخته
              </span>
              <span className={styles.attested}>
                <Num value={measured.types_attested} /> نوشته‌شده
              </span>
              <span className={styles.rateValue}>{rate(measured.realisation_rate)}</span>
            </>
          ) : (
            <span className={styles.unmeasured}>
              {measured?.unmeasurable_reason
                ? "سنجیده نشد"
                : "هنوز سنجشی انجام نشده"}
            </span>
          )}
        </span>
      </div>

      {rule.explanation_fa ? (
        <p className={styles.explanation}>{rule.explanation_fa}</p>
      ) : null}

      <div className={styles.marks}>
        {rule.strength ? (
          <span className={styles.strength}>
            سرچشمه: {STRENGTH_LABEL[rule.strength] ?? rule.strength}
          </span>
        ) : null}
        {measured?.band ? (
          <span className={styles.band}>
            سنجش: {BAND_LABEL[measured.band] ?? measured.band}
          </span>
        ) : null}
        {measured?.disagrees_with_strength ? (
          <span className={styles.disagrees}>
            سرچشمه و سنجش یکی نیستند
          </span>
        ) : null}
        {!rule.active ? <span className={styles.retired}>بازنشسته</span> : null}
        {rule.needs_expert_check ? (
          <span className={styles.flagged}>نیازمند بررسی</span>
        ) : null}
      </div>

      {/* Why the rule was retired, in Persian. It used to be the badge and
          nothing more: every `retired_reason` is written in English for
          whoever reads the repository, and the interface may not invent
          Persian — so a reader was told *that* a rule no longer applies and
          never why, which for N-090 is the whole of the interesting part.
          Authored in `rules/decisions.yaml` beside the ruling. Absent for any
          retirement nobody has written up, which shows the badge alone rather
          than a sentence somebody guessed. S14. */}
      {!rule.active && rule.retired_reason_fa ? (
        <p className={styles.retiredReason}>{rule.retired_reason_fa}</p>
      ) : null}

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.toggle}
          aria-expanded={open}
          onClick={() => setOpen((was) => !was)}
        >
          {open ? "بستن جزئیات" : "جزئیات"}
        </button>

        {/* *Rule 10 should not fire here* is one of docs/REVIEW.md's targets,
            and it is about the rule, not about the page listing 195 of them.
            The measurement travels with it, because a judgement about a rule
            is a judgement about the rule as it was measured. */}
        <Judge
          subject={{
            target_type: "rule",
            target_id: rule.id,
            label: `دستور ${rule.id}`,
            corpus_version: measured?.corpus_version ?? null,
            context: {
              rule_id: rule.id,
              affix: rule.affix,
              authored_strength: rule.strength,
              measured_band: measured?.band ?? null,
              realisation_rate: measured?.realisation_rate ?? null,
              disagrees_with_strength: measured?.disagrees_with_strength ?? false,
            },
          }}
        />
      </div>

      {open ? (
        <dl className={styles.detail}>
          <div>
            <dt>می‌گیرد</dt>
            <dd>
              {rule.input_types.map((one) => (
                <Latin key={one}>{one}</Latin>
              ))}
            </dd>
          </div>
          <div>
            <dt>می‌دهد</dt>
            <dd>
              {rule.output_types.map((one) => (
                <Latin key={one}>{one}</Latin>
              ))}
            </dd>
          </div>
          {rule.semantic_tags.length > 0 ? (
            <div>
              <dt>معنا</dt>
              <dd>
                {rule.semantic_tags.map((one) => (
                  <Latin key={one}>{one}</Latin>
                ))}
              </dd>
            </div>
          ) : null}
          {rule.examples.length > 0 ? (
            <div>
              <dt>نمونه‌ها</dt>
              <dd>
                {rule.examples.slice(0, 6).map((one) => (
                  <Latin key={one}>{one}</Latin>
                ))}
              </dd>
            </div>
          ) : null}
          {measured?.unmeasurable_reason ? (
            <div>
              <dt>چرا سنجیده نشد</dt>
              <dd className={styles.reason}>{measured.unmeasurable_reason}</dd>
            </div>
          ) : null}
          {measured?.echo_share ? (
            <div>
              <dt>هم‌سان با ورودی</dt>
              <dd>{rate(measured.echo_share)}</dd>
            </div>
          ) : null}
          {/* The semantic centre, straight from the artefact. Every word here
              is either a count or a base the batch job ranked — the component
              writes no Persian about the meaning and computes nothing. A rule
              without a centre says so, because a blank would read as "this
              rule has nothing typical". */}
          <div>
            <dt>پایه‌های شاخص</dt>
            <dd>
              {rule.semantic ? (
                <>
                  <span className={styles.reason}>
                    میانگین <Num value={rule.semantic.bases} /> پایهٔ نوشته‌شده
                  </span>
                  {rule.semantic.typical_bases.map((base) => (
                    <span key={base.latin} className={styles.typical}>
                      <span>{base.fa}</span>
                      <Latin>{base.latin}</Latin>
                    </span>
                  ))}
                </>
              ) : (
                <span className={styles.reason}>
                  برای این دستور سنجش معنایی در دست نیست
                </span>
              )}
            </dd>
          </div>
          {rule.notes && rule.notes.length > 0 ? (
            <div>
              <dt>یادداشت</dt>
              <dd className={styles.reason}>{rule.notes.join(" ")}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}
    </li>
  );
}
