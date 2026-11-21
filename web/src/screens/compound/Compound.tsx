/**
 * Compound words: what the grammar joins to a word, and who wrote which.
 *
 * **The first screen in this app to show a compound at all.** Sixteen rules
 * have licensed compounding since the rule pack was transcribed and nothing
 * ever called them, so a reader could see *soxanguy* named as an example and
 * never see one made.
 *
 * **What the screen shows is the attested list, and it says what it is not
 * showing.** One noun makes thousands and the corpus holds a fraction of a
 * percent — دل builds 4,652 and 220 were ever written — so the three counts
 * are printed beside every list. A list of forty is meaningless without the
 * number it came out of.
 *
 * **A row that may not be a compound is marked and sunk, never dropped.** دلم
 * carries 12,947 documents and is دل plus a possessive; دلبر carries 2,920 and
 * is a real compound the dictionary also holds. Both are shown, the difference
 * is on the row, and only the first sinks.
 */

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import {
  everyCompound,
  type CompoundReading,
  type Compounds,
} from "../../api/compound";
import { wordClasses, type WordClass } from "../../api/generate";
import { Latin } from "../../text/Latin";
import { Num } from "../../text/Num";
import {
  FROM_LEXICON,
  LEXICON,
  notFound,
  wasCut,
  wordGroup,
} from "../../text/lexicon";
import { SCREENS } from "../../shell/screens";
import { Suggest } from "../../suggest/Suggest";
import { wordSource } from "../../suggest/sources";
import { CompoundTable } from "./CompoundTable";
import styles from "./Compound.module.css";

const SCREEN = SCREENS.find((one) => one.path === "/compound")!;

/** Only words the rules build from: a compound needs a word that takes part. */
const BUILDS = wordSource({ builds: true });

/** Nouns that make compounds. Checked against the API, never guessed. */
const EXAMPLES = ["دل", "آب", "سر", "دست", "کار"];

/**
 * The first few words of the dictionary's definition, enough to tell two
 * entries apart on a button: «قلب و فؤاد» against «در همدان اِشَنَک را…».
 * A bracket at the very start is the source or the part of speech — آهن opens
 * «(از پهلوی آسین) گوهری کانی…» — and is skipped; then the text is cut at the
 * first full stop, semicolon, colon, bracket or comma.
 */
function gloss(definition: string | null | undefined, words = 4): string {
  const opening = (definition ?? "").replace(/^(\s*\([^)]*\))+/, "");
  const first = opening.split(/[.؛:()،]/)[0]?.trim() ?? "";
  const said = first.split(/\s+/).filter(Boolean);
  return said.length > words ? `${said.slice(0, words).join(" ")}…` : said.join(" ");
}

/** One entry, in the address and as a key: karbon's row id where there is one. */
function entryOf(reading: CompoundReading): string {
  return reading.entry != null
    ? String(reading.entry)
    : `${reading.spelling_fa}:${reading.latin}`;
}

/**
 * Why the first entry is first, from the number of each entry's words the
 * dictionary and the corpus both confirm (`confirmed`, ranked by the API).
 *
 * - `lead`: the first has more than any other.
 * - `tied`: the first few have the same number, above zero — شیر's lion and
 *   milk build the same Latin, so nothing measured separates them, though
 *   both stand above an entry with none.
 * - `none`: no entry has any; the order is the dictionary's.
 *
 * Null where it was not measured (an older API, or a corpus that did not
 * answer): a sentence about evidence nobody looked at would be false.
 */
type Why =
  | { kind: "lead"; count: number }
  | { kind: "tied"; count: number }
  | { kind: "none" };

function whyFirst(readings: CompoundReading[]): Why | null {
  if (readings.some((one) => one.confirmed == null)) return null;
  const [first, second] = readings.map((one) => one.confirmed as number);
  if (first === undefined || second === undefined) return null;
  if (first > second) return { kind: "lead", count: first };
  if (first > 0) return { kind: "tied", count: first };
  return { kind: "none" };
}

