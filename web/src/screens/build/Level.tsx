/**
 * The level of a built word, and the one sentence that gives its reason.
 *
 * **The project lead's choice of 2026-11-13** (DECISIONS): a reader who is not
 * a linguist could not tell from three separate figures whether a word is one
 * Persian already has, a well-made coinage or a long shot. So each row says it
 * as one of three levels — آشنا، خوش‌ساخت، کم‌پشتوانه — with three bars beside
 * the name so the level is a shape and not only a word or a colour, and one
 * sentence of reason under the word. The figures themselves are behind
 * «شواهد» (`Signals.tsx`).
 *
 * The API decides the level (`murfulu/scoring/level.py`); this file only says
 * it. The names and thresholds are **unconfirmed** until the linguist rules
 * (FOR_THE_LINGUIST L36).
 *
 * **The reason never says a word does not exist.** A zero is «در پیکره نیامده
 * است» — the corpus is classical poetry, and a modern word can be missing from
 * it and still be in use (OPEN_QUESTIONS S33). The intro line above the list
 * says so once.
 */

import type { BuiltForm, FormLevel } from "../../api/generate";
import { Info } from "../../text/Info";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { FUNCTION_WORD_HOMOGRAPH } from "../../text/lexicon";
import styles from "./Level.module.css";
import { LEVEL_NAME, LEVEL_SAYS, MIN_TEXTS, NOT_KNOWN } from "./levels";

export function LevelBadge({ form }: { form: BuiltForm }) {
  const level = form.level;
  // An older API sends no level. Then the badge says only what is known for
  // certain — that the corpus was not asked, where it was not — and is
  // otherwise left out rather than claiming «سنجیده نشده».
  if (!level && form.attestation) return null;
  const value = level?.level ?? null;
  const name = value ? LEVEL_NAME[value] : NOT_KNOWN;
  return (
    <span className={styles.badge} data-level={value ?? "none"}>
      <span className={styles.bars} aria-hidden="true">
        {[1, 2, 3].map((step) => (
          <i key={step} className={value && step <= value ? styles.on : ""} />
        ))}
      </span>
      <span className={styles.name}>{name}</span>
      {value ? <Info label={name}>{LEVEL_SAYS[value]}</Info> : null}
    </span>
  );
}

function affixWord(affix: string): string {
  if (affix.startsWith("-") || affix.startsWith("‒")) return "پسوند";
  if (affix.endsWith("-")) return "پیشوند";
  return "دستور";
}

/** The rule half of the sentence: the chain's weakest rule and its record. */
function ruleSays(level: FormLevel): React.ReactNode {
  const rule = level.weakest_rule;
  if (!rule || rule.types === null || rule.attested === null) {
    return "دستورهایش هنوز سنجیده نشده‌اند";
  }
  const who = affixWord(rule.affix);
  const named =
    who === "دستور" ? <Latin>{rule.rule_id}</Latin> : <Latin affix>{rule.affix}</Latin>;
  if (level.level === 1) {
    const few =
      rule.attested === 0 ? (
        "هیچ‌کدام را"
      ) : rule.attested === 1 ? (
        "تنها یکی را"
      ) : (
        <>
          تنها <Num value={rule.attested} /> تا را
        </>
      );
    return (
      <>
        {who} {named} از <Num value={rule.types} /> واژه‌ای که ساخته، {few} در
        پیکره دارد
      </>
    );
  }
  return (
    <>
      {who} {named} <Num value={rule.attested} /> واژه ساخته که در پیکره
      آمده‌اند
    </>
  );
}

/** The corpus half: what the corpus says about this word, in words. */
function corpusSays(form: BuiltForm): React.ReactNode {
  const found = form.attestation;
  if (!found) return null;
  if (found.function_word) return FUNCTION_WORD_HOMOGRAPH;
  if (found.level === "none") return "در پیکره نیامده است";
  if (found.level === "spelling") {
    return (
      <>
        این حرف‌ها در <Num value={found.doc_count} /> متن آمده‌اند، ولی
        {form.inflection ? " خوانش دیگری هم دارند" : " شاید به خوانشی دیگر"}
      </>
    );
  }
  return (
    <>
      {found.doc_count < MIN_TEXTS ? "تنها " : ""}در <Num value={found.doc_count} /> متن
      از <Num value={found.author_count} /> نویسنده آمده است
    </>
  );
}

/** One sentence: what the corpus says, then — unless familiar — the rule. */
export function Reason({ form }: { form: BuiltForm }) {
  const corpus = corpusSays(form);
  if (corpus === null) return null;
  // The function word's sentence is whole already: the count is another
  // word's, and nothing about the rule can stand in for it.
  if (corpus === FUNCTION_WORD_HOMOGRAPH) {
    return <p className={styles.reason}>{corpus}</p>;
  }
  const level = form.level;
  if (!level || level.level === 3) {
    return <p className={styles.reason}>{corpus}.</p>;
  }
  return (
    <p className={styles.reason}>
      {corpus}؛ {ruleSays(level)}.
    </p>
  );
}

/**
 * The first result's "what am I looking at" line (FRONTEND.md): what the three
 * levels mean, and what the corpus is — classical poetry, so that a word it
 * does not hold is not read as a word nobody uses (OPEN_QUESTIONS S33).
 *
 * **The corpus version is said here, once for the list**, and again beside
 * every count behind «شواهد». The sentence under each word does not repeat
 * it: one answer is measured against one corpus, so ten rows saying «پیکرهٔ
 * v16» would say nothing the line above does not (DECISIONS 2026-11-13).
 */
export function LevelIntro({ corpusVersion }: { corpusVersion: string | null }) {
  return (
    <div className={styles.intro}>
      <p>
        هر واژه یک درجه دارد. <strong>{LEVEL_NAME[3]}</strong>: {LEVEL_SAYS[3]}{" "}
        <strong>{LEVEL_NAME[2]}</strong>: {LEVEL_SAYS[2]}{" "}
        <strong>{LEVEL_NAME[1]}</strong>: {LEVEL_SAYS[1]}
      </p>
      <p>
        پیکره متن‌های کهن فارسی است، بیشترش شعر
        {corpusVersion ? (
          <>
            ، در نسخهٔ <Latin>{corpusVersion}</Latin>
          </>
        ) : null}
        . واژه‌ای که در آن نیامده، ممکن است امروز به کار برود.
      </p>
    </div>
  );
}
