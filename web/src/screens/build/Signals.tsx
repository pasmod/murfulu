/**
 * What a word's two values rest on: three fields behind «شواهد», each opening on
 * a press to the figures behind it. Where the corpus has lines for the word,
 * «پیکره» is open already when «شواهد» opens (2026-11-22).
 *
 * **The project lead's choice of 2026-11-21**: the two values are on the
 * row; what they rest on stays one press away, and separate, because a single opaque number is
 * what the project argues against (FRONTEND.md). A press is what a phone has;
 * nothing here waits for a hover.
 *
 * - **پیکره** — how many texts hold the word, under this reading or as
 *   letters only, and on a press the lines themselves.
 * - **دستور** — how well built, out of 100, from the chain's weakest rule, and
 *   on a press each rule's own record and the ground under the chain.
 * - **معنا** — in neither value: how close the base sits to the bases
 *   the rule usually takes, as up to three dots, and on a press the bases it
 *   was measured against.
 */

import { useId, useState } from "react";

import type { BuiltForm } from "../../api/generate";
import { Latin } from "../../text/Latin";
import { Mixed } from "../../text/Mixed";
import { Num } from "../../text/Num";
import { persianNumber, persianPercent } from "../../text/numbers";
import { CorpusLines } from "./CorpusLines";
import { Evidence } from "./Evidence";
import { hasLines } from "./hasLines";
import { BUILD_MAX, hasValues } from "./scoring";
import styles from "./Signals.module.css";

type Field = "corpus" | "rule" | "meaning";

const NAME: Record<Field, string> = {
  corpus: "پیکره",
  rule: "دستور",
  meaning: "معنا",
};

function Dots({ count, ring = false }: { count: number; ring?: boolean }) {
  return (
    <span className={styles.dots} aria-hidden="true">
      {[1, 2, 3].map((at) => (
        <i
          key={at}
          className={at <= count ? (ring ? styles.ring : styles.on) : ""}
        />
      ))}
    </span>
  );
}

/**
 * What a field shows before it is pressed: what the corpus says, how well the
 * word is built out of 100, or the meaning's dots — or why there is none.
 */
function shown(
  form: BuiltForm,
  field: Field,
): { mark: React.ReactNode; said: string } {
  if (field === "corpus") {
    const found = form.attestation;
    if (!found) return { mark: "سنجیده نشده", said: "سنجیده نشده" };
    if (found.function_word || found.headword_homograph)
      return { mark: "به معنای واژه‌ای دیگر", said: "به معنای واژه‌ای دیگر" };
    if (found.level === "none") return { mark: "نیامده", said: "نیامده" };
    const texts = `${persianNumber(found.doc_count)} متن`;
    const said =
      found.level === "reading" ? texts : `${texts}، شاید واژه‌ای دیگر`;
    return { mark: said, said };
  }
  const score = form.score;
  if (!score) return { mark: null, said: "" };
  if (field === "meaning") {
    const value = score.meaning_mark;
    if (value === null || value === undefined) {
      return { mark: "سنجیده نشده", said: "سنجیده نشده" };
    }
    return {
      mark: <Dots count={value} />,
      said: `${persianNumber(value)} از ${persianNumber(3)}`,
    };
  }
  if (!hasValues(form)) return { mark: null, said: "" };
  const said = `${persianNumber(score.build)} از ${persianNumber(BUILD_MAX)}`;
  return { mark: said, said };
}

function CorpusDetail({ form }: { form: BuiltForm }) {
  return (
    <>
      <p>
        <Evidence attestation={form.attestation} />
      </p>
      {/* The letters also read as an inflection of a word the dictionary
          holds. 95.6% of these are spelled by a derivational rule too, so the
          letters cannot settle which reading is meant; which is right is the
          linguist's. Ranked down, never removed. */}
      {form.inflection ? (
        <p className={styles.caution}>
          این املا را جور دیگری هم می‌شود خواند: {form.inflection.label_fa} از{" "}
          <span dir="rtl">{form.inflection.base}</span>.{" "}
          {form.inflection.shared_with.length > 0 ? (
            <>
              همین املا را دستور واژه‌سازی هم می‌سازد (
              {form.inflection.shared_with.map((id, index) => (
                <span key={id}>
                  {index > 0 ? "، " : ""}
                  <Latin>{id}</Latin>
                </span>
              ))}
              )، پس از روی املا نمی‌شود گفت کدام منظور است.
            </>
          ) : (
            "هیچ دستور واژه‌سازی این املا را نمی‌سازد."
          )}
        </p>
      ) : null}
      {/* The lines the figures were counted from, fetched when this opens. */}
      <CorpusLines form={form} />
    </>
  );
}

