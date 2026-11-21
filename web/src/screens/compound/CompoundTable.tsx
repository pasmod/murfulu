/**
 * One entry's compounds as the build screen's table.
 *
 * **The project lead asked for the build screen's score here, and for both
 * screens to look and behave alike** (2026-11-21). So this is the build
 * table's pattern with its own parts: the view switch «همهٔ واژه‌ها» /
 * «واژه‌های تازه», the class tabs, the two filters as chips, the sort from the
 * head row, fifty rows and a button for the rest, and the line under the
 * table. The styles, the chips, the score bar and the corpus cell are the
 * build screen's own (`../build`), not copies.
 *
 * **What differs is what «ساخت» measures.** The build screen's value rests on
 * a rule's rate, and a noun's whole page is built by three rules, so it would
 * be one number for every row. Here it is what the second half has made
 * before — the compounds the dictionary holds under that reading and the
 * corpus has — on a scale of its own where «‑دار», the best half, is 100
 * (DECISIONS 2026-11-21, *a build value for compounds*). The ⓘ beside the
 * filter says so, and the row's «شواهد» gives the two numbers behind it.
 */

import { useState } from "react";

import type { CompoundScore, Pairing } from "../../api/compound";
import type { WordClass } from "../../api/generate";
import { Info } from "../../text/Info";
import { Latin } from "../../text/Latin";
import { Mixed } from "../../text/Mixed";
import { Num } from "../../text/Num";
import { Term } from "../../text/Term";
import { FUNCTION_WORD_SHORT, LEXICON } from "../../text/lexicon";
import { Chips, FIRST } from "../build/Build";
import { CorpusCell, ScoreCell, ScoreLegend } from "../build/Score";
import {
  BUILD_RANGES,
  CANDIDATES_SAY,
  CORPUS_SAYS,
  IN_CORPUS,
  type SortKey,
  creditedTexts,
  isCandidate,
} from "../build/scoring";
import table from "../build/Build.module.css";
import cells from "../build/FormRow.module.css";
import styles from "./Pairings.module.css";

/** What «ساخت» means on this page, in the ⓘ beside its filter. */
const COMPOUND_BUILD_SAYS =
  "این عدد، از ۰ تا ۱۰۰، می‌گوید نیمهٔ دومِ این ترکیب پیش‌تر چقدر ترکیب ساخته است: با چند واژهٔ دیگر واژه‌ای ساخته که واژه‌نامه آن را ترکیب می‌داند و در پیکره هم آمده است. ۱۰۰ از آنِ «‑دار» است، پرکارترین نیمهٔ دوم. برای ترکیبی که در پیکره هست و ترکیبی که نیست، یکسان حساب می‌شود.";

/** The table's order: the API's (best built first), a count's, or the alphabet's. */
function sorted(rows: Pairing[], by: SortKey): Pairing[] {
  if (by === "build") return rows;
  const place = new Map(rows.map((row, at) => [row, at]));
  return [...rows].sort((a, b) =>
    by === "texts"
      ? creditedTexts(b) - creditedTexts(a) || place.get(a)! - place.get(b)!
      : a.form_fa.localeCompare(b.form_fa, "fa") ||
        a.form_latin.localeCompare(b.form_latin),
  );
}

/** How many rows each class has, biggest first: the tabs' order. */
function classCounts(rows: Pairing[]): [string, number][] {
  const counts = new Map<string, number>();
  for (const row of rows) {
    counts.set(row.word_class, (counts.get(row.word_class) ?? 0) + 1);
  }
  return [...counts].sort((a, b) => b[1] - a[1]);
}

