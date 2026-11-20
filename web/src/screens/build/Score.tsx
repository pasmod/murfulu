/**
 * A built word's score, what the corpus says about it, and the one sentence
 * that says why — the cells of the build table that carry the evidence.
 *
 * **The project lead's choice of 2026-11-21** (DECISIONS): the three levels
 * of 2026-11-13 read as names a reader had to learn, and a list could not be
 * sorted or filtered by them. So each row now shows **one number from 0 to
 * 100** with a bar beside it, so the score is a length and not only a figure;
 * the parts it is made of are behind «شواهد» (`Signals.tsx`).
 *
 * The API decides the score (`murfulu/scoring/score.py`); this file only says
 * it. Unconfirmed until the linguist rules (FOR_THE_LINGUIST L36).
 *
 * **Nothing here says a word does not exist.** A zero is «نیامده»: the corpus
 * is classical poetry, and a modern word can be missing from it and still be
 * in use (OPEN_QUESTIONS S33). The legend under the table says so once.
 */

import type { BuiltForm, FormScore } from "../../api/generate";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { FUNCTION_WORD_HOMOGRAPH } from "../../text/lexicon";
import { persianNumber } from "../../text/numbers";
import styles from "./Score.module.css";

/** The number and its bar; a dash where nothing was measured. */
export function ScoreCell({ form }: { form: BuiltForm }) {
  const value = form.score?.value ?? null;
  if (value === null) {
    return (
      <span className={styles.none} title="سنجیده نشده">
        —
      </span>
    );
  }
  return (
    <span
      className={styles.score}
      aria-label={`امتیاز ${persianNumber(value)} از ${persianNumber(100)}`}
    >
      <b>
        <Num value={value} />
      </b>
      <span className={styles.bar} aria-hidden="true">
        <i style={{ inlineSize: `${Math.max(0, Math.min(100, value))}%` }} />
      </span>
    </span>
  );
}

/** What the corpus has, short enough for a cell. */
export function CorpusCell({ form }: { form: BuiltForm }) {
  const found = form.attestation;
  if (!found) return <span className={styles.faint}>سنجیده نشده</span>;
  if (found.function_word || found.headword_homograph) {
    return <span className={styles.letters}>واژهٔ دیگری است</span>;
  }
  if (found.level === "none")
    return <span className={styles.faint}>نیامده</span>;
  if (found.level === "spelling") {
    return (
      <span className={styles.letters}>
        همین حروف، <Num value={found.doc_count} /> متن
      </span>
    );
  }
  return (
    <span>
      <Num value={found.doc_count} /> متن
    </span>
  );
}

function affixWord(affix: string | null | undefined): string | null {
  if (!affix) return null;
  if (affix.startsWith("-")) return "پسوند";
  if (affix.endsWith("-")) return "پیشوند";
  return null;
}

/** The rule the word is built with: the last step's affix, or its rule. */
export function MadeWith({ form }: { form: BuiltForm }) {
  const steps = form.paths[0] ?? [];
  const last = steps[steps.length - 1];
  if (!last) return null;
  return (
    <span className={styles.made}>
      {affixWord(last.affix) ? (
        <Latin affix className={styles.affix}>
          {last.affix!}
        </Latin>
      ) : (
        <Latin className={styles.ruleId}>{last.rule_id}</Latin>
      )}
      <span className={styles.faint}>
        {" "}
        در <Num value={steps.length} /> گام
      </span>
    </span>
  );
}

/** The rule half of the sentence: how often the weakest rule builds a real word. */
function ruleSays(score: FormScore): React.ReactNode {
  const rule = score.weakest_rule;
  if (
    !rule ||
    rule.types === null ||
    rule.attested === null ||
    rule.types <= 0
  ) {
    return "دستورهای این واژه هنوز سنجیده نشده‌اند";
  }
  const who = affixWord(rule.affix);
  const named = who ? (
    <>
      {who} <Latin affix>{rule.affix}</Latin>
    </>
  ) : (
    <>
      دستور <Latin>{rule.rule_id}</Latin>
    </>
  );
  const rate = rule.attested / rule.types;
  if (rule.attested === 0) {
    return (
      <>
        {named} از <Num value={rule.types} /> واژه‌ای که می‌سازد، هیچ‌کدام در
        پیکره نیست
      </>
    );
  }
  if (rate < 0.001) {
    return (
      <>
        {named} از <Num value={rule.types} /> واژه‌ای که می‌سازد، تنها{" "}
        {rule.attested === 1 ? (
          "یکی"
        ) : (
          <>
            <Num value={rule.attested} /> تا
          </>
        )}{" "}
        در پیکره هست
      </>
    );
  }
  const per = rate < 0.01 ? 1000 : 100;
  return (
    <>
      {named} از هر <Num value={per} /> واژه‌ای که می‌سازد، حدود{" "}
      <Num value={Math.max(1, Math.round(rate * per))} /> تا در پیکره هست
    </>
  );
}

/** The corpus half: what the corpus says about this word, in words. */
function corpusSays(form: BuiltForm): React.ReactNode {
  const found = form.attestation;
  if (!found) return null;
  if (found.function_word) return FUNCTION_WORD_HOMOGRAPH;
  if (found.headword_homograph) {
    return "این حروف در پیکره هستند، ولی همیشه به معنای واژهٔ دیگری";
  }
  if (found.level === "none") return "در پیکره نیامده است";
  if (found.level === "spelling") {
    return (
      <>
        همین حروف در <Num value={found.doc_count} /> متن آمده‌اند، ولی شاید
        {form.inflection
          ? " شکل صرف‌شدهٔ واژهٔ دیگری باشند"
          : " واژهٔ دیگری باشند"}
      </>
    );
  }
  return (
    <>
      در <Num value={found.doc_count} /> متن از{" "}
      <Num value={found.author_count} /> نویسنده آمده است
    </>
  );
}

/**
 * Why the word has its score, in one or two plain sentences: what the corpus
 * says, then what the rule says. Shown at the top of the evidence.
 */
export function Reason({ form }: { form: BuiltForm }) {
  const corpus = corpusSays(form);
  if (corpus === null) return null;
  if (corpus === FUNCTION_WORD_HOMOGRAPH) {
    return <p className={styles.reason}>{corpus}</p>;
  }
  return (
    <p className={styles.reason}>
      {corpus}.{form.score ? <> {ruleSays(form.score)}.</> : null}
    </p>
  );
}

/**
 * The line under the table: what the corpus is, in which version — said once
 * for the list (DECISIONS 2026-11-13), and again beside every count behind
 * «شواهد».
 */
export function ScoreLegend({
  corpusVersion,
}: {
  corpusVersion: string | null;
}) {
  return (
    <p className={styles.legend}>
      پیکره متن‌های کهن فارسی است، بیشترش شعر
      {corpusVersion ? (
        <>
          {" "}
          (نسخهٔ <Latin>{corpusVersion}</Latin>)
        </>
      ) : null}
      . واژه‌ای که در آن نیامده، شاید امروز به کار برود. امتیازها سنجشی
      تقریبی‌اند، نه داوری دربارهٔ واژه.
    </p>
  );
}
