/**
 * The build screen: a word in, everything the grammar can make from it out.
 *
 * **Grouped by what each result *is*.** A reader looking for a noun should not
 * have to read past forty adjectives. The group's name is what traditional
 * grammar calls the class — اسم, صفت, اسم مصدر — served from the rule pack
 * rather than written here. The project's own coined terms (کارنام, کاربن دو)
 * are not in the data at all, so nothing shows them; see OPEN_QUESTIONS S3.
 *
 * **Sorted by level, then by evidence, never by depth.** A three-step form is
 * not worse for being three steps — *Guyāyi* is two steps and entirely
 * ordinary. What ranks a form is its level (`Level.tsx`, 2026-11-13), and
 * within a level what the corpus says about it.
 *
 * **Three steps are offered, and a deep answer is a page.** One verb at three
 * steps builds tens of thousands of forms, of which fifty are words the corpus
 * has — so the route ranks before it pages and the screen asks for the best six
 * hundred, saying plainly how many of how many it is showing. See {@link
 * DEPTHS} for why this waited on the ranking rather than on the paging.
 */

import { useCallback, useEffect, useId, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import {
  DEEP_LIMIT,
  generate,
  wordClasses,
  type BuiltForm,
  type Generated,
  type WordClass,
} from "../../api/generate";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import { Waiting } from "../../text/Waiting";
import {
  ALSO_WRITTEN,
  FROM_LEXICON,
  LEXICON,
  NEEDS_REVIEW,
  notFound,
  wasCut,
} from "../../text/lexicon";
import { SCREENS } from "../../shell/screens";
import styles from "./Build.module.css";
import { useSubject } from "../../feedback/subject";
import { FormRow } from "./FormRow";
import { ScoreLegend } from "./Score";
import {
  IN_CORPUS,
  BUILD_RANGES,
  BUILD_SAYS,
  CANDIDATES_SAY,
  CORPUS_SAYS,
  isCandidate,
  creditedTexts,
  buildOrder,
  hasValues,
  type SortKey,
} from "./scoring";
import { Info } from "../../text/Info";
import { WordInput } from "./WordInput";

const SCREEN = SCREENS.find((one) => one.path === "/build")!;

/**
 * One, two and three steps.
 *
 * **Three was withheld until it could be ranked, not until it could be sent.**
 * The size was never the whole problem — رفتن at three steps is 39 MB and the
 * route has paged since PLAN 6.2 — the problem was that a page of an unranked
 * answer is a random handful. At three steps only 50 of 17,717 words are ones
 * the corpus has, so the ordering is the feature and the list is nothing
 * without it.
 *
 * What made it possible is the realisation figure: how often each rule on the
 * way produces a word the corpus has. *hamandišande*, which PLAN 9.10 exists
 * to reach, sat at 10,551 of 17,717 and now sits at 676. The route ranks and
 * then pages, so {@link DEEP_LIMIT} is the best six hundred rather than the
 * first six hundred.
 */
const DEPTHS = [1, 2, 3];

/** Below this the screen asks for every form; at or above it, one page. */
const DEEP = 3;

/**
 * Strongest evidence first. Depth never enters into it.
 *
 * Three states, in this order: **the corpus has it**, the corpus does not,
 * and the corpus was never asked. The last is not the middle one — an
 * unchecked word is not an absent one — so it sorts on its own.
 *
 * Among the unattested, the ground under the chain decides: measured on
 * رفتن, 231 of its 510 words are built on an intermediate form nobody ever
 * wrote — three unwritten step-one forms carry over 150 step-two words —
 * and those sink below forms whose every step is written. Sunk, never
 * hidden: an absent word can still be good Persian the poets never needed.
 *
 * **How the match was linked is a tie-breaker, not a rank.** It used to come
 * first, and the level says whether the lexicon holds a headword for that
 * exact spelling — a fact about the dictionary rather than about the word.
 * So گویه, written in 6 poems, sat above گفت, written in 19,839. A
 * `spelling` match may still be a homograph, which is why the level survives
 * as the tie-breaker and why the row says so; see OPEN_QUESTIONS S8.
 *
 * **And a count the dictionary attributes to another word does not rank a
 * form at all.** Sorting purely on the count opened رفتن with روی — `ravi`,
 * 31,830 poems, which the lexicon reads *Rui*, "face" — above رفتار and روش.
 * See {@link ours}.
 */
const RANK = { reading: 0, spelling: 1, none: 2 } as const;

/**
 * Whether the corpus count under a form is evidence about *this* form.
 *
 * A spelling-level hit counted the letters. Where the lexicon holds a reading
 * for those letters and none of them is the one we built, the count belongs
 * to a different word — روی is *Rui*, مهره is *Mohre* — and a form must not
 * be ranked on it. The number stays on screen with its caveat; it is the
 * ranking that stops using it.
 *
 * **Case is folded first.** گفت is `Goft` to us and `goft` in the lexicon:
 * one word in two classes, not two words. Comparing case-sensitively would
 * sink the commonest word the screen has.
 *
 * **Narrow on purpose.** Where the lexicon knows no reading for the spelling
 * at all — `other_readings` empty — nothing *here* can tell رفتی, an inflected
 * form, from گفتار, which is exactly the word we built. Neither is touched by
 * this test. That half of S8 is answered separately, by `form.inflection`,
 * which asks the inflection analyser rather than the attestation record; see
 * {@link ranked}.
 */
function ours(form: BuiltForm): boolean {
  const found = form.attestation;
  if (!found || found.level !== "spelling") return true;
  // A function word's letters are never this form's evidence, whatever the
  // case-folded reading says: *Keh* is که, and که is the conjunction.
  if (found.function_word) return false;
  if (found.other_readings.length === 0) return true;
  const mine = form.form_latin.toLowerCase();
  return found.other_readings.some((one) => one.toLowerCase() === mine);
}

/**
 * Written, written-as-another-word, not written, or never asked.
 *
 * Four answers, not three. *The corpus has these letters and reads them as a
 * different word* is weaker than evidence and stronger than none, so it sits
 * between them rather than being folded into either.
 */
function standing(form: BuiltForm): number {
  if (!form.attestation) return 3;
  if (form.attestation.level === "none") return 2;
  return ours(form) ? 0 : 1;
}

function ranked(forms: BuiltForm[]): BuiltForm[] {
  return [...forms].sort((a, b) => {
    // **How well built, then what the corpus says, then its texts** — the
    // whole of `order` in murfulu/scoring/score.py, before any older
    // tie-breaker, so the two sides agree (the review of 2026-11-21).
    const scored = buildOrder(a) - buildOrder(b);
    if (scored !== 0) return scored;
    if (hasValues(a) && hasValues(b)) {
      const texts = (b.score?.texts ?? 0) - (a.score?.texts ?? 0);
      if (texts !== 0) return texts;
    }
    const known = standing(a) - standing(b);
    if (known !== 0) return known;
    // Whether the letters also read as an inflection of a word the dictionary
    // already holds — رفتی is "you went" before it is anything we built.
    //
    // **This closes the second half of S8, on 2026-08-17.** `ours` above stops
    // a count belonging to another *reading* from ranking a form. What was
    // left had no fix in the fields the screen holds: where the lexicon knows
    // no reading for a spelling at all, nothing separated رفتی from گفتار, and
    // both are unlinked. The API asks the inflection analyser, which is the
    // only thing that can separate them.
    //
    // It sits above the count and below the evidence level, because the
    // complaint is exactly that a count which may not be this word's outranks
    // everything else. Measured on رفتن at two steps: **seven of the top
    // twenty read as inflections before this, and none does now.** رفتار moves
    // 13 → 10, روش 16 → 13, رونده 21 → 14; رفتی 12 → 57.
    //
    // Sunk, never hidden, and the row says which kind it is — 95.6% of them
    // are spelled by a derivational rule too, so the letters cannot settle it.
    const inflectedA = a.inflection ? 1 : 0;
    const inflectedB = b.inflection ? 1 : 0;
    if (inflectedA !== inflectedB) return inflectedA - inflectedB;
    const counted =
      (b.attestation?.doc_count ?? 0) - (a.attestation?.doc_count ?? 0);
    if (counted !== 0) return counted;
    // How often the rules on the way here produce words the corpus has. This
    // is what orders a deep answer: at three steps everything below is either
    // flat or silent, and this is the only part of the score that can speak
    // about a word standing on invented ground. هماندیشنده sat at 10,551 of
    // 17,717 before it existed.
    //
    // **`_ranked` in murfulu/api/generate.py has to say the same thing.** A
    // deep answer is ranked and paged there, because 39 MB cannot be sorted in
    // a browser; steps 1 and 2 still ask for every form and are sorted here.
    // The two are kept in step by hand, and a difference between them shows up
    // as a page whose contents and whose order disagree.
    const madeA = a.realisation?.median;
    const madeB = b.realisation?.median;
    if (madeA !== undefined && madeB !== undefined && madeA !== madeB) {
      return madeB - madeA;
    }
    // false sinks; true and "not checked" (null) rank alike, because an
    // unchecked chain is not a broken one.
    //
    // **It used to come before the line above, and the project lead swapped
    // them on 2026-08-17.** Grounding is wrong about a whole family of words:
    // بازگوینده is in the corpus and this marks it as standing on air, because
    // the step in between is the *infinitive* of a prefixed verb and the poets
    // wrote *they retold* rather than *to retell*. A stepping stone missing
    // for that reason says nothing about the destination. It still ranks, one
    // place lower; what it no longer does is outrank a measure that is not
    // wrong about words we can prove are real. هماندیشنده: 676 → 189.
    const sunkA = a.base_attested === false ? 1 : 0;
    const sunkB = b.base_attested === false ? 1 : 0;
    if (sunkA !== sunkB) return sunkA - sunkB;
    const linked =
      (a.attestation ? RANK[a.attestation.level] : 3) -
      (b.attestation ? RANK[b.attestation.level] : 3);
    if (linked !== 0) return linked;
    // The last tie-breaker: semantic typicality, where both sides have one.
    // Unmeasured never loses to measured-low — a missing centroid says
    // nothing about the word — so it only orders forms that both carry it.
    const semA = a.semantic?.typicality;
    const semB = b.semantic?.typicality;
    if (semA !== undefined && semB !== undefined && semA !== semB) {
      return (semB ?? 0) - (semA ?? 0);
    }
    return a.form_latin.localeCompare(b.form_latin);
  });
}

/**
 * How many rows the table starts with.
 *
 * Fifty is a page a reader can scan, and the table's rows are a line or two
 * high, where the old cards were four. Nothing is hidden: the count of what
 * is held back is on the button that shows it (measured in 2026-08: بلند at
 * depth 2 rendered 3,185 rows and 588,102px of page at 375px when every form
 * was on screen at once).
 */
export const FIRST = 50;

/** The table's order: the score's, a count's, or the alphabet's. */
function sorted(forms: BuiltForm[], by: SortKey): BuiltForm[] {
  const best = ranked(forms);
  if (by === "build") return best;
  const place = new Map(best.map((form, at) => [form, at]));
  return [...best].sort((a, b) =>
    by === "texts"
      ? creditedTexts(b) - creditedTexts(a) || place.get(a)! - place.get(b)!
      : a.form_fa.localeCompare(b.form_fa, "fa") ||
        a.form_latin.localeCompare(b.form_latin),
  );
}

/** How many words each class has, biggest first: the tabs' order. */
function classCounts(forms: BuiltForm[]): [string, number][] {
  const counts = new Map<string, number>();
  for (const form of forms) {
    counts.set(form.word_class, (counts.get(form.word_class) ?? 0) + 1);
  }
  return [...counts].sort((a, b) => b[1] - a[1]);
}

function startsOn(form: BuiltForm, stem: string): boolean {
  return form.paths.some((steps) => steps[0]?.applied_to === stem);
}

export function Build() {
  const [params, setParams] = useSearchParams();
  const wanted = params.get("word") ?? "";
  const depth = Number(params.get("depth") ?? "2");

  const [built, setBuilt] = useState<Generated | null>(null);
  const [classes, setClasses] = useState<WordClass[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    document.title = `${SCREEN.title} — مورفولو`;
    const stop = new AbortController();
    wordClasses(stop.signal)
      .then(setClasses)
      .catch(() => setClasses([]));
    return () => stop.abort();
  }, []);

  useEffect(() => {
    if (!wanted) {
      setBuilt(null);
      setError(null);
      // The request this replaces was cancelled and will not clear it itself.
      setBusy(false);
      return;
    }
    const stop = new AbortController();
    setBusy(true);
    setError(null);
    generate(wanted, depth, stop.signal, depth >= DEEP ? DEEP_LIMIT : 0)
      .then(setBuilt)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError")
          return;
        setBuilt(null);
        setError(
          reason instanceof ApiError
            ? reason
            : new ApiError("unreachable", 0, String(reason)),
        );
      })
      // **Only the request that is still the current one may say the wait is
      // over.** A change of word or of depth cancels the request before it, and a
      // cancelled request settles too: its `finally` used to clear `busy`
      // although the request that replaced it had only just started, so the
      // button read as ready while an answer was on its way. In development
      // that was every first load, because strict mode runs an effect twice.
      .finally(() => {
        if (!stop.signal.aborted) setBusy(false);
      });
    return () => stop.abort();
  }, [wanted, depth]);

  const run = useCallback(
    (word: string, steps: number) => {
      setParams(word ? { word, depth: String(steps) } : {});
    },
    [setParams],
  );

  // What the screen as a whole is about, so the button in the corner is never
  // about nothing. A single word gets its own button on its own row.
  useSubject(
    wanted
      ? {
          target_type: "derivation",
          target_id: wanted,
          label: `ساختِ ${wanted}`,
          corpus_version: built?.corpus_version ?? null,
          context: { built_from: wanted, depth },
        }
      : null,
  );

  /**
   * What a group's heading says: the project's own term, the traditional one,
   * and the one line explaining the class.
   *
   * **It used to be the traditional term flat**, so the screen said اسم مصدر
   * where FRONTEND.md says کارنام is primary — the interface labelling its own
   * output in the vocabulary the project replaces. S3. The strings all come
   * from `/rules`; nothing Persian is written here.
   *
   * **Returned as data rather than as a rendered `Term`.** The heading is now
   * the control that opens the group, and `Term` is a button — a button inside
   * a button is invalid and a keyboard cannot reach the inner one. Group.tsx
   * writes the explanation out instead, which is also where a reader choosing
   * between eight classes actually needs it.
   *
   * An older API that serves neither field still gets a heading: the machine
   * id in Latin, which is what it did before any of this existed.
   */
  /**
   * How many of a reading's words start on one stem.
   *
   * Counted from the first step of each form's first route, which is where a
   * chain names its base. Not sent by the API as a figure — it is derived, so
   * it cannot disagree with the forms actually listed.
   */
  /**
   * Which class is open, as `reading:class`, and whether it is showing all of
   * its words. One at a time: the grid is the reader's place to stand, and two
   * open classes put it back where it was.
   */
  // The table's choices: which class, which scores, in the corpus or not, and
  // in what order. One set for the screen; a word read two ways shows two
  // tables, and the same choice applies to both.
  const [wordClass, setWordClass] = useState<string>("all");
  const [range, setRange] = useState("all");
  const [inCorpus, setInCorpus] = useState("all");
  // **Built first** by default (DECISIONS 2026-11-21): the reader looks for
  // the best-made words whether or not the poets used them, and the corpus
  // column says which are known.
  const [sortBy, setSortBy] = useState<SortKey>("build");
  // All words, or only the candidates for new ones: not in the corpus under
  // this reading, best-built first.
  const [view, setView] = useState<"all" | "new">("all");
  const [whole, setWhole] = useState(false);
  const choose =
    <T,>(set: (value: T) => void) =>
    (value: T) => {
      set(value);
      setWhole(false);
    };

  const builtOn = (reading: Generated["readings"][number], stem: string) =>
    reading.forms.filter((one) => startsOn(one, stem)).length;

  /**
   * Which stems are showing, per reading, as `reading → stems`.
   *
   * **Absent means all of them**, which is what a reader arriving sees: the
   * answer is not narrowed until they narrow it.
   */
  const [stems, setStems] = useState<Record<string, string[]>>({});

  const showing = (reading: Generated["readings"][number]) =>
    stems[reading.latin] ?? reading.built_from.map((one) => one.latin);

  const toggleStem = (reading: Generated["readings"][number], stem: string) => {
    const now = showing(reading);
    const next = now.includes(stem)
      ? now.filter((one) => one !== stem)
      : [...now, stem];
    // Never nothing. Turning the last stem off would empty the screen and say
    // nothing about why, so it stays on.
    if (!next.length) return;
    setStems({ ...stems, [reading.latin]: next });
    setWhole(false);
  };

  /**
   * A reading's words, narrowed to the stems that are showing.
   *
   * Narrowed **before** grouping, so a class tile counts what the reader can
   * actually see. Counting the whole answer under a filter would put a number
   * on a tile that disagrees with its own list.
   */
  const shownForms = (reading: Generated["readings"][number]) => {
    const on = showing(reading);
    if (on.length === reading.built_from.length) return reading.forms;
    return reading.forms.filter((form) =>
      on.some((stem) => startsOn(form, stem)),
    );
  };

  const classOf = (wordClass: string) => {
    const found = classes.find((one) => one.name === wordClass);
    if (!found?.label_fa) return undefined;
    return {
      name: found.label_fa,
      explanation: found.explanation_fa,
      // Not repeated when the heading is already the traditional term — which
      // is the vocative, the one class with no coined term of its own.
      traditional: found.label_is_traditional
        ? undefined
        : (found.traditional_fa ?? undefined),
    };
  };

  return (
    <article className={styles.screen}>
      <h1>{SCREEN.title}</h1>
      <p className={styles.purpose}>{SCREEN.purpose}</p>

      <WordInput
        value={wanted}
        depth={depth}
        depths={DEPTHS}
        busy={busy}
        onBuild={run}
      />

      {error ? (
        <p className={styles.trouble} role="status">
          {error.trouble === "missing"
            ? notFound("نمی‌دانیم پایه‌اش چیست و نمی‌توانیم از آن واژه بسازیم.")
            : "سرور جواب نداد. کمی بعد دوباره امتحان کنید."}
        </p>
      ) : null}

      {busy && !built && !error ? <Waiting /> : null}

      {built?.readings.map((reading) => (
        <section
          key={reading.latin}
          className={styles.reading}
          aria-labelledby={`reading-${reading.latin}`}
        >
          {/* **Said as a sentence.** It read «از raftan ۵۹۴ واژه»: a Latin
              word and a bare number, and the project lead asked on 2026-11-20
              why it was so cryptic. The word is named in its own script, the
              number says what it counts, and the reading stays beside it,
              small, because a word read two ways — بلند is Baland and boland —
              has one of these per reading and the Latin is what tells them
              apart. */}
          <h2 id={`reading-${reading.latin}`} className={styles.readingTitle}>
            <span>
              از «{reading.spelling_fa_marked ?? reading.spelling_fa}» <Num value={reading.count} /> واژه
              ساخته می‌شود
            </span>{" "}
            <Latin className={styles.readingLatin}>{reading.latin}</Latin>
          </h2>

          {/* **The two stems, named and counted.**
              This was «بر پایهٔ raft row» — two bare Latin words in grey, with
              nothing saying they are کاربن یک and کاربن دو, which is which, or
              that they are different starting points. The project is named
              after kārbon and this was how the screen showed it. The split was
              measured all along and thrown away: رفتن builds 16 words from رفت
              and 22 from رو. Raised by the project lead on 2026-08-18. */}
          {/* **And they filter.** A stem is where a word starts, so it is the
              other axis a reader wants beside the class — *show me only what
              گو makes*. Both are on when the screen opens; the class tiles
              below count what is showing, never the whole answer. */}
          <ul className={styles.stems}>
            {reading.built_from.map((base) => {
              const on = showing(reading).includes(base.latin);
              return (
                <li key={base.latin}>
                  <button
                    type="button"
                    className={styles.stem}
                    aria-pressed={on}
                    onClick={() => toggleStem(reading, base.latin)}
                  >
                    <span className={styles.stemLabel}>
                      {classOf(base.word_class)?.name ?? (
                        <Latin>{base.word_class}</Latin>
                      )}
                    </span>
                    <span className={styles.stemForms}>
                      <span className={styles.stemFa}>{base.fa}</span>
                      <Latin className={styles.stemLatin}>{base.latin}</Latin>
                      {/* «۱۵۷ واژه» alone left the reader to guess what was
                          counted; the project lead asked on 2026-11-20. */}
                      <span className={styles.stemCount}>
                        <Num value={builtOn(reading, base.latin)} /> واژه از این
                        بن ساخته می‌شود
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          {/* The dictionary's own doubt, which was being dropped. بلند is
              read two ways — Baland, flagged, and boland, clean — and the
              flagged one builds the longer list, so a reader who is not told
              takes the doubtful reading for the settled one. Said, never
              filtered on: 31.5% of the snapshot carries the flag, and a flag
              is a note to check rather than a verdict. */}
          {reading.needs_review ? (
            <p className={styles.doubted}>{NEEDS_REVIEW}</p>
          ) : null}

          {/* What the dictionary says this word means. Marked as the
              dictionary's. karbon cuts at 200 characters and 53.5% of v11's
              definitions are cut; the «…» marks those and not the rest.
              A مصدر never has one, so a verb shows nothing here. */}
          {reading.definition_fa ? (
            <p className={styles.definition}>
              <span className={styles.definitionLabel}>{FROM_LEXICON}</span>{" "}
              {reading.definition_fa}
              {wasCut(reading.definition_fa) ? "…" : ""}
            </p>
          ) : null}

          {/* A second pronunciation the dictionary itself lists. برنا is
              barnā and the same row also says bornā; the screen printed the
              first and never said the second existed, so a reader who hears
              bornā in the poem has no way to tell whether we know it.
              7,181 of 44,788 readings — 16.0% — carry one. Shown, never
              chosen between: which is right is not ours to say. */}
          {reading.latin_variants.length > 0 ? (
            <p className={styles.note}>
              {ALSO_WRITTEN}{" "}
              {reading.latin_variants.map((variant, index) => (
                <span key={variant}>
                  {index > 0 ? "، " : ""}
                  <Latin>{variant}</Latin>
                </span>
              ))}
            </p>
          ) : null}

          {reading.truncated ? (
            <p className={styles.note}>
              این فهرست کوتاه شده است و همهٔ واژه‌های ساخته‌شده را نشان نمی‌دهد.
            </p>
          ) : null}

          {/* A page is not the answer, and must never look like it. At three
              steps the answer runs to tens of thousands of واژه and the screen
              shows the strongest of them — so it says both numbers. */}
          {reading.has_more && reading.returned ? (
            <p className={styles.note}>
              از <Num value={reading.count} /> واژه‌ای که ساخته شد، اینجا{" "}
              <Num value={reading.returned} /> واژه را می‌بینید: آن‌هایی که
              بیشترین شاهد را دارند.
            </p>
          ) : null}

          {reading.count === 0 ? (
            <p className={styles.note}>
              هیچ دستوری روی این واژه کار نمی‌کند: {LEXICON} گونهٔ آن را ننوشته
              است.
            </p>
          ) : null}

          {reading.forms.length > 0 ? (
            <Table
              forms={shownForms(reading)}
              idPrefix={reading.latin}
              classOf={classOf}
              corpusVersion={built.corpus_version}
              wordClass={wordClass}
              onWordClass={choose(setWordClass)}
              range={range}
              onRange={choose(setRange)}
              view={view}
              onView={choose((next: "all" | "new") => {
                setView(next);
                if (next === "new") setSortBy("build");
              })}
              inCorpus={inCorpus}
              onInCorpus={choose(setInCorpus)}
              sortBy={sortBy}
              onSort={choose(setSortBy)}
              whole={whole}
              onWhole={() => setWhole(true)}
            />
          ) : null}
        </section>
      ))}

      {built ? (
        <p className={styles.version}>
          {built.corpus_version ? (
            <>
              شواهد از پیکرهٔ <Latin>{built.corpus_version}</Latin>.
            </>
          ) : (
            "پیکره در دسترس نبود، پس هیچ واژه‌ای سنجیده نشد."
          )}
        </p>
      ) : null}
    </article>
  );
}

interface ClassSaid {
  name: string;
  explanation?: string;
  traditional?: string;
}

/**
 * The words as one table: class tabs, filters, a head row that sorts, and the
 * rows. **Direction A, the project lead's choice of 2026-11-21**, from three
 * rendered drafts; it replaced the class tiles of 2026-08-18, which made a
 * reader open one class before seeing any word.
 *
 * Every word is on the table when it opens, best-built first. A class, a
 * build range and what the corpus says narrow it; nothing is removed from the
 * answer, and the line above the rows says how many are showing. **«واژه‌های
 * تازه»** (2026-11-21) shows only the candidates for new words — not in the
 * corpus under this reading — best-built first: the words the project looks
 * for, which the single score of the morning had sunk to the bottom.
 */
function Table({
  forms,
  idPrefix,
  classOf,
  corpusVersion,
  wordClass,
  onWordClass,
  range,
  onRange,
  view,
  onView,
  inCorpus,
  onInCorpus,
  sortBy,
  onSort,
  whole,
  onWhole,
}: {
  forms: BuiltForm[];
  idPrefix: string;
  classOf: (name: string) => ClassSaid | undefined;
  corpusVersion: string | null;
  wordClass: string;
  onWordClass: (name: string) => void;
  range: string;
  onRange: (key: string) => void;
  view: "all" | "new";
  onView: (view: "all" | "new") => void;
  inCorpus: string;
  onInCorpus: (key: string) => void;
  sortBy: SortKey;
  onSort: (key: SortKey) => void;
  whole: boolean;
  onWhole: () => void;
}) {
  const classes = classCounts(forms);
  // A class the stems no longer reach falls back to all, rather than showing
  // an empty table under a tab that is not there.
  const chosen = classes.some(([name]) => name === wordClass)
    ? wordClass
    : "all";
  const keepRange = BUILD_RANGES.find((one) => one.key === range)!;
  // The candidates view has its own corpus filter: not under this reading.
  const keepCorpus =
    view === "new"
      ? { keeps: isCandidate }
      : IN_CORPUS.find((one) => one.key === inCorpus)!;
  const kept = sorted(
    forms.filter(
      (form) =>
        (chosen === "all" || form.word_class === chosen) &&
        keepRange.keeps(form) &&
        keepCorpus.keeps(form),
    ),
    sortBy,
  );
  const rows = whole ? kept : kept.slice(0, FIRST);
  const held = kept.length - rows.length;
  const said = chosen === "all" ? undefined : classOf(chosen);
  const nameOf = (name: string) => classOf(name)?.name ?? <Latin>{name}</Latin>;
  const tabs: [string, number][] = [["all", forms.length], ...classes];
  const tabKeys = tabs.map(([name]) => name);

  const sortButton = (key: SortKey, label: string) => (
    <button
      type="button"
      className={styles.sort}
      aria-pressed={sortBy === key}
      onClick={() => onSort(key)}
    >
      {label}
      {sortBy === key ? <span aria-hidden="true">▾</span> : null}
    </button>
  );

  return (
    <div className={styles.table}>
      <fieldset className={styles.views}>
        <legend className="visually-hidden">کدام واژه‌ها</legend>
        {(
          [
            ["all", "همهٔ واژه‌ها"],
            ["new", "واژه‌های تازه"],
          ] as const
        ).map(([key, label]) => (
          <label key={key} className={styles.view}>
            <input
              type="radio"
              name={`view-${idPrefix}`}
              className="visually-hidden"
              checked={view === key}
              onChange={() => onView(key)}
            />
            {label}
          </label>
        ))}
      </fieldset>
      <div
        className={styles.tabs}
        role="tablist"
        aria-label="گونهٔ واژه"
        onKeyDown={(event) => {
          // The arrow keys move between the tabs, as a tablist promises; in a
          // right-to-left row the left arrow is the next one.
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
          onWordClass(tabKeys[to]!);
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
            // One tab stop for the row: the chosen tab.
            tabIndex={chosen === name ? 0 : -1}
            className={styles.tab}
            onClick={() => onWordClass(name)}
          >
            {name === "all" ? "همه" : nameOf(name)}
            <span className={styles.tabCount}>
              <Num value={count} />
            </span>
          </button>
        ))}
      </div>

      {said?.explanation ? (
        <p className={styles.classSays}>
          {said.explanation}
          {said.traditional ? (
            <span className={styles.classTraditional}>
              {" "}
              در دستور سنتی: {said.traditional}
            </span>
          ) : null}
        </p>
      ) : null}

      {view === "new" ? (
        <p className={styles.classSays}>{CANDIDATES_SAY}</p>
      ) : null}

      <div className={styles.tools}>
        <Chips
          legend="ساخت"
          info={<Info label="ساخت">{BUILD_SAYS}</Info>}
          options={BUILD_RANGES}
          value={range}
          onChange={onRange}
        />
        {view === "all" ? (
          <Chips
            legend="پیکره"
            info={<Info label="پیکره">{CORPUS_SAYS}</Info>}
            options={IN_CORPUS}
            value={inCorpus}
            onChange={onInCorpus}
          />
        ) : null}
        <div className={styles.phoneSort}>
          <span className={styles.sortLabel}>ترتیب</span>
          {sortButton("build", "ساخت")}
          {sortButton("texts", "شمار متن‌ها")}
          {sortButton("alpha", "الفبا")}
        </div>
        <span className={styles.shown} role="status">
          <Num value={kept.length} /> واژه
        </span>
      </div>

      <div className={styles.head}>
        {sortButton("alpha", "واژه")}
        <span>گونه</span>
        {sortButton("build", "ساخت")}
        {sortButton("texts", "در پیکره")}
        <span>وند</span>
        <span />
      </div>

      {rows.length ? (
        <div
          id={`words-${idPrefix}`}
          role="tabpanel"
          aria-labelledby={`tab-${idPrefix}-${chosen}`}
        >
          <ul className={styles.forms}>
            {rows.map((form) => (
              <FormRow
                key={`${form.form_latin}:${form.word_class}:${form.depth}`}
                form={form}
                className={nameOf(form.word_class)}
                corpusVersion={corpusVersion}
              />
            ))}
          </ul>
        </div>
      ) : (
        <p id={`words-${idPrefix}`} className={styles.empty}>
          با این گزینه‌ها هیچ واژه‌ای نمی‌ماند. یکی از آن‌ها را بردارید.
        </p>
      )}

      {held > 0 ? (
        <button type="button" className={styles.more} onClick={onWhole}>
          <Num value={held} /> واژهٔ دیگر را هم نشان بده
        </button>
      ) : null}

      <ScoreLegend corpusVersion={corpusVersion} />
    </div>
  );
}

/**
 * One filter as a row of chips, only one of which can be on.
 *
 * **Native radio buttons drawn as chips**, so the keyboard is the browser's:
 * one tab stop for the group, the arrow keys move the choice. Buttons with a
 * radio role were a tab stop each and ignored the arrows (the review of
 * 2026-11-21).
 */
export function Chips({
  legend,
  info = null,
  options,
  value,
  onChange,
}: {
  legend: string;
  /** What the filter's measure is, one press away. */
  info?: React.ReactNode;
  options: { key: string; label: string }[];
  value: string;
  onChange: (key: string) => void;
}) {
  const name = useId();
  return (
    <fieldset className={styles.filter}>
      <legend>
        {legend} {info}
      </legend>
      {options.map((one) => (
        <label key={one.key} className={styles.chip}>
          <input
            type="radio"
            name={name}
            className="visually-hidden"
            checked={value === one.key}
            onChange={() => onChange(one.key)}
          />
          {one.label}
        </label>
      ))}
    </fieldset>
  );
}