/** Why the row has its «ساخت», in one sentence, from the two numbers behind it. */
function buildSays(score: CompoundScore | undefined): React.ReactNode {
  const half = score?.weakest_rule;
  if (!score || score.build === null || !half || half.types === null) {
    // Generic on purpose: the API does not say why, and the reasons differ —
    // a one-letter half, a template rule, a stem the run never saw, or no
    // figures configured at all (the review of 2026-11-21).
    return "ساختِ این ترکیب سنجیده نشده است";
  }
  const named = <>«‑{half.affix}»</>;
  if (!half.attested) {
    return (
      <>
        {named} پس از هیچ‌یک از <Num value={half.types} /> واژه‌ای که این دستور در
        نیمهٔ نخست می‌پذیرد، ترکیبی نساخته که هم در {LEXICON} باشد و هم در پیکره
      </>
    );
  }
  return (
    <>
      {named} پس از <Num value={half.types} /> واژه‌ای که این دستور در نیمهٔ نخست
      می‌پذیرد، <Num value={half.attested} /> ترکیب ساخته که هم در {LEXICON} هست و
      هم در پیکره
    </>
  );
}

export function CompoundTable({
  rows,
  classes,
  idPrefix,
}: {
  rows: Pairing[];
  classes: WordClass[];
  idPrefix: string;
}) {
  const [view, setView] = useState<"all" | "new">("all");
  const [wordClass, setWordClass] = useState("all");
  const [range, setRange] = useState("all");
  const [inCorpus, setInCorpus] = useState("all");
  const [sortBy, setSortBy] = useState<SortKey>("build");
  const [whole, setWhole] = useState(false);
  // As on the build screen: every choice returns to the first fifty rows, and
  // «واژه‌های تازه» to the best-built order its line promises.
  const choose =
    <T,>(set: (value: T) => void) =>
    (value: T) => {
      set(value);
      setWhole(false);
    };
  const chooseView = choose((next: "all" | "new") => {
    setView(next);
    if (next === "new") setSortBy("build");
  });

  const counts = classCounts(rows);
  const chosen = counts.some(([name]) => name === wordClass) ? wordClass : "all";
  const keepRange = BUILD_RANGES.find((one) => one.key === range)!;
  const keepCorpus =
    view === "new"
      ? { keeps: isCandidate }
      : IN_CORPUS.find((one) => one.key === inCorpus)!;
  const kept = sorted(
    rows.filter(
      (row) =>
        (chosen === "all" || row.word_class === chosen) &&
        keepRange.keeps(row) &&
        keepCorpus.keeps(row),
    ),
    sortBy,
  );
  const shown = whole ? kept : kept.slice(0, FIRST);
  const held = kept.length - shown.length;
  const corpusVersion =
    rows.find((row) => row.attestation)?.attestation?.corpus_version ?? null;

  const classOf = (name: string) => classes.find((one) => one.name === name);
  const nameOf = (name: string) => classOf(name)?.label_fa ?? <Latin>{name}</Latin>;
  const said = chosen === "all" ? undefined : classOf(chosen);
  const tabs: [string, number][] = [["all", rows.length], ...counts];
  const tabKeys = tabs.map(([name]) => name);

  const sortButton = (key: SortKey, label: string) => (
    <button
      type="button"
      className={table.sort}
      aria-pressed={sortBy === key}
      onClick={() => choose(setSortBy)(key)}
    >
      {label}
      {sortBy === key ? <span aria-hidden="true">▾</span> : null}
    </button>
  );

  return (
    <div className={table.table}>
      <fieldset className={table.views}>
        <legend className="visually-hidden">کدام واژه‌ها</legend>
        {(
          [
            ["all", "همهٔ واژه‌ها"],
            ["new", "واژه‌های تازه"],
          ] as const
        ).map(([key, label]) => (
          <label key={key} className={table.view}>
            <input
              type="radio"
              name={`view-${idPrefix}`}
              className="visually-hidden"
              checked={view === key}
              onChange={() => chooseView(key)}
            />
            {label}
          </label>
        ))}
      </fieldset>

      <div
        className={table.tabs}
        role="tablist"
        aria-label="گونهٔ واژه"
        onKeyDown={(event) => {
          // As on the build screen: the arrows move between the tabs, and in
          // a right-to-left row the left arrow is the next one.
          const at = tabKeys.indexOf(chosen);
          const step =
            event.key === "ArrowLeft" ? 1 : event.key === "ArrowRight" ? -1 : 0;
          const to =
            event.key === "Home"
              ? 0
              : event.key === "End"
                ? tabKeys.length - 1
                : step
                  ? (at + step + tabKeys.length) % tabKeys.length
                  : -1;
          if (to < 0) return;
          event.preventDefault();
          choose(setWordClass)(tabKeys[to]!);
          document.getElementById(`tab-${idPrefix}-${tabKeys[to]}`)?.focus();
        }}
      >
        {tabs.map(([name, count]) => (
          <button
            key={name}
            type="button"
            role="tab"
            id={`tab-${idPrefix}-${name}`}
            aria-selected={chosen === name}
            aria-controls={`words-${idPrefix}`}
            tabIndex={chosen === name ? 0 : -1}
            className={table.tab}
            onClick={() => choose(setWordClass)(name)}
          >
            {name === "all" ? "همه" : nameOf(name)}
            <span className={table.tabCount}>
              <Num value={count} />
            </span>
          </button>
        ))}
      </div>

      {said?.explanation_fa ? (
        <p className={table.classSays}>
          {said.explanation_fa}
          {said.traditional_fa && !said.label_is_traditional ? (
            <span className={table.classTraditional}>
              {" "}
              در دستور سنتی: {said.traditional_fa}
            </span>
          ) : null}
        </p>
      ) : null}

      {view === "new" ? <p className={table.classSays}>{CANDIDATES_SAY}</p> : null}

      <div className={table.tools}>
        <Chips
          legend="ساخت"
          info={<Info label="ساخت">{COMPOUND_BUILD_SAYS}</Info>}
          options={BUILD_RANGES}
          value={range}
          onChange={choose(setRange)}
        />
        {view === "all" ? (
          <Chips
            legend="پیکره"
            info={<Info label="پیکره">{CORPUS_SAYS}</Info>}
            options={IN_CORPUS}
            value={inCorpus}
            onChange={choose(setInCorpus)}
          />
        ) : null}
        <div className={table.phoneSort}>
          <span className={table.sortLabel}>ترتیب</span>
          {sortButton("build", "ساخت")}
          {sortButton("texts", "شمار متن‌ها")}
          {sortButton("alpha", "الفبا")}
        </div>
        <span className={table.shown} role="status">
          <Num value={kept.length} /> واژه
        </span>
      </div>

      <div className={table.head}>
        {sortButton("alpha", "واژه")}
        <span>گونه</span>
        {sortButton("build", "ساخت")}
        {sortButton("texts", "در پیکره")}
        <span>دو نیمه</span>
        <span />
      </div>

      {shown.length ? (
        <div
          id={`words-${idPrefix}`}
          role="tabpanel"
          aria-labelledby={`tab-${idPrefix}-${chosen}`}
        >
          <ul className={table.forms}>
            {shown.map((row) => (
              <CompoundRow
                key={`${row.form_fa}:${row.form_latin}:${row.rule_id}:${row.behind.latin}`}
                row={row}
                classes={classes}
              />
            ))}
          </ul>
        </div>
      ) : (
        <p id={`words-${idPrefix}`} className={table.empty}>
          با این گزینه‌ها هیچ واژه‌ای نمی‌ماند. یکی از آن‌ها را بردارید.
        </p>
      )}

      {held > 0 ? (
        <button type="button" className={table.more} onClick={() => setWhole(true)}>
          <Num value={held} /> واژهٔ دیگر را هم نشان بده
        </button>
      ) : null}

      <ScoreLegend corpusVersion={corpusVersion} />
    </div>
  );
}