function RuleDetail({
  form,
  corpusVersion,
}: {
  form: BuiltForm;
  corpusVersion: string | null;
}) {
  /* Each rule of the route the row shows, with its own record: counts a
     reader can check, never a rate. The first route, because routes differ
     in their first rule and every route is listed under «راه ساخت». A rule
     the run never measured is left out rather than shown as a zero. */
  const counted = (form.paths[0] ?? []).flatMap((step) => {
    const built = step.built;
    if (
      typeof built?.types !== "number" ||
      typeof built.attested !== "number"
    ) {
      return [];
    }
    return [
      {
        rule_id: step.rule_id,
        types: built.types,
        attested: built.attested,
        corpus_version: built.corpus_version,
      },
    ];
  });
  /** The word the first step makes, which is the second step's base. */
  const middle = form.paths[0]?.[1]?.applied_to ?? null;
  return (
    <>
      {counted.length ? (
        <>
          <p>این واژه با این دستورها ساخته شده است:</p>
          <ul className={styles.list}>
            {counted.map((one) => (
              <li key={one.rule_id}>
                <Latin>{one.rule_id}</Latin> — <Num value={one.types} /> واژه
                می‌سازد و <Num value={one.attested} /> تای آن‌ها در پیکرهٔ{" "}
                <Latin>{one.corpus_version}</Latin> آمده است.
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p>دستورهای این واژه هنوز سنجیده نشده‌اند.</p>
      )}
      {/* Built on an intermediate the corpus does not have. Said in the
          project's wording — never "does not exist": the corpus is classical
          poetry, and a word absent from it may be ordinary prose. */}
      {form.base_attested === false ? (
        <p className={styles.caution}>
          {middle ? (
            <>
              <Latin>{form.form_latin}</Latin> از <Latin>{middle}</Latin> ساخته
              شده است، و <Latin>{middle}</Latin> خودش در پیکرهٔ{" "}
              <Latin>{corpusVersion ?? "?"}</Latin> نیامده است؛ آن را هم ما
              ساخته‌ایم. پس این واژه دو گام با متن‌های پیکره فاصله دارد.
            </>
          ) : (
            <>
              واژه‌ای که این واژه از آن ساخته شده، خودش در پیکرهٔ{" "}
              <Latin>{corpusVersion ?? "?"}</Latin> نیامده است؛ آن را هم ما
              ساخته‌ایم.
            </>
          )}
        </p>
      ) : null}
    </>
  );
}

function MeaningDetail({
  form,
  corpusVersion,
}: {
  form: BuiltForm;
  corpusVersion: string | null;
}) {
  const semantic = form.semantic;
  /* The figure is shown against the bases it was measured against, never
     bare: a reader cannot know what «۸۵٪» means without them. The infinitive
     in brackets where the stem has one. And it says the rule *built a word*
     from these stems that was found — not that the stems were found. */
  if (!semantic?.typical?.length) {
    return <p>معنای این واژه سنجیده نشده است.</p>;
  }
  return (
    <>
      <p>
        دستور <Latin>{semantic.rule_id}</Latin> از{" "}
        <Num value={semantic.bases_measured} /> بن واژه‌هایی ساخته که در پیکرهٔ{" "}
        <Latin>{corpusVersion ?? "?"}</Latin> آمده‌اند. از میان آن بن‌ها، این‌ها از
        همه بیشتر به بن‌های معمول این دستور می‌مانند. درصد کنار هر کدام اندازهٔ
        این همانندی است، و آخر از همه بن همین واژه آمده است:
      </p>
      <p className={styles.bases}>
        {semantic.typical.slice(0, 5).map((one, at) => (
          <span key={one.latin}>
            {at > 0 ? " · " : ""}
            {one.fa}
            {one.of?.length ? (
              <span className={styles.of}> ({one.of.join("، ")})</span>
            ) : null}{" "}
            {persianPercent(one.typicality)}
          </span>
        ))}
        {" — و "}
        <Latin>{semantic.base}</Latin> {persianPercent(semantic.typicality)}
      </p>
      {semantic.rule_says_fa ? (
        <p className={styles.rule}>
          <Latin>{semantic.rule_id}</Latin>
          <span className={styles.ruleSays}>
            <Mixed>{semantic.rule_says_fa}</Mixed>
          </span>
        </p>
      ) : null}
    </>
  );
}

export function Signals({
  form,
  corpusVersion,
}: {
  form: BuiltForm;
  corpusVersion: string | null;
}) {
  // «شواهد» opens on the lines where the corpus has any: the reader pressed
  // for evidence, and three closed fields were not it — the project lead asked
  // where the lines were (2026-11-22). The other two fields stay a press away.
  const [open, setOpen] = useState<Field | null>(() =>
    hasLines(form) ? "corpus" : null,
  );
  const id = useId();

  return (
    <div className={styles.signals}>
      <div className={styles.fields}>
        {(Object.keys(NAME) as Field[]).map((field) => {
          const { mark, said } = shown(form, field);
          return (
            <button
              key={field}
              type="button"
              className={styles.field}
              aria-expanded={open === field}
              aria-controls={open === field ? `${id}-${field}` : undefined}
              aria-label={said ? `${NAME[field]}: ${said}` : NAME[field]}
              onClick={() => setOpen((was) => (was === field ? null : field))}
            >
              <span className={styles.name}>{NAME[field]}</span>
              <span className={styles.mark}>{mark}</span>
            </button>
          );
        })}
      </div>
      {open ? (
        <div id={`${id}-${open}`} className={styles.detail}>
          {open === "corpus" ? <CorpusDetail form={form} /> : null}
          {open === "rule" ? (
            <RuleDetail form={form} corpusVersion={corpusVersion} />
          ) : null}
          {open === "meaning" ? (
            <MeaningDetail form={form} corpusVersion={corpusVersion} />
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
