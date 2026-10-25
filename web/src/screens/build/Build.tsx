/**
 * The build screen: a word in, everything the grammar can make from it out.
 *
 * **Grouped by what each result *is*.** A reader looking for a noun should not
 * have to read past forty adjectives. The group's name is what traditional
 * grammar calls the class — اسم, صفت, اسم مصدر — served from the rule pack
 * rather than written here. The project's own coined terms (کارنام, کاربن دو)
 * are not in the data at all, so nothing shows them; see OPEN_QUESTIONS S3.
 *
 * **Sorted by evidence, never by depth.** A three-step form is not worse for
 * being three steps — *Guyāyi* is two steps and entirely ordinary. What ranks
 * a form is what the corpus says about it.
 *
 * **Three steps are offered, and a deep answer is a page.** One verb at three
 * steps builds tens of thousands of forms, of which fifty are words the corpus
 * has — so the route ranks before it pages and the screen asks for the best six
 * hundred, saying plainly how many of how many it is showing. See {@link
 * DEPTHS} for why this waited on the ranking rather than on the paging.
 */

import { useCallback, useEffect, useState } from "react";
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
import { ClassTile, ClassWords } from "./Group";
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

function grouped(forms: BuiltForm[]): Map<string, BuiltForm[]> {
  const groups = new Map<string, BuiltForm[]>();
  for (const form of ranked(forms)) {
    const found = groups.get(form.word_class);
    if (found) found.push(form);
    else groups.set(form.word_class, [form]);
  }
  return groups;
}

/**
 * Whether any route to this form starts on this stem.
 *
 * *Any*, not the first: a word the grammar can reach two ways belongs to both
 * starting points. Measured on گفتن — 16 words from گفت, 22 from گو, and **no
 * word reachable from both** — so on this data the two are a clean split and
 * the counts add up to the whole.
 */
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
      .finally(() => setBusy(false));
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
  const [openClass, setOpenClass] = useState<string | null>(null);
  const [whole, setWhole] = useState(false);

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
    setOpenClass(null);
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
            ? notFound("نمی‌دانیم از چه ساخته شده است.")
            : "پاسخی از سرور نرسید. کمی بعد دوباره بیازمایید."}
        </p>
      ) : null}

      {built?.readings.map((reading) => (
        <section
          key={reading.latin}
          className={styles.reading}
          aria-labelledby={`reading-${reading.latin}`}
        >
          <h2 id={`reading-${reading.latin}`} className={styles.readingTitle}>
            از <Latin>{reading.latin}</Latin>
            <span className={styles.readingCount}>
              <Num value={reading.count} /> واژه
            </span>
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
                      <span className={styles.stemCount}>
                        <Num value={builtOn(reading, base.latin)} /> واژه
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
              این فهرست کوتاه شده است؛ همهٔ آنچه ساخته شد نشان داده نشده.
            </p>
          ) : null}

          {/* A page is not the answer, and must never look like it. At three
              steps the answer runs to tens of thousands of واژه and the screen
              shows the strongest of them — so it says both numbers. */}
          {reading.has_more && reading.returned ? (
            <p className={styles.note}>
              نیرومندترین <Num value={reading.returned} /> واژه از{" "}
              <Num value={reading.count} /> واژه‌ای که ساخته شد نشان داده شده
              است، به ترتیب شواهد.
            </p>
          ) : null}

          {reading.count === 0 ? (
            <p className={styles.note}>
              هیچ دستوری بر این واژه کار نمی‌کند. گونهٔ آن در {LEXICON} نگاشته
              نشده است.
            </p>
          ) : null}

          {/* Closed until asked for. Eight classes is a thing a reader can
              choose from; sixteen open groups of twenty rows is not. */}
          {/* The classes, then the words of whichever one is open — apart,
              so choosing a class never pushes the others off the screen. */}
          <div className={styles.groups}>
            {[...grouped(shownForms(reading))].map(([wordClass, forms]) => {
              const said = classOf(wordClass);
              const key = `${reading.latin}:${wordClass}`;
              return (
                <ClassTile
                  key={wordClass}
                  name={said?.name ?? <Latin>{wordClass}</Latin>}
                  explanation={said?.explanation}
                  traditional={said?.traditional}
                  count={forms.length}
                  open={openClass === key}
                  panelId={`words-${key}`}
                  onToggle={() => {
                    setWhole(false);
                    setOpenClass(openClass === key ? null : key);
                  }}
                />
              );
            })}
          </div>

          {[...grouped(shownForms(reading))]
            .filter(([wordClass]) => openClass === `${reading.latin}:${wordClass}`)
            .map(([wordClass, forms]) => (
              <ClassWords
                key={wordClass}
                forms={forms}
                corpusVersion={built.corpus_version}
                panelId={`words-${reading.latin}:${wordClass}`}
                whole={whole}
                onWhole={() => setWhole(true)}
              />
            ))}
        </section>
      ))}

      {built ? (
        <p className={styles.deeper}>
          گام سوم و پس از آن هنوز در دسترس نیست: پاسخ آن برای یک واژه بیش از
          بیست مگابایت است و باید صفحه‌بندی شود.
        </p>
      ) : null}

      {built ? (
        <p className={styles.version}>
          {built.corpus_version ? (
            <>
              شواهد از پیکرهٔ <Latin>{built.corpus_version}</Latin>.
            </>
          ) : (
            "پیکره‌ای در دسترس نبود، پس هیچ واژه‌ای سنجیده نشده است."
          )}
        </p>
      ) : null}
    </article>
  );
}