/**
 * One compound: the build table's row, with this page's evidence and steps.
 *
 * The two marks that mattered most on the old row stay, now behind «شواهد»
 * with the sentence for the value: **«این حروف را این‌طور هم می‌شود
 * خواند»** — دلم is دل plus a possessive — and **«در واژه‌نامهٔ کاربن هست»**,
 * which is confirmation, not doubt.
 */
function CompoundRow({ row, classes }: { row: Pairing; classes: WordClass[] }) {
  const [showing, setShowing] = useState(false);
  const [open, setOpen] = useState(false);

  const found = (name: string | null) =>
    name ? classes.find((one) => one.name === name) : undefined;
  const builds = found(row.word_class);
  /** A class's name as plain text, for the steps (no button inside a button). */
  const wordFor = (name: string | null) => found(name)?.label_fa ?? null;

  return (
    <li className={cells.row}>
      <div className={cells.cells}>
        <span className={cells.word}>
          <span className={cells.fa}>{row.form_fa_marked ?? row.form_fa}</span>
          <Latin className={cells.latin}>{row.form_latin}</Latin>
        </span>
        <span className={cells.wordClass}>
          {/* What the row builds: the one thing that tells V-078's دلبر, the
              doer, from V-079's, the done-to (FOR_THE_LINGUIST L49). */}
          {builds?.label_fa ? (
            <Term
              term={builds.label_fa}
              explanation={builds.explanation_fa}
              traditional={
                builds.label_is_traditional
                  ? undefined
                  : (builds.traditional_fa ?? undefined)
              }
            />
          ) : null}
        </span>
        <span className={cells.scoreCell}>
          <ScoreCell form={row} />
        </span>
        <span className={cells.corpus}>
          <CorpusCell form={row} />
          {/* On a phone the class column is hidden, and every V-078 row has
              a V-079 twin with the same letters: the class, said here, is
              what tells the doer from the done-to. */}
          {builds?.label_fa ? (
            <span className={styles.phoneClass}>{builds.label_fa}</span>
          ) : null}
        </span>
        <span className={cells.made}>
          {row.front.fa} + {row.behind.fa}{" "}
          <Latin className={styles.rule}>{row.rule_id}</Latin>
        </span>
        <div className={cells.actions}>
          <button
            type="button"
            className={cells.toggle}
            aria-expanded={showing}
            onClick={() => setShowing((was) => !was)}
          >
            شواهد
          </button>
          <button
            type="button"
            className={cells.toggle}
            aria-expanded={open}
            onClick={() => setOpen((was) => !was)}
          >
            راه ساخت
          </button>
        </div>
      </div>

      {showing ? (
        <div className={cells.evidence}>
          <p className={styles.evidence}>{buildSays(row.score)}.</p>
          {row.attestation?.function_word ? (
            <p className={styles.evidence}>{FUNCTION_WORD_SHORT}</p>
          ) : row.attestation?.level === "none" ? (
            <p className={styles.evidence}>
              «{row.form_fa}» در پیکره نیامده است
            </p>
          ) : row.attestation ? (
            // **The count belongs to the spelling, not to this reading**: the
            // corpus has no vowels, so دلبر is one row in it whether it is
            // read delbar or delber, and both carry the same figure.
            <p className={styles.evidence}>
              املای «{row.form_fa}» در <Num value={row.attestation.doc_count} /> متن
              از <Num value={row.attestation.author_count} /> نویسنده آمده است
            </p>
          ) : null}
          {row.also_an_inflection ? (
            <p className={styles.warning}>
              این حروف را این‌طور هم می‌شود خواند: {row.also_an_inflection.base} +{" "}
              {row.also_an_inflection.label_fa}؛ پس شاید این شمار از آنِ این ترکیب
              نباشد.
            </p>
          ) : null}
          {row.already_a_word ? (
            <p className={styles.known}>در {LEXICON} هست</p>
          ) : null}
        </div>
      ) : null}

      {open ? (
        <div className={cells.derivation}>
          {/* How it was built, step by step: which half is the reader's word,
              which verb the other half is a stem of, and the rule's own
              sentence — what a reader asked for on 2026-08-18 about دستور. */}
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
                <span className={styles.stepSays}>از کارواژهٔ {row.behind.of.fa}</span>
              ) : null}
            </li>
            <li className={styles.step}>
              <span className={styles.stepWord}>{row.form_fa}</span>
              {wordFor(row.word_class) ? (
                <span className={styles.stepIs}>{wordFor(row.word_class)}</span>
              ) : null}
              <span className={styles.stepSays}>
                این دو کنار هم، بی‌هیچ چیزی میانشان
              </span>
            </li>
          </ol>
          {row.explanation_fa ? (
            <p className={styles.howRule}>
              <Latin>{row.rule_id}</Latin>
              {": "}
              <Mixed>{row.explanation_fa}</Mixed>
            </p>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}