export function Compound() {
  const [params, setParams] = useSearchParams();
  const word = params.get("word") ?? "";
  // **Which of a spelling's entries is showing.** دل is four entries in the
  // dictionary — the heart, a tree, an ailment and an adjective — and the page
  // stacked all four, the tree first, so the reader met «دل Dal» and the
  // heart's own words three cards down. One entry at a time now, the
  // best-evidenced first, with the others one tap away and in the address.
  const chosen = params.get("entry");
  const [draft, setDraft] = useState(word);
  // In an effect, not during the render: the router navigates inside a
  // transition and a render-time adjustment can be discarded when the
  // transition replays. Measured on the other two search boxes.
  useEffect(() => setDraft(word), [word]);
  const [found, setFound] = useState<Compounds | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  // **What tells two identical-looking rows apart.** V-078 and V-079 both join
  // a noun to a present stem and both write دلبر; one means the doer and the
  // other the done-to, and `compounding.py` keeps both on purpose because that
  // is information. The screen printed only the rule id, so the reader saw the
  // same word twice with the same evidence and no way to tell why. The class
  // is on every row already; this is the Persian for it, from the rule pack.
  const [classes, setClasses] = useState<WordClass[]>([]);
  useEffect(() => {
    document.title = `${SCREEN.title} — مورفولو`;
  }, []);

  useEffect(() => {
    if (!word) return;
    const stop = new AbortController();
    wordClasses(stop.signal)
      .then(setClasses)
      .catch(() => setClasses([]));
    return () => stop.abort();
  }, [word]);

  useEffect(() => {
    if (!word) {
      setFound(null);
      return;
    }
    const stop = new AbortController();
    setError(null);
    // The best thousand, ranked best built first by the API, and every row
    // the corpus has; the table filters.
    everyCompound(word, stop.signal)
      .then(setFound)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setFound(null);
        setError(
          reason instanceof ApiError
            ? reason
            : new ApiError("unreachable", 0, String(reason)),
        );
      });
    return () => stop.abort();
  }, [word]);

  const run = useCallback(
    (next: string) => setParams(next ? { word: next } : {}),
    [setParams],
  );

  const readings = found?.readings ?? [];
  const shown = readings.find((one) => entryOf(one) === chosen) ?? readings[0];
  const why = whyFirst(readings);
  const oneSpelling = new Set(readings.map((one) => one.spelling_fa)).size === 1;

  /** Class ids as the reader's own words: `karnam` → «کارنام». */
  const saying = (names: string[]) => {
    const said = names.map(
      (name) => classes.find((one) => one.name === name)?.label_fa ?? name,
    );
    return said.length ? said.join(" یا ") : "چیز دیگری";
  };

  return (
    <article className={styles.screen}>
      <h1>{SCREEN.title}</h1>
      <p className={styles.purpose}>{SCREEN.purpose}</p>

      <form
        className={styles.box}
        onSubmit={(event) => {
          event.preventDefault();
          run(draft.trim());
        }}
      >
        <label className={styles.label} htmlFor="compound-word">
          واژه‌ای بنویسید
        </label>
        <div className={styles.row}>
          <Suggest
            id="compound-word"
            className={styles.input}
            dir="auto"
            placeholder="دل"
            value={draft}
            onChange={setDraft}
            source={BUILDS}
            listLabel="واژه‌هایی که می‌شود با آن‌ها ترکیب ساخت"
            onPick={(one) => {
              setDraft(one.word.value);
              run(one.word.value);
            }}
          />
          <button className={styles.submit} type="submit">
            بچسبان
          </button>
        </div>
        {/* Five, not one — each checked against the running API. */}
        {!word ? (
          <p className={styles.examples}>
            <span className={styles.examplesSays}>برای نمونه:</span>
            {EXAMPLES.map((one) => (
              <button
                key={one}
                type="button"
                className={styles.example}
                onClick={() => {
                  setDraft(one);
                  run(one);
                }}
              >
                {one}
              </button>
            ))}
          </p>
        ) : null}
      </form>

      {error ? (
        <p className={styles.trouble} role="status">
          {error.trouble === "missing"
            ? notFound("نمی‌توانیم آن را با واژهٔ دیگری ترکیب کنیم.")
            : "سرور جواب نداد. کمی بعد دوباره امتحان کنید."}
        </p>
      ) : null}

      {readings.length > 1 && shown ? (
        <div
          className={styles.entries}
          role="group"
          aria-label={`مدخل‌های «${oneSpelling ? shown.spelling_fa : word}»`}
        >
          <p className={styles.entriesSay}>
            {/* One spelling, several entries — دل — or a Latin that matched
                entries of different spellings: *Allākolang* is الاکلنگ and
                الا کلنگ, one entry each, and «الاکلنگ ۲ مدخل دارد» was false. */}
            {oneSpelling ? (
              <>
                «{shown.spelling_fa}» در {LEXICON} <Num value={readings.length} />{" "}
                مدخل جدا دارد.
              </>
            ) : (
              <>
                برای «{word}» در {LEXICON} <Num value={readings.length} /> مدخل
                پیدا شد.
              </>
            )}{" "}
            {why?.kind === "lead" ? (
              <>
                اول آن یکی آمده که <Num value={why.count} /> واژهٔ ساخته از آن هم
                در همین واژه‌نامه هست و هم در پیکره.
              </>
            ) : why?.kind === "tied" ? (
              <>
                اول آن‌هایی آمده‌اند که از هر کدام <Num value={why.count} /> واژهٔ
                ساخته هم در همین واژه‌نامه هست و هم در پیکره؛ میان آن‌ها پیکره
                داوری نمی‌کند.
              </>
            ) : why?.kind === "none" ? (
              "هیچ‌یک از واژه‌های ساخته از این مدخل‌ها هم در واژه‌نامه و هم در پیکره نیامده، پس ترتیبشان همان ترتیب واژه‌نامه است."
            ) : null}
          </p>
          <p className={styles.showing}>
            {readings.map((one) => (
              <button
                key={entryOf(one)}
                type="button"
                className={styles.pick}
                aria-pressed={one === shown}
                onClick={() =>
                  setParams({ word, entry: entryOf(one) }, { replace: true })
                }
              >
                {oneSpelling ? null : (
                  <span className={styles.entrySpelling}>{one.spelling_fa}</span>
                )}
                <Latin>{one.latin}</Latin>
                {gloss(one.definition_fa) ? (
                  <span className={styles.gloss}>{gloss(one.definition_fa)}</span>
                ) : null}
              </button>
            ))}
          </p>
        </div>
      ) : null}

      {(shown ? [shown] : []).map((reading) => (
        <section
          key={entryOf(reading)}
          className={styles.reading}
          aria-labelledby={`reading-${reading.latin}`}
        >
          <h2 id={`reading-${reading.latin}`} className={styles.readingTitle}>
            {reading.spelling_fa} <Latin>{reading.latin}</Latin>
            {wordGroup(reading) ? (
              <span className={styles.category}>{wordGroup(reading)}</span>
            ) : null}
          </h2>

          {/* The dictionary's words, as the build screen shows them: with two
              entries a tap apart, this is what says which one is open. */}
          {reading.definition_fa ? (
            <p className={styles.definition}>
              <span className={styles.definitionLabel}>{FROM_LEXICON}</span>{" "}
              {reading.definition_fa}
              {wasCut(reading.definition_fa) ? "…" : ""}
            </p>
          ) : null}

          {/* **A zero gets a reason, not a count.** «دستور زبان می‌تواند ۰
              ترکیب بسازد؛ ۰ تای آن در پیکره آمده است. برای این شمار، ۱٬۷۴۱
              واژهٔ دیگر … آزموده شد» is three figures about nothing, and the
              reader's actual question — why nothing? — went unanswered.
              Reported for کار on 2026-08-18. */}
          {reading.built > 0 ? (
            <p className={styles.counts}>
              دستورها با این واژه <Num value={reading.built} /> ترکیب می‌سازند و{" "}
              <Num value={reading.attested} /> تای آن‌ها در پیکره آمده است. برای
              این کار، <Num value={reading.partners_tried} /> واژهٔ دیگر را در
              نیمهٔ دوم ترکیب امتحان کردیم.
            </p>
          ) : (
            <p className={styles.counts}>
              با این واژه هیچ ترکیبی ساخته نشد.
            </p>
          )}

          {Object.keys(reading.skipped).map((kind) => (
            <p key={kind} className={styles.skipped}>
              {/* **Said with an example, not with a term.** It read «الگوهای
                  دو-بُنی بر این واژه کار نمی‌کنند: آنها هر دو بُن را از یک
                  کارواژه می‌گیرند» — three words a reader has to already know
                  (الگوی دو-بُنی، بُن، کارواژه) to learn one fact. The project
                  lead did not understand it on 2026-08-18, which settles it.
                  «گفت‌وگو» carries the whole idea: both halves out of گفتن. */}
              {kind === "template"
                ? `ده دستور از دستورهای ترکیب هر دو نیمهٔ واژه را از یک کارواژه می‌گیرند، مثل «گفت‌وگو» که هر دو نیمه‌اش از «گفتن» است. «${reading.spelling_fa}» کارواژه نیست، پس این ده دستور اینجا به کار نمی‌آیند${
                    reading.built > 0 ? "؛ آنچه می‌بینید کار شش دستور دیگر است" : ""
                  }.`
                : /* **The other six, and why they can refuse a perfectly
                     ordinary noun.** They all want a نام in front, and the
                     source grammar counts a word like کار — اسم معنی — as a
                     کارنام. Nothing is broken; the front slot's meaning is an
                     open question with the linguist (L18). Both class names
                     come from the rule pack, never from here. */
                  `شش دستور دیگر در نیمهٔ نخست ${saying(reading.slot_wants)} می‌خواهند، ولی «${reading.spelling_fa}» در دستگاه دستوری ${saying(reading.word_classes)} است. پس هیچ‌کدام روی آن کار نمی‌کنند. اینکه نیمهٔ نخست باید ${saying(reading.word_classes)} را هم بپذیرد یا نه، هنوز پرسشی بی‌پاسخ است.`}
            </p>
          ))}

          {/* **The list is the build screen's table** (2026-11-21): its view
              switch replaces the two buttons «آنچه در پیکره آمده» and «همه، با
              واژه‌های نو», and its «پیکره» filter keeps what the first one
              kept. The table opens on every word, best built first. */}
          {reading.pairings.length > 0 ? (
            <>
              {(reading.count ?? reading.pairings.length) > reading.pairings.length ? (
                <p className={styles.skipped}>
                  از <Num value={reading.count ?? reading.built} /> ترکیب،{" "}
                  <Num value={reading.pairings.length} /> تا را نشان می‌دهیم:
                  خوش‌ساخت‌ترین‌ها و همهٔ آن‌هایی که در پیکره آمده‌اند.
                </p>
              ) : null}
              <CompoundTable
                key={entryOf(reading)}
                rows={reading.pairings}
                classes={classes}
                idPrefix={`compound-${entryOf(reading)}`}
              />
            </>
          ) : null}
        </section>
      ))}
    </article>
  );
}
